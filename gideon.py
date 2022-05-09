#!/usr/bin/python3
'''
-----------------------------
 @Name Gideon
 @Author Ethann Schneider
 @Version 2.3.0
 @Date 08.04.22
-----------------------------
'''

from __future__ import unicode_literals
import discord
import os
import time
import yt_dlp
import random
import urllib.request
import re
import datetime
import time
import math
from pathlib import Path
import re
from urllib.parse import urlparse, parse_qs
from contextlib import suppress
from discord.ext import tasks
import json

lock = {}

global TOKEN
global queue

TOKEN = None
with open("/home/ethann/gideon/key.txt", "r") as key:
    TOKEN = key.readline()

intents = discord.Intents.default()
intents.members = True

client = discord.Client(intents=intents)

vc = {}

queue = {}

blague = []

excuse = []

'''
@Name load Perms
@Description To load permission from file
@return json of perms
'''
def permsLoad():
    with open("/home/ethann/gideon/perms/option.json", "r") as jsonFile:
        return json.load(jsonFile, object_hook = None)

'''
@Name save Perms
@Description To save permission to file
@return Null
'''
def permsSave():
    with open("/home/ethann/gideon/perms/option.json", "w") as jsonFile:
        jsonFile.write(json.dumps(options))

# Music function

'''
@Name join Channel
@Description To made bot join Vocal Channel where user is
@args1 Message Message that was send by User
@return Null
'''
def joinChannel(message):
    return message.author.voice.channel.connect()

'''
@Name play Music
@Description play Music with path or add it to the queue
@args1 path Path To File
@args2 voc Vocal where to play
@args3 id server id
@return text to send in chat
'''
def playMusic(path, voc, id):
    if not voc.is_playing():
        voc.play(discord.FFmpegPCMAudio(path))

        return "playing"
    else:
        if id not in queue:
            queue[id] = []

        queue[id].insert(0, path)
        return "Added to queue"

'''
@Name next Music
@Description play next music in queue
@args1 voc Vocal where to play
@args2 id server id
@return text to send in chat
'''
def nextMusic(voc, id):
    if id not in queue:
        queue[id] = []

    if queue[id]:
        if voc.is_playing():
            voc.stop()

        return playMusic(queue[id].pop(), voc, id)
    else:
        return "Queue is empty"

'''
@Name get youtube id
@Description get youtube id with url
@link https://stackoverflow.com/questions/4356538/how-can-i-extract-video-id-from-youtubes-link-in-python
@args1 url
@args2 ignore_playlist=False If ignore playlist
@return id of video
'''
def get_yt_id(url, ignore_playlist=False):
    # Examples:
    # - http://youtu.be/SA2iWivDJiE
    # - http://www.youtube.com/watch?v=_oPAwA_Udwc&feature=feedu
    # - http://www.youtube.com/embed/SA2iWivDJiE
    # - http://www.youtube.com/v/SA2iWivDJiE?version=3&amp;hl=en_US
    query = urlparse(url)
    if query.hostname == 'youtu.be': return query.path[1:]
    if query.hostname in {'www.youtube.com', 'youtube.com', 'music.youtube.com'}:
        if not ignore_playlist:
        # use case: get playlist id not current video in playlist
            with suppress(KeyError):
                return parse_qs(query.query)['list'][0]
        if query.path == '/watch': return parse_qs(query.query)['v'][0]
        if query.path[:7] == '/watch/': return query.path.split('/')[1]
        if query.path[:7] == '/embed/': return query.path.split('/')[2]
        if query.path[:3] == '/v/': return query.path.split('/')[2]

'''
@Name youtube Dowload
@Description Dowload Video with link
@args1 ytb Link
@return Null
'''
def youtubeDwl(ytb):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': '/home/ethann/gideon/music/%(id)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        },
        ],
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download(ytb)

# Music function

# Music commands

