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
        self.file_path = "logs/forum_records.json"
        
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"[ForumTracker] OK: Monitoring Forum ID {self.target_forum_id}")

    @commands.Cog.listener()
    async def on_thread_create(self, thread):
        if thread.parent_id != self.target_forum_id:
            return

        try:
            # 最初のメッセージを取得（投稿内容と投稿者情報を取得）
            first_msg = await thread.fetch_message(thread.id)
            content = first_msg.content
            
            # 投稿者情報の取得
            author = first_msg.author
            author_name = author.display_name # サーバー内の名前
            author_id = author.id             # ユーザーID

            match = self.timestamp_pattern.search(content)
            
            if match:
                unix_timestamp = match.group(1)
                full_tag = match.group(0)
                
                await self.record_to_json(
                    thread_id=thread.id, 
                    title=thread.name, 
                    timestamp=unix_timestamp, 
                    full_tag=full_tag,
                    author_name=author_name,
                    author_id=author_id
                )
                print(f"[Record] Saved to JSON: {thread.name} by {author_name}")
            else:
                print(f"[Log] No timestamp found in thread: {thread.name}")

        except Exception as e:
            print(f"Error fetching forum post: {e}")

    async def record_to_json(self, thread_id, title, timestamp, full_tag, author_name, author_id):
        """
        JSONファイルに配列形式で追記する（投稿者情報を含む）
        """
        new_data = {
            "thread_id": thread_id,
            "title": title,
            "author": {
                "name": author_name,
                "id": author_id
            },
            "timestamp": int(timestamp),
            "full_tag": full_tag,
            "created_at": discord.utils.utcnow().isoformat()
        }

        data = []

        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if not isinstance(data, list):
                        data = []
            except json.JSONDecodeError:
                data = []

        data.append(new_data)

        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

def setup(bot):
    return bot.add_cog(ForumTracker(bot))
