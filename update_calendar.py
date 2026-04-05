import os
import requests
import pytz
from datetime import datetime, timedelta
from icalendar import Calendar, Event

# --- [설정] ---
NX = int(os.environ.get('KMA_NX', 60))
NY = int(os.environ.get('KMA_NY', 127))
LOCATION_NAME = os.environ.get('LOCATION_NAME', '우리집')
REG_ID_TEMP = os.environ.get('REG_ID_TEMP', '11B10101')
REG_ID_LAND = os.environ.get('REG_ID_LAND', '11B00000')
API_KEY = os.environ.get('KMA_API_KEY')

def get_weather_info(sky, pty):
    sky, pty = str(sky), str(pty)
    if pty != '0':
        if pty in ['1', '4', '5']: return "🌧️", "비"
        if pty in ['2', '6']: return "🌨️", "비/눈"
        if pty in ['3', '7']: return "❄️", "눈"
        return "🌧️", "강수"
    if sky == '1': return "☀️", "맑음"
    if sky == '3': return "⛅", "구름많음"
    if sky == '4': return "☁️", "흐림"
    return "🌡️", "정보없음"

def get_mid_emoji(wf):
    if not wf: return "🌡️"
    if '비' in wf or '소나기' in wf or '적심' in wf: return "🌧️"
    if '눈' in wf or '진눈깨비' in wf: return "🌨️"
    if '구름많음' in wf: return "⛅"
    if '흐림' in wf: return "☁️"
    if '맑음' in wf: return "☀️"
    return "☀️"

def fetch_api(url):
    try:
        res = requests.get(url, timeout=15)
        if res.status_code == 200: return res.json()
    except: return None
    return None

def main():
    seoul_tz = pytz.timezone('Asia/Seoul')
    now = datetime.now(seoul_tz)
    cal = Calendar()
    cal.add('X-WR-CALNAME', f'기상청 날씨 ({LOCATION_NAME})')
    cal.add('X-WR-TIMEZONE', 'Asia/Seoul')

    # --- [1. 데이터 수집] ---
    base_date = now.strftime('%Y%m%d')
    base_h = max([h for h in [2, 5, 8, 11, 14, 17, 20, 23] if h <= now.hour], default=2)
    base_time = f"{base_h:02d}00"
    url_short = f"https://apihub.kma.go.kr/api/typ02/openApi/VilageFcstInfoService_2.0/getVilageFcst?dataType=JSON&base_date={base_date}&base_time={base_time}&nx={NX}&ny={NY}&numOfRows=1000&authKey={API_KEY}"
    
    forecast_map = {}
    short_res = fetch_api(url_short)
    if short_res and 'response' in short_res and 'body' in short_res['response']:
        for it in short_res['response']['body']['items']['item']:
            d, t, cat, val = it['fcstDate'], it['fcstTime'], it['category'], it['fcstValue']
            if d not in forecast_map: forecast_map[d] = {}
            if t not in forecast_map[d]: forecast_map[d][t] = {}
            forecast_map[d][t][cat] = val

    # --- [2. 단기 예보 조립 (하루 1개 일정 + 메모란에 상세정보)] ---
    short_limit = (now + timedelta(days=3)).strftime('%Y%m%d')
    for d_str in sorted(forecast_map.keys()):
        if d_str > short_limit: continue
        
        day_data = forecast_map[d_str]
        tmps = [float(day_data[t]['TMP']) for t in day_data if 'TMP' in day_data[t]]
        if not tmps: continue

        # 하루 요약 정보 계산
        t_min, t_max = int(min(tmps)), int(max(tmps))
        # 오후 12시 혹은 가장 빠른 시간의 날씨를 대표 아이콘으로 사용
        rep_t = '1200' if '1200' in day_data else sorted(day_data.keys())[0]
        rep_emoji, _ = get_weather_info(day_data[rep_t].get('SKY','1'), day_data[rep_t].get('PTY','0'))
        
        event = Event()
        event.add('summary', f"{rep_emoji} {t_min}°C/{t_max}°C")
        
        # --- 시간대별 상세 데이터를 메모(Description)로 생성 ---
        description = []
        for t_str in sorted(day_data.keys()):
            t_data = day_data[t_str]
            emoji, wf_str = get_weather_info(t_data['SKY'], t_data['PTY'])
            temp = t_data['TMP']
            reh = t_data.get('REH', '-')
            wsd = t_data.get('WSD', '-')
            pty = t_data.get('PTY', '0')
            pop = t_data.get('POP', '0')
            
            pop_str = f" ☔{pop}%" if pty != '0' else ""
            line = f"{t_str[:2]}:{t_str[2:]} - {emoji} {wf_str} {temp}°C{pop_str} (습도{reh}%, 풍속{wsd}m/s)"
            description.append(line)
        
        event.add('description', "\n".join(description))
        
        # 하루 종일 일정으로 설정
        event_date = datetime.strptime(d_str, '%Y%m%d').date()
        event.add('dtstart', event_date)
        event.add('dtend', event_date + timedelta(days=1))
        event.add('uid', f"{d_str}@short_summary")
        cal.add_component(event)

    # --- [3. 중기 예보 수집 (기존과 동일)] ---
    # ... (생략된 중기 예보 로직은 위에서 드린 최종본과 동일하게 유지하시면 됩니다) ...
    # (내용이 길어 본문에는 핵심만 담았습니다. 전체 코드가 필요하시면 말씀해 주세요!)

    with open('weather.ics', 'wb') as f:
        f.write(cal.to_ical())

if __name__ == "__main__":
    main()
