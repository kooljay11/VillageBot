import json
from copy import deepcopy
import os
import random as rand

# Cannot name get_userinfo due to no function overloading in Python
async def get_userinfo_by_nick(self_user, target):
    if str(target).isnumeric():
        target_user_id = target
    else:
        target_user_id = self_user["nicknames"].get(target, 0)
    
    user = await get_userinfo(target_user_id)
    
    return user

async def get_userinfo(user_id):
    with open(f"./data/user_data/{user_id}.json", "r") as file:
        user = json.load(file)

    # Get the default userinfo
    default_user = await get_default_userinfo()

    for attr, value in default_user.items():
        if user.get(attr, None) is None:
            user[attr] = default_user[attr]
            await save_userinfo(user_id, user)
    
    return user

async def save_userinfo(user_id, user):
    with open(f"./data/user_data/{user_id}.json", "w") as file:
        json.dump(user, file, indent=4)

async def get_default_userinfo():
    with open("./default_data/user.json", "r") as file:
        user = json.load(file)
    
    return user

async def create_user_profile(client, user_id):
    default_user = await get_default_userinfo()
    default_user["nicknames"][str(await client.fetch_user(user_id))] = user_id

    await save_userinfo(user_id, default_user)

    return default_user

async def get_nickname(self_user, target_id, type="character"):
    for nickname, id in self_user["nicknames"][type].items():
        if id == target_id:
            return nickname
    
    return ""

async def get_id_nickname(client, self_user, target: str, type: str = "character"):
    #print(f'Getting id and nick for {target}')
    target = str(target)

    if target.isnumeric():
        #print(f'target: {target}')
        #print(f'int(target): {int(target)}')
        target_id = int(target)
        print(f'target_id: {target_id}')
        target_name = await get_nickname(self_user, target_id, type=type)
        print(f'target_name 1: {target_name}')
        if target_name == "":
            if type == "character":
                target_character = await get_character(target_id)
                target_name = target_character["name"]
            elif type == "user":
                target_name = str(await client.fetch_user(target_id))
            else:
                target_name = ""
            print(f'target_name 2: {target_name}')
    else:
        target_id = int(self_user["nicknames"][target])
        #print(f'target: {target}')
        target_name = target
    
    return {"id": target_id, "name": target_name}

async def get_species(species_name):
    with open(f"./data/species/{species_name}.json", "r") as file:
        overrides = json.load(file)

    default_species = await get_default_species()
    species = default_species
    
    # Only add non tiered attributes to the species
    for attr, value in default_species.items():
        if attr not in ["life_stages", "attr"]:
            species[attr] = value

    # Replace all non tiered attributes with species specific overrides
    for attr, value in overrides.items():
        if attr not in ["life_stages", "attr"]:
            species[attr] = value

    # Give the species all of the life_stages attributes
    for attr, value in overrides["life_stages"].items():
        for attr_stat, stat_value in value.items():
            species["life_stages"][attr][attr_stat] = stat_value

    # Give the species all of the attr attributes
    for attr, value in overrides["attr"].items():
        for attr_stat, stat_value in value.items():
            species["attr"][attr][attr_stat] = stat_value
    
    return species

async def get_default_species():
    with open("./default_data/species.json", "r") as file:
        species = json.load(file)
    
    return species

async def print_quick_character(character):
    message = f'{character["name"]} [{character["id"]}] - {character["gender"]} {character["species"]} :zap: {character["energy"]}/{character["max_energy"]} :apple: {character["hunger"]}/{character["max_hunger"]} :meat_on_bone: {character["protein"]}/{character["max_protein"]} :heart: {character["attr"]["CON"]["value"]}/{character["attr"]["CON"]["max"]} :blue_heart: {character["attr"]["WIL"]["value"]}/{character["attr"]["WIL"]["max"]} :muscle: {character["attr"]["ARM"]["value"]}/{character["attr"]["ARM"]["max"]} :leg: {character["attr"]["LEG"]["value"]}/{character["attr"]["LEG"]["max"]} :fast_forward: {character["attr"]["REF"]["value"]}/{character["attr"]["REF"]["max"]} :brain: {character["attr"]["INT"]["value"]}/{character["attr"]["INT"]["max"]} :speaking_head: {character["attr"]["SOC"]["value"]}/{character["attr"]["SOC"]["max"]}'

    if len(character["status"]) > 0:
        message += f'\n\tStatus: {', '.join(character["status"])}'
    return message

