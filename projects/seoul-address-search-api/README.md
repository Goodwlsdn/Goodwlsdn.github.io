# 주소 검색 · 지오코딩 API

공공 주소 데이터를 SQLite 검색 인덱스로 구성하고, 주소 검색·지오코딩·역지오코딩 기능을 HTTP API로 제공하는 FastAPI 프로젝트입니다.

## 데이터 출처 및 공개 범위

- 데이터 출처: [주소기반산업지원서비스(juso.go.kr)](https://www.juso.go.kr/)
- 이 저장소에는 **주소 데이터 원본, 가공 데이터, SQLite DB를 포함하지 않습니다.**
- 데이터를 사용하려면 출처 사이트의 이용 조건과 최신 안내를 확인한 뒤 직접 내려받아야 합니다.
- API 소스 코드와 로컬 실행 도구만 공개합니다.

## 주요 기능

- 주소 및 행정구역 검색: `GET /search`
- 검색 결과의 대표 좌표 반환: `GET /geocode`
- 좌표에 해당하는 주소 조회: `GET /reverse`
- 개별 공간 객체 조회: `GET /features/{feature_id}`
- 상태 및 데이터 메타정보 확인: `GET /health`
- Swagger API 문서: `GET /docs`
- GeoJSON 응답과 EPSG:4326 좌표 제공
- SQLite FTS 기반 검색 및 요청 로그 기록

## 기술 스택

- Python 3.12
- FastAPI / Uvicorn
- SQLite / FTS
- Shapely / pyproj
- Leaflet

## 로컬 실행

### 1. 환경 구성

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

macOS에서는 다음 스크립트를 사용할 수도 있습니다.

```bash
bash Setup-Mac.command
```

### 2. 데이터베이스 준비

원본 데이터는 저장소에 포함되지 않습니다. 별도로 준비한 SQLite 파일을 프로젝트 폴더에 `seoul.sqlite`라는 이름으로 두거나, 환경변수로 경로를 지정합니다.

```bash
export SEOUL_DB=/absolute/path/to/seoul.sqlite
```

### 3. API 실행

```bash
python serve.py --port 8000
```

실행 후 다음 주소에서 API 문서를 확인할 수 있습니다.

```text
http://127.0.0.1:8000/docs
```

## 호출 예시

```bash
curl --get 'http://127.0.0.1:8000/search' \
  --data-urlencode 'q=중구 세종대로 110' \
  --data-urlencode 'limit=5' \
  --data-urlencode 'include_geometry=false'
```

```bash
curl --get 'http://127.0.0.1:8000/reverse' \
  --data-urlencode 'longitude=126.9784' \
  --data-urlencode 'latitude=37.5667'
```

## 프로젝트 구조

```text
.
├── app.py             # FastAPI 엔드포인트와 검색 로직
├── access_logs.py     # SQLite 요청 로그
├── map.html           # 검색 결과 지도 UI
├── serve.py           # 로컬 실행 진입점
├── log-queries.sql    # 로그 분석 예시 쿼리
├── requirements.txt
├── Setup-Mac.command
└── Run-Mac.command
```

## 참고

현재 공개 범위에는 데이터베이스 생성 파이프라인과 데이터 파일이 포함되지 않습니다. API는 프로젝트가 기대하는 스키마로 구성된 SQLite DB가 있어야 동작합니다.
