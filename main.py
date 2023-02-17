import discord
from discord.ext import commands
from discord.utils import get
from copy import deepcopy
import os
import utils
import pickle
from log import *
from settings import *


# Code for the bot itself (parse commands)
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
client = commands.Bot(command_prefix='.', intents=intents)
client.help_command = None


@client.command()
@commands.check(utils.is_admin)
async def add_loser(ctx, user_id):
    member = ctx.guild.get_member(int(user_id))
    if member is None:
        await ctx.message.reply("Utilisateur introuvable")
        return

    role = get(ctx.guild.roles, name=LOSER_ROLE_NAME)
    await member.add_roles(role)
    msg = "Role {} added to {}".format(LOSER_ROLE_NAME, member.display_name)
    log_info(msg)
    await utils.send_msg([msg], ctx)


@client.command()
@commands.check(utils.is_admin)
async def rm_loser(ctx, user_id):
    member = ctx.guild.get_member(int(user_id))
    if member is None:
        await ctx.message.reply("Utilisateur introuvable")
        return

    role = get(ctx.guild.roles, name=LOSER_ROLE_NAME)
    await member.remove_roles(role)
    msg = "Role {} removed from {}".format(LOSER_ROLE_NAME, member.display_name)
    log_info(msg)
    await utils.send_msg([msg], ctx)


@client.command(name='<:nini:696420822855843910>')
@commands.check(utils.is_admin)
async def nini(ctx):
    await scoreboard(ctx)


@client.command(name='S2<:nini:696420822855843910>')
@commands.check(utils.is_admin)
async def niniS2(ctx):
    await scoreboard(ctx, NINI_SAVE_FILE_PREFIX + "nini_saison2", "Ceci est le classement de la Saison 2 du NiNi, qui a commencée le 1er Février 2021 à 0h00 !")