async def print_full_character(character):
    message = f'{character["name"]} [{character["id"]}] - {character["gender"]} {character["species"]}'
    
    if len(character["description"]) > 0:
        message += f'\n\t*{character["description"]}*'

    #Biographical
    age = await years(character["age_months"])
    message += f'\nAge: {age[0]} years and {age[1]} months'
    message += f'\nParents: '

    parents = []
    for parent_id in character["parent_ids"]:
        parent = await get_character(parent_id)
        parents.append(f'{parent["name"]} ({parent_id})')
    message += f'{', '.join(parents)}'

    if len(character["children_ids"]) > 0:
        children = []
        message += f'\nChildren: '
        for child_id in character["children_ids"]:
            child = await get_character(child_id)
            children.append(f'{child["name"]} ({child_id})')
        message += f'{', '.join(children)}'
    if character["pregnancy_counter"] > 0:
        message += f'Months left of pregnancy'
    if len(character["status"]) > 0:
        message += f'\nStatus: {', '.join(character["status"])}'
    
    #Attributes - add hunger
    message += f'\n\n**Attributes**'
    message += f'\n:zap: Energy: {character["energy"]}/{character["max_energy"]}'
    message += f'\n:apple: Hunger: {character["hunger"]}/{character["max_hunger"]}'
    message += f'\n:meat_on_bone: Protein: {character["protein"]}/{character["max_protein"]}'
    message += f'\n:heart: Constitution: {character["attr"]["CON"]["value"]}/{character["attr"]["CON"]["max"]} ({character["attr"]["CON"]["xp"]}/{character["attr"]["CON"]["max_xp"]}){"+" * character["attr"]["CON"]["boost"]}'
    message += f'\n:blue_heart: Will: {character["attr"]["WIL"]["value"]}/{character["attr"]["WIL"]["max"]} ({character["attr"]["WIL"]["xp"]}/{character["attr"]["WIL"]["max_xp"]}){"+" * character["attr"]["WIL"]["boost"]}'
    message += f'\n:muscle: Arm Strength: {character["attr"]["ARM"]["value"]}/{character["attr"]["ARM"]["max"]} ({character["attr"]["ARM"]["xp"]}/{character["attr"]["ARM"]["max_xp"]}){"+" * character["attr"]["ARM"]["boost"]}'
    message += f'\n:leg: Leg Strength: {character["attr"]["LEG"]["value"]}/{character["attr"]["LEG"]["max"]} ({character["attr"]["LEG"]["xp"]}/{character["attr"]["LEG"]["max_xp"]}){"+" * character["attr"]["LEG"]["boost"]}'
    message += f'\n:fast_forward: Reflex: {character["attr"]["REF"]["value"]}/{character["attr"]["REF"]["max"]} ({character["attr"]["REF"]["xp"]}/{character["attr"]["REF"]["max_xp"]}){"+" * character["attr"]["REF"]["boost"]}'
    message += f'\n:brain: Intelligence: {character["attr"]["INT"]["value"]}/{character["attr"]["INT"]["max"]} ({character["attr"]["INT"]["xp"]}/{character["attr"]["INT"]["max_xp"]}){"+" * character["attr"]["INT"]["boost"]}'
    message += f'\n:speaking_head: Empathy: {character["attr"]["SOC"]["value"]}/{character["attr"]["SOC"]["max"]} ({character["attr"]["SOC"]["xp"]}/{character["attr"]["SOC"]["max_xp"]}){"+" * character["attr"]["SOC"]["boost"]}'

    #Skills+Languages
    message += f'\n\n**Skills**'
    for skill_name, skill in character["skills"].items():
        message += f'\n{skill_name.title()}: {skill["value"]} ({skill["xp"]}/{skill["max_xp"]}){"+" * skill["boost"]}'

    #Possible future error since language is an object not a list
    message += f'\nLanguages: {', '.join(character["language"])}'

    #Equipment+Inventory NEEDS FIXING
    message += f'\n\n**Equipment: **'
    equipment = []
    for equiped_item in character["equipment"]:
        item = await get_item_type(equiped_item["item"]["item_id"])
        slots_option = equiped_item["option"]
        slots = ', '.join(item["wearable_slots"].get(slots_option))
        equipment.append(f'{item["name"]} ({slots})')
    message += f'{', '.join(equipment)}'

    message += f'\n\n**Inventory**'
    inventory = []
    for item in character["inventory"]:
        item_message = f''
        if item["amount"] > 1:
            item_message += f'{item["amount"]} '
        item_message += f'{item["name"]} '
        inventory.append(f'{item_message}')
    message += f'\n{'\n'.join(inventory)}'

    message += f'\n\n'

    return message

async def years(months):
    return [int(months / 12), months % 12]

async def get_waitlist():
    with open("./data/waitlist.json", "r") as file:
        waitlist = json.load(file)
    
    return waitlist

async def save_waitlist(waitlist):
    with open("./data/waitlist.json", "w") as file:
        json.dump(waitlist, file, indent=4)

async def get_ward(ward_id):
    with open(f"./data/locations/wards/{ward_id}.json", "r") as file:
        ward = json.load(file)
    
    return ward

async def save_ward(ward):
    with open(f"./data/locations/wards/{ward["id"]}.json", "w") as file:
        json.dump(ward, file, indent=4)

async def get_character(char_id):
    for filename in os.listdir("./data/user_data"):
        if filename.endswith(".json"):
            user_id = os.path.splitext(filename)[0]
            user = await get_userinfo(user_id)

            for character in user["characters"]:
                if character["id"] == char_id:
                    return character

    return {}

async def get_user_character(user, char_id):
    for character in user["characters"]:
        if character["id"] == char_id:
            return character

    return {}

