import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'✅ {bot.user}로 로그인했습니다!')
    try:
        synced = await bot.tree.sync()
        print(f'✅ {len(synced)}개의 슬래시 명령어가 동기화되었습니다!')
    except Exception as e:
        print(f'❌ 명령어 동기화 실패: {e}')
    
    await bot.load_extension('gambling')

async def main():
    async with bot:
        await bot.start(TOKEN)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())