'''
@Name Play
@Description Command play to play music in vocal
@args1 message message that was sent by user
@args2 commands commands that was sent by user
@return Null
'''
async def play(message,commands):
    global vc, queue
    if not isinstance(message.channel, discord.channel.DMChannel):
        if message.guild.id not in lock:
            lock[message.guild.id] = False

        if message.guild.id not in vc:
            vc[message.guild.id] = None

        if lock[message.guild.id] and message.author.id not in root:
            await message.channel.send("non Désolé, "+getExcuse())
            return

        if 'youtu.be' in commands[0][2] or 'youtube.com' in commands[0][2]:
            try:
                if vc[message.guild.id] == None:
                    vc[message.guild.id] = await joinChannel(message)
                fileName = "/home/ethann/gideon/music/"+get_yt_id(commands[0][2])+".mp3"
                if not os.path.exists(fileName):
                    youtubeDwl(commands[0][2])
                await message.channel.send(playMusic(fileName, vc[message.guild.id], message.guild.id))
            except Exception as e:
                await message.channel.send("Erreur technique vérifier que se soit une video téléchargeable ou que vous soyez dans un salon vocaux")
                print(e)
        else:
            await message.channel.send("lien Youtube uniquement (youtube.com, youtu.be)")

'''
@Name Stop
@Description Command stop to stop music in vocal
@args1 message Message that was sent by user
@args2 commands Commands that was sent by user
@return Null
'''
async def stop(message,commands):
    global vc, queue

    if not isinstance(message.channel, discord.channel.DMChannel):
        if message.guild.id not in lock:
            lock[message.guild.id] = False

        if lock[message.guild.id] and message.author.id not in root:
            await message.channel.send("non Désolé, "+getExcuse())
            return

        if vc[message.guild.id] != None:
            vc[message.guild.id].stop()
            await vc[message.guild.id].disconnect()

            vc[message.guild.id] = None
            queue[message.guild.id] = []

            await message.channel.send("Stopping")
        else:
            await message.channel.send("Nothing to Stop")

'''
@Name Skip
@Description Command to Skip current music with one in the queue
@args1 message message that was sent by user
@args2 commands commands that was sent by user
@return Null
'''
async def skip(message,commands):
    global vc, queue
    if not isinstance(message.channel, discord.channel.DMChannel):
        if message.guild.id not in lock:
            lock[message.guild.id] = False

        if message.guild.id not in vc:
            vc[message.guild.id] = None

        if lock[message.guild.id] and message.author.id not in root:
            await message.channel.send("non Désolé, "+getExcuse())
            return

        try:
            if vc[message.guild.id] == None:
                await message.channel.send("non Désolé, "+getExcuse())
                return

            await message.channel.send(nextMusic(vc[message.guild.id], message.guild.id))
        except Exception as e:
            await message.channel.send("Erreur technique vérifier que se soit une video téléchargeable ou que vous soyez dans un salon vocaux")
            print(e)


'''
@Name active Lock
@Description Active lock to made stop user that use the vocal command in the server only authorize root to use it
@args1 message Message that was sent by user
@args2 commands Commands that was sent by user
@return Null
'''
async def actLock(message,commands):
    global lock

    if not isinstance(message.channel, discord.channel.DMChannel):
        if message.guild.id not in lock:
            lock[message.guild.id] = False

        if lock[message.guild.id]:
            lock[message.guild.id] = False
            await message.channel.send("Lock désactiver")
        else:
            lock[message.guild.id] = True
            await message.channel.send("Lock activer")

# Music commands end

# Function

'''
@Name get Joke
@Description get Joke in a data file
@return Joke that was getted
'''
def getJoke():
    global blague
    blague = Path("/home/ethann/gideon/library/blague.txt").read_text().split('\n')

    return blague[random.randint(0,len(blague)-1)]

'''
@Name get Excuse
@Description get Excuse in a data file
@return Excuse that was getted
'''
def getExcuse():
    excuse = Path("/home/ethann/gideon/library/excuse.txt").read_text().split('\n')

    return excuse[random.randint(0,len(excuse)-1)]

# end Function

'''
@Name Help
@Description Help page to help you ;)
@args1 message Message that was sent by user
@args2 commands Commands that was sent by user
@return Null
'''
async def help(message,commands):
    embed = None;

    if commands[0][2] in options and not options[commands[0][2]]['hide']:
        embed=discord.Embed(title="!"+commands[0][2], description=options[commands[0][2]]['description'], color=0x138EC3)

    elif commands[0][2] in rootoptions:
        if message.author.id in root:
            embed=discord.Embed(title="!"+commands[0][2], description=rootoptions[commands[0][2]]['description'], color=0x138EC3)

    else:
        embed=discord.Embed(title="List Command Help", color=0x138EC3)

        for i in options:
            if not options[i]['hide']:
                embed.add_field(name="!"+i, value=options[i]['description'], inline=False)

    await message.channel.send(embed=embed)

