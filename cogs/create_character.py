import discord
from discord import app_commands
from discord.ext import commands, tasks
from utilities import *

class CreateCharacter(commands.Cog):
    def __init__(self, client):
        self.client = client
    
    @commands.Cog.listener()
    async def on_ready(self):
        await self.client.tree.sync()
        print(f'{__name__} loaded successfully!')
    
    @app_commands.command(name="createcharacter", description="Creates a new character.")
    async def create_character(self, interaction: discord.Interaction, name: str, gender: str, species_name: str):
        user_id = interaction.user.id

        # Make sure this player exists
        try:
            user = await get_userinfo(user_id)
        except:
            await reply(self.client, interaction, "You aren't part of the game yet! Do /waffle first.")
            return
        
        #Make sure the species chosen is valid
        try:
            species = await get_species(species_name)
        except:
            await reply(self.client, interaction, "You chose an invalid species. Do /species to check the available choices.")
            return

        #Make sure chosen gender is valid
        if gender not in species["gender_options"]:
            await reply(self.client, interaction, "You chose an invalid gender. Do /species to check the available choices.")
            return
        
        global_info = await get_globalinfo()
        
        #Generate a new character id
        new_char_id = global_info["character_counter"]

        #Prepare the character
        character = {
            "id": new_char_id,
            "name": name,
            "gender": gender,
            "species": species_name,
        }

        #Add default species values
        character["max_energy"] = species["max_energy"]

        #Add the character with the new character id to the user's file
        user["characters"].append(character)

        #Increment the character count on global info
        global_info["character_counter"] += 1
        await save_globalinfo(global_info)

        await save_userinfo(user_id, user)

        message = f'New character created: {character["name"]} [{character["id"]}] - {character["gender"]} {character["species"]}'

        await reply(self.client, interaction, message)


async def setup(client):
    await client.add_cog(CreateCharacter(client))