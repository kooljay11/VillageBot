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

            message += f'\n\nCharacters: '
            for character in user["characters"]:
                char_message = await print_quick_character(character)
                message += f'\n{char_message}'
                

        except:
            message = 'Error while fetching user information.'

        await reply(self.client, interaction, message)



    async def char_mode_autocomplete(self, interaction: discord.Interaction, current: str,) -> list[app_commands.Choice[str]]:
        choices = ['quick', 'full']
        return [
            app_commands.Choice(name=choice, value=choice)
            for choice in choices if current.lower() in choice.lower()
        ]

    @app_commands.command(name="charinfo", description="Check your character's information.")
    #@app_commands.autocomplete(mode=char_mode_autocomplete)
    @app_commands.describe(mode="Mode")
    @app_commands.choices(mode=[
        app_commands.Choice(name="Quick", value="quick"),
        app_commands.Choice(name="Full", value="full")
    ])
    async def char_info(self, interaction: discord.Interaction, chararacter_id: int = -1, mode: str = "quick"):
        user_id = interaction.user.id

        # Make sure this player exists in user_info
        try:
            user = await get_userinfo(user_id)
        except:
            await reply(self.client, interaction, "That user has not waffled yet.")
            return
        
        #Get character
        try:
            if chararacter_id < 0:
                #Get the user's selected character
                character = await get_selected_character(user)
            else:
                character = await get_character(chararacter_id)
        except:
            await reply(self.client, interaction, "Character not found.")
            return
        
        if mode == "quick":
            message = await print_quick_character(character)
        elif mode == "full":
            message = await print_full_character(character)
        else:
            message = f'Mode incorrectly selected.'

        await reply(self.client, interaction, message)

async def setup(client):
    await client.add_cog(UserInfo(client))