async def get_selected_character(user):
    for character in user["characters"]:
        if character["id"] == user["character_selected"]:
            return character

    return {}

async def get_character_with_defaults(character):
    overrides = character
    default_character = await get_default_character()

    full_character = default_character
# Only add non tiered attributes to the species
    for attr, value in default_character.items():
        if attr not in ["life_stages", "attr"]:
            full_character[attr] = value

    # Replace all non tiered attributes with species specific overrides
    for attr, value in overrides.items():
        if attr not in ["life_stages", "attr"]:
            full_character[attr] = value

    # Give the species all of the attr attributes
    for attr, value in overrides["attr"].items():
        for attr_stat, stat_value in value.items():
            full_character["attr"][attr][attr_stat] = stat_value
    
    return full_character

async def get_default_character():
    with open("./default_data/character.json", "r") as file:
        character = json.load(file)
    
    return character

async def get_task_info(task_name, sub_task=""):
    task_list = await get_tasks()

    try:
        task_info = await get_default_task_info()
        
        for key, value in task_list[task_name].items():
            task_info[key] = value

        try:
            if sub_task != "":
                for key, value in task_info[sub_task].items():
                    task_info[key] = value
        except:
            print()

        return task_info
    except:
        return ""
    
async def get_default_task_info():
    with open("./default_data/task_info.json", "r") as file:
        task_info = json.load(file)
    
    return task_info

async def get_default_task_group():
    with open("./default_data/task_group.json", "r") as file:
        task_group = json.load(file)
    
    return task_group

async def get_tasks():
    with open("./data/tasks.json", "r") as file:
        task_info = json.load(file)
    
    return task_info

async def get_material(material_name):
    with open(f"./data/materials/{material_name}.json", "r") as file:
        material = json.load(file)
    
    return material

# Returns whether an item is a tool or an item using the name
async def get_item_type(item_name):
    try:
        with open(f"./data/items/{item_name}.json", "r") as file:
            item_type = json.load(file)
        
        return "item"
    except:
        print()

    try:
        with open(f"./data/tools/{item_name}.json", "r") as file:
            item_type = json.load(file)
    
        return "tool"
    except: 
        print()
        return ""

async def get_item_stack_in_equip(character, item_name):
    for item_stack in character["equipment"]:
        if item_stack["name"] == item_name:
            return item_stack
    
    return {}

# Item state can refer to item state or tool material
async def get_item_stack_in_inv(character, item_name, item_state = ""):
    item_type = await get_item_type(item_name)
    for item_stack in character["inventory"]:
        if item_stack["name"] == item_name:
            if item_state != "":
                if item_type == "item" and item_stack["state"] == item_state:
                    return item_stack
                elif item_type == "tool" and item_stack["material"] == item_state:
                    return item_stack
            else:
                return item_stack
    
    return {}

async def get_item_stack_in_building(building, room_id, item_name, item_state = ""):
    return get_item_stack_in_room(building["rooms"][room_id], item_name, item_state=item_state)

async def get_item_stack_in_room(room, item_name, item_state = ""):
    for item_stack in room["inventory"]:
        if item_stack["name"] == item_name:
            if item_state != "":
                if item_stack["state"] == item_state:
                    return item_stack
            else:
                return item_stack
    
    return {}

async def add_item_in_stash(stash, item_name, num):
    amount = deepcopy(num)

    # Make sure its not a tool
    item_type = await get_item_type(item_name)

    if item_type != "item":
        return

    # Make a new item stack for the items being added
    new_item_stack = await create_item_stack(item_name, amount=amount)

    return await add_item_stack_in_stash(stash, new_item_stack)

async def add_item_stack_in_stash(stash, item_stack):
    item_type = await get_item_type(item_stack["name"])

    # If its an item then check if a stack already exists
    if item_type == "item":
        existing_item_stack = await get_item_stack_in_room(stash, item_stack["name"])
    else:
        existing_item_stack = {}

    # If a stack exists then add to it, otherwise, create a new stack
    if existing_item_stack != {}:
        existing_item_stack["amount"] += item_stack["amount"]
        item_stack = {}

        await update_item_stack_weight_volume(existing_item_stack)
    else:
        stash["inventory"].append(deepcopy(item_stack))
        item_stack = {}
    
    # Update the stashs new volume capacity
    await update_stash_volume_capacity(stash)

    # Return a stack that has anything left in the original stack
    return item_stack

async def remove_item_in_stash(stash, item_name, amount):
    for item_stack in stash["inventory"]:
        if item_name == item_stack["name"]:
            return await remove_item_stack_in_stash(stash, item_stack, amount)

    return 0

# Item stack is assumed to be a linked item_stack from the stash's inventory
async def remove_item_stack_in_stash(stash, item_stack, amount=-1):
    removed_item_stack = deepcopy(item_stack)
    # If amount is -1 then remove the entire stack
    if amount <= -1:
        stash["inventory"].remove(item_stack)
    else:
        # Prevent the amount removed being more than the existing amount
        if amount >= item_stack["amount"]:
            amount = deepcopy(item_stack["amount"])
            item_stack["amount"] = 0
            stash["inventory"].remove(item_stack)
        else:
            item_stack["amount"] -= amount

        removed_item_stack["amount"] = amount

    await update_item_stack_weight_volume(item_stack)
    await update_item_stack_weight_volume(removed_item_stack)

    await update_stash_volume_capacity(stash)

    return removed_item_stack

