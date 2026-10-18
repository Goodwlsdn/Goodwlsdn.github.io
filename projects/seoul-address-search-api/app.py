"""Read-only Seoul search/geocoding API. GeoJSON coordinates: [longitude, latitude]."""
import json
import os
import re
import sqlite3
import zlib
import asyncio
import logging
import time
import uuid
from functools import lru_cache
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pyproj import Transformer
from shapely import from_wkb
from shapely.geometry import mapping, Point
from shapely.ops import transform
from access_logs import init_logs,write_log,timestamp

ROOT = Path(__file__).resolve().parent
DB = Path(os.environ.get('SEOUL_DB',str(ROOT/'seoul.sqlite'))).resolve()
init_logs(DB)
TR = Transformer.from_crs(5179,4326,always_xy=True)
TO_SOURCE = Transformer.from_crs(4326,5179,always_xy=True)
Kind = Literal['province','district','dong','road','building','complex','parcel']
app = FastAPI(title='서울 주소 검색 · 지오코딩 API',version='1.0.0',
    description='서울 시·구·법정동 폴리곤, 도로 선, 건물 폴리곤을 검색합니다. 모든 응답 좌표는 EPSG:4326 [경도, 위도]입니다.')
app.add_middleware(CORSMiddleware,allow_origins=['*'],allow_methods=['GET'],allow_headers=['*'])

@app.middleware('http')
async def log_api_request(request,call_next):
    if request.url.path in ('/','/health','/docs','/docs/oauth2-redirect','/redoc','/openapi.json'):
        return await call_next(request)
    started=time.perf_counter();requested_at=timestamp();request_id=uuid.uuid4().hex
    status=500;error=None
    try:
        response=await call_next(request)
        status=response.status_code
        response.headers['X-Request-ID']=request_id
        return response
    except Exception as exc:
        error=type(exc).__name__
        raise
    finally:
        duration=round((time.perf_counter()-started)*1000,3)
        if status>=400 and error is None:error=f'HTTP_{status}'
        params=json.dumps(list(request.query_params.multi_items()),ensure_ascii=False)
        count=getattr(request.state,'result_count',None)
        result_status='error' if status>=400 else ('found' if count else 'no_results') if count is not None else None
        if status>=400:count=0
        entry=(request_id,requested_at,request.method,request.url.path,request.query_params.get('q'),
               params,status,int(200<=status<400),duration,error,count,result_status)
        try:
            await asyncio.to_thread(write_log,DB,entry)
        except Exception:
            logging.getLogger('uvicorn.error').exception('Failed to record API request %s',request_id)

@app.get('/reverse')
def reverse(longitude:float=Query(ge=-180,le=180),latitude:float=Query(ge=-90,le=90),request:Request=None):
    x,y=TO_SOURCE.transform(longitude,latitude)
    point=Point(x,y)
    with connect() as c:
        candidates=c.execute('''SELECT f.* FROM feature_bounds b JOIN features f ON f.id=b.id
          WHERE b.min_x<=? AND b.max_x>=? AND b.min_y<=? AND b.max_y>=?''',(x,x,y,y)).fetchall()
    hits=[r for r in candidates if from_wkb(zlib.decompress(r['geom'])).covers(point)]
    priority={'complex':0,'building':1,'parcel':2,'dong':3,'district':4,'province':5}
    hits.sort(key=lambda r:(priority[r['kind']],from_wkb(zlib.decompress(r['geom'])).area,r['id']))
    results=[feature(r,False)['properties'] for r in hits]
    best=results[0] if results else None
    parcels=[r for r in results if r['kind']=='parcel']
    parcel_roads=[]
    with connect() as c:
        for parcel in parcels:
            parcel_roads.extend(r[0] for r in c.execute('SELECT address FROM parcel_road_addresses WHERE pnu=? ORDER BY address',(parcel['code'],)))
    jibun_addresses=list(dict.fromkeys(r['address'] for r in parcels if r['address']))
    selected=next((r for r in results if r['kind'] in ('complex','building') and r['address']),None)
    if selected:
        road_addresses=[selected['address']]
        road_selection=selected['kind']
    else:
        candidates=sorted(set([r['attributes']['road_address'] for r in parcels if r['attributes'].get('road_address')]+parcel_roads))
        road_addresses=candidates if len(candidates)==1 else []
        road_selection='parcel_unique' if len(candidates)==1 else ('parcel_ambiguous' if candidates else 'none')
    polygon=selected or next((r for r in results if r['kind']=='parcel'),None)
    if request is not None:request.state.result_count=int(polygon is not None)
    return {'coordinate_system':'EPSG:4326','coordinates':[longitude,latitude],
            'road_selection':road_selection,'polygon_feature_id':polygon['id'] if polygon else None,
            'road_address':road_addresses[0] if road_addresses else None,'road_addresses':road_addresses,
            'jibun_address':jibun_addresses[0] if jibun_addresses else None,'jibun_addresses':jibun_addresses,
            'address':best['address'] if best else None,
            'precision':best['kind'] if best else None,'results':results}

