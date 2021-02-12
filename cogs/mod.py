import discord
from discord.ext import commands
import time


class Mod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(ban_members=True)
    @commands.guild_only()
    async def bword(self, ctx, word):
        guild_id = str(ctx.guild.id)
        wordsbanned = await self.bot.pg_con.fetchrow("SELECT ban_words FROM guild WHERE guild_id = $1", guild_id)
        currentbans = None
        if wordsbanned:
            currentbans = wordsbanned['ban_words']

        await ctx.send(f"I just added the word `{word}` to the blacklist")
        word = str(word + ";")
        if currentbans == None:
            await self.bot.pg_con.execute("UPDATE guild SET ban_words=$1 WHERE guild_id=$2", word, guild_id)
        else:
            newbans = currentbans + word
            await self.bot.pg_con.execute("UPDATE guild SET ban_words=$1 WHERE guild_id=$2", newbans, guild_id)

    @commands.command()
    @commands.has_permissions(ban_members=True)
    @commands.guild_only()
    async def unbword(self, ctx, message):
        guild_id = str(ctx.guild.id)
        bannedwords = await self.bot.pg_con.fetchrow("SELECT ban_words FROM guild WHERE guild_id = $1", guild_id)
        currentbannedwords = bannedwords['ban_words']
        if (str(message) in currentbannedwords):
            currentbannedwords = currentbannedwords.replace(str(message) + ";", '')
            await self.bot.pg_con.execute("UPDATE guild SET ban_words=$1 WHERE guild_id=$2", currentbannedwords,
                                          guild_id)
            await ctx.send(f"The word `{message}` is now allowed.")
        else:
            await ctx.send(f"The word `{message}` is not blocked.")

    @commands.command()
    @commands.has_permissions(ban_members=True)
    @commands.guild_only()
    async def unbwordall(self, ctx):
        guild_id = str(ctx.guild.id)
        wordsbanned = await self.bot.pg_con.fetchrow("SELECT ban_words FROM guild WHERE guild_id = $1", guild_id)
        if wordsbanned:
            await self.bot.pg_con.execute("UPDATE guild SET ban_words=$1 WHERE guild_id=$2", "", guild_id)
        await ctx.send(f"The ban words have been reseted.")

    @commands.command()
    @commands.has_permissions(kick_members=True)
    # @commands.has_any_role("rolename"/roleid,"rolename"/roleid,"rolename"/roleid ...)
    @commands.guild_only()
    async def clear(self, ctx, amount: int):
        deleted = await ctx.channel.purge(limit=amount + 1)
        await ctx.send(f"{len(deleted)} messages deleted by {ctx.author}.")
        time.sleep(1)
        await ctx.channel.purge(limit=1)

    @commands.command()
    @commands.has_permissions(kick_members=True)
    @commands.guild_only()
    async def kick(self, ctx, user: discord.Member, *, reason=None):
        await user.kick(reason=reason)
        await ctx.channel.purge(limit=1)
        await ctx.send(f"{user.name} just have been kicked by {ctx.author}.")

    @commands.command()
    @commands.has_permissions(ban_members=True)
    @commands.guild_only()
    async def ban(self, ctx, user: discord.Member, *, reason=None):
        await user.ban(reason=reason)
        await ctx.channel.purge(limit=1)
        await ctx.send(f"{user.name} just have been banned by {ctx.author}.")

    @commands.command()
    @commands.has_permissions(ban_members=True)
    @commands.guild_only()
    async def unban(self, ctx, *, member):
        banned_users = await ctx.guild.bans()
        member_name, member_discriminator = member.split("#")

        for ban_entry in banned_users:
            user = ban_entry.user

            if (user.name, user.discriminator) == (member_name, member_discriminator):
                await ctx.guild.unban(user)
                await ctx.send(f"{user.mention} just have been unbanned by {ctx.author.mention}.")
                return

    @clear.error
    async def clear_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send(f":name_badge: `Tu ne possède pas la permission.` {ctx.author.mention} :name_badge:")
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(
                f":name_badge: `Pense à spécifier le nombre de messages à supprimer.` {ctx.author.mention} :name_badge:")
        if isinstance(error, commands.BadArgument):
            await ctx.send(f":name_badge: `Il faut donner un entier.` {ctx.author.mention} :name_badge:")

    @ban.error
    async def ban_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send(f":name_badge: `Tu ne possède pas la permission.` {ctx.author.mention} :name_badge:")
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f":name_badge: `Tu ne dis pas qui bannir.` {ctx.author.mention} :name_badge:")
        if isinstance(error, commands.BadArgument):
            await ctx.send(
                f":name_badge: `Cet utilisateur n'existe pas, pense à le mentionner avec le @` {ctx.author.mention} :name_badge:")

    @kick.error
    async def kick_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send(f":name_badge: `Tu ne possède pas la permission.` {ctx.author.mention} :name_badge:")
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f":name_badge: `Tu ne dis pas qui exclure.` {ctx.author.mention} :name_badge:")
        if isinstance(error, commands.BadArgument):
            await ctx.send(
                f":name_badge: `Cet utilisateur n'existe pas, pense à le mentionner avec le @` {ctx.author.mention} :name_badge:")


def setup(bot):
    bot.add_cog(Mod(bot))
