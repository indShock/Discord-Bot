import functools
import logging
from discord.ext import commands

logger = logging.getLogger(__name__)

def log_command(func):
    """Декоратор для логування виконання команд"""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        # args[1] - це ctx для команд
        if len(args) > 1 and hasattr(args[1], 'command'):
            ctx = args[1]
            logger.info(f"Command executed: {ctx.command} by {ctx.author}")
        return await func(*args, **kwargs)
    return wrapper

def has_permissions(**perms):
    """Декоратор для перевірки прав користувача"""
    def predicate(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            if len(args) > 1 and hasattr(args[1], 'author'):
                ctx = args[1]
                if not all(getattr(ctx.author.guild_permissions, perm, None) for perm in perms.keys()):
                    await ctx.send("❌ У вас недостатньо прав для виконання цієї команди!")
                    return
            return await func(*args, **kwargs)
        return wrapper
    return predicate

# Видаляємо власний cooldown, використовуємо вбудований з discord.py