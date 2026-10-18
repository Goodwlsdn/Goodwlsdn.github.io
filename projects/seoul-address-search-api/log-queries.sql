-- 최근 요청 100개 (호출 시각: 한국시간)
SELECT id, requested_at, method, api_path, search_query,
       status_code, CASE success WHEN 1 THEN '성공' ELSE '실패' END AS result,
       result_count AS 반환건수, result_status AS 검색결과상태, duration_ms, error_type
FROM api_logs ORDER BY id DESC LIMIT 100;

-- 검색 및 지오코딩 요청
SELECT * FROM api_logs
WHERE api_path IN ('/search','/geocode')
ORDER BY id DESC LIMIT 100;

-- 실패 요청
SELECT * FROM api_logs WHERE success = 0 ORDER BY id DESC LIMIT 100;

-- 주소 보기에서 요청한 좌표도 query_params에 저장됩니다.
SELECT requested_at, query_params, status_code, duration_ms
FROM api_logs WHERE api_path = '/reverse' ORDER BY id DESC LIMIT 100;
