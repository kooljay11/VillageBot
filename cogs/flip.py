import discord
from discord import app_commands
from discord.ext import commands, tasks
from utilities import *
import random

class Flip(commands.Cog):
    def __init__(self, client):
        self.client = client
    
    @commands.Cog.listener()
    async def on_ready(self):
        await self.client.tree.sync()
        print(f'{__name__} loaded successfully!')
    
    @app_commands.command(name="flip", description="Flip a coin to double your tetra bet.")
    async def ping(self, interaction: discord.Interaction, number: int):
        user_id = interaction.user.id

        # Make sure this player exists in user_info
        try:
            user = await get_userinfo(user_id)
        except:
            await reply(self.client, interaction, "You aren't part of the game yet! Do /waffle first.")
            return

        # Make sure the player can't bet negative tetra
        if number < 1:
            await reply(self.client, interaction, "Nice try.")
            return

        # Make sure the player can't bet more tetra than they have
        try:
            if int(user["tetra"]) < number:
                await reply(self.client, interaction, "You don't have enough tetra for that.")
                return
        except:
            await reply(self.client, interaction, "You don't have enough tetra for that.")
            return

        # Give the player tetra if they win the bet
        if random.choice([True, False]):
            user["tetra"] += number
            message = f'You won {number} tetra!'
        else:
            user["tetra"] -= number
            message = f'You lost {number} tetra...'

        # Save to database
        await save_userinfo(user_id, user)

        await reply(self.client, interaction, message)


async def setup(client):
    await client.add_cog(Flip(client))