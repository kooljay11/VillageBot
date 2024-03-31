import discord
from discord import app_commands
from discord.ext import commands, tasks
from utilities import *

class UserInfo(commands.Cog):
    def __init__(self, client):
        self.client = client
    
    @commands.Cog.listener()
    async def on_ready(self):
        await self.client.tree.sync()
        print(f'{__name__} loaded successfully!')
    
    @app_commands.command(name="userinfo", description="Check someone's user info.")
    async def user_info(self, interaction: discord.Interaction, user_id: str = ""):
        global_info = await get_globalinfo()

        if user_id == "":
            user_id = interaction.user.id

        # Make sure this player exists in user_info
        try:
            user = await get_userinfo(user_id)
        except:
            await reply(self.client, interaction, "That user has not waffled yet.")
            return

        try:
            message = f'{self.client.get_user(int(user_id))}'
            if user["waffle_rank"] != "":
                message += f' the {user["waffle_rank"]}'

            message += f' has waffled {user["waffles"]} times and is on a {user["waffle_streak"]} day streak. '

            next_rank = await get_next_waffle_rank(user["waffle_rank"])

            if next_rank != "":
                waffles = int(user["waffles"])
                next_waffles = int(global_info["waffle_rank"][next_rank])

                message += f'They are {next_waffles - waffles} waffles away from the next rank of {next_rank}. '

            message += f'They have spent {user.get("spent_waffles", 0)} quacks and have {user.get("tetra", 0)} tetra. '

            if user["poker_spins"] > 0:
                message += f'\n\nPoker slot machine spins available: {user["poker_spins"]}'

        except:
            message = 'Error while fetching user information.'

        await reply(self.client, interaction, message)


async def setup(client):
    await client.add_cog(UserInfo(client))