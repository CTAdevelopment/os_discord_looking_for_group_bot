#!/usr/bin/python3.10
import gc
import os, re, sys
from unicodedata import category
import discord, random, asyncio
from datetime import datetime
from dotenv import load_dotenv
from discord.ext import commands
from discord import app_commands

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
serverCategorieName = os.getenv('SERVER_CAT_NAME')
server_TextChannel_toSearchPlay_name = os.getenv('SEARCH_CHANNEL_NAME')
server_MainHost = os.getenv('SERVER_MAIN_NAME')
commands = 'The current commands are:\n/zoek <game> <req. players> <max. players> \n/idea <title> <idea>\n....'

class dClient(discord.Client):

    def __init__(self):
        super().__init__(intents=discord.Intents.default(), command_prefix='!')
        self.synced = False

    async def on_ready(self):
        await self.wait_until_ready()

        if not self.synced:
            await tree.sync()
            self.synced = True

        self.tempChannels = {}
        self.voiceChannels = {}
        self.openGroupRequests = {}
        
        guilds = '\n'.join([guild.name for guild in self.guilds])

        try:
            self.ownServerID = await bot.fetch_guild([a.id for a in bot.guilds if a.name == server_MainHost][0])
        except Exception as e:
            sys.exit(f'.env details are not set correctly, or the bot is not yet implemented in the main server. Exiting script. Exception caught: {e}')
           
        
        if self.ownServerID != None:

            # fetch roles
            self.guildRoles = [[role.name, role.permissions] for role in bot.ownServerID.roles]

            # using 'await fetch_channels', as 'guild.channels' returns an empty list.. 
            self.voiceChannels = {
                k.name : k for k in await self.ownServerID.fetch_channels()
            }

            #initiate Idea Master - if any
            self.idea_master = await self.ownServerID.fetch_member(os.getenv('IDEA_MASTER'))
            

        # voiceChannels contain all channels, not only the voice ones!
        for key, channel in self.voiceChannels.items():

            # find the channel Obj in which to store, if None -> will be created later
            if key == serverCategorieName and channel.type.name == 'category':
                self.outputCategorie = channel
                continue

            # if TMP channel for ZoekBotje -> add to {}
            if channel.type.name == 'voice' and '#TMP' in channel.name:
                self.tempChannels[channel.id] = channel

        print(
            f'\n{self.user} is connected\n'
            f'Guilds: {guilds}\n'
            f'Server ID: {self.ownServerID}\n'
            #f'Server Roles: {self.guildRoles}\n'
            f'Temp Voice Channels: {self.tempChannels}\n'
            f'Open Requests Msgs: {self.openGroupRequests}\n'
            f'Categories: {self.outputCategorie}\n'
        )
    
    def __str__(self):

        return(
            f'\n{self.user} is connected\n'
            f'Server ID: {self.ownServerID}\n'
            #f'Server Roles: {self.guildRoles}\n'
            f'Temp Voice Channels: {self.tempChannels}\n'
            f'Open Requests Msgs: {self.openGroupRequests}\n'
            f'Categories: {self.outputCategorie}\n'
        )

bot = dClient()
tree = app_commands.CommandTree(bot)

async def _tmp_channel_manager(chanObj):
    """ chechks whether the obj exists in self.TempChannels, if > 1 old + 0 members -> Delete"""
    print(f'_tmp_channel_manager called\n')
    if not chanObj.id in bot.tempChannels.keys():
        return

    creationAtTz = chanObj.created_at.tzinfo
    channelExistingTime = datetime.now(tz=creationAtTz) - chanObj.created_at

    # delete the actual channel
    try:
        if channelExistingTime.days > 1 and len(chanObj.members) == 0:
            
            print('channel existing longer than 1 day')
            await chanObj.delete()
            bot.tempChannels.pop(chanObj.id)

    except Exception as e:
        print(f'couldnt get datetime.days, or couldnt delete the channel, msg:\n{e}')
    
    # delete the corresponding messages and inform the owner
    if chanObj.id in bot.openGroupRequests.keys():

        try:
            for msgObj in bot.openGroupRequests[chanObj.id]['messages']:
                await msgObj.delete()
        except Exception as e:
            print(f'could not delete the messages corresponding to the deleted voice channel {chanObj.name}, error: {e}')

        try:
            bot.openGroupRequests[chanObj.id]['owner'].send(f'Your Temp Channel({chanObj.name}) is Removed {chanObj.mention}')
        except Exception as e:
            print(f'could not inform the owner corresponding to the delete voice channel {chanObj.name}, error: {e}')

        bot.openGroupRequests.pop(chanObj.id)