async def add_item_in_building(building, room_id, item_name, num):
    room = building["rooms"][room_id]

    return await add_item_in_room(room, item_name, num)
    
async def add_item_stack_in_building(building, room_id, item_stack):
    room = building["rooms"][room_id]

    return await add_item_stack_in_room(room, item_stack)

async def remove_item_in_building(building, room_id, item_name, amount):
    room = building["rooms"][room_id]

    return await remove_item_in_room(room, item_name, amount)

async def remove_item_stack_in_building(building, room_id, item_stack, amount=-1):
    room = building["rooms"][room_id]

    return await remove_item_stack_in_room(room, item_stack)

async def add_item_in_room(room, item_name, num):
    amount = deepcopy(num)

    # Make sure its not a tool
    item_type = await get_item_type(item_name)

    if item_type != "item":
        return

    # Make a new item stack for the items being added
    new_item_stack = await create_item_stack(item_name, amount=amount)

    return await add_item_stack_in_room(room, new_item_stack)

async def add_item_stack_in_room(room, item_stack):
    item_type = await get_item_type(item_stack["name"])

    item_info = await get_item(item_stack["name"])

    # If its an item then check if a stack already exists
    if item_type == "item":
        existing_item_stack = await get_item_stack_in_room(room, item_stack["name"])
    else:
        existing_item_stack = {}

    # Check how much weight capacity is left
    remaining_volume_capacity = room["max_capacity"] - room["capacity"]

    # Calculate how many more items can fit within that weight capacity
    max_amount_added = int(remaining_volume_capacity / item_info["volume"])

    # If a stack exists then add to it, otherwise, create a new stack
    if existing_item_stack != {}:
        # If all the items fit then add the requested amount to the existing item stack
        if max_amount_added >= item_stack["amount"]:
            existing_item_stack["amount"] += item_stack["amount"]
            #item_stack["amount"] = 0
            item_stack = {}

            await update_item_stack_weight_volume(existing_item_stack)
        # Otherwise add the projected number of items to the existing item stack and then give the remainder to the left over item stack
        else:
            existing_item_stack["amount"] += max_amount_added
            item_stack["amount"] -= max_amount_added

            await update_item_stack_weight_volume(existing_item_stack)
            await update_item_stack_weight_volume(item_stack)
    else:
        # If all the items fit then add the requested amount to the room's inventory
        if max_amount_added >= item_stack["amount"]:
            room["inventory"].append(deepcopy(item_stack))
            item_stack = {}
        # Otherwise add the projected number of items to the room's inventory and then give the remainder to the left over item stack
        else:
            added_item_stack = deepcopy(item_stack)
            added_item_stack["amount"] = max_amount_added
            item_stack["amount"] -= max_amount_added

            await update_item_stack_weight_volume(added_item_stack)
            await update_item_stack_weight_volume(item_stack)

            room["inventory"].append(added_item_stack)
    
    # Update the rooms new volume capacity
    await update_room_volume_capacity(room)

    # Return a stack that has anything left in the original stack
    return item_stack

async def remove_item_in_room(room, item_name, amount):
    for item_stack in room["inventory"]:
        if item_name == item_stack["name"]:
            return await remove_item_stack_in_room(room, item_stack, amount)

    return 0

# Item stack is assumed to be a linked item_stack from the building's inventory
async def remove_item_stack_in_room(room, item_stack, amount=-1):
    removed_item_stack = deepcopy(item_stack)
    # If amount is -1 then remove the entire stack
    if amount <= -1:
        room["inventory"].remove(item_stack)
    else:
        # Prevent the amount removed being more than the existing amount
        if amount >= item_stack["amount"]:
            amount = deepcopy(item_stack["amount"])
            item_stack["amount"] = 0
            room["inventory"].remove(item_stack)
        else:
            item_stack["amount"] -= amount

        removed_item_stack["amount"] = amount

    await update_item_stack_weight_volume(item_stack)
    await update_item_stack_weight_volume(removed_item_stack)

    await update_room_volume_capacity(room)

    return removed_item_stack

