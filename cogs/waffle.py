import discord
from discord import app_commands
from discord.ext import commands
import json
from utilities import *

class Waffle(commands.Cog):
    def __init__(self, client):
        self.client = client
    
    @commands.Cog.listener()
    async def on_ready(self):
        await self.client.tree.sync()
        print(f'{__name__} loaded successfully!')

    @app_commands.command(name="waffle", description="A waffle a day will make your worries waft away!")
    async def waffle(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        username = self.client.get_user(user_id)

        global_info = await get_globalinfo()

        try:
            user = await get_userinfo(user_id)

            if not bool(user["waffled_today"]):
                user["waffled_today"] = True
                user["waffles"] += 1
                user["waffle_streak"] += 1

                message = f'{username} waffled around.'

                if user["waffle_streak"] >= global_info["max_waffle_streak_length"]:
                    user["waffle_streak"] -= global_info["max_waffle_streak_length"]
                    user["waffles"] += global_info["waffle_streak_reward"]
                    message += f'\n{username} finished a streak and got an extra {global_info["waffle_streak_reward"]} waffles.'
            else:
                message = f'{username} tried to waffle but they already waffled too much today.'
        except:
            user = await get_default_userinfo()
            message = f'{username} waffled for the first time!'

        # Save to database
        await save_userinfo(user_id, user)

        await reply(self.client, interaction, message)
        #await interaction.response.send_message(message)


async def setup(client):
    await client.add_cog(Waffle(client))