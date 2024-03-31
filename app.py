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
from utilities import *
from reset import reset
#https://discordpy.readthedocs.io/en/stable/intro.html

client = commands.Bot(command_prefix="/", intents=discord.Intents.all())

@tasks.loop(time=[datetime.time(hour=12, minute=0, tzinfo=datetime.timezone.utc)])
#@tasks.loop(hours=1)
async def dailyReset():
    reset(client)

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

