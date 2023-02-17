import discord
from settings import *
from log import *

def is_private(channel):
    return isinstance(channel, discord.abc.PrivateChannel)

def is_allowed(channel):
    return is_private(channel) or channel.name in ALLOWED_CHAN

async def is_admin(ctx):
    return ctx.author.id in ADMIN

async def send_msg(msg_chunks, channel):
    res = ''
    c = 0
    for m in msg_chunks:
        c += 1
        if len(m) > 2000:
            log_error("(send_msg) Message too long, cannot send.")
            return 1

        if len(res + m) > 2000:
            await channel.send(res)
            res = ''

        res += m + "\n"
    await channel.send(res)
    return 0
