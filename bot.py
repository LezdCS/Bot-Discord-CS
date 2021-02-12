import discord
import os
from discord.ext import commands
import asyncpg


async def create_db_pool():
    bot.pg_con = await asyncpg.create_pool(database="postgres", user="postgres", password="LezdSql39", port="5433")


prefix = ","
bot = commands.Bot(command_prefix=commands.when_mentioned_or(prefix),
                   description='CS:BOT will be always here for you')


@bot.event
async def on_ready():
    i = 0
    print('Logged in as {0} ({0.id})'.format(bot.user))
    print('------')
    print(discord.__version__)

    for server in bot.guilds:
        print("---->" + server.name)
        for _ in server.members:
            i = i + 1

    await bot.change_presence(status=discord.Status.online, activity=discord.Game(',help - ' + str(i) + ' users'))


@bot.event
async def on_guild_join(guild):
    guild_search = await bot.pg_con.fetchrow("SELECT guild_id FROM guild WHERE guild_id=$1", str(guild.id))
    if not guild_search:
        await bot.pg_con.execute("INSERT INTO guild (guild_id, mute_levels_notification) VALUES ($1, $2)", str(guild.id), False)
    for member in guild.members:
        user_search = await bot.pg_con.fetchrow("SELECT user_id FROM users WHERE user_id=$1", str(member.id))
        if not user_search:
            await bot.pg_con.execute("INSERT INTO levels (user_id , guild_id, user_lvl, user_xp) VALUES ($1 , $2, $3 , $4)", str(member.id), str(guild.id), 0, 0)
            await bot.pg_con.execute("INSERT INTO users (user_id , success_rate) VALUES ($1 , $2)", str(member.id), 0)

for cog in os.listdir(".\\cogs"):
    if cog.endswith(".py"):
        try:
            cog = f"cogs.{cog.replace('.py', '')}"
            bot.load_extension(cog)
        except Exception as e:
            print(f"{cog} can not be loaded :")
            raise e

bot.loop.run_until_complete(create_db_pool())

bot.run('NDg1ODUwMDU5NjYyMDMyODk2.XM8zpQ.6xH8-0sI5iFVAWadY-keF7hCwYs')