'''
@Name Ngrok
@Description command to start and stop Ngrok instance
@args1 message Message that was sent by user
@args2 commands Commands that was sent by user
@return Null
'''
async def funcngrok(message,commands):
    osreturn = os.popen("screen -list")
    if commands[0][2] == 'stop':
        os.popen("screen -S ngrok -X stuff $'\003'").read()
        await message.channel.send("Client NGROK arrêté !")
        return
    elif 'ngrok' not in osreturn.read():
        if commands[0][2] == 'minecraft':
            os.popen("screen -S ngrok -d -m /home/ethann/.local/bin/ngrok tcp 25565 -region eu").read()
            await message.channel.send("Client NGROK démarré.(Minecraft)")
        else:
            os.popen("screen -S ngrok -d -m /home/ethann/.local/bin/ngrok tcp 22 -region eu").read()
            await message.channel.send("Client NGROK démarré.(ssh)")
    time.sleep(1)
    ngrokreq=urllib.request.urlopen('http://127.0.0.1:4040/api/tunnels')
    ngrokans=ngrokreq.read().decode("UTF-8")
    ngrokurl=re.findall(r'"public_url":"(tcp://[^"]*)"',ngrokans)
    await message.channel.send("ip : **"+ngrokurl[0]+"**")

'''
@Name Clear
@Description Clear channel if not in DMChannel
@args1 message Message that was sent by user
@args2 commands Commands that was sent by user
@return Null
'''
async def clear(message,commands):
    if not isinstance(message.channel, discord.channel.DMChannel):
        await message.channel.purge()

'''
@Name quit
@Description Made bot disconnect and close everything
@args1 message Message that was sent by user
@args2 commands Commands that was sent by user
@return Null
'''
async def quit(message,commands):
    await message.channel.send("bye, bye")
    await client.logout()
    await client.close()

'''
@Name reload
@Description Made bot reload command
@args1 message Message that was sent by user
@args2 commands Commands that was sent by user
@return Null
'''
async def reload(message,commands):
    global options
    options = permsLoad()
    await message.channel.send("reloaded")

'''
@Name Wake on lan
@Description Start EthannGaming pc
@args1 message Message that was sent by user
@args2 commands Commands that was sent by user
@return Null
'''
async def wol(message, commands):
    os.popen("wakeonlan 34:97:F6:25:AC:E4").read()
    await message.channel.send("VERY GOOD MY FRIEND YOU START YOUR COMPUTER BY USING DISCORD ARE YOU HAPPY !!!!!")

'''
@Name SendMessage
@Description Send a message with or without a file
@args1 message Message that was sent by user
@args2 commands Commands that was sent by user
@args3 messages Message to send
@args4 files=Null File to send
@return Null
'''
async def SendMessage(message, commands, messages, files=None):
    if files == None:
        await message.channel.send(messages)
    if os.path.isdir(files):
        list = os.listdir(files)
        await message.channel.send(file=discord.File(files+"/"+list[random.randint(0,len(list))-1]))
    else:
        await message.channel.send(messages, file=discord.File(files))

rootoptions = { # Root commands
        'quit' : {'cmd': help, 'description': "Pour éteinde le bot", 'hide':False , "nsfw": False},
        'clear' : {'cmd': clear, 'description': "Pour clear tout les messages d'un salon textuelle", 'hide':False , "nsfw": False},
        'reload' : {'cmd': reload, 'description': "Pour reload les commands du bot", 'hide':False , "nsfw": False},
        'ngrok' : {'cmd': funcngrok, 'description': "Demarrer un Client Ngrok !", 'hide':True, "nsfw": False },
        'wol' : {'cmd': wol, 'description': "Demarrer EthannGaming avec un wake on lan", 'hide':True, "nsfw": False},
        'lock' : {'cmd': actLock, 'description': "Activer la lock pour le non root a l'accés du bot au salon musique", 'hide':True, "nsfw": False}
}