async def scoreboard(ctx, histfile=None, preamble=None):
    #return
    log_info("nini start")
    if preamble is not None:
        await utils.send_msg([preamble], ctx)
    await utils.send_msg(["Je commence à lire vos messages... :drum:"], ctx)
    message = ctx.message

    if histfile is not None:
        filename = histfile
    else:
        filename = NINI_SAVE_FILE_PREFIX + ctx.message.channel.name

    message_count = 0
    if os.path.isfile(filename):
        log_info("nini history file found")
        with open(filename, "rb") as f:
            history = pickle.load(f)
        date = history[0]
        all_losers = history[1]
    else:
        log_error("nini history file not found")
        all_losers = {}
        date = None

    old_losers = deepcopy(all_losers)

    async for m in message.channel.history(limit=None, after=date, oldest_first=True):
        message_count += 1
        auth_id = m.author.id
        if auth_id not in all_losers:
            all_losers[auth_id] = {"messages": 0, "errors": 0, "streak": 0, "streak_max": 0, "username": m.author.display_name}
        all_losers[auth_id]["messages"] += 1
        all_losers[auth_id]["username"] = m.author.display_name

        react_lose = False
        losers = set()
        for reaction in m.reactions:
            if reaction.emoji == '🚨':
                if not react_lose:
                    losers.add((m.author.display_name, auth_id))
                await m.add_reaction('🚨')
            if reaction.emoji in ['👌', '🙉', '🙊', '🙈', '🚳', '🚷', '⛔', '🚭', '📵', '🚯', '🔕', '🆗', '🙆', '🙅', '😶'] :
                if not react_lose:
                    losers = set()
                    react_lose = True

                for l in await reaction.users().flatten():
                    losers.add((l.display_name, l.id))
                await m.add_reaction('🚨')

        for l, l_id in losers:
            if l_id not in all_losers:
                all_losers[l_id] = {"messages": 0, "errors": 0, "streak": 0, "streak_max": 0, "username": l}
            all_losers[l_id]["errors"] += 1
            all_losers[l_id]["streak"] = -1                    # SO THE ERROR MESSAGE DOES NOT COUNT THEIR STREAK ANYMORE

        all_losers[auth_id]["streak"] += 1
        all_losers[auth_id]["streak_max"] = max(all_losers[auth_id]["streak_max"], all_losers[auth_id]["streak"])

    # SAVE DATA AS PICKLE

    date = m.created_at
    with open(filename, "wb") as f:
        pickle.dump([date, all_losers], f)

    # WEEKLY RANKING UPDATE AND LOSERS OF THE WEEK

    # LOSERS OF THE WEEK COMPUTE (BEFORE SORTING DICT)
    loss = {}

    for uid in all_losers:
        if uid not in old_losers:
            loss[uid] = (all_losers[uid]["errors"], all_losers[uid]["username"])
        else:
            nLoss = all_losers[uid]["errors"] - old_losers[uid]["errors"]
            if nLoss > 0:
                loss[uid] = (nLoss, all_losers[uid]["username"])

    loss_ranking = sorted([(uid, loss[uid][1], loss[uid][0]) for uid in loss if loss[uid][0] > 0], key=lambda x: x[2], reverse=True)

    ratios = [data["messages"]/data["errors"] if data["errors"] != 0 else -1 for _, data in all_losers.items() if (data["messages"] >= 300)]
    max_ratio = -1
    if len(ratios) > 0:
        max_ratio = max(ratios)

    # RANKING UPDATE
    old_losers = sorted([(uid, data) for uid, data in old_losers.items() if (data["messages"] >= 300)],
                        key=lambda x: x[1]["messages"]/x[1]["errors"] if x[1]["errors"] != 0 else max_ratio+x[1]["messages"], reverse=True)

    old_ranking = {}
    for rank, (uid, data) in enumerate(old_losers):
        old_ranking[uid] = rank

    all_losers_sorted = sorted([(uid, data) for uid, data in all_losers.items() if (data["messages"] >= 300)],
                                key=lambda x: x[1]["messages"]/x[1]["errors"] if x[1]["errors"] != 0 else max_ratio+x[1]["messages"], reverse=True)

    for new_rank, (uid, data) in enumerate(all_losers_sorted):
        if uid not in old_ranking:
            old_rank = len(old_ranking)
        else:
            old_rank = old_ranking[uid]
        update = old_rank-new_rank
        if update > 0:
            update = "🔼"+str(update)
        elif update < 0:
            update = "🔽"+str(-update)
        else:
            update = "🟦0"
        data["rank_update"] = update

    # RANKING MESSAGE
    res = ["Classement du <:nini:696420822855843910>"]
    res.append("`{} | {} | {} | {} | {} | {} | {}`".format("Pseudo".center(40), "# messages".center(12), "# défaites".center(12),
                                                      "Ratio".center(7), "Streak".center(12), "Streak max".center(12), "Évolution".center(12)))

    for uid, data in all_losers_sorted:
        res.append("`{} | {} | {} | {} | {} | {} | {}`".format(data["username"].center(40), str(data["messages"]).center(12), str(data["errors"]).center(12),
                                                          str(int(data["messages"]/data["errors"]) if data["errors"] != 0 else "∞").center(7), str(data["streak"]).center(12), str(data["streak_max"]).center(12), data["rank_update"].center(12)))

    log_info('\n'.join(res))


    # LOSER MESSAGE AND ROLES
    nLoser = len(loss_ranking)
    loss_ranking = loss_ranking[:nLoser]

    if nLoser == 0:
        loseMsg = "Il n'y a pas de grand loooooser.euse cette semaine."
    elif nLoser == 1:
        loseMsg = "Le.a grand.e loooooser.euse de cette semaine est "
    else:
        loseMsg = "Les {} grand.e.s loooooser.euse.s de cette semaine sont ".format(nLoser)

    for n, l in enumerate(loss_ranking):
        loseMsg += l[1] + " ({})".format(l[2])
        if n < nLoser-2:
            loseMsg += ", "
        elif n < nLoser-1:
            loseMsg += " et "
        else:
            loseMsg += "."

    res.append(loseMsg)

    # REMOVE ALL CURRENT LOSERS
    role = get(ctx.guild.roles, name=LOSER_ROLE_NAME)

    for member in ctx.guild.members:
        if role in member.roles:
            await member.remove_roles(role)

    for uid, name, _ in loss_ranking:
        try:
            member = ctx.guild.get_member(uid)
            await member.add_roles(role)
            log_info("Loser role added to {}.".format(name))
        except:
            continue

    # SEND MESSAGE
    res.append("J'ai lu {} messages !".format(message_count))
    await utils.send_msg(res, ctx)
    log_info("nini command done! {} messages".format(message_count))


@client.event
async def on_ready():
    log_info("We have logged in as {0.user}".format(client))


@client.event
async def on_message(message):
    if message.author.id == client.user.id:
        return

    if not utils.is_allowed(message.channel):
        return

    if message.content.startswith("."):
        log_info("{} ({}): {}".format(message.author.name, message.author.id, message.content))

    await client.process_commands(message)


client.run(BOT_TOKEN)
