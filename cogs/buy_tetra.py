import discord
from discord import app_commands
from discord.ext import commands, tasks
from utilities import *

class BuyTetra(commands.Cog):
    def __init__(self, client):
        self.client = client
    
    @commands.Cog.listener()
    async def on_ready(self):
        await self.client.tree.sync()
        print(f'{__name__} loaded successfully!')
    
    @app_commands.command(name="buytetra", description="Trade in some of your waffles for tetra.")
    async def buytetra(self, interaction: discord.Interaction, waffles: int):
        global_info = await get_globalinfo()

        user_id = interaction.user.id

        # Make sure this player exists in user_info
        try:
            user = await get_userinfo(user_id)
        except:
            await reply(self.client, interaction, "You aren't part of the game yet! Do /waffle first.")
            return

        # Make sure the player has enough waffles
        if int(user["waffles"]) - int(user["spent_waffles"]) < waffles:
            await reply(self.client, interaction, "You don't have enough waffles for that.")
            return

        user["spent_waffles"] += waffles
        result = int(global_info["t_exchange_rate"]) * waffles
        user["tetra"] = user.get("tetra", 0) + result

        # Save to database
        await save_userinfo(user_id, user)

        message = f'You bought {result} tetra using {waffles} waffles. You now have {user["tetra"]} tetra and {user["waffles"]-user["spent_waffles"]} unspent waffles.'

        await reply(self.client, interaction, message)


async def setup(client):
    await client.add_cog(BuyTetra(client))