options = permsLoad(); # User Commands
# {
#         "help":{"cmd": "help(message, commands)", "description":"Simple Help page", "hide":false, "nsfw": false},
#         "salut":{"cmd": "SendMessage(message, commands, 'Hello there')", "description":"Say hello", "hide":false, "nsfw": false},
#         "pileFace":{"cmd": "SendMessage(message, commands, '', '/home/ethann/gideon/image/'+['face','pile'][random.randint(0,1)]+'.png')", "description":"Simple Pile Ou Face", "hide":false, "nsfw": false},
#         "play": {"cmd": "play(message, commands)", "description": "play Music", "hide": false, "nsfw": false},
#         "skip": {"cmd": "skip(message, commands)", "description": "skip Music", "hide": false, "nsfw": false},
#         "stop": {"cmd": "stop(message, commands)", "description": "stop Music", "hide": false, "nsfw": false},
#         "pi": {"cmd": "SendMessage(message, commands, 'π = **3.1415926535897932384626433832795028841971693993751058209749445923**')", "description": "tell you pi Number", "hide": false, "nsfw": false},
#         "joke": {"cmd": "SendMessage(message, commands, getJoke())", "description": "tell you a joke", "hide": false, "nsfw": false},
#         "hentai": {"cmd": "SendMessage(message, commands, '', '/home/ethann/gideon/image/hentai/')", "description": "Give you hentai picture", "hide": true, "nsfw": true},
#         "sel": {"cmd": "SendMessage(message, commands, '', '/home/ethann/gideon/image/salt.jpg')", "description": "Give you salt picture", "hide": false, "nsfw": false},
#         "disquette": {"cmd": "SendMessage(message, commands, '', '/home/ethann/gideon/image/disquette.png')", "description": "Give you disquette", "hide": false, "nsfw": false}
# }

root = { # Root people
    386200134628671492 : { 'name' : "Ethann8" }
}

'''
@event
@Name LoopMusic
@Description to leave bot when there is no more music
@return Null
'''
@tasks.loop(seconds = 1)
async def LoopMusic():
    global vc, queue
    for i in vc:
        if vc[i] != None:
            if not vc[i].is_playing():
                if queue[i]:
                    nextMusic(vc[i], i)
                else:
                    vc[i].stop()
                    await vc[i].disconnect()

                    vc[i] = None
                    queue[i] = []

'''
@event
@Name on Message
@Description When a message sent
@args1 message Message that was sent by user
@return Null
'''
@client.event
async def on_message(message):
    print("(in "+str(message.channel)+" at "+str(datetime.datetime.now())+")"+str(message.author)+": "+message.content)
    with open("/home/ethann/gideon/log.txt", "a") as f:
        f.write("(in "+str(message.channel)+" at "+str(datetime.datetime.now())+")"+str(message.author)+": "+message.content+"\n")

    if message.author == client.user:
        return

    #calc
    num = re.findall(r'^([+-]?(\d*\.)?\d+)(\s*([+*/%^-]|//)\s*([+-]?(\d*\.)?\d+))+$',message.content)

    if num:
        calc = eval(message.content.replace("^", "**"))
        await message.channel.send(calc)
    #end calc

    commands=re.findall(r'^!(\S+)(\s+(\S+))?(\s+(\S+))?$',message.content)

    if commands:
        if commands[0][0] in rootoptions:
            if message.author.id in root:
                await rootoptions[commands[0][0]]['cmd'](message,commands)
            else:
                await message.channel.send("non Désolé, "+getExcuse())
        if commands[0][0] in options:
            if options[commands[0][0]]['nsfw']:
                if isinstance(message.channel, discord.channel.DMChannel):
                    await message.channel.send("non Désolé, "+getExcuse())
                elif message.channel.is_nsfw():
                    await eval(options[commands[0][0]]['cmd'])
            else:
                await eval(options[commands[0][0]]['cmd'])

    elif 'hello' in message.content.lower() and 'there' in message.content.lower():
        await message.channel.send("GENERAL "+message.author.name+" !")

'''
@event
@Name on Member Join
@Description When a member join a server
@args1 member member that join the server
@return Null
'''
@client.event
async def on_member_join(member):
    with open("/home/ethann/gideon/log.txt", "a") as f:
        f.write(str(member)+" as join "+str(member.guild.name)+"\n")
    print(str(member)+" as join "+str(member.guild.name))
    if member.guild.id == 899007170178322462:
        role = discord.utils.get(member.guild.roles, id=899009268458594344)
        await member.add_roles(role)

