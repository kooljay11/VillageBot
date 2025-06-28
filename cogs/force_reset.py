import discord
from discord import app_commands
from discord.ext import commands
import json
from utilities import *
from reset import reset

class ForceReset(commands.Cog):
    def __init__(self, client):
        self.client = client
    
    @commands.Cog.listener()
    async def on_ready(self):
        await self.client.tree.sync()
        print(f'{__name__} loaded successfully!')


    @app_commands.command(name="forcereset", description="Developer: Force a daily reset.")
    @app_commands.default_permissions(administrator=True)
    async def force_reset(self, interaction: discord.Interaction):
        user_id = interaction.user.id

        developerlist = await get_developerlist()

        # Make sure this user is a developer/gamemaster
        if str(user_id) not in developerlist:
            await reply(self.client, interaction, 'You are not a developer.')
            return
        
        await reset(self.client)
        message = f'Force reset complete'

        await reply(self.client, interaction, message)



async def setup(client):
    await client.add_cog(ForceReset(client))