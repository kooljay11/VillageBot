import discord
from discord import app_commands
from discord.ext import commands, tasks
from utilities import *

class Gather(commands.Cog):
    def __init__(self, client):
        self.client = client
    
    @commands.Cog.listener()
    async def on_ready(self):
        await self.client.tree.sync()
        print(f'{__name__} loaded successfully!')
    
    @app_commands.command(name="gather", description="Gather stuff")
    @app_commands.describe(item_name="Item")
    @app_commands.choices(item_name=[
        app_commands.Choice(name="Berries", value="berry"),
        app_commands.Choice(name="Mushrooms", value="mushroom"),
        app_commands.Choice(name="Bugs", value="bug"),
        app_commands.Choice(name="Herbs", value="herb"),
        app_commands.Choice(name="Branches", value="branch"),
        app_commands.Choice(name="Seeds (faster with sickle or scythe)", value="seed"),
        app_commands.Choice(name="Crop (faster with sickle or scythe)", value="crop"),
        app_commands.Choice(name="Dirt (faster with shovel or adze)", value="dirt"),
        app_commands.Choice(name="Logs (needs axe or adze)", value="log"),
        app_commands.Choice(name="Stones (faster with pickaxe or hammer_chisel)", value="stone"),
        app_commands.Choice(name="Mineral flakes (need pan)", value="mineral_flake"),
        app_commands.Choice(name="Mineral ore (need pickaxe)", value="mineral_ore")
    ])
    #async def gather(self, interaction: discord.Interaction, item: str, item_state: str = "", amount: int = 1, dump_building_id: str = "", dump_room_id: str = "", dump_subroom_id: str = "", with_character_id: str = ""):
    async def gather(self, interaction: discord.Interaction, item_name: str, dump_building_id: str = "", dump_room_id: str = "", with_character_id: str = ""):
        user_id = interaction.user.id

        # Make sure this player exists
        try:
            user = await get_userinfo(user_id)
        except:
            await reply(self.client, interaction, "That user has not waffled yet.")
            return
        
        # Get the user's selected character
        try:
            character = await get_selected_character(user)
        except:
            await reply(self.client, interaction, "Selected character not found.")
            return
        
        # Make sure the character is currently alive
        if "alive" not in character["status"]:
            await reply(self.client, interaction, "Selected character is not alive.")
            return
        
        # Make sure the character exists in a valid ward
        if character["ward_id"] >= 0:
            try:
                ward = await get_ward(character["ward_id"])
            except:
                await reply(self.client, interaction, "Specified ward does not exist.")
                return
        else:
            await reply(self.client, interaction, "Ward not specified.")
            return
        
        # Make sure the item exists in the database
        # Otherwise check the material database
        try:
            item_info = await get_item(item_name)
        except:
            try:
                item_info = await get_material(item_name)
            except:
                await reply(self.client, interaction, "Item not found in the database.")
                return
            
        # Make sure the item exists in tasks.json
        task_info = await get_task_info("gather", item_name)
        if task_info == "":
            task_info = await get_task_info("gather", item_info["material_type"])

            if task_info == "":
                await reply(self.client, interaction, "Task info for this item was not found in the task list.")
                return
        
        # Make sure they have an appropriate tool if required
        tool_modifier = 0
        for tool_name in task_info["tools"]:
            tool = await get_item_stack_in_inv(character, tool_name)

            if tool != {}:

                tool_modifier = max(task_info["tools"][tool_name], tool_modifier)
                
        if tool_modifier == 0:
            if item_info["requires_harvesting_tool"]:
                await reply(self.client, interaction, "You don't have the correct tool for this action.")
                return

        # Make sure the character has enough energy to do the action
        # energy_required = amount * task_info["base_collection_energy"] * tool_modifier * skill_modifier * ATR_modifier
        energy_required = item_info["base_collection_energy"]

        if character["energy"] < energy_required:
            await reply(self.client, interaction, f'You need {energy_required} to do this action, but you only have {character["energy"]} energy left.')
            return

        # Make sure the item is available in the land
        item_available = await get_item_available_in_ward(ward, item_name)

        if not item_available:
            # item_available = await get_item_available_in_ward(ward, item_info["material_type"])

            # if not item_available:
            #     await reply(self.client, interaction, f'{item_name} cannot be collected from this ward.')
            #     return
            await reply(self.client, interaction, f'{item_name} cannot be collected from this ward. There needs to be available {item_info["land_required"]}')
            return

        # Make sure the dump location is a valid location
        dump_location = []

        try:
            dump_building = await get_building(ward, dump_building_id)
            dump_room = dump_building[dump_room_id]
            #dump_subroom = dump_room[dump_subroom_id]
        except:
            print()
        

        # Change the friend alias to the friend character id
        # If numeric then just add
        # If not then check for aliases
        if with_character_id == "":
            with_character_id = -1
        elif with_character_id.isnumeric():
            with_character_id = int(with_character_id)
        else:
            user["nicknames"]["character"].get(with_character_id, -1)

        # Negate energy from the user
        character["energy"] -= energy_required

        # Add to the task queue
        result = await add_to_queue(user_id, character["id"], "gather", item_name, character["ward_id"], dump_id=dump_location,friend_char_id=with_character_id, subtask=item_name)

        if result == None:
            # Save the user info
            await save_userinfo(user_id, user)
            # message = f'{character["name"]} began collecting {amount} {item_name}.'
            message = f'{character["name"]} began collecting {item_name}.'
        else:
            message = f'Error in adding the action to the queue. Make sure the task group you are joining was started this month.'
            print(f'result: {result}')
            if with_character_id > -1:
                message += f'Make sure your friend\'s character id is valid and that the group you are trying to join is taking the same action, with the same item, and has enough slots left for new members.'

        await reply(self.client, interaction, message)



async def setup(client):
    await client.add_cog(Gather(client))