import asyncio
import os
from discord.ext import commands
import discord
from dotenv import load_dotenv
import time as tm
load_dotenv(".env")        

class Pomodoro(commands.Cog):    
    def __init__(self, bot):
        self.bot = bot
 
    # 起動時
    @commands.Cog.listener()
    async def on_ready(self):
        print("[Pomodoro] OK")


    @commands.hybrid_command(
        name = "start_pomodoro",
        description = "",
        with_app_command = True
    )
    @commands.guild_only()
    async def start_pomodoro(self, ctx, time: str):
        """
        time: str
            5,25,5,25,15,25
        """
        if (
            ctx.author == self.bot.user or                       # 自身を除外
            self.bot.stop                                        # 緊急モード
        ):
            return      
        
         # コマンドを実行したメンバーのVoiceチャンネルを取得
        voice_state = ctx.author.voice

        if voice_state is None or voice_state.channel is None:
            await ctx.send(content="Please join a Voice channel before executing this command.", ephemeral=True)
            return
        
        voice_channel = ctx.author.voice.channel
            
        if time == "" :
            time = "5,25"
            
        time = time.replace(" ", "")
        time_list = time.split(",")
        time_list = [int(item) for item in time_list if item.strip()]

        # Voiceチャンネルに参加
        self.voice_client = await voice_channel.connect()
        
        remain_time = int(tm.time()) + time_list[0] * 60
        
        msg = await ctx.send(content=f"{time}\n<t:{remain_time}:R>")
        self.msg_id = msg.id
        local_msg_id = msg.id
        
        self.voice_client.play(discord.FFmpegPCMAudio("../assets/sound/se01.mp3"))
        
        while self.voice_client.is_connected():
            for i in range(len(time_list)):
                print(f"wait: {time_list[i]} min")
                
                remain_time = int(tm.time()) + time_list[i] * 60
                time_string = ",".join([f"**[{item}]**" if j == i else str(item) for j, item in enumerate(time_list)])
                
                edited_message = await ctx.fetch_message(local_msg_id)
                await edited_message.edit(content=f"{time_string}\n<t:{remain_time}:R>")
                
                await asyncio.sleep(time_list[i]*60)
                
                if await self.is_message_deleted(ctx, local_msg_id): return
                if not self.voice_client.is_connected(): return
                
                self.voice_client.play(discord.FFmpegPCMAudio("audio/se01.mp3"))
            
        edited_message = await ctx.fetch_message(local_msg_id)
        await edited_message.edit(content=f"終了")
            
            
    async def is_message_deleted(self, ctx, message_id):
        try:
            await ctx.fetch_message(message_id) 
            return False 
        except:
            return True
        
        
    # [コマンド] 翻訳切り替え    
    @commands.hybrid_command(
        name = "stop_pomodoro",
        description = "",
        with_app_command = True
    )
    @commands.guild_only()
    async def stop_pomodoro(self, ctx):               
        if not self.voice_client.is_connected(): return
        
        await self.voice_client.disconnect()
        edited_message = await ctx.fetch_message(self.msg_id)
        await edited_message.delete()
        await ctx.send(content=f"終了")

                    

def setup(bot):
    return bot.add_cog(Pomodoro(bot), guilds=[discord.Object(id=os.getenv("DISCORD_SERVER_ID"))])
