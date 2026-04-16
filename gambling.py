import discord
from discord.ext import commands
from discord import app_commands
import asyncio

from games.blackjack import BlackjackGame
from games.slots import SlotGame
from games.ladder import LadderGame
from games.rps import RPS
from economy.wallet import Wallet

class Gambling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.wallet = Wallet()
        self.wallet.load_from_file('wallet_data.json')
        self.active_games = {}
    
    @app_commands.command(name="잔액", description="현재 잔액을 확인합니다")
    async def balance(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        if user_id not in self.wallet.balances:
            self.wallet.create_user(user_id)
            self.wallet.add_balance(user_id, 10000)
        
        balance = self.wallet.get_balance(user_id)
        embed = discord.Embed(
            title="💰 계좌 조회",
            description=f"**{balance:,} 코인**",
            color=discord.Color.gold()
        )
        embed.set_footer(text=f"사용자: {interaction.user}")
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="일일보너스", description="하루에 한 번 보너스를 받습니다")
    async def daily(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        if user_id not in self.wallet.balances:
            self.wallet.create_user(user_id)
            self.wallet.add_balance(user_id, 10000)
        
        if self.wallet.claim_daily_bonus(user_id):
            embed = discord.Embed(
                title="🎁 일일 보너스",
                description=f"**+{self.wallet.daily_bonus:,} 코인** 획득!",
                color=discord.Color.green()
            )
            self.wallet.save_to_file('wallet_data.json')
        else:
            embed = discord.Embed(
                title="⏰ 일일 보너스",
                description="이미 오늘 보너스를 받았습니다!",
                color=discord.Color.red()
            )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="송금", description="다른 사람에게 돈을 송금합니다")
    @app_commands.describe(user="받을 사용자", amount="송금 금액")
    async def transfer(self, interaction: discord.Interaction, user: discord.User, amount: int):
        from_id = str(interaction.user.id)
        to_id = str(user.id)
        
        if from_id not in self.wallet.balances:
            self.wallet.create_user(from_id)
            self.wallet.add_balance(from_id, 10000)
        
        if to_id not in self.wallet.balances:
            self.wallet.create_user(to_id)
            self.wallet.add_balance(to_id, 10000)
        
        if amount <= 0:
            await interaction.response.send_message("금액은 0보다 커야 합니다!")
            return
        
        if self.wallet.transfer(from_id, to_id, amount):
            embed = discord.Embed(
                title="📤 송금 완료",
                description=f"**{user.mention}**에게 **{amount:,} 코인** 송금했습니다",
                color=discord.Color.blue()
            )
            self.wallet.save_to_file('wallet_data.json')
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("잔액이 부족합니다!")
    
    @app_commands.command(name="블랙잭", description="블랙잭을 플레이합니다")
    @app_commands.describe(bet="베팅 금액")
    async def blackjack(self, interaction: discord.Interaction, bet: int):
        user_id = str(interaction.user.id)
        
        if user_id not in self.wallet.balances:
            self.wallet.create_user(user_id)
            self.wallet.add_balance(user_id, 10000)
        
        if bet <= 0:
            await interaction.response.send_message("베팅 금액은 0보다 커야 합니다!")
            return
        
        if not self.wallet.deduct_balance(user_id, bet):
            await interaction.response.send_message("잔액이 부족합니다!")
            return
        
        game = BlackjackGame()
        status = game.start()
        
        embed = discord.Embed(
            title="🃏 블랙잭",
            color=discord.Color.green()
        )
        embed.add_field(name="당신의 카드", value=", ".join(status["player_cards"]), inline=False)
        embed.add_field(name="당신의 점수", value=f"**{status['player_value']}**", inline=False)
        embed.add_field(name="딜러의 카드", value=f"{status['dealer_cards'][0]}, {status['dealer_cards'][1]}", inline=False)
        embed.add_field(name="베팅 금액", value=f"{bet} 코인", inline=False)
        
        self.active_games[user_id] = {"game": game, "bet": bet}
        self.wallet.save_to_file('wallet_data.json')
        
        await interaction.response.send_message(embed=embed, content="Hit 또는 Stand를 선택하세요!")
    
    @app_commands.command(name="슬롯", description="슬롯머신을 플레이합니다")
    @app_commands.describe(bet="베팅 금액")
    async def slots(self, interaction: discord.Interaction, bet: int):
        await interaction.response.defer()
        
        user_id = str(interaction.user.id)
        
        if user_id not in self.wallet.balances:
            self.wallet.create_user(user_id)
            self.wallet.add_balance(user_id, 10000)
        
        if bet <= 0:
            await interaction.followup.send("베팅 금액은 0보다 커야 합니다!")
            return
        
        if not self.wallet.deduct_balance(user_id, bet):
            await interaction.followup.send("잔액이 부족합니다!")
            return
        
        game = SlotGame(bet)
        game.spin()
        
        is_win, winnings, payline = game.check_win()
        
        if is_win:
            self.wallet.add_balance(user_id, winnings)
            embed = discord.Embed(
                title="🎉 대박!",
                description=game.display(),
                color=discord.Color.green()
            )
            embed.add_field(name="상금", value=f"{winnings} 코인", inline=False)
        else:
            embed = discord.Embed(
                title="❌ 실패",
                description=game.display(),
                color=discord.Color.red()
            )
        
        self.wallet.save_to_file('wallet_data.json')
        await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="가위바위보", description="봇과 가위바위보를 합니다")
    @app_commands.describe(bet="베팅 금액", choice="rock, paper, scissors")
    async def rps(self, interaction: discord.Interaction, bet: int, choice: str):
        user_id = str(interaction.user.id)
        
        if user_id not in self.wallet.balances:
            self.wallet.create_user(user_id)
            self.wallet.add_balance(user_id, 10000)
        
        if bet <= 0:
            await interaction.response.send_message("베팅 금액은 0보다 커야 합니다!")
            return
        
        if choice.lower() not in ["rock", "paper", "scissors"]:
            await interaction.response.send_message("rock, paper, scissors 중 하나를 선택하세요!")
            return
        
        if not self.wallet.deduct_balance(user_id, bet):
            await interaction.response.send_message("잔액이 부족합니다!")
            return
        
        game = RPS()
        result = game.play(choice.lower())
        
        if result["result"] == "win":
            winnings = bet * 2
            self.wallet.add_balance(user_id, winnings)
            color = discord.Color.green()
            title = "🎉 승리!"
        elif result["result"] == "draw":
            winnings = bet
            self.wallet.add_balance(user_id, winnings)
            color = discord.Color.yellow()
            title = "⚖️ 비겼습니다!"
        else:
            winnings = 0
            color = discord.Color.red()
            title = "❌ 패배!"
        
        embed = discord.Embed(
            title=title,
            description=f"당신: {result['player_emoji']} vs 봇: {result['bot_emoji']}",
            color=color
        )
        embed.add_field(name="상금", value=f"{winnings} 코인", inline=False)
        
        self.wallet.save_to_file('wallet_data.json')
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="사다리", description="사다리게임을 플레이합니다")
    @app_commands.describe(bet="베팅 금액")
    async def ladder(self, interaction: discord.Interaction, bet: int):
        await interaction.response.defer()
        
        user_id = str(interaction.user.id)
        
        if user_id not in self.wallet.balances:
            self.wallet.create_user(user_id)
            self.wallet.add_balance(user_id, 10000)
        
        if bet <= 0:
            await interaction.followup.send("베팅 금액은 0보다 커야 합니다!")
            return
        
        if not self.wallet.deduct_balance(user_id, bet):
            await interaction.followup.send("잔액이 부족합니다!")
            return
        
        game = LadderGame(players=2)
        winner = game.get_winner()
        
        if winner == 0:
            winnings = bet * 2
            self.wallet.add_balance(user_id, winnings)
            result_msg = f"🎉 **승리!** +{winnings} 코인"
            color = discord.Color.green()
        else:
            result_msg = f"❌ **패배!** -{bet} 코인"
            color = discord.Color.red()
        
        embed = discord.Embed(
            title="🪜 사다리게임",
            description=result_msg,
            color=color
        )
        
        self.wallet.save_to_file('wallet_data.json')
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Gambling(bot))