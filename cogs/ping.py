import discord
from discord.ext import commands, tasks

class Ping(commands.Cog):
    def __init__(self, client):
        self.client = client
    
    @commands.Cog.listener()
    async def on_ready(self):
        await self.client.tree.sync()
        print("Ping.py is ready!")
    
    @commands.command()
    async def ping(self, ctx):
        bot_latency = round(self.client.latency * 1000)
        await ctx.send(f'Pong! {bot_latency} ms.')


async def setup(client):
    await client.add_cog(Ping(client))