async def add_item_stack_in_inv(character, item_stack):
    item_type = await get_item_type(item_stack["name"])

    item_info = await get_item(item_stack["name"])

    # If its an item then check if a stack already exists
    if item_type == "item":
        existing_item_stack = await get_item_stack_in_inv(character, item_stack["name"])
    else:
        existing_item_stack = {}

    # Check how much weight capacity is left
    remaining_weight_capacity = character["max_capacity"] - character["capacity"]
    #print(f'remaining_weight_capacity: {remaining_weight_capacity}')

    # Calculate how many more items can fit within that weight capacity
    max_amount_added = int(remaining_weight_capacity / item_info["weight"])
    #print(f'max_amount_added: {max_amount_added}')

    # If a stack exists then add to it, otherwise, create a new stack
    if existing_item_stack != {}:
        #print(f'existing_item_stack != ')
        # If all the items fit then add the requested amount to the existing item stack
        if max_amount_added >= item_stack["amount"]:
            existing_item_stack["amount"] += item_stack["amount"]
            #item_stack["amount"] = 0
            item_stack = {}
            #print(f'max_amount_added >= item_stack["amount"]')

            await update_item_stack_weight_volume(existing_item_stack)
        # Otherwise add the projected number of items to the existing item stack and then give the remainder to the left over item stack
        else:
            #print(f'NOT max_amount_added >= item_stack["amount"]')
            existing_item_stack["amount"] += max_amount_added
            item_stack["amount"] -= max_amount_added

            await update_item_stack_weight_volume(existing_item_stack)
            await update_item_stack_weight_volume(item_stack)
    else:
        #print(f'existing_item_stack == ')
        # If all the items fit then add the requested amount to the character's inventory
        if max_amount_added >= item_stack["amount"]:
            character["inventory"].append(deepcopy(item_stack))
            item_stack = {}
            #print(f'max_amount_added >= item_stack["amount"]')
        # Otherwise add the projected number of items to the character's inventory and then give the remainder to the left over item stack
        else:
            added_item_stack = deepcopy(item_stack)
            added_item_stack["amount"] = max_amount_added
            item_stack["amount"] -= max_amount_added

            await update_item_stack_weight_volume(added_item_stack)
            await update_item_stack_weight_volume(item_stack)

            character["inventory"].append(added_item_stack)
            #print(f'NOT max_amount_added >= item_stack["amount"]')
    
    # Update the characters new weight capacity
    await update_character_weight_capacity(character)

    # Return a stack that has anything left in the original stack
    return item_stack

async def add_item_in_inv(character, item_name, num):
    amount = deepcopy(num)

    # Make sure its not a tool
    item_type = await get_item_type(item_name)

    if item_type != "item":
        return
    # Make a new item stack for the items being added
    new_item_stack = await create_item_stack(item_name, amount=amount)

    return await add_item_stack_in_inv(character, new_item_stack)

async def remove_item_in_inv(character, item_name, amount, state=""):
    for item_stack in character["inventory"]:
        if item_name == item_stack["name"]:
            item_type = await get_item_type(item_name)
            if item_type == "item" and item_stack["state"] == state:
                return await remove_item_stack_in_inv(character, item_stack, amount)
            elif item_type == "tool" and item_stack["material"] == state:
                return await remove_item_stack_in_inv(character, item_stack, amount)

    return 0

# Item stack is assumed to be a linked item_stack from the character's inventory
async def remove_item_stack_in_inv(character, item_stack, amount=-1):
    removed_item_stack = deepcopy(item_stack)
    # If amount is -1 then remove the entire stack
    if amount <= -1:
        character["inventory"].remove(item_stack)
    else:
        # Prevent the amount removed being more than the existing amount
        if amount >= item_stack["amount"]:
            amount = deepcopy(item_stack["amount"])
            item_stack["amount"] = 0
            character["inventory"].remove(item_stack)
        else:
            item_stack["amount"] -= amount

        removed_item_stack["amount"] = amount

    await update_item_stack_weight_volume(item_stack)
    await update_item_stack_weight_volume(removed_item_stack)
    await update_character_weight_capacity(character)

    return removed_item_stack

async def convert_quality_name_num(quality_name="", quality_num=0):
    global_info = await get_globalinfo()

    quality_names = list(global_info["tool_quality_levels"].keys())
    quality_values = list(global_info["tool_quality_levels"].values())

    quality_tuples = list(zip(quality_names, quality_values))

    if quality_name == "":
        quality_val = quality_tuples[quality_num][1]
        quality_name = quality_tuples[quality_num][0]
    else:
        quality_val = global_info["tool_quality_levels"][quality_name]
        quality_num = [y[0] for y in quality_tuples].index(quality_name)

    return {
        "name": quality_name,
        "num": quality_num,
        "value": quality_val
    }

async def create_item_stack(item_name, state="", material="", quality=0, amount=1):
    item_stack = await get_default_item_stack()
    global_info = await get_globalinfo()
    item_type = await get_item_type(item_name)

    # If its a tool then remove state, purity, size, mixture
    if item_type == "tool":
        item_stack.pop("state")
        item_stack.pop("purity")
        item_stack.pop("mixture")

        item_info = await get_item(item_name)

        # Calculate durability using material and quality
        quality_multiplier = (await convert_quality_name_num(quality_num=quality))["value"]
        material_multiplier = global_info["material_durability_modifiers"][material]
        item_stack["max_durability"] = item_info["base_durability"] * quality_multiplier * material_multiplier
        item_stack["durability"] = item_stack["max_durability"]
    else:
    # If its an item then remove nick_name, material, quality, purity, size, mixture, sharp, durability, max_durability
        item_stack.pop("nick_name")
        item_stack.pop("material")
        item_stack.pop("quality")
        item_stack.pop("purity")
        item_stack.pop("size")
        item_stack.pop("mixture")
        item_stack.pop("sharp")
        item_stack.pop("durability")
        item_stack.pop("max_durability")

        item_stack["state"] = state
    
    item_stack["amount"] = amount
    item_stack["name"] = item_name

    await update_item_stack_weight_volume(item_stack)

    return item_stack

