import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
PREFIX = os.getenv('BOT_PREFIX', '!')
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///bot.db')