def connect():
    c = sqlite3.connect(DB.as_uri()+'?mode=ro',uri=True)
    c.row_factory = sqlite3.Row
    return c

@lru_cache(maxsize=256)
def geometry(blob):
    return transform(TR.transform,from_wkb(zlib.decompress(blob)))

def feature(r,include_geometry=True):
    g = geometry(r['geom'])
    point = g.representative_point()
    # Keep the displayed center on the geometry, including concave polygons and roads.
    if g.geom_type in ('LineString','MultiLineString'):
        center = g.interpolate(g.length / 2)
        center_method = 'line_midpoint'
    else:
        center = g.representative_point()
        center_method = 'representative_point'
    props = {'id':r['id'],'kind':r['kind'],'name':r['name'],'address':r['address'],
             'code':r['code'],'district':r['district'],'dong':r['dong'],
             'road_name':r['road_name'],'source_layer':r['source_layer'],
             'longitude':point.x,'latitude':point.y,'point_method':'representative_point',
             'center_longitude':center.x,'center_latitude':center.y,'center_method':center_method,
             'attributes':json.loads(r['properties'])}
    props['address_status'] = 'road_name_missing' if r['kind'] in ('building','complex') and not r['road_name'] else 'complete'
    if props['address_status'] == 'road_name_missing':
        props['address'] = None
    return {'type':'Feature','id':r['id'],'bbox':list(g.bounds),'properties':props,
            'geometry':mapping(g) if include_geometry else None}

def normalized(q):
    q = re.sub(r'\s+',' ',q.strip())
    q = re.sub(r'^서울시(?=\s|[가-힣]|$)','서울특별시 ',q)
    q = re.sub(r'^서울(?!특별시)(?=\s|[가-힣]|$)','서울특별시 ',q)
    return q.strip()

def find(q,kind,limit,offset):
    q = normalized(q)
    # Split administrative prefixes in compact input such as 서울강남구역삼동.
    q = re.sub(r'^(서울특별시)(?=\S)',r'\1 ',q)
    with connect() as c:
        districts = [r[0] for r in c.execute("SELECT name FROM features WHERE kind='district'")]
    for d in districts:
        q = re.sub(r'(^|\s)'+re.escape(d)+r'(?=\S)',lambda m:m[0]+' ',q)
    q=re.sub(r'([동가])(?=(?:산)?\d+(?:-\d+)?$)',r'\1 ',q)
    number = re.search(r'\s+(?:지하\s*|산\s*)?(\d+)(?:-(\d+))?$',q)
    tokens = re.findall(r'[\w]+',q,flags=re.UNICODE)
    if not tokens:
        raise HTTPException(400,'검색할 주소나 이름을 입력하세요.')
    inferred = kind
    if inferred is None:
        last = q.split()[-1]
        if q in ('서울특별시','Seoul','seoul'):
            inferred = 'province'
        elif number:
            prefix=q[:number.start()].strip().split()[-1] if q[:number.start()].strip() else ''
            inferred = 'parcel' if prefix.endswith(('동','가')) or '산' in number[0] else 'building'
        elif last.endswith('구'):
            inferred = 'district'
        elif last.endswith(('동','가')):
            inferred = 'dong'
        elif last.endswith(('로','길')):
            inferred = 'road'
    prefer_complex = number is not None and (kind=='complex' or (kind is None and inferred=='building'))
    if prefer_complex:
        inferred = 'building'
    params = []
    filters = []
    if inferred:
        filters.append('f.kind=?')
        params.append(inferred)
    if number and inferred in ('building','parcel'):
        tokens = re.findall(r'[\w]+',q[:number.start()].replace('지하',''))
        filters.extend(['f.main_no=?','f.sub_no=?','f.underground=?'])
        params.extend([int(number[1]),int(number[2] or 0),int(('산' if inferred=='parcel' else '지하') in number[0])])
    road_token = tokens[-1] if tokens else ''
    if inferred in ('road','building'):
        with connect() as c:
            exact_road = c.execute("SELECT 1 FROM features WHERE kind='road' AND name=? LIMIT 1",(road_token,)).fetchone()
        if exact_road:
            filters.append('f.road_name=?')
            params.append(road_token)
    # Search addresses only; retain POI names for display, never as search terms.
    if number is None:
        filters.append("f.kind IN ('province','district','dong','road')")
    elif inferred not in ('building','parcel'):
        return q,inferred,[],False
    for token in tokens:
        if token.lower() == 'seoul':
            token = '서울특별시'
        escaped = token.replace('!','!!').replace('%','!%').replace('_','!_')
        filters.append("f.address LIKE ? ESCAPE '!'")
        params.append('%'+escaped+'%')
    match = ' AND '.join('"'+t+'"*' for t in tokens)
    where = ' AND '.join(['search_index MATCH ?']+filters)
    with connect() as c:
        if prefer_complex:
            if kind=='complex':
                where += ' AND bc.complex_id IS NOT NULL'
            rows = c.execute(f'''SELECT DISTINCT d.* FROM search_index JOIN features f ON f.id=search_index.rowid
              LEFT JOIN building_complex bc ON bc.building_id=f.id
              JOIN features d ON d.id=coalesce(bc.complex_id,f.id)
              WHERE {where} ORDER BY CASE WHEN d.kind='complex' THEN 0 ELSE 1 END,d.address,d.id LIMIT ? OFFSET ?''',
              [match]+params+[limit+1,offset]).fetchall()
            inferred = 'complex' if rows and all(r['kind']=='complex' for r in rows) else 'building'
        else:
            if kind is None and inferred is None:
                where += " AND NOT EXISTS(SELECT 1 FROM building_complex bc WHERE bc.building_id=f.id)"
            rows = c.execute(f'''SELECT f.* FROM search_index JOIN features f ON f.id=search_index.rowid
          WHERE {where} ORDER BY CASE WHEN f.address=? OR f.name=? THEN 0 ELSE 1 END,
          bm25(search_index),length(f.address),f.address,f.id LIMIT ? OFFSET ?''',
          [match]+params+[q,q,limit+1,offset]).fetchall()
    return q,inferred,rows[:limit],len(rows)>limit