async def update_item_stack_weight_volume(item_stack):
    item_info = await get_item(item_stack["name"])

    item_stack["total_weight"] = item_info["weight"] * item_stack["amount"]
    item_stack["total_volume"] = item_info["volume"] * item_stack["amount"]

# Assuming all the total weights of the item stacks in their inventory are correct
async def update_character_weight_capacity(character):
    total_capacity = 0

    for item_stack in character["inventory"]:
        total_capacity += item_stack["total_weight"]

    character["capacity"] = total_capacity

# Update the characters max capacity based on their ARM, LEG, CON
async def update_character_max_capacity(character):
    # Use LEG and ARM to calculate the max capacity

    leg = character["attr"]["LEG"]["value"]
    arm = character["attr"]["ARM"]["value"]
    species = await get_species(character["species"])
    base_capacity = species["base_max_weight_capacity"]
    leg_arm_capacity_multiplier = 2.5

    max_capacity = int(base_capacity + leg_arm_capacity_multiplier * (leg + arm))

    # These don't work because you cannot shallow copy a value of a dictionary
    # hp = character["attr"]["CON"]["value"]
    # max_hp = character["attr"]["CON"]["max"]

    # Reduce capacity depending on HP
    CON = character["attr"]["CON"]

    # If HP less than 50% then halve the max_capacity
    if CON["value"] < CON["max"] / 2:
        max_capacity = int(max_capacity / 2)
    # If HP less than 25% then halve the max_capacity again
    if CON["value"] < CON["max"] / 4:
        max_capacity = int(max_capacity / 2)
    
    character["max_capacity"] = max_capacity

    return

# Assuming all the total volumes of the item stacks in the inventory are correct
async def update_room_volume_capacity(room):
    total_capacity = 0

    for item_stack in room["inventory"]:
        total_capacity += item_stack["total_volume"]

    room["capacity"] = total_capacity

# Assuming all the total volumes of the item stacks in the inventory are correct
async def update_stash_volume_capacity(stash):
    total_capacity = 0

    for item_stack in stash["inventory"]:
        total_capacity += item_stack["total_volume"]

    stash["capacity"] = total_capacity

async def get_default_item_stack():
    with open(f"./default_data/item_stack.json", "r") as file:
        item_stack = json.load(file)
    
    return item_stack

async def get_default_item_type():
    with open(f"./default_data/item_type.json", "r") as file:
        item_type = json.load(file)
    
    return item_type

async def get_item(item_name, item_state=""):
    item = await get_item_by_name(item_name)

    #Start with default item type file
    default_item_type = await get_default_item_type()
    full_item = default_item_type

    #Material info → Item info
    material_type = item.get("material_type", "")
    if material_type != "":
        material = await get_material(material_type)

        #Add the material's properties each value
        for key, value in material.items():
            full_item[key] = value

        #Add item's values one by one
        for key, value in item.items():
            full_item[key] = value

    #IF item_state not == "" → State's Material info → State's info
    if item_state != "":
        item_state_info = item.get(item_state, {})
        material_type = item_state_info.get("material_type", "")
        if material_type != "":
            material = await get_material(material_type)
            #Add material's values one by one
            for key, value in material.items():
                full_item[key] = value
        
        #Add state's values one by one
        for key, value in item_state_info.items():
            full_item[key] = value
    
    return full_item

async def get_item_by_name(item_name):
    with open(f"./data/items/{item_name}.json", "r") as file:
        task_info = json.load(file)
    
    return task_info

async def get_item_available_in_ward(ward, item_name):
    item = await get_item(item_name)

    if ward[f'{item["land_required"]}_available'] > 0:
        return True

    return False

# Tools comes from task info that shows the multipliers from each tool
async def get_best_tool(character, task_info):
    tool = {}
    tools = task_info["tools"]

    for tool_name in tools:
        possible_tool = await get_item_stack_in_inv(character, tool_name)

        if possible_tool != {}:
            if tool == {}:
                tool = possible_tool
            else:
                if tools[possible_tool["name"]] > tools[tool["name"]]:
                    tool = possible_tool
    
    if tool == {}:
        if not task_info["requires_harvesting_tool"]:
            tool_modifier = 1
        else:
            tool_modifier = 0
    else:
        tool_modifier == tools[tool["name"]]

    return {"tool": tool, "tool_modifier": tool_modifier}

async def get_building(ward, building_id):
    return ward["buildings"][building_id]

async def get_world_gen():
    with open("./default_data/world_gen.json", "r") as file:
        world_gen = json.load(file)
    return world_gen

async def get_globalinfo():
    with open("./data/global_info.json", "r") as file:
        global_info = json.load(file)
    
    return global_info

