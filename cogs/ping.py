import discord
from discord import app_commands
from discord.ext import commands, tasks

class Ping(commands.Cog):
    def __init__(self, client):
        self.client = client
    
    @commands.Cog.listener()
    async def on_ready(self):
        await self.client.tree.sync()
        print("Ping.py is ready!")
    
    @app_commands.command(name="ping", description="Sends a test message.")
    async def ping(self, interaction: discord.Interaction):
        bot_latency = round(self.client.latency * 1000)
        await interaction.response.send_message(f'Pong! {bot_latency} ms.')


async def setup(client):
    await client.add_cog(Ping(client))