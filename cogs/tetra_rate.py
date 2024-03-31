import discord
from discord import app_commands
from discord.ext import commands, tasks
from utilities import *

class TetraRate(commands.Cog):
    def __init__(self, client):
        self.client = client
    
    @commands.Cog.listener()
    async def on_ready(self):
        await self.client.tree.sync()
        print(f'{__name__} loaded successfully!')
    
    @app_commands.command(name="trate", description="Check the current waffle-tetra exchange rate.")
    async def trate(self, interaction: discord.Interaction):
        global_info = await get_globalinfo()
        message = f'Currently 1 waffle can buy {global_info["t_exchange_rate"]} tetra.'
        await reply(self.client, interaction, message)


async def setup(client):
    await client.add_cog(TetraRate(client))