import discord
import asyncio
import datetime
import os
from discord.ext import commands, tasks
from dotenv import load_dotenv

# 🌟 .env 파일에서 환경 변수 불러오기
load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")  # 디스코드 봇 토큰
GUILD_ID = int(os.getenv("GUILD_ID"))  # 서버 ID
FORUM_CHANNEL_ID = int(os.getenv("FORUM_CHANNEL_ID"))  # 포럼 채널 ID

# 🌟 봇의 권한 설정
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True  # 메시지 내용 읽기

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ {bot.user} 봇이 온라인입니다!")
    # GitHub Actions에서 실행할 때는 스케줄링 작업을 시작하지 않음
    if not os.getenv("GITHUB_ACTIONS"):
        daily_scrum_task.start()

# 🌟 매일 오전 9시에 실행
@tasks.loop(time=datetime.time(hour=9, minute=0, tzinfo=datetime.timezone.utc))
async def daily_scrum_task():
    await create_daily_scrum()

@bot.command(name="scrum")
async def manual_scrum(ctx):
    """수동으로 스크럼을 생성하는 명령어"""
    if ctx.author.guild_permissions.administrator:
        await create_daily_scrum()
        await ctx.send("✅ 스크럼이 생성되었습니다!")
    else:
        await ctx.send("❌ 이 명령어는 관리자만 사용할 수 있습니다.")

async def create_daily_scrum():
    """스크럼 생성 로직"""
    guild = bot.get_guild(GUILD_ID)
    forum_channel = guild.get_channel(FORUM_CHANNEL_ID)

    if not forum_channel:
        print("⚠️ 포럼 채널을 찾을 수 없습니다.")
        return

    # 🌟 어제 스크럼을 안 쓴 멤버 확인
    missing_members = await get_missing_scrum_members(guild, forum_channel)

    # 🌟 포럼에 새 글 작성
    today = datetime.date.today()
    today_str = today.strftime("%Y-%m-%d")
    weekday_korean = ["월", "화", "수", "목", "금", "토", "일"]
    weekday = weekday_korean[today.weekday()]

    post_title = f"📢 {today_str}({weekday}) 데일리 스크럼"
    post_content = "1️⃣ 어제 한 일\n"
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
                   "(예: \"오늘 오후 3시에 팀 미팅 예정\")"

    if missing_members:
        post_content += "🚨 어제 스크럼을 작성하지 않은 분들: " + " ".join([member.mention for member in missing_members])

    thread = await forum_channel.create_thread(name=post_title, content=post_content)
    print(f"✅ 스크럼 포스트 생성: {thread.name}")

async def  (guild, forum_channel):
    """ 🌟 어제 스크럼을 작성하지 않은 멤버 확인 """
    yesterday = datetime.date.today() - datetime.timedelta(days=1)
    missing_members = []
    active_members = set()

    # 🌟 어제 날짜의 모든 포스트 가져오기
    async for thread in forum_channel.threads:
        if thread.name.startswith(f"📢 {yesterday}"):
            async for message in thread.history(limit=None):
                active_members.add(message.author)

    # 🌟 전체 멤버 중 어제 스크럼을 안 쓴 멤버 찾기
    for member in guild.members:
        if not member.bot and member not in active_members:
            missing_members.append(member)

    return missing_members

if __name__ == "__main__":
    bot.run(TOKEN)
