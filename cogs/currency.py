import os
from discord.ext import commands
import requests
import discord
from dotenv import load_dotenv
load_dotenv(".env")        

class Currency(commands.Cog):    
    def __init__(self, bot):
        self.bot = bot
        self.currencies = ['JPY', 'TWD', 'CNY', 'EUR', 'USD', 'KRW']

    # 起動時
    @commands.Cog.listener()
    async def on_ready(self):
        print("[Currency] OK")


    # [コマンド] 翻訳切り替え    
    @commands.hybrid_command(
        name = "convert_currency",
        description = "",
        with_app_command = True,
    )
    @commands.guild_only()
    async def convert_currency_command(self, ctx, amount: float, from_currency: str, to_currency: str):
        """
        from_currency: str
            JPY, TWD, USD, CNY, EUR, KRW
        to_currency: str
            JPY, TWD, USD, CNY, EUR, KRW
        """
        if (
            ctx.author == self.bot.user or                       # 自身を除外
            self.bot.stop                                        # 緊急モード
        ):
            return      
        
        if not from_currency in self.currencies:
            await ctx.send(f"[Error] {from_currency}")
            return
        
        if not to_currency in self.currencies:
            await ctx.send(f"[Error] {to_currency}")
            return          
        
        result = self.convert_currency(from_currency, to_currency, amount)
        await ctx.send(result) 


    def convert_currency(self, from_currency, to_currency, amount):
        if from_currency == to_currency:
            return f"{amount} {from_currency}"

        # Alpha VantageのAPIエンドポイント
        endpoint = 'https://www.alphavantage.co/query'

        # APIリクエストパラメータ
        params = {
            'function': 'CURRENCY_EXCHANGE_RATE',
            'from_currency': from_currency,
            'to_currency': to_currency,
            'apikey': os.getenv("ALPHA_VANTAGE_API")
        }

        try:
            # APIリクエストを送信
            response = requests.get(endpoint, params=params)
            data = response.json()

            # レート情報を取得
            exchange_rate = data['Realtime Currency Exchange Rate']['5. Exchange Rate']

            # 金額を変換
            converted_amount = amount * float(exchange_rate)

            return f"{amount:,.2f} {from_currency} ↔ {converted_amount:,.2f} {to_currency}"

        except Exception as e:
            return f'Error'


def setup(bot):
    return bot.add_cog(Currency(bot), guilds=[discord.Object(id=os.getenv("DISCORD_SERVER_ID"))])