'''
@event
@Name on Raw Reaction Add
@Description When a reaction add
@args1 reaction Reaction that was added
@return Null
'''
@client.event
async def on_raw_reaction_add(reaction):
                                             #messages id         channel id        emoji    guild/server id   role_id
    await add_role_with_reaction(reaction, 897092776326467644, 892069238607601684, "✅" ,890236281785810956, 890491849540763648) # membre
    await add_role_with_reaction(reaction, 897165689918484511, 897161421568225363, "ℹ️" ,890236281785810956, 897165728082452520) # Informaticien
    await add_role_with_reaction(reaction, 897165689918484511, 897161421568225363, "🌐" ,890236281785810956, 897165921209172048) # Médiamaticien
    await add_role_with_reaction(reaction, 897165689918484511, 897161421568225363, "💻" ,890236281785810956, 897170662467190846) # Developer
    await add_role_with_reaction(reaction, 897165689918484511, 897161421568225363, "🖥️" ,890236281785810956, 897171651026894898) # hardware
    await add_role_with_reaction(reaction, 897165689918484511, 897161421568225363, "🖨️" ,890236281785810956, 897171027870765066) # System
    await add_role_with_reaction(reaction, 897165689918484511, 897161421568225363, "🖼️" ,890236281785810956, 897174889490972693) # Designer
    await add_role_with_reaction(reaction, 897165689918484511, 897161421568225363, "shkermit" ,890236281785810956, 897175294354554931) # Shkermit

'''
@event
@Name on Raw Reaction Remove
@Description When a reaction Remove
@args1 reaction Reaction that was removed
@return Null
'''
@client.event
async def on_raw_reaction_remove(reaction):
                                             #messages id         channel id        emoji    guild/server id   role_id
    await remove_role_with_reaction(reaction, 897092776326467644, 892069238607601684, "✅" ,890236281785810956, 890491849540763648) # membre
    await remove_role_with_reaction(reaction, 897165689918484511, 897161421568225363, "ℹ️" ,890236281785810956, 897165728082452520) # informaticien
    await remove_role_with_reaction(reaction, 897165689918484511, 897161421568225363, "🌐" ,890236281785810956, 897165921209172048) # Médiamaticien
    await remove_role_with_reaction(reaction, 897165689918484511, 897161421568225363, "💻" ,890236281785810956, 897170662467190846) # Developer
    await remove_role_with_reaction(reaction, 897165689918484511, 897161421568225363, "🖥️" ,890236281785810956, 897171651026894898) # hardware
    await remove_role_with_reaction(reaction, 897165689918484511, 897161421568225363, "🖨️" ,890236281785810956, 897171027870765066) # System
    await remove_role_with_reaction(reaction, 897165689918484511, 897161421568225363, "🖼️" ,890236281785810956, 897174889490972693) # Designer
    await remove_role_with_reaction(reaction, 897165689918484511, 897161421568225363, "shkermit" ,890236281785810956, 897175294354554931) # Shkermit

'''
@Name Add Role With Reaction
@Description To add role with the reaction
@args1 reaction Reaction that was Added
@args2 message_id Message where reaction need to be added
@args3 channel_id Channel where reaction need to be added
@args4 emoji Emoji where reaction need to be added
@args5 guild_id Guild where reaction need to be added
@args6 role_id Role to add
@return Null
'''
async def add_role_with_reaction(reaction, message_id, channel_id, emoji, guild_id, role_id):
    if(reaction.message_id == message_id and reaction.channel_id == channel_id and reaction.emoji.name == emoji and reaction.guild_id == guild_id):
        role = discord.utils.get(reaction.member.guild.roles, id=role_id)
        await reaction.member.add_roles(role)

'''
@Name Remove Role With Reaction
@Description To remove role with the reaction
@args1 reaction Reaction that was removed
@args2 message_id Message where reaction need to be removed
@args3 channel_id Channel where reaction need to be removed
@args4 emoji Emoji where reaction need to be removed
@args5 guild_id Guild where reaction need to be added
@args6 role_id Role to remove
@return Null
'''
async def remove_role_with_reaction(reaction, message_id, channel_id, emoji, guild_id, role_id):
    member = client.get_user(reaction.user_id)
    guild = client.get_guild(reaction.guild_id)
    if(reaction.message_id == message_id and reaction.channel_id == channel_id and reaction.emoji.name == emoji and reaction.guild_id == guild_id):
        role = discord.utils.get(guild.roles, id=role_id)
        member2 = discord.utils.get(guild.members, id=reaction.user_id)
        await member2.remove_roles(role)

'''
@event
@Name on Ready
@Description When bot is started
@return Null
'''
@client.event
async def on_ready():
    print('Logged in as')
    print(client.user)
    print(client.user.id)
    print('------')
    options = permsLoad()
    LoopMusic.start()
    #await client.get_user(386200134628671492).send("Bot Allumer")

client.run(TOKEN)
