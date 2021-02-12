from discord.ext import commands


class admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def setserversstatus(self, ctx):
        await ctx.channel.purge(limit=1)
        guild_id = str(ctx.guild.id)
        await self.bot.pg_con.execute("UPDATE guild SET channel_status_cs_embed=$1 WHERE guild_id=$2",
                                      str(ctx.channel.id), guild_id)
        message = await ctx.send("Done.")
        await self.bot.pg_con.execute("UPDATE guild SET message_embed_id=$1 WHERE guild_id=$2", str(message.id),
                                      guild_id)

    @commands.command()
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def setcsgostats(self, ctx):
        await ctx.channel.purge(limit=1)
        guild_id = str(ctx.guild.id)
        await self.bot.pg_con.execute("UPDATE guild SET channel_statsp_cs_embed=$1 WHERE guild_id=$2",
                                      str(ctx.channel.id), guild_id)
        message = await ctx.send("Done.")
        await self.bot.pg_con.execute("UPDATE guild SET message_embed_statsp_id=$1 WHERE guild_id=$2", str(message.id),
                                      guild_id)

    @commands.command()
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def regionadd(self, ctx, *, message):
        guild_id = str(ctx.guild.id)
        liste = ["EU West", "EU East", "EU North", "Poland", "Spain",
                 "US Northwest", "US Northeast", "US Northcentral", "US Southwest", "US Southeast",
                 "Australia", "Brazil", "Chile", "Emirates", "India", "India East", "Peru", "Japan", "Hong Kong",
                 "Singapore", "South Africa",
                 "China Shanghai", "China Guangzhou", "China Tianjin"]
        if message == "list":
            await ctx.send(liste)
        else:
            if message in liste:
                RegionsToUpdate = await self.bot.pg_con.fetchrow(
                    "SELECT regions_serversstatus FROM guild WHERE guild_id=$1", str(guild_id))
                current_regions = RegionsToUpdate['regions_serversstatus']
                if current_regions is not None and message not in current_regions:
                    new_string_regions = current_regions + message + ";"
                    await self.bot.pg_con.execute("UPDATE guild SET regions_serversstatus=$1 WHERE guild_id=$2",
                                                  str(new_string_regions), guild_id)
                    await ctx.send("The region have been correctly added in the track list.")
                else:
                    message = message + ";"
                    await self.bot.pg_con.execute("UPDATE guild SET regions_serversstatus=$1 WHERE guild_id=$2",
                                                  str(message), guild_id)
                    await ctx.send("The region have been correctly added in the track list.")
            else:
                await ctx.send("The region you want to track don't exist, please look the list with `,region list`.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def cblock(self, ctx):
        guild_id = str(ctx.guild.id)

        bannedchannels = await self.bot.pg_con.fetchrow("SELECT blocked_channels FROM guild WHERE guild_id = $1",
                                                        guild_id)
        currentbanned = bannedchannels['blocked_channels']

        channelban = str(ctx.channel.id) + ";"

        if (currentbanned == None):
            await self.bot.pg_con.execute("UPDATE guild SET blocked_channels=$1 WHERE guild_id=$2", channelban,
                                          guild_id)
        else:
            if (str(ctx.channel.id) not in currentbanned):
                newchannels = currentbanned + channelban
                await self.bot.pg_con.execute("UPDATE guild SET blocked_channels=$1 WHERE guild_id=$2", newchannels,
                                              guild_id)

        await ctx.send("This channel is now going to be blocked for every commands of the bot.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def cunblock(self, ctx):
        guild_id = str(ctx.guild.id)
        bannedchannels = await self.bot.pg_con.fetchrow("SELECT blocked_channels FROM guild WHERE guild_id = $1",
                                                        guild_id)
        currentbanned = bannedchannels['blocked_channels']
        if (str(ctx.channel.id) in currentbanned):
            currentbanned = currentbanned.replace(str(ctx.channel.id) + ";", '')
            await self.bot.pg_con.execute("UPDATE guild SET blocked_channels=$1 WHERE guild_id=$2", currentbanned,
                                          guild_id)
            await ctx.send("This channel is now unblocked, you can use the bot commands here.")
        else:
            await ctx.send("This channel is not blocked.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def cunblockall(self, ctx):
        guild_id = str(ctx.guild.id)
        bannedchannels = await self.bot.pg_con.fetchrow("SELECT blocked_channels FROM guild WHERE guild_id = $1",
                                                        guild_id)
        if bannedchannels:
            await self.bot.pg_con.execute("UPDATE guild SET blocked_channels=$1 WHERE guild_id=$2", "", guild_id)
        await ctx.send("Now, you can use the bot commands everywhere on the server.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def hltvset(self, ctx):
        guild_id = str(ctx.guild.id)
        await self.bot.pg_con.execute("UPDATE guild SET channel_hltv_id=$1 WHERE guild_id=$2", str(ctx.channel.id),
                                      guild_id)
        await ctx.send("This channel is now going to be the channel where you will receive the hltv news.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def lvlset(self, ctx):
        guild_id = str(ctx.guild.id)
        await self.bot.pg_con.execute("UPDATE guild SET channel_lvl_id=$1 WHERE guild_id=$2", str(ctx.channel.id),
                                      guild_id)
        await ctx.send("This channel is now going to be the channel where you will receive the levels notifications.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def lvlmute(self, ctx):
        guild_id = str(ctx.guild.id)

        guild = await self.bot.pg_con.fetch("SELECT * FROM guild WHERE guild_id = $1", guild_id)
        # if not guild:
        # await self.bot.pg_con.execute("INSERT INTO guild (guild_id, mute_levels_notification) VALUES ($1, $2)",guild_id, False)

        state = await self.bot.pg_con.fetchrow("SELECT mute_levels_notification FROM guild WHERE guild_id = $1",
                                               guild_id)
        if not state['mute_levels_notification']:
            await self.bot.pg_con.execute("UPDATE guild SET mute_levels_notification=$1 WHERE guild_id=$2", True,
                                          guild_id)
            await ctx.send("You will no longer receive the levels notifications on this server.")
        else:
            await self.bot.pg_con.execute("UPDATE guild SET mute_levels_notification=$1 WHERE guild_id=$2", False,
                                          guild_id)
            await ctx.send("Now,you will receive the levels notifications on this server.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def modset(self, ctx, role):
        guild_id = str(ctx.guild.id)

        await self.bot.pg_con.execute("UPDATE guild SET mod_rank = $1 WHERE guild_id=$2", str(role), guild_id)
        await ctx.send("The role " + str(role) + " have been correctly set as the mod rank.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def updatechannel(self, ctx):
        guild_id = str(ctx.guild.id)
        await self.bot.pg_con.execute("UPDATE guild SET csupdateschannel = $1 WHERE guild_id=$2", str(ctx.channel.id),
                                      guild_id)
        await ctx.send("You will receive the csgo updates in this channel now.")

    @modset.error
    async def modset_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send(
                f":name_badge: `You need to be admin to use that command.` {ctx.author.mention} :name_badge:")
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"🤔 `Please specifie a role.` {ctx.author.mention} 🤔")
        if isinstance(error, commands.BadArgument):
            await ctx.send(f"😢 `That role don't exist, sorry` {ctx.author.mention} 😢")


def setup(bot):
    bot.add_cog(admin(bot))