@app.get('/',response_class=HTMLResponse,include_in_schema=False)
def home():
    return (ROOT/'map.html').read_text(encoding='utf-8')
    return '''<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
    <title>서울 주소 검색 API</title><style>body{font:17px system-ui;max-width:980px;margin:50px auto;padding:20px;background:#f4f7fa;color:#172b40}
    input,button,select{font:inherit;padding:12px;border:1px solid #ccd5df;border-radius:8px}input{width:55%}button{background:#135fc3;color:white;cursor:pointer}
    pre{white-space:pre-wrap;overflow-wrap:anywhere;background:white;padding:20px;border-radius:12px;max-height:600px;overflow:auto}a{color:#135fc3}</style>
    <h1>서울 주소 검색 · 지오코딩</h1><p>시 → 구 → 법정동 → 도로명 → 건물 주소 · EPSG:4326</p>
    <p><a href="/docs">API 문서</a> · <a href="/health">DB 상태</a></p>
    <form id="form"><input id="q" value="서울특별시 중구 세종대로 110" aria-label="검색어"><button>검색</button></form>
    <p>예시: <a href="#" data-q="서울">서울</a> · <a href="#" data-q="강남구">강남구</a> · <a href="#" data-q="강남구 역삼동">역삼동</a> · <a href="#" data-q="중구 세종대로">세종대로</a></p>
    <pre id="result">검색하면 결과의 주소, 경도·위도와 GeoJSON API 링크를 표시합니다.</pre>
    <script>async function search(){let q=document.getElementById('q').value;let out=document.getElementById('result');out.textContent='검색 중…';try{let url='/search?q='+encodeURIComponent(q)+'&limit=5&include_geometry=false';let r=await fetch(url);let data=await r.json();out.textContent=JSON.stringify(data,null,2)}catch(e){out.textContent=e.message}}
    document.getElementById('form').onsubmit=e=>{e.preventDefault();search()};document.querySelectorAll('[data-q]').forEach(a=>a.onclick=e=>{e.preventDefault();document.getElementById('q').value=a.dataset.q;search()})</script></html>'''

@app.get('/health')
def health():
    with connect() as c:
        meta = {r['key']:json.loads(r['value']) for r in c.execute('SELECT * FROM metadata')}
    meta.pop('source_directory',None)
    if 'parcel_import' in meta:
        meta['parcel_import'].pop('extracted_directory',None)
    return {'status':'ok',**meta}

@app.get('/search')
def search(q:str=Query(min_length=1,max_length=200),kind:Kind|None=None,
           limit:int=Query(default=10,ge=1,le=50),offset:int=Query(default=0,ge=0,le=10000),
           include_geometry:bool=True,request:Request=None):
    query,inferred,rows,more = find(q,kind,limit,offset)
    if request is not None:request.state.result_count=len(rows)
    return {'type':'FeatureCollection','query':query,'kind':inferred,'coordinate_system':'EPSG:4326',
            'count':len(rows),'has_more':more,'offset':offset,'features':[feature(r,include_geometry) for r in rows]}

@app.get('/features/{feature_id}')
def get_feature(feature_id:int,request:Request=None):
    with connect() as c:
        r = c.execute('SELECT * FROM features WHERE id=?',(feature_id,)).fetchone()
    if r is None:
        raise HTTPException(404,'검색 결과 ID가 없습니다.')
    if request is not None:request.state.result_count=1
    return feature(r)

@app.get('/geocode')
def geocode(q:str=Query(min_length=1,max_length=200),limit:int=Query(default=5,ge=1,le=20),request:Request=None):
    query,inferred,rows,more = find(q,None,limit,0)
    if request is not None:request.state.result_count=len(rows)
    results = []
    for r in rows:
        props = feature(r,False)['properties']
        results.append({**props,'geometry':{'type':'Point','coordinates':[props['longitude'],props['latitude']]}})
    return {'query':query,'coordinate_system':'EPSG:4326','point_method':'representative_point',
            'has_more':more,'results':results}
