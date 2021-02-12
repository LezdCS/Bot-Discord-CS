import discord
from discord.ext import commands
from requests import get
from lxml import html
import requests


class Util(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def lvl_up(self, user):
        cur_xp = user['user_xp']
        cur_lvl = user['user_lvl']
        if cur_lvl != 18:
            if cur_xp >= round((4 * (cur_lvl ** 3)) / 5):
                await self.bot.pg_con.execute("UPDATE levels SET user_lvl = $1 WHERE user_id=$2 AND guild_id = $3",
                                              cur_lvl + 1, user['user_id'], user['guild_id'])
                return True
            else:
                return False

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
        author_id = str(message.author.id)
        author_mention = message.author.mention
        try:
            guild_id = str(message.guild.id)

            bannedchannels = await self.bot.pg_con.fetchrow("SELECT blocked_channels FROM guild WHERE guild_id = $1",
                                                            guild_id)
            currentbanned = bannedchannels['blocked_channels']
            if (str(message.channel.id) in str(currentbanned) and message.content[
                0] == ',' and message.content != ',cunblockall' and message.content != ',cunblock'):
                channel = self.bot.get_channel(int(message.channel.id))
                await message.delete()
                async for message in channel.history(limit=1):
                    if message.author == self.bot.user:
                        await message.delete()
                await channel.send(f"Sorry {author_mention}, you can't use commands in this channel.")

            wordsbanned = await self.bot.pg_con.fetchrow("SELECT ban_words FROM guild WHERE guild_id = $1", guild_id)
            currentbans = wordsbanned['ban_words']
            if currentbans:
                currentbans = currentbans.split(';')
            wordsecurity = message.content.lower()
            if currentbans and wordsecurity in currentbans and message.author != self.bot.user:
                channel = self.bot.get_channel(int(message.channel.id))
                await message.delete()
                await channel.send(f"Sorry {message.author.mention}, the word `{message.content}` is not allowed.")

            user = await self.bot.pg_con.fetch("SELECT * FROM levels WHERE user_id = $1 and guild_id = $2", author_id,
                                               guild_id)

            await self.bot.pg_con.execute("UPDATE levels SET user_xp = $1 WHERE user_id=$2 AND guild_id = $3",
                                          user['user_xp'] + 1, author_id, guild_id)

            if await self.lvl_up(user):
                rank = ["SILVER I", "SILVER II", "SILVER III", "SILVER IV", "Silver Elite", "Silver Elite Master",
                        "Gold Nova 1", "Gold Nova 2", "Gold Nova 3", "Gold Nova Master",
                        "Master Guardian 1", "Master Guardian 2", "Master Guardian Elite",
                        "Distinguished Master Guardian CS:GO", "Legendary Eagle", "Legendary Eagle Master",
                        "Supreme Master First Class", "Global Elite"]

                check_autorisation = await self.bot.pg_con.fetchrow(
                    "SELECT mute_levels_notification FROM guild WHERE  guild_id = $1", guild_id)
                channel_to_send = await self.bot.pg_con.fetchrow(
                    "SELECT channel_lvl_id FROM guild WHERE  guild_id = $1 AND channel_lvl_id IS NOT NULL", guild_id)
                if not channel_to_send:
                    if (check_autorisation['mute_levels_notification'] == False):
                        await message.channel.send(
                            f"{message.author.mention} is now ranked " + rank[user['user_lvl']] + ".")
                else:
                    if (check_autorisation['mute_levels_notification'] == False):
                        sendto = channel_to_send['channel_lvl_id']
                        channel = self.bot.get_channel(int(sendto))
                        await channel.send(f"{message.author.mention} rand up to " + rank[user['user_lvl']] + ".")
        except:
            pass

    @commands.command()
    @commands.guild_only()
    async def cp(self, ctx, member: discord.Member = None):
        if not member:
            member = ctx.author

        # Here we check if the value of each permission is True.
        perms = '\n'.join(perm for perm, value in member.guild_permissions if value)

        embed = discord.Embed(title='Permissions for:', description=ctx.guild.name, colour=member.colour)
        embed.set_author(icon_url=member.avatar_url, name=str(member))
        # \uFEFF is a Zero-Width Space, which basically allows us to have an empty field name.
        embed.add_field(name='\uFEFF', value=perms)

        await ctx.send(content=None, embed=embed)

    @commands.command()
    async def add(self, ctx, steamprofile):

        author_id = str(ctx.author.id)

        steamid = []
        if steamprofile[27:29] == "id":
            pseudo = steamprofile[30:len(steamprofile)]

            url = 'https://steamidfinder.com/lookup/{}/'.format(pseudo)
            page = requests.get(url)
            tree = html.fromstring(page.content)
            steamidfind = tree.xpath('/html/body/div[2]/div[1]/div[1]/div/article/div/div[3]/code[3]')
            for user in steamidfind:
                steamid.append(user.text)

        if steamprofile[27:35] == "profiles":
            steamid.append(steamprofile[36:len(steamprofile)])

        profile = await self.bot.pg_con.fetch("SELECT * FROM vac WHERE steam_id = $1 AND report_author_id = $2",
                                              steamid[0], author_id)

        if not profile:
            url = 'http://api.steampowered.com/ISteamUser/GetPlayerBans/v1/?key=1244D7A7656A97CD1D6FB4A06C1EA8E7&steamids={}'.format(
                steamid[0])
            response = get(url)
            idsteam, comban, vacban, numofvac, dslb, NoGB, EcoBan = response.text.split(',')
            await self.bot.pg_con.execute(
                "INSERT INTO vac (steam_id , vac_status, report_author_id) VALUES ($1 , $2, $3)", steamid[0],
                vacban[12:len(vacban)], author_id)

        await ctx.send("This profile has been correctly added to our database and will be now tracked.")


def setup(bot):
    bot.add_cog(Util(bot))