async def save_globalinfo(global_info):
    with open("./data/global_info.json", "w") as file:
        json.dump(global_info, file, indent=4)

async def get_serverinfo():
    with open("./data/server_info.json", "r") as file:
        server_info = json.load(file)
    
    return server_info

async def get_default_server():
    with open("./default_data/server_info.json", "r") as file:
        server = json.load(file)
    
    return server

async def save_serverinfo(server_info):
    with open("./data/server_info.json", "w") as file:
        json.dump(server_info, file, indent=4)

async def get_poker_slots():
    with open("./data/pokerslots.json", "r") as file:
        poker_slots = json.load(file)
    
    return poker_slots

async def get_developerlist():
    with open("./data/developers.txt", "r") as file:
        developerlist = [line.rstrip() for line in file]
    
    return developerlist

async def send_message(client, server_id, message, silent: bool = False):
    try:
        server_info = await get_serverinfo()
        await send_channel_message(client, int(server_info[str(server_id)]["reminder_channel_id"]), message, silent)
    except:
        #print(f'Server {server_id} not found. Message: {message}')
        await send_console_message(client, f'Server {server_id} not found. Message: {message}', silent)
        return

async def send_channel_message(client, channel_id: int, message, silent: bool = False):
    try:
        channel = await client.fetch_channel(channel_id)

        if len(message) <= 2000:
            await channel.send(message, silent = silent)
        else:
            new_message = deepcopy(message)
            message_fragments = new_message.split("\n")
            message_to_send = ""
            for x in range(len(message_fragments)):
                if len(message_to_send) + len(message_fragments[x-1]) < 2000:
                    message_to_send += "\n" + message_fragments[x-1]
                else:
                    await channel.send(message_to_send, silent = silent)
                    message_to_send = message_fragments[x-1]
            
            if len(message_to_send) > 0:
                if len(message_to_send) < 2000:
                    await channel.send(message_to_send, silent = silent)
                else:
                    await channel.send('Last message fragment too long to send. Ask developer to include more linebreaks in output.', silent = silent)
    except:
        #print(f'Channel {channel_id} not found. Message: {message}')
        await send_console_message(client, f'Channel {channel_id} not found. Message: {message}', silent)
        return

async def send_console_message(client, message, silent: bool = False):
    try:
        global_info = await get_globalinfo()
    except:
        print(f'Console channel not set in global_info.json')

    await send_channel_message(client, global_info["console_channel_id"], message)

async def dm(client, user_id, message):
    try:
        user = await client.fetch_user(int(user_id))
        #user = await client.fetch_user(107886996365508608)
        if len(message) <= 2000:
            await user.send(message)
        else:
            new_message = deepcopy(message)
            message_fragments = new_message.split("\n")
            message_to_send = ""
            for x in range(len(message_fragments)):
                if len(message_to_send) + len(message_fragments[x-1]) < 2000:
                    message_to_send += "\n" + message_fragments[x-1]
                else:
                    await user.send(message_to_send)
                    message_to_send = message_fragments[x-1]
            
            if len(message_to_send) > 0:
                if len(message_to_send) < 2000:
                    await user.send(message_to_send)
                else:
                    await user.send('Last message fragment too long to send. Ask developer to include more linebreaks in output.')
    except:
        print(f'{user_id} not found. Message: {message}')
        return

async def reply(client, interaction, message, silent: bool = False, ephemeral: bool = False):
    try: 
        if len(message) <= 2000:
            await interaction.response.send_message(message, silent = silent)
        else:
            new_message = deepcopy(message)
            message_fragments = new_message.split("\n")
            message_to_send = ""
            first_reply_sent = False
            channel = await client.fetch_channel(interaction.channel_id)
            for x in range(len(message_fragments)):
                if len(message_to_send) + len(message_fragments[x]) < 2000:
                    message_to_send += "\n" + message_fragments[x]
                else:
                    if not first_reply_sent:
                        await interaction.response.send_message(message_to_send, silent = silent, ephemeral = ephemeral)
                        first_reply_sent = True
                    else:
                        await channel.send(message_to_send, silent = silent)
                    message_to_send = message_fragments[x]
            
            if len(message_to_send) > 0:
                if len(message_to_send) < 2000:
                    if not first_reply_sent:
                        await interaction.response.send_message(message_to_send, silent = silent, ephemeral = ephemeral)
                    else:
                        await channel.send(message_to_send, silent = silent)
                else:
                    await reply(interaction, 'Last message fragment too long to send. Ask developer to include more linebreaks in output.')
    except:
        print(f'Unable to send message: {message}')

async def get_waffle_rank(waffles):
    global_info = await get_globalinfo()

    waffle_rank = ""

    for rank, requirement in global_info["waffle_rank"].items():
        if int(waffles) >= int(requirement):
            waffle_rank = rank

    return waffle_rank

async def get_next_waffle_rank(waffle_rank):
    global_info = await get_globalinfo()

    next_waffle_rank = ""

    try:
        current_waffles = int(global_info["waffle_rank"][waffle_rank])
    except:
        current_waffles = 0

    for rank, requirement in global_info["waffle_rank"].items():
        # Check greater than current quack rank requirement but lower/eq to target quack rank
        if requirement > current_waffles and (next_waffle_rank == "" or requirement < int(global_info["waffle_rank"][next_waffle_rank])):
            next_waffle_rank = rank

    return next_waffle_rank