@tree.command(name='commands')
async def commandos(ctx):
    await ctx.response.send_message(commands)
    return

@tree.command(name='idea')
async def _idea(ctx, title: str, content: str):
    print(f'idea command: {ctx.user.name} submitted an idea:\n{title}\n{content}\n')

    if title == '' or content == '':
        response_failed = f'Your idea has not been submitted, pleaes provide your idea with a title and it\'s content'
        await ctx.response.send_message(response_failed, ephemeral=True)
        return

    # sending response to user from Bot
    try:
        response_succes = f'Beste {ctx.user.name}, thanks for submitting your idea!'
        await ctx.response.send_message(response_succes, ephemeral=True)
    except Exception as _:
        print(f'exception caught {_}')

    # sending the Idea to the 'idea_master' from .env
    await bot.idea_master.send(f'<@{ctx.user.id}> submitted the following idea\n\ntitle: {title}\ncontent: {content}')

@tree.command(name='zoek')
async def _zoek(ctx, game: str, spelers: int, limiet_spelers: int):
    
    username = ctx.user.name.capitalize()
    if limiet_spelers == spelers: limiet_spelers += 1


    ''' # if searching for <game> <players>'''
    commandObj = ctx.command
    print(f'zoek command: {username} looking for {spelers}/{limiet_spelers} gamers for {game}')

    try:
        if spelers == 1:
            txt_count = 'gamer'
        else:
            txt_count = 'gamers'
    except Exception as e:
        await ctx.user.send(f'Your command was not recognized, please see !commands for help.')
        return

    ''' create the DBE SERVER category if not existing '''
    if bot.outputCategorie == None:
        bot.outputCategorie = await bot.ownServerID.create_category(name=serverCategorieName)

    ''' creating the Temporary Voice Channel - for this group of people'''
    ''' if the user already has a channel -> change it '''
    try:
        channelNameStr = f'#TMP {username} - {game.capitalize()}'
        channelExists = False

        for key, chan in bot.tempChannels.items():
            
            if username in chan.name:
                channelObj = chan
                channelExists = True
                await ctx.response.send_message(
                    f'There is already a channel existing for you {chan.mention}.\n\nWe changed it\'s name and stats.\nDBE will help you to find {spelers} {txt_count} for {game} in our DBE server',
                    ephemeral=True
                    )
                channelObj = await chan.edit(name=channelNameStr, user_limit=limiet_spelers, category=bot.outputCategorie)
                print('changed existing to: ', channelObj.name, channelObj.category, channelObj.type)
                break
    
    except Exception as e:
        print(f'Error occured while creating the VoiceChannel {e}')
        return
     
    ''' # sending response to user from Bot'''
    if not channelExists:
        print(f'Creating a VoiceChannel in {bot.ownServerID} for {username.capitalize()}')
        channelObj = await bot.ownServerID.create_voice_channel(name=channelNameStr, user_limit=limiet_spelers, category=bot.outputCategorie)
        bot.tempChannels[channelObj.id] = channelObj

        try:
            response_succes = f'Dear {username}, DBE will help you to find {spelers} {txt_count} for the game: {game} in our DBE server @{channelObj.jump_url}!'
            await ctx.response.send_message(response_succes, ephemeral=True)
        except Exception as _:
            print(f'Exception caught {_}')
        
    ''' # for each server -> post in #FIND-PLAYERS'''
    for g in bot.guilds:

        # for each text channel  
        for txt_channel in g.text_channels:

            # check if channel qualifies for 'searching_info' 
            if server_TextChannel_toSearchPlay_name in txt_channel.name:

                try:
                    # send msg in text channel of current <guild>
                    msg = await txt_channel.send(
                        f'Gamers, <@{ctx.user.id}> is looking for <{spelers}/{limiet_spelers}> {txt_count} for {game}.\nBe fast and join @{channelObj.jump_url}'
                    )

                    if bot.openGroupRequests.get(channelObj.id) == None:
                        bot.openGroupRequests[channelObj.id] = {
                            'owner' : '',
                            'game' : '',
                            'messages' : None
                        }
                        bot.openGroupRequests[channelObj.id]['owner'] = ctx.user
                        bot.openGroupRequests[channelObj.id]['game'] = game
                        bot.openGroupRequests[channelObj.id]['messages'] = [msg]
                    else:
                        bot.openGroupRequests[channelObj.id]['messages'].append(msg)
                except Exception as e:
                    print(f'Not having the right access to send a msg in the server {g.name}\n')
                    await bot.idea_master.send(content=f'Bot has not the right access to {g.name}')


            else:
                continue

