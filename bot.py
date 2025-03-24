import discord
import asyncio
import datetime
import os
import pytz
from discord.ext import commands, tasks
from dotenv import load_dotenv

# 🌟 .env 파일에서 환경 변수 불러오기
load_dotenv()

# 🌟 환경 변수 검증
def validate_env_vars():
    required_vars = ["DISCORD_TOKEN", "GUILD_ID", "FORUM_CHANNEL_ID"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise ValueError(f"필수 환경 변수가 누락되었습니다: {', '.join(missing_vars)}")

# 🌟 환경 변수 검증 실행
validate_env_vars()

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
FORUM_CHANNEL_ID = int(os.getenv("FORUM_CHANNEL_ID"))
KST = pytz.timezone('Asia/Seoul')

# 🌟 봇의 권한 설정
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True
intents.members = True  # 🌟 멤버 목록을 가져오기 위한 권한 추가

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ {bot.user} 봇이 온라인입니다!")
    try:
        await create_daily_scrum()
        print("✅ 스크럼 생성이 완료되었습니다.")
        if os.getenv("GITHUB_ACTIONS"):
            print("✅ GitHub Actions 환경에서 작업이 완료되었습니다.")
            await bot.close()
    except Exception as e:
        print(f"❌ 스크럼 생성 중 오류 발생: {str(e)}")
        if os.getenv("GITHUB_ACTIONS"):
            await bot.close()
    if not os.getenv("GITHUB_ACTIONS"):
        daily_scrum_task.start()

# 🌟 매일 오전 9시에 실행 (한국 시간)
@tasks.loop(time=datetime.time(hour=9, minute=0, tzinfo=KST))
async def daily_scrum_task():
    try:
        await create_daily_scrum()
    except Exception as e:
        print(f"❌ 스크럼 생성 중 오류 발생: {str(e)}")

async def get_missing_scrum_members(guild, forum_channel):
    """ 🌟 어제 스크럼을 작성하지 않은 멤버 확인 """
    try:
        yesterday = datetime.datetime.now(KST).date() - datetime.timedelta(days=1)
        missing_members = []
        active_members = set()
                
        # 🌟 아카이브된 스레드 가져오기
        archived_count = 0
        async for thread in forum_channel.archived_threads():
            archived_count += 1
            print(f"스레드 멤버 확인: {guild.members}")
            print(f"🔍 스레드 객체 정보: {thread}")
            print(f"🔍 스레드 객체 타입: {type(thread)}")
            print(f"🔍 스레드 객체 속성들: {dir(thread)}")
            print(f"🔍 스레드 이름: {thread.name}")
            print(f"🔍 스레드 ID: {thread.id}")
            print(f"🔍 스레드 생성일: {thread.created_at}")
            print(f"🔍 스레드 아카이브 상태: {'아카이브됨' if thread.archived else '활성'}")
            print(f"🔍 스레드 자동 아카이브 시간: {thread.auto_archive_duration}시간")
            print(f"쓰레드 찾았냐?", thread.name.startswith(f"📢 {yesterday}"))
            
            if thread.name.startswith(f"📢 {yesterday}"):
                print(f"🔍 어제 날짜의 스레드 찾음: {thread.name}")
                # 🌟 최근 100개의 메시지만 확인
                async for message in thread.history(limit=100):
                    print(f"🔍 메시지 찾음: {message.author.name}")
                    active_members.add(message.author)
                # 🌟 어제 날짜의 스레드를 찾았으면 바로 break
                break
        
        print(f"🔍 아카이브된 스레드 수: {archived_count}")

        # 🌟 전체 멤버 중 어제 스크럼을 안 쓴 멤버 찾기
        print(f"🔍 전체 멤버 수: {len(guild.members)}")
        for member in guild.members:
            print(f"🔍 멤버 찾음: {member.name}")
            if not member.bot and member not in active_members:
                missing_members.append(member)

        return missing_members
        
    except Exception as e:
        print(f"❌ 스크럼 멤버 확인 중 오류 발생: {str(e)}")
        return []

async def create_daily_scrum():
    """스크럼 생성 로직"""
    try:
        guild = bot.get_guild(GUILD_ID)
        if not guild:
            raise ValueError("서버를 찾을 수 없습니다.")

        forum_channel = guild.get_channel(FORUM_CHANNEL_ID)
        if not forum_channel:
            raise ValueError("포럼 채널을 찾을 수 없습니다.")

        # 🌟 어제 스크럼을 안 쓴 멤버 확인
        missing_members = await get_missing_scrum_members(guild, forum_channel)
        print(f"🔍 어제 스크럼을 안 쓴 멤버 수: {len(missing_members)}")

        # 🌟 포럼에 새 글 작성
        today = datetime.datetime.now(KST).date()
        today_str = today.strftime("%Y-%m-%d")
        weekday_korean = ["월", "화", "수", "목", "금", "토", "일"]
        weekday = weekday_korean[today.weekday()]

        post_title = f"📢 {today_str}({weekday}) 데일리 스크럼 - 테스트임 댓글달지마세요."
        post_content = ("1️⃣ 어제 한 일\n"
                       "(예: \"jira 티켓 번호 : 로그인 API 리팩토링 완료\")\n"
                       "(예: \"jira 티켓 번호 : 결제 모듈 오류 수정 및 테스트 진행\")\n\n"
                       "2️⃣ 오늘 할 일\n"
                       "(예: \"jira 티켓 번호 : 상품 상세 페이지 API 성능 개선\")\n"
                       "(예: \"jira 티켓 번호 : 배치 스케줄러 버그 수정\")\n\n"
                       "3️⃣ 현재 문제/도움 필요한 사항\n"
                       "(예: \"jira 티켓 번호 : 카프카 메시지 처리 중 지연 발생, 원인 파악 중\")\n"
                       "(예: \"jira 티켓 번호 : FeignClient 타임아웃 조정 관련 의견 필요\")\n\n"
                       "4️⃣ 작업 시간\n"
                       "(예: \"작업 시간 : 15 ~ 23시\")\n\n"
                       "5️⃣ 기타 공유 사항\n"
                       "(예: \"오늘 오후 3시에 팀 미팅 예정\")")

        if missing_members:
            post_content += "\n\n🚨 어제 스크럼을 작성하지 않은 분들: " + " ".join([f"{member.display_name}" for member in missing_members])

        thread = await forum_channel.create_thread(name=post_title, content=post_content)
        print(f"✅ 스크럼 포스트 생성: {post_content}")
        
    except Exception as e:
        print(f"❌ 스크럼 생성 중 오류 발생: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        bot.run(TOKEN)
    except Exception as e:
        print(f"❌ 봇 실행 중 오류 발생: {str(e)}")
