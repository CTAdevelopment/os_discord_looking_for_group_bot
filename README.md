# Discord Bot - Search Gamers in your community
## Made by Ko-Lin Chang for DBE (Den Bosch E-Sports)

## Installation

# Prerequisits
- The .env variables should be set in order to work: 
    - discord_token: *requires the Discord API Key*
    - discord_guild: *requires the discord guild role 'ambachtelijk'*
    - server_cat_name: *the category name in which the temporary voicechannels will be created. This category is automatically made if it doesnt exist. Please specify this, or the bot will not run*
    - server_main_name : *The name of the Server in which the bot will create temporary channels for groups of players*
    - idea_master: *the user ID of the person whom will receive messages sent by the command '/idea'*
    - invite_link: *after adding the bot, create a link for your bot in the Discord configuration menu (https://discord.com/developers/applications/). You can use the following parameters for the permissions and the scope: permissions=406142855248&scope=bot*
- ideally there is a category in your server that includes the name 'bot' or 'bots'. The bot will auto-add a channel 'find-players' to your category (if any), else
    it is created in the server itself. If this channel is private, the bot is unable to post messages in this category -> channel. There is no solution from Discord yet, so take this in consideration.
- run 'pip install -r requirements.txt' in your local/virtual environment to install the required packages. Working on a PIP package.

# Practical Installation
- *Add the Bot to your community servers. You are able to change the name in the .env*
- *Note: the following commands will be added to your server (/idea, /zoek, /commandos)*

# Functions

- /zoek [game} [looking for X gamers] [max amount of gamers]
- /idea [title of the idea] [body of the idea]
- /commandos -- will provide the user with the above commands

# /zoek 
- If the user types /zoek in the channel or in a DM to the bot, there is a prompt [game X] [looking for X gamers] [max amount of gamers]
- once confirmed, a temporary voice channel is created with a max of X players ([max amount ..]) in the discord_guild (.env).
- all servers in which the bot sits will receive a message in #zoek-gamers where a post is made according to the users request. If the bot has no access to one of these channels. The idea_master(.env) will receive an update aboout this.

- the voicechannel will be removed if a user leaves the channels & the channel is older than 1 day and empty
- the voicechannel can be adjusted by sending another request
- the messages within the servers- are changed on /join, /leave of the TMP voicechannel
- can be manually deleted -- will also delete the messages corresponding to the TMP voice_channel


