import discord
from discord.ext import commands
import json
from copy import deepcopy

class AppCommands(commands.Cog):
    def __init__(self, client):
        self.client = client
    
    @commands.Cog.listener()
    async def on_ready(self):
        await self.client.tree.sync()
        print(f'{__name__} loaded successfully!')

    @commands.command(name="waffle")
    async def waffle(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        username = self.client.get_user(user_id)

        with open("./data/global_info.json", "r") as file:
            global_info = json.load(file)

        try:
            with open(f"./data/user_data/{user_id}.json", "r") as file:
                user = json.load(file)

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
            with open("./default_data/user.json", "r") as file:
                user_info = json.load(file)
            new_user = deepcopy(user_info)
            message = f'{username} waffled for the first time!'

        # Save to database
        with open(f"./data/user_data/{user_id}.json", "w") as file:
            json.dump(user, file, indent=4)

        #await reply(interaction, message)
        await interaction.response.send_message(message)


async def setup(client):
    await client.add_cog(AppCommands(client))