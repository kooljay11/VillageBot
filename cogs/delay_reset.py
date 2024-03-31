import discord
from discord import app_commands
from discord.ext import commands, tasks
from utilities import *

class DelayReset(commands.Cog):
    def __init__(self, client):
        self.client = client
    
    @commands.Cog.listener()
    async def on_ready(self):
        await self.client.tree.sync()
        print(f'{__name__} loaded successfully!')
    
    @app_commands.command(name="delayreset", description="Dev: Delay the daily reset by a number of days.")
    async def delay_reset(self, interaction: discord.Interaction, num: int):
        user_id = interaction.user.id

        developerlist = await get_developerlist()

        # Make sure this user is a developer/gamemaster
        if str(user_id) not in developerlist:
            await reply(self.client, interaction, 'You are not a developer.')
            return
        
        global_info = await get_globalinfo()
        global_info["new_day_delay"] += num
        await save_globalinfo(global_info)

        await reply(self.client, interaction, f'Next daily reset delayed by {num} days.')


async def setup(client):
    await client.add_cog(DelayReset(client))