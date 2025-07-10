import discord
from discord import app_commands
from discord.ext import commands, tasks
from utilities import *

class Basics(commands.Cog):
    def __init__(self, client):
        self.client = client
    
    @commands.Cog.listener()
    async def on_ready(self):
        await self.client.tree.sync()
        print(f'{__name__} loaded successfully!')
    
    @app_commands.command(name="eat", description="Gather stuff")
    @app_commands.describe(item_name="Item")
    @app_commands.choices(item_name=[
        app_commands.Choice(name="Berries", value="berry"),
        app_commands.Choice(name="Mushrooms", value="mushroom"),
        app_commands.Choice(name="Bugs", value="bug"),
        app_commands.Choice(name="Bread", value="bread"),
        app_commands.Choice(name="Raw Meat", value="raw_meat"),
        app_commands.Choice(name="Cooked Meat", value="cooked_meat")
    ])
    @app_commands.describe(item_state="State")
    @app_commands.choices(item_state=[
        app_commands.Choice(name="Raw", value="raw"),
        app_commands.Choice(name="Cooked", value="cooked"),
        app_commands.Choice(name="Unsafe", value="unsafe"),
        app_commands.Choice(name="Questionable", value="questionable"),
        app_commands.Choice(name="Borderline", value="borderline"),
        app_commands.Choice(name="Good", value="good"),
        app_commands.Choice(name="Excellent", value="excellent")
    ])
    async def eat(self, interaction: discord.Interaction, item_name: str, item_state: str = "", amount: int = 1):
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
        
        # Make sure the item exists in the database
        # Otherwise check the material database
        try:
            item_info = await get_item(item_name, item_state)
        except:
            try:
                item_info = await get_material(item_name)
            except:
                await reply(self.client, interaction, "Item not found in the database.")
                return

        # Make sure the item is available in the character's inventory
        try:
            item_stack = await get_item_stack_in_inv(character, item_name, item_state=item_state)
        except:
            await reply(self.client, interaction, "Item not found in this character's inventory.")
            return
        
        # Make sure the amount of items specified is actually available
        if amount > item_stack["amount"]:
            await reply(self.client, interaction, f"This character only has {item_stack["amount"]} {item_name}.")
            return
        
        total_hunger_replenishment = item_info["hunger_replenishment"] * amount
        total_protein_replenishment = item_info["protein_replenishment"] * amount
        
        # Make sure the item is actually food
        if total_hunger_replenishment <= 0 and total_protein_replenishment <= 0:
            await reply(self.client, interaction, "This item is not food.")
            return
        
        # Make sure the item will actually lead to a full point of hunger/protein
        if total_hunger_replenishment < 1 and total_protein_replenishment < 1:
            await reply(self.client, interaction, "This item is not food.")
            return
        
        hunger_needed = character["max_hunger"] - character["hunger"]
        protein_needed = character["max_protein"] - character["protein"]
        
        # Make sure the character only consumes how much they need
        if item_info["hunger_replenishment"] > 0:
            amount_need_hunger = int(min(hunger_needed, total_hunger_replenishment) / item_info["hunger_replenishment"])
        else:
            amount_need_hunger = 0
        
        if item_info["protein_replenishment"] > 0:
            amount_need_protein = int(min(protein_needed, total_protein_replenishment) / item_info["protein_replenishment"])
        else:
            amount_need_protein = 0
        
        # Make sure the character is not at max hunger/protein depending on which one the food refills
        amount_used = max(amount_need_hunger, amount_need_protein)
        amount_remaining = amount - amount_used

        total_hunger_replenishment = item_info["hunger_replenishment"] * amount_used
        total_protein_replenishment = item_info["protein_replenishment"] * amount_used

        # Refill hunger and protein
        item_stack["amount"] -= amount_used
        character["hunger"] += total_hunger_replenishment
        character["protein"] += total_protein_replenishment

        character["hunger"] = min(character["hunger"], character["max_hunger"])
        character["protein"] = min(character["protein"], character["max_protein"])

        # Save the user info
        await save_userinfo(user_id, user)

        if total_hunger_replenishment > 0 and total_protein_replenishment > 0:
            message = f'{character["name"]} ate {amount_used} {item_name} and gained {total_hunger_replenishment} hunger and {total_protein_replenishment} protein. '
        elif total_hunger_replenishment > 0:
            message = f'{character["name"]} ate {amount_used} {item_name} and gained {total_hunger_replenishment} hunger. '
        elif total_protein_replenishment > 0:
            message = f'{character["name"]} ate {amount_used} {item_name} and {total_protein_replenishment} protein. '
        else:
            message = f''

        if amount_remaining > 0:
            message += f'They were too full to eat {amount_remaining} {item_name}.'

        await reply(self.client, interaction, message)


    # Give item num
    @app_commands.command(name="give", description="Give an item to another character")
    async def give(self, interaction: discord.Interaction, recipient: str, item_name: str = "", item_state: str = "", item_index: int = -1, amount: int = 1):
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
        
        # Make sure the recipient is a valid character in the same ward
        recipient_id_nick = await get_id_nickname(self.client, user, recipient)
        try:
            recipient = await get_character(recipient_id_nick["id"])
        except:
            await reply(self.client, interaction, "Recipient character not found.")
            return
        
        if character["ward_id"] != recipient["ward_id"]:
            await reply(self.client, interaction, f"{recipient["name"]} is not in the same ward as {character["name"]}.")
            return
        
        # Make sure the item exists in the database
        # Otherwise check the material database
        try:
            item_info = await get_item(item_name, item_state=item_state)
        except:
            try:
                item_info = await get_material(item_name)
            except:
                await reply(self.client, interaction, "Item not found in the database.")
                return

        # Make sure the item is available in the character's inventory
        try:
            if item_index <= -1:
                item_stack = await get_item_stack_in_inv(character, item_name, item_state=item_state)
            else:
                item_stack = character["inventory"][item_index]
                item_name = item_stack["name"]
                item_type = await get_item_type(item_name)
                if item_type == "item":
                    item_state = item_stack["state"]
                elif item_type == "tool":
                    item_state = item_stack["material"]
        except:
            await reply(self.client, interaction, "Item not found in this character's inventory.")
            return
        
        # Make sure the amount of items specified is actually available
        if amount > item_stack["amount"]:
            await reply(self.client, interaction, f"This character only has {item_stack["amount"]} {item_name}.")
            return
        
        # Put it in the task queue
        await add_to_queue(user_id, character["id"], "give", item_name, character["ward_id"], amount=amount, target_id=recipient["id"], state=item_state)

        message = f'{character["name"]} is proposing to give {amount} {item_name} to {recipient["name"]}.'
        
        # Save the user info
        await save_userinfo(user_id, user)

        await reply(self.client, interaction, message)

    @app_commands.command(name="gift", description="List/Accept/Deny gifts from another character")
    @app_commands.describe(mode="Mode")
    @app_commands.choices(mode=[
        app_commands.Choice(name="List", value="list"),
        app_commands.Choice(name="Accept", value="accept"),
        app_commands.Choice(name="Deny", value="deny")
    ])
    async def gift(self, interaction: discord.Interaction, mode: str = "list", gift_index: int = -1):
        user_id = interaction.user.id

        # Make sure this player exists
        try:
            user = await get_userinfo(user_id)
        except:
            await reply(self.client, interaction, "That user has not waffled yet.")
            return
        
        # Get the user's selected character
        try:
            recipient = await get_selected_character(user)
        except:
            await reply(self.client, interaction, "Selected character not found.")
            return
        
        # Make sure the character is currently alive
        if "alive" not in recipient["status"]:
            await reply(self.client, interaction, "Selected character is not alive.")
            return
        
        # Make sure the character exists in a valid ward
        if recipient["ward_id"] >= 0:
            try:
                ward = await get_ward(recipient["ward_id"])
            except:
                await reply(self.client, interaction, "Specified ward does not exist.")
                return
        else:
            await reply(self.client, interaction, "Ward not specified.")
            return
        
        # Get the list of gift tasks that have this user's character id as the target_id
        list_gifts = await get_list_gifts(ward, recipient["id"])
        
        if mode == "list":
            message = f'**List of Gifts**'
            index = 0

            for gift in list_gifts:
                user_giver_id = gift["members"][0]["user_id"]
                user_giver = await get_userinfo(user_giver_id)
                char_giver_id = gift["members"][0]["char_id"]
                giver = await get_user_character(user_giver, char_giver_id)

                amount = gift["members"][0]["amount"]

                message += f'\n[{index}] {amount} {gift["item"]} {gift["state"]} from {giver["name"]}.'
                index += 1
        elif mode == "accept":
            # Get the task group in question
            task_group = list_gifts[gift_index]

            # Make sure the giver is a valid character in the same ward
            user_giver_id = task_group["members"][0]["user_id"]
            user_giver = await get_userinfo(user_giver_id)
            char_giver_id = task_group["members"][0]["char_id"]
            giver = await get_user_character(user_giver, char_giver_id)

            amount = task_group["members"][0]["amount"]
            print(f'amount: {amount}')
            
            # Make sure both characters are in the same ward
            if giver["ward_id"] != recipient["ward_id"]:
                await reply(self.client, interaction, f"{recipient["name"]} is not in the same ward as {giver["name"]}.")
                return
            
            # Make sure the item is available in the givers's inventory
            try:
                item_stack = await get_item_stack_in_inv(giver, task_group["item"], item_state=task_group["state"])
            except:
                await reply(self.client, interaction, "Item not found in this character's inventory.")
                return
            
            # Make sure the amount of items specified is actually available
            if amount > item_stack["amount"]:
                await reply(self.client, interaction, f"This character only has {item_stack["amount"]} {item_stack["name"]}.")
                return
            
            print(f'item_stack["amount"]: {item_stack["amount"]}')

            # Take out the specified amount of items
            removed_stack = await remove_item_in_inv(giver, task_group["item"], amount, state=task_group["state"])
            print(f'removed_stack: {removed_stack}')

            # Put in the specified amount of items
            left_over_stack = await add_item_stack_in_inv(recipient, removed_stack)
            print(f'left_over_stack: {left_over_stack}')

            # Put left overs back in the giver's inventory
            if left_over_stack != {}:
                message = f'{giver["name"]} gave {recipient["name"]} {amount - left_over_stack["amount"]} {task_group["item"]}.'
                await add_item_stack_in_inv(giver, left_over_stack)
            else:
                message = f'{giver["name"]} gave {recipient["name"]} {amount} {task_group["item"]}.'
            
            print(f'left_over_stack post: {left_over_stack}')
            # Remove the task_group from the task queue
            ward["task_queue"].remove(task_group)
            print(f'ward["task_queue"]: {ward["task_queue"]}')

            await save_userinfo(user_id, user)
            await save_userinfo(user_giver_id, user_giver)
            await save_ward(ward)

        elif mode == "deny":
            # Get the task group in question
            task_group = list_gifts[gift_index]

            amount = task_group["members"][0]["amount"]
            
            message = f'Denied gift of {amount} {task_group["item"]}.'

            # Remove it
            ward["task_queue"].remove(task_group)

            await save_ward(ward)
        
        await reply(self.client, interaction, message)

async def get_list_gifts(ward, recipient_id):
    list_gifts = []

    for task_group in ward["task_queue"]:
        if task_group["task"] == "give" and task_group["target_id"] == recipient_id:
            list_gifts.append(task_group)
        
    return list_gifts

async def setup(client):
    await client.add_cog(Basics(client))