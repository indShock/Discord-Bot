import discord
from discord.ext import commands
import logging
import asyncio
from datetime import datetime
from config import TOKEN, PREFIX
from database import init_db, get_db, User, UserStats
from decorators import log_command, has_permissions
import random
import sqlalchemy as sa

# Налаштування логування
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class MyBot(commands.Bot):
    def __init__(self):
        # Правильні налаштування intents
        intents = discord.Intents.default()
        intents.messages = True
        intents.message_content = True
        intents.members = True
        intents.guilds = True

        super().__init__(command_prefix=PREFIX, intents=intents)

        # Ініціалізація бази даних
        init_db()

    async def setup_hook(self):
        """Виконується при запуску бота"""
        logger.info("Бот запускається...")

    async def on_ready(self):
        """Виконується коли бот готовий до роботи"""
        logger.info(f'Бот {self.user} увійшов у систему!')
        print(f'Бот {self.user} онлайн!')

        # Створюємо активність бота
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.listening,
                name=f"{PREFIX}help"
            )
        )

    async def on_message(self, message):
        """Обробка всіх повідомлень"""
        if message.author == self.user:
            return

        # Оновлення статистики користувача
        await self.update_user_stats(message)

        await self.process_commands(message)

    async def update_user_stats(self, message):
        """Оновлення статистики користувача"""
        try:
            with next(get_db()) as db:
                user = db.query(User).filter(User.discord_id == message.author.id).first()

                if not user:
                    user = User(
                        discord_id=message.author.id,
                        username=str(message.author),
                        message_count=1,
                        xp=5,
                        level=1
                    )
                    db.add(user)
                else:
                    user.message_count += 1
                    user.xp += 5

                    # Перевірка на новий рівень
                    new_level = user.xp // 100 + 1
                    if new_level > user.level:
                        user.level = new_level
                        await message.channel.send(
                            f"🎉 {message.author.mention} досяг {new_level} рівня! 🎊"
                        )

                db.commit()
        except Exception as e:
            logger.error(f"Помилка оновлення статистики: {e}")


# Ініціалізація бота
bot = MyBot()


# Команди для користувачів
@bot.command(name='hello')
@log_command
@commands.cooldown(1, 5, commands.BucketType.user)
async def hello(ctx):
    """Привітальна команда"""
    await ctx.send(f'Привіт, {ctx.author.mention}! 👋')


@bot.command(name='ping')
@log_command
async def ping(ctx):
    """Перевірка пінгу бота"""
    latency = round(bot.latency * 1000)
    await ctx.send(f'🏓 Понг! {latency}мс')


@bot.command(name='stats')
@log_command
async def stats(ctx, member: discord.Member = None):
    """Показати статистику користувача"""
    target = member or ctx.author

    try:
        with next(get_db()) as db:
            user = db.query(User).filter(User.discord_id == target.id).first()

            if user:
                embed = discord.Embed(
                    title=f"📊 Статистика {target.name}",
                    color=discord.Color.blue()
                )
                embed.add_field(name="Рівень", value=user.level, inline=True)
                embed.add_field(name="XP", value=user.xp, inline=True)
                embed.add_field(name="Повідомлення", value=user.message_count, inline=True)

                if target.avatar:
                    embed.set_thumbnail(url=target.avatar.url)

                await ctx.send(embed=embed)
            else:
                await ctx.send("❌ Статистика не знайдена!")
    except Exception as e:
        logger.error(f"Помилка статистики: {e}")
        await ctx.send("❌ Помилка при отриманні статистики!")


# Команди модерації
@bot.command(name='clear')
@has_permissions(manage_messages=True)
@log_command
async def clear(ctx, amount: int = 5):
    """Очистити повідомлення (тільки для модераторів)"""
    if amount > 100:
        await ctx.send("❌ Не можна видалити більше 100 повідомлень!")
        return

    try:
        deleted = await ctx.channel.purge(limit=amount + 1)
        message = await ctx.send(f'✅ Видалено {len(deleted) - 1} повідомлень!')
        await asyncio.sleep(5)
        await message.delete()
    except Exception as e:
        logger.error(f"Помилка очищення: {e}")
        await ctx.send("❌ Помилка при видаленні повідомлень!")


@bot.command(name='kick')
@has_permissions(kick_members=True)
@log_command
async def kick(ctx, member: discord.Member, *, reason="Не вказано"):
    """Кікнути користувача (тільки для модераторів)"""
    try:
        await member.kick(reason=reason)
        await ctx.send(f'✅ {member.mention} був кікнут! Причина: {reason}')
    except Exception as e:
        logger.error(f"Помилка кіку: {e}")
        await ctx.send("❌ Помилка при кіку користувача!")


@bot.command(name='ban')
@has_permissions(ban_members=True)
@log_command
async def ban(ctx, member: discord.Member, *, reason="Не вказано"):
    """Забанити користувача (тільки для модераторів)"""
    try:
        await member.ban(reason=reason)
        await ctx.send(f'✅ {member.mention} був забанений! Причина: {reason}')
    except Exception as e:
        logger.error(f"Помилка бана: {e}")
        await ctx.send("❌ Помилка при бані користувача!")


# Розважальний модуль
@bot.command(name='advice')
@log_command
@commands.cooldown(1, 10, commands.BucketType.user)
async def advice(ctx):
    """Отримати випадкову пораду"""
    advice_list = [
        "Ніколи не відкладай на завтра те, що можна зробити сьогодні!",
        "Вірь у себе і все вийде!",
        "Краще робити і шкодувати, ніж не робити і шкодувати!",
        "Не бійся помилятися - це частина навчання!",
        "Завжди знайди час для відпочинку!",
        "Читай більше книг - вони розширюють кругозір!",
        "Будь добрим до інших - це повертається!"
    ]

    advice_text = random.choice(advice_list)
    embed = discord.Embed(
        title="💡 Порада дня",
        description=advice_text,
        color=discord.Color.gold()
    )
    await ctx.send(embed=embed)


@bot.command(name='ask')
@log_command
@commands.cooldown(1, 5, commands.BucketType.user)
async def ask(ctx, *, question):
    """Задати питання боту"""
    responses = [
        "Так, звичайно! ✅",
        "Ні, не думаю. ❌",
        "Можливо... 🤔",
        "Скоріше за все так! 👍",
        "Мабуть ні. 👎",
        "Абсолютно впевнений - так! 🌟",
        "Зосередься і спитай ще раз! 🔄",
        "Наразі не можу відповісти... ⏳"
    ]

    response = random.choice(responses)
    embed = discord.Embed(
        title="🎱 Магічна куля",
        description=f"Питання: {question}\nВідповідь: {response}",
        color=discord.Color.purple()
    )
    await ctx.send(embed=embed)


# Обробка помилок
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("❌ Команда не знайдена! Спробуй !help")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ У вас недостатньо прав для цієї команди!")
    elif isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"⏳ Зачекай {error.retry_after:.1f} секунд перед наступним використанням!")
    else:
        logger.error(f"Помилка команди: {error}")
        await ctx.send("❌ Сталася помилка при виконанні команди!")


if __name__ == "__main__":
    try:
        bot.run(TOKEN)
    except Exception as e:
        logger.error(f"Помилка запуску бота: {e}")