@bot.event
async def on_voice_state_update(member, before, after):
    """ 
    whenever a user joins one of the temporary channels, check if there is an open GroupRequest
    if there is - > change the message in the community (also change looking for X/Y players)
    if the channel exists within the tempChannels & is older than 1 hour without players => delete
    """

    if before.channel != None:
        await _tmp_channel_manager(before.channel)

    # change the messages in case required!
    # transmute holds the channels for which the msgs should be transmuted (replaced)
    ids_to_transmute = []

    if before.channel != None:
        if before.channel.id in bot.openGroupRequests.keys():
            ids_to_transmute.append(before.channel)
    
    if after.channel != None:
        if after.channel.id in bot.openGroupRequests.keys():
            ids_to_transmute.append(after.channel)

    if len(ids_to_transmute) > 0:
        for transmute_id in ids_to_transmute:

            msgObjs = bot.openGroupRequests[transmute_id.id]['messages']
            for msgObj in msgObjs:
                await msgObj.edit(
                    content=f'Gamers, <@{bot.openGroupRequests[transmute_id.id]["owner"].id}> is looking for <{transmute_id.user_limit - len(transmute_id.members)}/{transmute_id.user_limit}> gamers for {bot.openGroupRequests[transmute_id.id]["game"]}.\nBe fast and join @{transmute_id.jump_url}'
                )
        
        #print(f'{len(msgObjs)} msgs are edited..')
        ...

@bot.event
async def on_guild_channel_delete(channel) -> None:
    """ 
    cleans up the messages containing users looking for players
    removes any temporary voiceChannels or openGroupRequests from the bot(Class)
    """

    #clean TMP voice Channels & Clean the OpenGroupRequests
    if channel.id in bot.voiceChannels.keys():
        bot.voiceChannels.pop(channel.id)
    
    if channel.id in bot.openGroupRequests.keys():
        for msg in bot.openGroupRequests[channel.id]['messages']:
            await msg.delete()

        bot.openGroupRequests.pop(channel.id)

@bot.event
async def on_guild_join(guild):
    """ if bot joins guild, if guild is not in self.guilds -> if guild.textchannel #search-gamers does not exists -> create textchannel """

    # creating the text_channel according to .env variables
    if server_TextChannel_toSearchPlay_name in [g.name for g in guild.text_channels]:
        return
    
    # check if there is already a suitable category 
    guildCategories = {cat.name.lower() : cat for cat in guild.categories}
    regex = r'(bots|bot)|(gamers|gamer)'
    guildCategories_contains_str = {cat_name : cat_obj for cat_name, cat_obj in guildCategories.items() if re.search(regex, cat_name)}

    print(f'guildCategories filtered {guildCategories_contains_str}')
    
    # searching for a category in which the channel could fit
    category_for_text_channel = None

    if len(guildCategories_contains_str.keys()) > 0:
        for cat_name, cat_obj in guildCategories_contains_str.items():
            print(f'iteration {cat_name} and type: {cat_obj.type}')
            if cat_obj.type == 'private':
                print(f'category {cat_name} is private')
                continue

            category_for_text_channel = cat_obj
            

    print(category_for_text_channel)

    # conclusion -> action
    await guild.create_text_channel(server_TextChannel_toSearchPlay_name, category=category_for_text_channel, reason='creating text_channel for the community find players bot')
    print(f'textchannel \'find-players\' created in the guild {guild.name}')

    
bot.run(TOKEN)
