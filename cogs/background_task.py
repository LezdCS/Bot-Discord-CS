import discord
from discord.ext import commands
import requests
from requests import get
from bs4 import BeautifulSoup
import asyncio
import psycopg2
import datetime
import json
import feedparser


class background_task(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


def setup(bot):
    def get_parsed_page(url):
        # This fixes a blocked by cloudflare error i've encountered
        headers = {
            "referer": "https://blog.counter-strike.net/index.php/category/updates/",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
        return BeautifulSoup(requests.get(url, headers=headers).text, "lxml")

    async def hltv_news():
        await bot.wait_until_ready()
        while not bot.is_closed():
            d = feedparser.parse('https://www.hltv.org/rss/news')
            Titre_current = await bot.pg_con.fetchrow("SELECT hltvtitle FROM infos")
            Titre_current = Titre_current['hltvtitle']
            titre = str(d['entries'][0]['title'])
            lien = str(d['entries'][0]['link'])
            if Titre_current != titre:
                await bot.pg_con.execute("UPDATE infos SET hltvtitle = $1", str(titre))
                connection = psycopg2.connect(dbname="postgres", user="postgres", password="LezdSql39", port="5433")
                cur = connection.cursor()
                cur.execute("""SELECT channel_hltv_id from guild where channel_hltv_id is not null """)
                channels = cur.fetchall()
                for chan in channels:
                    sendto = int(chan[0])
                    channel = bot.get_channel(int(sendto))
                    await channel.send(str(lien))

            await asyncio.sleep(60)

    async def steam_status():
        await bot.wait_until_ready()
        while not bot.is_closed():
            serverlist = []
            status_server = []
            page = requests.get(
                'https://api.steampowered.com/ICSGOServers_730/GetGameServersStatus/v1/?key=1ACC6F6F361B041BDE0B1971746891B8')
            contenu = json.loads(page.text)
            for i in contenu['result']['datacenters']:
                serverlist.append(i)
                status_server.append(contenu['result']['datacenters'][i].get('load'))

            for server in bot.guilds:
                RegionsToUpdate = await bot.pg_con.fetchrow("SELECT regions_serversstatus FROM guild WHERE guild_id=$1",
                                                            str(server.id))
                RegionsToUpdate = RegionsToUpdate['regions_serversstatus']

                channel_embed_status = await bot.pg_con.fetchrow(
                    "SELECT channel_status_cs_embed FROM guild WHERE guild_id=$1", str(server.id))
                channel_embed_status = channel_embed_status['channel_status_cs_embed']

                # PARTIE POUR STATS NOMBRE DE JOUEURS EN LIGNE ET EN RECHERCHE
                channel_embed_stats = await bot.pg_con.fetchrow(
                    "SELECT channel_statsp_cs_embed FROM guild WHERE guild_id=$1", str(server.id))
                channel_embed_stats = channel_embed_stats['channel_statsp_cs_embed']
                message_embed_stats = await bot.pg_con.fetchrow(
                    "SELECT message_embed_statsp_id FROM guild WHERE guild_id=$1", str(server.id))
                message_embed_stats = message_embed_stats['message_embed_statsp_id']
                online_players = contenu['result']['matchmaking'].get('online_players')
                searching_players = contenu['result']['matchmaking'].get('searching_players')
                if channel_embed_stats is not None and message_embed_stats is not None:
                    sendto = channel_embed_stats
                    try:
                        channel_statsp = bot.get_channel(int(sendto))
                    except:
                        pass
                    embed = discord.Embed(title="📊 Players statistics 📊", color=0x7ed6df, url="",
                                          description="", timestamp=datetime.datetime.utcnow())
                    embed.set_footer(text="Dead game you said ?️", icon_url=bot.user.avatar_url)

                    embed.add_field(name="Online players 🌐", value=str(online_players), inline=False)
                    embed.add_field(name="Searching players 🔍", value=str(searching_players), inline=False)
                    try:
                        msg = await channel_statsp.fetch_message(message_embed_stats)
                        await msg.edit(content=None, embed=embed)
                    except:
                        await channel_statsp.send(
                            "Oops, you maybe deleted something, please write `,setcsgostats` or click on the cross to unset that channel as the csgo stats channel ")

                if channel_embed_status is not None:
                    sendto = channel_embed_status
                    try:
                        channel = bot.get_channel(int(sendto))
                    except:
                        pass
                message_embed = await bot.pg_con.fetchrow("SELECT message_embed_id FROM guild WHERE guild_id=$1",
                                                          str(server.id))
                message_embed = message_embed['message_embed_id']

                statusservertracked = []
                if RegionsToUpdate is not None:
                    RegionsToUpdate = RegionsToUpdate.split(";")
                    RegionsToUpdate.remove('')
                    for i in RegionsToUpdate:
                        placement = serverlist.index(i)
                        status = status_server[placement]
                        statusservertracked.append(status)

                    if channel_embed_status is not None and message_embed is not None:
                        embed = discord.Embed(
                            title="<:servers:677273110772187163> Server status <:servers:677273110772187163>",
                            color=0xe74c3c, url="",
                            description="Your servers list 📑", timestamp=datetime.datetime.utcnow())
                        embed.set_footer(text="BIP BIP, servers ok ? 🤖", icon_url=bot.user.avatar_url)
                        for i in range(0, len(RegionsToUpdate), 1):
                            statusserv = str(statusservertracked[i])
                            if statusserv == "low" or "medium" or "high":
                                statusserv = "✅"
                            else:
                                statusserv = "❌"
                            embed.add_field(name=str(RegionsToUpdate[i]), value=str(statusserv), inline=True)
                            # content += "\n"+RegionsToUpdate[i]+" -> "+statusserv

                        try:
                            msg = await channel.fetch_message(message_embed)
                            await msg.edit(content=None, embed=embed)
                        except:
                            await channel.send("Oops, you maybe deleted something, please write `,setserversstatus` ")
            await asyncio.sleep(240)

    async def vac_checker():
        await bot.wait_until_ready()
        while not bot.is_closed():
            connection = psycopg2.connect(dbname="postgres", user="postgres", password="LezdSql39", port="5433")
            cur = connection.cursor()

            chaineIds = ""
            compteur = 0
            cur.execute("""SELECT steam_id from vac""")
            rows = cur.fetchall()
            for row in rows:
                chaineIds += str(row)
                compteur += 1

            url = 'http://api.steampowered.com/ISteamUser/GetPlayerBans/v1/?key=1244D7A7656A97CD1D6FB4A06C1EA8E7&steamids=' + chaineIds
            response = get(url).json()

            for i in range(0, compteur, 1):
                steamid = response['players'][i]['SteamId']
                if (response['players'][i]['VACBanned']):
                    authorid = await bot.pg_con.fetch("SELECT report_author_id FROM vac WHERE steam_id = $1", steamid)
                    print(steamid + " has been banned from VAC servers.")
                    author = bot.get_user(int(authorid[0][0]))
                    await author.send(
                        "https://steamcommunity.com/profiles/" + steamid + " has been banned from VAC servers.")
                    await bot.pg_con.execute("DELETE FROM vac WHERE steam_id = $1", steamid)

            await asyncio.sleep(60)

    async def cs_update_checker():
        await bot.wait_until_ready()
        while not bot.is_closed():
            page = get_parsed_page("https://blog.counter-strike.net/index.php/category/updates/")
            contenu = str(page.find("h2"))

            date = contenu.split(">")
            titre = date[2][0:len(date[2]) - 3]
            lienUpdate = date[1][9:len(date[1]) - 2]

            currenttitle = await bot.pg_con.fetchrow("SELECT csupdatetitle FROM infos")

            if currenttitle['csupdatetitle'] != str(titre):
                await bot.pg_con.execute("UPDATE infos SET csupdatetitle = $1", str(titre))
                connection = psycopg2.connect(dbname="postgres", user="postgres", password="LezdSql39", port="5433")
                cur = connection.cursor()
                cur.execute("""SELECT csupdateschannel from guild where csupdateschannel is not null """)
                channels = cur.fetchall()
                for chan in channels:
                    sendto = int(chan[0])
                    channel = bot.get_channel(int(sendto))
                    emoji = "<a:confetti:677275128580800512>"
                    embed = discord.Embed(title=emoji + "HYPE ! New update detected." + emoji, color=0x00b894,
                                          url=f"{lienUpdate}",
                                          description="", timestamp=datetime.datetime.utcnow())
                    embed.set_image(
                        url="https://cdn1-www.gamerevolution.com/assets/uploads/2019/11/csgo-operation-shattered-web-update-patch-notes-highlights.png")
                    embed.set_author(name=bot.user.name, url="", icon_url=bot.user.avatar_url)
                    embed.set_footer(text="Zeus skin ? Chicken on vertigo 🐔?️", icon_url=bot.user.avatar_url)
                    embed.add_field(name=titre, value=f"{lienUpdate}")
                    await channel.send(content=None, embed=embed)
            await asyncio.sleep(60)

    async def update_matches():
        await bot.wait_until_ready()
        while not bot.is_closed():
            matches_page = "https://www.hltv.org/matches"

            page = get_parsed_page(matches_page)

            matches_day = page.find_all("div", {"class": "upcomingMatchesSection"})[1]

            matchs = matches_day.find_all("div", {"class": "upcomingMatch"})
            await bot.pg_con.execute("DELETE FROM match_day")
            for match in matchs:
                lien = match.find('a')

                teams_name = match.find_all("div", {"class": "matchTeamName"})
                teams_logos = match.find_all("div", {"class": "matchTeamLogo"})

                team1 = {}
                team2 = {}
                try:
                    team1['name'] = teams_name[0].text
                    team1['logo'] = teams_logos[0].find('img')['src']
                    team2['name'] = teams_name[1].text
                    team2['logo'] = teams_logos[1].find('img')['src']
                    match_hour = match.find("div", {"class": "matchTime"}).text

                    event_infos = match.find("td", {"class": "matchEvent"})
                    event = {}
                    event['name'] = event_infos.text
                    event['logo'] = event_infos.find('img')['src']

                    match_type = match.find("div", {"class": "matchMeta"}).text

                    await bot.pg_con.execute(
                        "INSERT INTO match_day (match_link , name_team1, logo_team1,name_team2 , logo_team2, heure_match,type_match , nom_event, logo_event) VALUES ($1 , $2, $3, $4, $5, $6,$7,$8,$9)",
                        lien['href'], team1['name'], team1['logo'], team2['name'], team2['logo'], match_hour,
                        match_type, event['name'], event['logo'])
                except:
                    pass

            await asyncio.sleep(80)

    async def check_matches():
        await bot.wait_until_ready()
        while not bot.is_closed():
            connection = psycopg2.connect(dbname="postgres", user="postgres", password="LezdSql39", port=5433)
            cur = connection.cursor()
            cur.execute("""SELECT * from match_day""")
            rows = cur.fetchall()
            for row in rows:
                now = datetime.datetime.now()
                heure_actuelle = str(now.hour) + ":" + str('{:02d}'.format(now.minute))
                heure_match = str(row[5])
                if heure_match == heure_actuelle:
                    await bot.pg_con.execute("INSERT INTO match_ongoing SELECT * FROM match_day WHERE match_link = $1",
                                             str(row[0]))
                    await bot.pg_con.execute("DELETE FROM match_day WHERE match_link = $1", str(row[0]))
                    cur = connection.cursor()
                    cur.execute("""SELECT * from users where teams_followed is not null """)
                    users_infos = cur.fetchall()
                    for user in users_infos:
                        if (row[1] in user[2] or row[3] in user[2]):
                            user_object = bot.get_user(int(user[0]))
                            await user_object.send("Yep")
            await asyncio.sleep(60)

    bot.loop.create_task(hltv_news())
    bot.loop.create_task(steam_status())
    bot.loop.create_task(vac_checker())
    bot.loop.create_task(cs_update_checker())
    bot.loop.create_task(update_matches())
    bot.loop.create_task(check_matches())
    bot.add_cog(background_task(bot))