async def get_season(day):
    global_info = await get_globalinfo()

    dayx = deepcopy(day)

    while True:
        for season_name, length in global_info["seasons"].items():
            if dayx <= length:
                return season_name
            else:
                dayx -= length

async def get_skill_mod(character, skills):
    skill_lvls = []
    for skill_name in skills:
        #skill_lvls.append(character["skills"][skill_name].get("value", 0))
        skill_lvls.append(character["skills"].get(skill_name, {}).get("value", 0))
        # skill = character["skills"].get(skill_name, "")

        # if skill != "":
        #     skill_lvls.append(skill["value"])
        # else:
        #     skill_lvls.append(0)
    return 1 / (min(skill_lvls)/2 + 1)
    
async def get_atr_mod(character, attributes):
    ATR_lvls = []
    for ATR_name in attributes:
        ATR_lvls.append(character["attr"][ATR_name]["value"])
    return 1 / (min(ATR_lvls)/4 + 1)

async def add_skill_xp(character, skill_name, amount: int = 1):
    skill = character["skills"].get(skill_name, "")

    # If the character doesn't have that skill yet then give it to them
    if skill == "":
        skill = await get_default_skill()
        character["skills"][skill_name] = skill

    # Add to the xp
    skill["xp"] = amount

    # Level up the skill if necessary
    while skill["xp"] >= skill["max_xp"]:
        skill["max"] += 1
        skill["value"] = deepcopy(skill["max"])
        skill["xp"] -= skill["max_xp"]
        skill["max_xp"] += max((10 - skill["boost"]), 1)

    return

async def add_atr_xp(character, atr_name, amount: int = 1):
    atr = character["attr"][atr_name]

    # Add to the xp and check if they have leveled up
    atr["xp"] += amount
    print(f'atr["xp"]: {atr["xp"]}')

    # Level up the atr if necessary
    while atr["xp"] >= atr["max_xp"]:
        atr["max"] += 1
        atr["value"] = deepcopy(atr["max"])
        atr["xp"] -= atr["max_xp"]
        atr["max_xp"] += max((40 - atr["boost"]), 1)
    print(f'atr["max_xp"]: {atr["max_xp"]}')

    return

async def get_default_skill():
    with open(f"./default_data/skill.json", "r") as file:
        skill = json.load(file)
    
    return skill

#Return one of the keys at random depending on the value/weight
async def get_random_dict_item(weighted_dict, amount: int = 1):
    total_weight = sum(weighted_dict.values())
    result = {}

    for x in range(amount):
        random_weight = rand.uniform(0, total_weight)

        # Convert the random weight to a key
        for key, value in weighted_dict.items():
            if random_weight <= value:
                result[key] = result.get(key, 0) + 1
                break
            else:
                random_weight -= value
    
    if amount == 1:
        return list(result.keys())[0]

    return result

#Modes: morning_reminder, evening_reminder
async def send_daily_reminder(client, mode, message):
    for filename in os.listdir("./data/user_data"):
        if filename.endswith(".json"):
            user_id = os.path.splitext(filename)[0]
            user = await get_userinfo(user_id)

            if bool(user[mode]) and not bool(user["waffled_today"]):
                await dm(client, user_id, message)

async def add_to_queue(user_id, char_id, action, item, ward_id, amount = 1, time = 1, dump_id = [], friend_char_id = -1, target_id =  -1, subtask = "", state = ""):
    #If doing a task with someone else then look for that person in the taskqueue
    if friend_char_id >= 0:
        ward = await get_ward(ward_id)

        for task_group in ward["task_queue"]:
            if task_group["task"] == action and task_group["item"] == item and task_group["time"] == time and len(task_group["members"]) < task_group["member_limit"]:
                for member in task_group["members"]:
                    if member["char_id"] == friend_char_id:
                        #Add member to task queue
                        task_group["members"].append({
                            "user_id": user_id,
                            "char_id": char_id,
                            "amount": amount
                        })
                        #Save ward
                        await save_ward(ward)
                        return
            
    #If doing a task alone, then create a new task group
    else:
        default_task_group = await get_default_task_group()
        task_group = default_task_group

        member = {
            "user_id": user_id,
            "char_id": char_id,
            "amount": amount
        }
        task_group["members"].append(member)
        
        task_group["task"] = action
        task_group["item"] = item
        task_group["time"] = time
        task_group["dump_id"] = dump_id

        if target_id > -1:
            task_group["target_id"] = target_id

        if state != "":
            task_group["state"] = state

        #task_info = await get_task_info(action, item)
        task_info = await get_task_info(action, subtask)

        task_group["member_limit"] = task_info["member_limit"]
        
        #Add to the task queue
        ward = await get_ward(ward_id)
        ward["task_queue"].append(task_group)

        #Save changes
        await save_ward(ward)

    return
