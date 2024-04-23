import discord
from discord import app_commands
from discord.ext import commands, tasks
from utilities import *

class Species(commands.Cog):
    def __init__(self, client):
        self.client = client
    
    @commands.Cog.listener()
    async def on_ready(self):
        await self.client.tree.sync()
        print(f'{__name__} loaded successfully!')
    
    async def print_species(self, species_name):
        species = await get_species(species_name)

        message = f'**{species["name"]}:** '
        for key, value in species.items():
            if key not in ["enabled", "name", "description", "life_stages", "equipment_slots", "attr"]:
                if type(value) == list:
                    message += f'\n\t{key}: {', '.join(value)}'
                else:
                    message += f'\n{key}: {value}'
            elif key in ["life_stages", "equipment_slots", "attr"]:
                message += f'\n{key}:'
                for subkey, subvalue in value.items():
                    if type(subvalue) == list:
                        message += f'\n\t{subkey}: {', '.join(subvalue)}'
                    elif type(subvalue) == dict:
                        message += f'\n\t{subkey}: {", ".join(f"{k}: {v}" for k, v in subvalue.items())}'
                    else:
                        message += f'\n\t{subkey}: {subvalue}'
        
        return message

    @app_commands.command(name="species", description="Lists all available species.")
    async def list_species(self, interaction: discord.Interaction):
        #Get a list of all the species
        species_list = []

        for filename in os.listdir("./data/species"):
            if filename.endswith(".json"):
                species_name = os.path.splitext(filename)[0]
                species = await get_species(species_name)
                species_list.append(species)

        message = f'**List of Playable Species**'

        for species in species_list:
            if bool(species["enabled"]):
                species_message = await self.print_species(species["name"])
                message += f'\n\n{species_message}'
        
        await reply(self.client, interaction, message)


    @app_commands.command(name="speciesinfo", description="Checks the info for a specific species.")
    async def species_info(self, interaction: discord.Interaction, species_name: str):
        #Make sure the species chosen is valid
        try:
            species = await get_species(species_name)
        except:
            await reply(self.client, interaction, "You chose an invalid species. Do /species to check the available choices.")
            return

        message = await self.print_species(species["name"])
        
        await reply(self.client, interaction, message)


async def setup(client):
    await client.add_cog(Species(client))