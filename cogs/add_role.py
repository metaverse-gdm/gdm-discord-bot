import os
from discord.ext import commands
import requests
import discord
from dotenv import load_dotenv
import yaml
load_dotenv(".env")        

class AddRole(commands.Cog):    
    def __init__(self, bot):
        self.bot = bot
        self.path="config/add_role.yaml"
        self.read()
        self.word_list = [
            "姓名",
            "名前",
            "役割",
            "紹介",
            "居住",
            "興趣",
            "ひとこと"
        ]
    
    # 読み込み
    def read(self):
        if not os.path.exists(self.path):
            return

        with open(self.path, encoding="utf-8") as yml:
            self.config = yaml.safe_load(yml)            


    # 起動時
    @commands.Cog.listener()
    async def on_ready(self):
        print("[AddRole] OK")


    # メッセージ送信
    @commands.Cog.listener(name='on_message')
    async def on_message(self, message):
        if (
            message.author.bot or                      # 自身を除外
            message.content == "" or
            self.bot.stop or
            message.channel.id != self.config["channel_id"] # 特定のチャンネル以外を除外
        ):
            return  
        
        # 自己紹介のキーワードが含まれているかチェック
        if not any(word in message.content for word in self.word_list):
            return
        
        # Roleが付与されているかチェック
        role = message.guild.get_role(self.config["role_id"])
        if role in message.author.roles:
            return        
        
        # Role付与
        role = message.guild.get_role(self.config["role_id"])
        print(f"[AddRole] {message.author.name} {role.name}")
        await message.author.add_roles(role)
                
        # Raction付与
        emoji = self.config["reaction"]
        await message.add_reaction(emoji)


def setup(bot):
    return bot.add_cog(AddRole(bot), guilds=[discord.Object(id=os.getenv("DISCORD_SERVER_ID"))])
