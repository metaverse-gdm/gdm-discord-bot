import discord
from discord.ext import commands
import re
import os
import json
from dotenv import load_dotenv

load_dotenv(".env")

class ForumTracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.target_forum_id = int(os.getenv("DISCORD_TARGET_FORUM_ID", "0"))
        self.timestamp_pattern = re.compile(r"<t:(\d+):[a-zA-Z]>")
        # 保存先のパス
        self.file_path = "logs/forum_records.json"
        
        # 起動時にディレクトリがなければ作成
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"[ForumTracker] OK: Monitoring Forum ID {self.target_forum_id}")

    @commands.Cog.listener()
    async def on_thread_create(self, thread):
        if thread.parent_id != self.target_forum_id:
            return

        try:
            # 最初のメッセージを取得（少し待機が必要な場合があるためfetch）
            first_msg = await thread.fetch_message(thread.id)
            content = first_msg.content

            match = self.timestamp_pattern.search(content)
            
            if match:
                unix_timestamp = match.group(1)
                full_tag = match.group(0)
                
                # JSONに記録
                await self.record_to_json(thread.id, thread.name, unix_timestamp, full_tag)
                print(f"[Record] Saved to JSON: {thread.name}")
            else:
                print(f"[Log] No timestamp found in thread: {thread.name}")

        except Exception as e:
            print(f"Error fetching forum post: {e}")

    async def record_to_json(self, thread_id, title, timestamp, full_tag):
        """
        JSONファイルに配列形式で追記する
        """
        new_data = {
            "thread_id": thread_id,
            "title": title,
            "timestamp": int(timestamp),
            "full_tag": full_tag
        }

        data = []

        # 1. 既存のデータを読み込む
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if not isinstance(data, list): # 配列でない場合は初期化
                        data = []
            except json.JSONDecodeError:
                # ファイルが空や壊れている場合は空リストから開始
                data = []

        # 2. データを追加
        data.append(new_data)

        # 3. ファイルに書き戻す
        with open(self.file_path, "w", encoding="utf-8") as f:
            # indent=4 で人間が見やすい形式にする
            # ensure_ascii=False で日本語の文字化けを防ぐ
            json.dump(data, f, indent=4, ensure_ascii=False)

def setup(bot):
    return bot.add_cog(ForumTracker(bot))
