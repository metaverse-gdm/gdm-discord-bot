import discord
import yaml
# from db import DB
from discord.ext import commands
import os
from dotenv import load_dotenv
load_dotenv(".env")        

class Bot(commands.Bot):
    def __init__(self): 
        self.stop = False                

        # Discordへ接続
        intents = discord.Intents().all()
        super().__init__(command_prefix='/', intents=intents)
        
    # 機能の読み込み
    async def setup_hook(self):
        # Load all cogs
        for file in os.listdir('./cogs'):
            if file.endswith('.py'):
                await self.load_extension(f'cogs.{file[:-3]}')
        
        # コマンドを反映
        await self.tree.sync(guild = discord.Object(id=os.getenv("DISCORD_SERVER_ID")))


    # 設定ファイル書き込み
    def write_config(self):
        with open(self.config_path, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False)    
    
    # 起動時
    async def on_ready(self):        
        print(f"[Main] OK")   
        print(f"[READY]: {self.user}")
        print(f"[GUILDS]: {len(self.guilds)}")
        print(f"[USERS]: {len(self.users)}")
        await self.tree.sync()#スラッシュコマンドを同期
                
    async def close(self):
        await super().close()

if __name__ == "__main__":
    # bot = Bot("test")
    bot = Bot()
    bot.run(os.getenv("DISCORD_TOKEN"))