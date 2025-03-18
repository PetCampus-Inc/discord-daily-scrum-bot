import requests
import datetime
import os

# 환경변수에서 Webhook URL 가져오기
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

if not WEBHOOK_URL:
    print("❌ DISCORD_WEBHOOK_URL 환경 변수가 설정되지 않았습니다.")
    exit(1)

def send_discord_webhook():
    today = datetime.date.today()
    today_str = today.strftime("%Y-%m-%d")
    
    # 한글 요일 변환 (0:월요일, 1:화요일, ...)
    weekday_korean = ["월", "화", "수", "목", "금", "토", "일"]
    weekday = weekday_korean[today.weekday()]

    data = {
        "content": "1️⃣ 어제 한 일\n"
                   "(예: \"jira 티켓 번호 : 로그인 API 리팩토링 완료\")\n"
                   "(예: \"jira 티켓 번호 : 결제 모듈 오류 수정 및 테스트 진행\")\n\n"
                   "2️⃣ 오늘 할 일\n"
                   "(예: \"jira 티켓 번호 : 상품 상세 페이지 API 성능 개선\")\n"
                   "(예: \"jira 티켓 번호 : 배치 스케줄러 버그 수정\")\n\n"
                   "3️⃣ 현재 문제/도움 필요한 사항\n"
                   "(예: \"jira 티켓 번호 : 카프카 메시지 처리 중 지연 발생, 원인 파악 중\")\n"
                   "(예: \"jira 티켓 번호 : FeignClient 타임아웃 조정 관련 의견 필요\")\n\n"
                   "4️⃣ 기타 공유 사항\n"
                   "(예: \"오늘 오후 3시에 팀 미팅 예정\")",
        "thread_name": f"📢 {today_str}({weekday}) 데일리 스크럼"
    }

    response = requests.post(WEBHOOK_URL, json=data)

    if response.status_code == 204:
        print("✅ 메시지가 성공적으로 전송되었습니다.")
    else:
        print(f"❌ 오류 발생: {response.status_code}, 응답 내용: {response.text}")

if __name__ == "__main__":
    send_discord_webhook()
