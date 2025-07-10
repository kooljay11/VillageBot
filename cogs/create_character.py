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
    @app_commands.describe(species_name="Item")
    @app_commands.choices(species_name=[
        app_commands.Choice(name="Human", value="human")
    ])
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

        #Add default character values
        default_character = await get_default_character()
        character = default_character

        # Make sure the character name is 1-100 characters long
        if not (len(name) >= 1 and len(name) <= 100):
            await reply(self.client, interaction, f'You must choose a character name that is 1-100 characters long.')
            return

        #Add the user's character options
        character["id"] = new_char_id
        character["name"] = name
        character["gender"] = gender
        character["species"] = species_name

        #Add default species values (update /selectcharacter whenever this is updated)
        character["energy"] = species["max_energy"]
        character["max_energy"] = species["max_energy"]
        #character["capacity"] = character["capacity"]
        #new_max_capacity = character["max_capacity"] * species["max_capacity_multiplier"] + species["bonus_max_capacity"]
        #character["max_capacity"] += min(new_max_capacity - character["max_capacity"], species["max_bonus_max_capacity"])
        character["max_capacity"] = species["base_max_weight_capacity"]
        character["hunger"] = species["max_hunger"]
        character["max_hunger"] = species["max_hunger"]
        character["protein"] = species["max_protein"]
        character["max_protein"] = species["max_protein"]

        for attr, value in species["attr"].items():
            new_value = character["attr"][attr]["value"] * value["multiplier"] + value["bonus"]
            character["attr"][attr]["value"] = min(character["attr"][attr]["value"] - new_value, value["max_bonus"])
            new_max = character["attr"][attr]["value"] * value["multiplier"] + value["bonus"]
            character["attr"][attr]["max"] = min(character["attr"][attr]["max"] - new_max, value["max_bonus"])
            
        #Add the character with the new character id to the user's file
        user["characters"].append(character)

        #Add the character's name to the user's list of character nicknames
        user["nicknames"]["character"][character["name"]] = character["id"]

        #Increment the character count on global info
        global_info["character_counter"] += 1
        await save_globalinfo(global_info)

        await save_userinfo(user_id, user)

        message = f'New character created: {character["name"]} [{character["id"]}] - {character["gender"]} {character["species"]}'

        await reply(self.client, interaction, message)
    

    @app_commands.command(name="selectcharacter", description="Select one of your characters.")
    async def select_character(self, interaction: discord.Interaction, character_id: int):
        user_id = interaction.user.id

        # Make sure this player exists
        try:
            user = await get_userinfo(user_id)
        except:
            await reply(self.client, interaction, "You aren't part of the game yet! Do /waffle first.")
            return
        
        character_belongs_to_user = False
        selected_character = {}

        for character in user["characters"]:
            if character["id"] == character_id:
                character_belongs_to_user = True
                selected_character = character
                break
        
        if character_belongs_to_user:
            user["character_selected"] = character_id
            message = f'You have selected {selected_character["name"]} (id:{character_id}).'
            
            #Save the changes
            await save_userinfo(user_id, user)
        else:
            message = f'You cannot select a character that doesn\'t belong to you.'

        await reply(self.client, interaction, message)

    #Add options to attr
    @app_commands.command(name="setcharacterattr", description="Set an attribute of one of your characters.")
    async def set_character_attr(self, interaction: discord.Interaction, attr: str, value: str, subattr: str = ""):
        user_id = interaction.user.id

        # Make sure this player exists
        try:
            user = await get_userinfo(user_id)
        except:
            await reply(self.client, interaction, "You aren't part of the game yet! Do /waffle first.")
            return
        
        #Get character
        character = await get_selected_character(user)

        if character == {}:
            await reply(self.client, interaction, "You haven't selected a valid character.")
            return
        
        #Editable attributes at any time before death: name
        #Editable attributes at any time: description
        #Editable attributes before birth only: gender, species (forces gender change to first avail one IF species is actually changed), attr boosts (cant be neg)
        if attr == "name" and "dead" not in character["status"]:
            character["name"] = value
        elif attr == "description":
            character["description"] = value
        #if alive or dead not in status
        elif "alive" not in character["status"] and "dead" not in character["status"]:
            species = await get_species(character["species"])
            if attr == "gender":
                #Make sure chosen gender is valid
                if value not in species["gender_options"]:
                    await reply(self.client, interaction, "You chose an invalid gender. Do /species to check the available choices.")
                    return
                
                character["gender"] = value
            elif attr == "species":
                #Make sure the species is different from before
                if value == character["species"]:
                    await reply(self.client, interaction, "Your character is already that species.")
                    return

                #Make sure the species chosen is valid
                try:
                    species = await get_species(value)
                except:
                    await reply(self.client, interaction, "You chose an invalid species. Do /species to check the available choices.")
                    return
                
                character["species"] = value
                # Give default gender for now
                character["gender"] = species["gender_options"][0]

                # Add default species values
                character["energy"] = species["max_energy"]
                character["max_energy"] = species["max_energy"]
                character["capacity"] = character["capacity"]
                new_max_capacity = (character["max_capacity"]) * species["max_capacity_multiplier"] + species["bonus_max_capacity"]
                character["max_capacity"] += min(new_max_capacity - character["max_capacity"], species["max_bonus_max_capacity"])
                character["hunger"] = species["max_hunger"]
                character["max_hunger"] = species["max_hunger"]

                for attribute, content in species["attr"].items():
                    new_value = character["attr"][attribute]["value"] * content["multiplier"] + content["bonus"]
                    character["attr"][attribute]["value"] = min(character["attr"][attribute]["value"] - new_value, content["max_bonus"])
                    new_max = character["attr"][attribute]["value"] * content["multiplier"] + content["bonus"]
                    character["attr"][attribute]["max"] = min(character["attr"][attribute]["max"] - new_max, content["max_bonus"])
            elif attr == "attr_boost":
                total_boosts = 0

                #Attr boosts can't be negative
                if value < 0:
                    await reply(self.client, interaction, "You cannot give a character negative boosts.")
                    return

                character["attr"][subattr]["boost"] = value

                #See what the new total attr boosts would be with the change
                for attribute, content in character["attr"]:
                    total_boosts += content["boost"]

                global_info = await get_globalinfo()

                #Get the maximum attr boosts this user can have
                #Make sure the new total attr boosts will be less than the user's maximum
                if total_boosts > global_info["waffle_attr_boosts"].get(user["waffle_rank"], 0):
                    await reply(self.client, interaction, "Your character would have too many boosts.")
                    return
        
        #Save the changes
        await save_userinfo(user_id, user)

        message = f'Character {attr} updated!'

        await reply(self.client, interaction, message)

async def setup(client):
    await client.add_cog(CreateCharacter(client))