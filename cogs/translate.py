import os
import deepl
from discord.ext import commands
from googletrans import Translator
import re
import yaml
import json
import requests
import emoji
import discord
from dotenv import load_dotenv
load_dotenv(".env")        

class Translate(commands.Cog):    
    def __init__(self, bot):
        self.bot = bot
        self.path="config/translate.yaml"
        
        self.translate_channel_list={
            int(os.getenv("DISCORD_SERVER_ID")): {}
        } # 翻訳対象Channel List
        self.read()
        
        self.translator_deepl = deepl.Translator(os.getenv("DEEPL_API_KEY"))
        self.translator_google= Translator()        
        self.pattern = "https?://[\w/:%#\$&\?\(\)~\.=\+\-]+"
        self.translate_text ={
            "ja": self.translate_jp,
            "ko": self.translate_kr,
            "zh": self.translate_ch,
            "th": self.translate_th,
            "en": self.translate_en
        }


    # 読み込み
    def read(self):
        if not os.path.exists(self.path):
            return

        with open(self.path, encoding="utf-8") as yml:
            self.translate_channel_list = yaml.safe_load(yml)
    
    
    # 書き出し
    def write(self):
        with open(self.path, 'w', encoding="utf-8") as f:
            yaml.dump(self.translate_channel_list, f, default_flow_style=False)


    # 起動時
    @commands.Cog.listener()
    async def on_ready(self):
        print("[Translate] OK")


    # [コマンド] 翻訳切り替え    
    @commands.hybrid_command(
        name = "start_translate",
        description = "日本語: ja, 中文: zh, English: en, 한국어: ko, ไทย: th",
        with_app_command = True
    )
    @commands.guild_only()
    async def start_translate(self, ctx, main: str, sub: str):
        if (
            ctx.author == self.bot.user or                       # 自身を除外
            self.bot.stop                                        # 緊急モード
        ):
            return      
        
        if not main in self.translate_text:
            await ctx.send(f"[Error] {main} は対応していません")
            return
        
        if not sub in self.translate_text:
            await ctx.send(f"[Error] {sub} は対応していません")
            return          
        
        self.add_translate_channel(ctx, main, sub)
        await ctx.send(f'**[翻譯開始]** {main} ↔ {sub}') 
        self.write() # 保存


    def add_translate_channel(self, ctx, main, sub):
        if not ctx.guild.id in self.translate_channel_list:
            self.translate_channel_list[ctx.guild.id] = {}
            
        if not ctx.channel.id in self.translate_channel_list[ctx.guild.id]:
            self.translate_channel_list[ctx.guild.id][ctx.channel.id] = {}
            
        self.translate_channel_list[ctx.guild.id][ctx.channel.id]["main"] = main
        self.translate_channel_list[ctx.guild.id][ctx.channel.id]["sub"] = sub   
        
        
    # [コマンド] 翻訳切り替え    
    @commands.hybrid_command(
        name = "end_translate",
        description = "Stop translating on this channel",
        with_app_command = True
    )
    @commands.guild_only()
    async def end_translate(self, ctx):
        if (
            ctx.author == self.bot.user or                       # 自身を除外
            self.bot.stop                                        # 緊急モード
        ):
            return                
                
        del self.translate_channel_list[ctx.guild.id][ctx.channel.id]
        await ctx.send('**[翻譯終了]**')        
                
        self.write() # 保存


    # メッセージ送信
    @commands.Cog.listener(name='on_message')
    async def on_message(self, message):
        if (
            message.author.bot or                      # 自身を除外
            message.content == "" or
            self.bot.stop or
            re.match(self.pattern, message.content) or                # URLの場合
            "http" in message.content
        ):
            return  
        
        # 翻訳対象Channelではない場合
        if not message.channel.id in self.translate_channel_list[message.guild.id]:            
            return

        # 絵文字を除外
        if self.is_only_emoji(message.content):
            return
        
        lang = self.translator_google.detect(message.content).lang
        channel_data = self.translate_channel_list[message.guild.id][message.channel.id]
        
        result = message.content
        if channel_data["main"] in lang:
            result = self.translate_text[channel_data["sub"]](message.content)
        else:
            result = self.translate_text[channel_data["main"]](message.content)
                
        await message.channel.send(result)
    
    
    def translate_jp(self, text):
        lang = self.translator_google.detect(text).lang
        
        if lang == "ko":
            return self.translator_papago(text, source=lang, dest="ja")
        else :
            # それ以外はDeepLを使用する
            return self.translator_deepl.translate_text(text, target_lang="JA").text


    def translate_ch(self, text):
        lang = self.translator_google.detect(text).lang
        
        if lang == "ko":
            return self.translator_papago(text, source=lang, dest="zh")
        else :
            # それ以外はDeepLを使用する
            txt = self.translator_deepl.translate_text(text, target_lang="zh").text
            return self.translator_google.translate(txt, dest="zh-tw").text


    def translate_en(self, text):
        return self.translator_deepl.translate_text(text, target_lang="EN-US").text
    
    def translate_kr(self, text):
        lang = self.translator_google.detect(text).lang
        return self.translator_papago(text, source=lang, dest="ko")
    
    def translate_th(self, text):
        return self.translator_google.translate(text, dest="th").text


    def translator_papago(self, text, source, dest):
        client_id = self.config['translate']['papago']['client_id']
        client_secret = self.config['translate']['papago']['client_secret']
        
        header = {"X-Naver-Client-Id":client_id,
                "X-Naver-Client-Secret":client_secret}
        
        url = "https://openapi.naver.com/v1/papago/n2mt" # API url
        
        
        
        data = {'text' : text,
                'source' : source,
                'target': dest} # translate to Korean

        response = requests.post(url, headers=header, data=data)
        rescode = response.status_code

        if(rescode==200):
            t_data = response.json()        
            return t_data['message']['result']['translatedText']
        else:
            print("n2mt Error Code:" , rescode) 
        
        
    # 絵文字のみか判定を行う
    def is_only_emoji(self, text):            
        text = emoji.replace_emoji(text, replace='')
        text = text.replace(" ", "")
        
        if len(text) == 0: return True
        if text[0] == "<" and text[-1] == ">":
            return True
        
        return False


def setup(bot):
    return bot.add_cog(Translate(bot), guilds=[discord.Object(id=os.getenv("DISCORD_SERVER_ID"))])
