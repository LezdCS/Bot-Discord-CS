import discord
from discord.ext import commands
from lxml import html
import requests
from requests import get
from bs4 import BeautifulSoup
from python_utils import converters


def get_parsed_page(url):
    # This fixes a blocked by cloudflare error i've encountered
    headers = {
        "referer": "https://www.hltv.org/stats",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    return BeautifulSoup(requests.get(url, headers=headers).text, "lxml")


def top30teams():
    global teamlist, teamnameclassement, teampointsclassement, teamchangeclassement
    page = get_parsed_page("http://www.hltv.org/ranking/teams/")
    teams = page.find("div", {"class": "ranking"})
    teamlist = []
    teamnameclassement = []
    teampointsclassement = []
    teamchangeclassement = []
    for team in teams.find_all("div", {"class": "ranked-team standard-box"}):
        newteam = {'name': team.find('div', {"class": "ranking-header"}).select('.name')[0].text.strip(),
                   'rank': converters.to_int(team.select('.position')[0].text.strip(), regexp=True),
                   'rank-points': converters.to_int(team.find('span', {'class': 'points'}).text, regexp=True),
                   'team-id': converters.to_int(team.find('a', {'class': 'details moreLink'})['href'].split('/')[-1])}
        teamnameclassement.append(team.find('div', {"class": "ranking-header"}).select('.name')[0].text.strip())
        teampointsclassement.append(str(converters.to_int(team.find('span', {'class': 'points'}).text, regexp=True)))
        changement = team.find('div', {"class": "change"}).text  # CHANHGEMENT DEP POSITION DANS LE CLASSEMENT
        changement = changement.split('>')

        teamchangeclassement.append(changement[0])
        teamlist.append(newteam)
    return teamlist


def get_team_info(teamname):
    global team_info

    url = "https://www.hltv.org/search?query={}".format(teamname)
    page = requests.get(url)
    tree = html.fromstring(page.content)
    teamidfind = tree.xpath('//a/@href')

    linksresult = []
    for team in teamidfind:
        if team.startswith("/team/", 0):
            linksresult.append(team)


    teamHREF = str(linksresult[0])
    if teamHREF[5:6] == "/" and teamHREF[11:12] == "/":
        teamid = teamHREF[6:11]
    if teamHREF[5:6] == "/" and teamHREF[10:11] == "/":
        teamid = teamHREF[6:10]
    if teamHREF[5:6] == "/" and teamHREF[9:10] == "/":
        teamid = teamHREF[6:9]
    if teamHREF[5:6] == "/" and teamHREF[8:9] == "/":
        teamid = teamHREF[6:8]
    if teamHREF[5:6] == "/" and teamHREF[7:8] == "/":
        teamid = teamHREF[6:7]

    page = get_parsed_page("http://www.hltv.org/?pageid=179&teamid=" + str(teamid))
    team_info = {}
    team_info['id'] = teamid
    team_info['team-name'] = page.find("div", {"class": "context-item"}).text

    current_lineup = _get_current_lineup(page.find_all("div", {"class": "col teammate"}))
    team_info['current-lineup'] = current_lineup

    team_stats_columns = page.find_all("div", {"class": "columns"})
    team_stats = {}
    for columns in team_stats_columns:
        stats = columns.find_all("div", {"class": "col standard-box big-padding"})

        for stat in stats:
            stat_value = stat.find("div", {"class": "large-strong"})
            stat_title = stat.find("div", {"class": "small-label-below"}).text
            team_stats[stat_title] = stat_value

    team_info['stats'] = team_stats

    return team_info


def get_image(team):
    url = "https://liquipedia.net/counterstrike/index.php?search={}".format(team)
    page = requests.get(url)
    tree = html.fromstring(page.content)
    teamidfind = tree.xpath('//img/@src')

    imageresult = []
    for image in teamidfind:
        if image.startswith("/commons/images/thumb/", 0):
            imageresult.append(image)
    page.connection.close()
    return f"https://liquipedia.net{imageresult[0]}"


def _get_current_lineup(player_anchors):
    """
    helper function for function above
    :return: list of players
    """
    players = []
    for player_anchor in player_anchors[0:5]:
        player = {'nickname': player_anchor.find("div", {"class": "teammate-info standard-box"}).find("div", {
            "class": "text-ellipsis"}).text}
        players.append(player)
    return players


class Hltv(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def ladder(self, ctx):
        """Display the current HLTV ladder"""
        global h1, h2, h3, h4, h5, page
        global top
        h1, h2, h3, h4, h5 = 0, 1, 2, 3, 4
        page = 1
        top30teams()
        embed = discord.Embed(title="Ranking | Page {}/6 🏆".format(page), url="https://hltv.org/ranking/teams",
                              color=6532572)  # ctx.author.colour)
        embed.set_author(name=str(ctx.author.name),
                         icon_url="https://is1-ssl.mzstatic.com/image/thumb/Purple128/v4/33/54/b0/3354b09c-ccb5-7bd4-5cd4-f71cc1964406/AppIcon-1x_U007emarketing-85-220-5.png/246x0w.jpg")

        embed.set_thumbnail(url=ctx.author.avatar_url)
        embed.add_field(name='\uFEFF',
                        value="🥇" + teamnameclassement[0] + " | " + teampointsclassement[0] + " points" + " | " + str(
                            teamchangeclassement[0]), inline=False)
        embed.add_field(name='\uFEFF',
                        value="🥈" + teamnameclassement[1] + " | " + teampointsclassement[1] + " points" + " | " + str(
                            teamchangeclassement[1]), inline=False)
        embed.add_field(name='\uFEFF',
                        value="🥉" + teamnameclassement[2] + " | " + teampointsclassement[2] + " points" + " | " + str(
                            teamchangeclassement[2]), inline=False)
        embed.add_field(name='\uFEFF',
                        value="4." + teamnameclassement[3] + " | " + teampointsclassement[3] + " points" + " | " + str(
                            teamchangeclassement[3]), inline=False)
        embed.add_field(name='\uFEFF',
                        value="5." + teamnameclassement[4] + " | " + teampointsclassement[4] + " points" + " | " + str(
                            teamchangeclassement[4]), inline=False)
        embed.set_footer(text="🔥 	Click on the arrow to go to the next page.")

        top = await ctx.send(content=None, embed=embed)
        await top.add_reaction("➡")

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        global h1, h2, h3, h4, h5, page
        try:
            page
        except NameError:
            page = None
        if page is not None and user != self.bot.user and page < 7 and reaction.emoji == "➡":
            h1, h2, h3, h4, h5 = h1 + 5, h2 + 5, h3 + 5, h4 + 5, h5 + 5
            page += 1
            await top.remove_reaction("➡", user)

            emupdate = discord.Embed(title="Ranking | Page {}/6 🏆".format(page), url="https://hltv.org/ranking/teams",
                                     color=6532572)  # user.colour)
            emupdate.set_author(name=str(user.name),
                                icon_url="https://is1-ssl.mzstatic.com/image/thumb/Purple128/v4/33/54/b0/3354b09c-ccb5-7bd4-5cd4-f71cc1964406/AppIcon-1x_U007emarketing-85-220-5.png/246x0w.jpg")
            emupdate.set_thumbnail(url=user.avatar_url)

            emupdate.add_field(name='\uFEFF',
                               value=str(h1 + 1) + ". " + teamnameclassement[h1] + " | " + teampointsclassement[
                                   h1] + " points" + " | " + str(teamchangeclassement[h1]), inline=False)
            emupdate.add_field(name='\uFEFF',
                               value=str(h2 + 1) + ". " + teamnameclassement[h2] + " | " + teampointsclassement[
                                   h2] + " points" + " | " + str(teamchangeclassement[h2]), inline=False)
            emupdate.add_field(name='\uFEFF',
                               value=str(h3 + 1) + ". " + teamnameclassement[h3] + " | " + teampointsclassement[
                                   h3] + " points" + " | " + str(teamchangeclassement[h3]), inline=False)
            emupdate.add_field(name='\uFEFF',
                               value=str(h4 + 1) + ". " + teamnameclassement[h4] + " | " + teampointsclassement[
                                   h4] + " points" + " | " + str(teamchangeclassement[h4]), inline=False)
            emupdate.add_field(name='\uFEFF',
                               value=str(h5 + 1) + ". " + teamnameclassement[h5] + " | " + teampointsclassement[
                                   h5] + " points" + " | " + str(teamchangeclassement[h5]), inline=False)
            emupdate.set_footer(text="🔥 Click on the arrow to go to the next page.")

            await top.edit(embed=emupdate)

    @commands.command()
    async def team(self, ctx, *, message):
        """Get infos about a team. Example : ,team vitality"""
        get_team_info(message)
        team_name = team_info['team-name']
        team_name_linkformat = team_name.replace(" ", "-")
        lineup = ""
        for i in range(0, 5, 1):
            player = team_info['current-lineup'][i].get('nickname')
            lineup = lineup + player + " | "

        maps_played = team_info['stats']['Maps played'].text
        WDL = team_info['stats']['Wins / draws / losses'].text
        ratio = team_info['stats']['K/D Ratio'].text

        embed = discord.Embed(title="{}".format(team_name),
                              url=f"https://www.hltv.org/team/{team_info['id']}/{team_name_linkformat}", color=12464799)
        embed.set_author(name=str(ctx.author.name), icon_url=ctx.author.avatar_url)
        embed.set_thumbnail(url=get_image(message))
        embed.add_field(name='Team name', value=team_name, inline=True)
        embed.add_field(name='Rank', value="Feature inc.", inline=True)
        embed.add_field(name='Map played', value=maps_played, inline=True)
        embed.add_field(name='Win/Draw/Lose', value=WDL, inline=True)
        embed.add_field(name='Ratio', value=ratio, inline=True)
        embed.add_field(name='Players', value=lineup[:-3], inline=True)
        embed.set_footer(text="🔥 Images and informations from Liquipedia and HLTV")

        await ctx.send(content=None, embed=embed)

    @commands.command()
    async def follow(self, ctx, *, message):
        author_id = str(ctx.author.id)

        page = get_parsed_page(f"https://www.hltv.org/search?query={message}")
        playersection = page.find_all("td", {"class": "table-header"})
        if playersection != [] and playersection[0].text == "Team":
            user = await self.bot.pg_con.fetch("SELECT * FROM users WHERE user_id = $1", author_id)
            if not user:
                await self.bot.pg_con.execute(
                    "INSERT INTO users (user_id , success_rate, teams_followed) VALUES ($1 , $2, $3)", author_id, None,
                    None)
            user_following = await self.bot.pg_con.fetchrow("SELECT teams_followed FROM users WHERE user_id = $1",
                                                            author_id)
            user_following_raw = user_following['teams_followed']
            team_follow = str(message) + ";"

            if user_following_raw is None:
                await self.bot.pg_con.execute("UPDATE users SET teams_followed=$1 WHERE user_id=$2", team_follow,
                                              author_id)
                await ctx.send(f"{message} has been correctly added.")
            else:
                if str(message) not in user_following_raw:
                    new_followings = user_following_raw + team_follow
                    await self.bot.pg_con.execute("UPDATE users SET teams_followed=$1 WHERE user_id=$2", new_followings,
                                                  author_id)
                    await ctx.send(f"{message} has been correctly added.")
        else:
            await ctx.send("Oops, that team does not exist, re-try with a correct name please.")

    @commands.command()
    async def player(self, ctx, *, message):

        page = get_parsed_page(f"https://www.hltv.org/search?query={message}")
        playersection = page.find_all("td", {"class": "table-header"})
        if playersection != [] and playersection[0].text == "Player":
            url = f"https://www.hltv.org/search?query={message}"
            response = get(url)
            tree = html.fromstring(response.content)

            lien_profile = tree.xpath('//@href')
            for i in lien_profile:
                if i.startswith('/player/'):
                    print(i)
                    player_page_url = f"https://www.hltv.org/stats{i}"

                    player_page_url = player_page_url.replace("player", "players")
                    page = get_parsed_page(player_page_url)

                    player_info = {}
                    images = page.find("div", {"class": "summaryBodyshotContainer"}).find_all('img')
                    player_info['team'] = page.find("div", {"class": "SummaryTeamname"}).text
                    if player_info['team'] == "No team":
                        player_info['teamlogo'] = ctx.author.avatar_url
                        player_info['photo'] = images[0]['src']
                    else:
                        player_info['teamlogo'] = get_image(player_info['team'])
                        print(player_info['teamlogo'])
                        player_info['photo'] = images[1]['src']
                    player_info['realname'] = page.find("div", {"class": "summaryRealname"}).text
                    player_info['age'] = page.find("div", {"class": "summaryPlayerAge"}).text

                    stats = page.find_all("div", {"class": "summaryStatBreakdownRow"})
                    statsUpperRow = stats[0].find_all("div", {"class": "summaryStatBreakdownDataValue"})
                    player_info['ratioKD'] = statsUpperRow[0].text
                    player_info['DPR'] = statsUpperRow[1].text
                    player_info['KAST'] = statsUpperRow[2].text

                    statsLowerRow = stats[1].find_all("div", {"class": "summaryStatBreakdownDataValue"})
                    player_info['impact'] = statsLowerRow[0].text
                    player_info['ADR'] = statsLowerRow[1].text
                    player_info['KPR'] = statsLowerRow[2].text

                    stats = page.find_all("div", {"class": "stats-row"})
                    mapsplayed = stats[6].find_all("span")
                    player_info['Maps Played'] = mapsplayed[1].text

                    embed = discord.Embed(title=" ", color=0x00cec9)
                    embed.set_author(name=str(message), icon_url=str(player_info['teamlogo']))
                    embed.set_thumbnail(url=str(player_info['photo']))
                    embed.add_field(name='Real name', value=player_info['realname'], inline=True)
                    embed.add_field(name='Age', value=player_info['age'], inline=True)
                    embed.add_field(name='Team', value=player_info['team'], inline=True)
                    embed.add_field(name='KD ratio', value=player_info['ratioKD'], inline=True)
                    embed.add_field(name='DPR', value=player_info['DPR'], inline=True)
                    embed.add_field(name='ADR', value=player_info['ADR'], inline=True)
                    embed.add_field(name='Kill Per Round', value=player_info['KPR'], inline=True)
                    embed.add_field(name='Maps played', value=player_info['Maps Played'], inline=True)
                    embed.set_footer(text="🐲 Images and informations provided by HLTV", icon_url=ctx.author.avatar_url)
                    await ctx.send(content=None, embed=embed)
                    break
        else:
            await ctx.send("Sorry but it seems that this player don't exist, try with a correct name :)")
    # @team.error
    # async def team_error(self, ctx, error):
    #    if isinstance(error, commands.MissingRequiredArgument):
    #       await ctx.send(f"🤔 `Please give a team name.` {ctx.author.mention} 🤔")
    #    if isinstance(error, commands.BadArgument):
    #        await ctx.send(f"😢 `That team don't exist, sorry` {ctx.author.mention} 😢")


def setup(bot):
    bot.add_cog(Hltv(bot))
