import os
import requests
from datetime import datetime
import pytz

def test_kma_api():
    # 1. 설정
    api_key = os.environ.get('KMA_API_KEY')
    nx, ny = 60, 127 # 서울 기준
    now = datetime.now(pytz.timezone('Asia/Seoul'))
    base_date = now.strftime('%Y%m%d')
    
    # 2. 단기예보 URL (기상청 API 허브 상세 단기예보)
    short_url = f"https://apihub.kma.go.kr/api/typ01/url/vsc_sfc_af_dtl.php?base_date={base_date}&nx={nx}&ny={NY}&authKey={api_key}"
    
    print("--- [1] 단기예보 API 호출 시도 ---")
    print(f"URL: {short_url.replace(api_key, 'SECRET')}") # 보안 위해 키는 가리고 출력
    
    try:
        res = requests.get(short_url)
        print(f"Status Code: {res.status_code}")
        print("--- [2] 응답 데이터 내용 시작 ---")
        print(res.text) # <--- 이 내용이 핵심입니다!
        print("--- [3] 응답 데이터 내용 끝 ---")
    except Exception as e:
        print(f"Error occurred: {e}")

    # 임시 weather.ics 파일 생성 (에러 방지용)
    with open('weather.ics', 'w') as f:
        f.write("BEGIN:VCALENDAR\nVERSION:2.0\nEND:VCALENDAR")

if __name__ == "__main__":
    test_kma_api()
