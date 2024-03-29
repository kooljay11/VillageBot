#https://discord.com/api/oauth2/authorize?client_id=1220893068018843681&permissions=139586776128&scope=bot
import os
import asyncio
import random
import math
import datetime
from copy import deepcopy
import json
import discord
from discord.ext import commands, tasks
#https://discordpy.readthedocs.io/en/stable/intro.html

client = commands.Bot(command_prefix="/", intents=discord.Intents.all())

@tasks.loop(time=[datetime.time(hour=12, minute=0, tzinfo=datetime.timezone.utc)])
#@tasks.loop(hours=1)
async def dailyReset():

    #newday_message = f'A new day has arrived and the ducks feel refreshed from their slumber. The current season is: {global_info["current_season"]}'
    newday_message = f''
    
    # Tell all specified channels about the update
    with open("./data/server_info.json", "r") as file:
        server_info = json.load(file)
    
    for server_id, server in server_info.items():
        for channel_id in server["daily_channels"]:
            try:
                await client.get_channel(channel_id).send(newday_message)
            except:
                #print(f'Error trying to execute the new day to channel {channel_id}.')
                print()


@client.event
async def on_ready():
    await client.tree.sync()
    print("Bot is connected to Discord")
    dailyReset.start()


async def load():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            await client.load_extension(f"cogs.{filename[:-3]}")
            print(f"{filename[:-3]} is loaded!")


async def main():
    async with client:
        await load()

        with open("config.json", "r") as file:
            config = json.load(file)

        await client.start(config['token'])

asyncio.run(main())

