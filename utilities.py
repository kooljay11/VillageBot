import json
from copy import deepcopy
import os

async def get_userinfo(self_user, target):
    if str(target).isnumeric():
        target_user_id = target
    else:
        target_user_id = self_user["nicknames"].get(target, 0)
    
    user = await get_userinfo(target_user_id)
    
    return user

async def get_userinfo(user_id):
    with open(f"./data/user_data/{user_id}.json", "r") as file:
        user = json.load(file)
    
    return user

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
    message = f'{character["name"]} [{character["id"]}] - {character["gender"]} {character["species"]} :zap: {character["energy"]}/{character["max_energy"]} :apple: {character["hunger"]}/{character["max_hunger"]} :heart: {character["attr"]["CON"]["value"]}/{character["attr"]["CON"]["max"]} :blue_heart: {character["attr"]["WIL"]["value"]}/{character["attr"]["WIL"]["max"]} :muscle: {character["attr"]["ARM"]["value"]}/{character["attr"]["ARM"]["max"]} :leg: {character["attr"]["LEG"]["value"]}/{character["attr"]["LEG"]["max"]} :fast_forward: {character["attr"]["REF"]["value"]}/{character["attr"]["REF"]["max"]} :brain: {character["attr"]["INT"]["value"]}/{character["attr"]["INT"]["max"]} :speaking_head: {character["attr"]["SOC"]["value"]}/{character["attr"]["SOC"]["max"]}'

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
        message += f'\n\tStatus: {', '.join(character["status"])}'
    
    #Attributes - add hunger
    message += f'\n\n**Attributes**'
    message += f'\n:zap: Energy: {character["energy"]}/{character["max_energy"]}'
    message += f'\n:apple: Hunger: {character["hunger"]}/{character["max_hunger"]}'
    message += f'\n:heart: Constitution: {character["attr"]["CON"]["value"]}/{character["attr"]["CON"]["max"]} ({character["attr"]["CON"]["xp"]}/{character["attr"]["CON"]["max_xp"]}){"+" * character["attr"]["CON"]["boost"]}'
    message += f'\n:blue_heart: Will: {character["attr"]["WIL"]["value"]}/{character["attr"]["WIL"]["max"]} ({character["attr"]["WIL"]["xp"]}/{character["attr"]["WIL"]["max_xp"]}){"+" * character["attr"]["WIL"]["boost"]}'
    message += f'\n:muscle: Arm Strength: {character["attr"]["ARM"]["value"]}/{character["attr"]["ARM"]["max"]} ({character["attr"]["ARM"]["xp"]}/{character["attr"]["ARM"]["max_xp"]}){"+" * character["attr"]["ARM"]["boost"]}'
    message += f'\n:leg: Leg Strength: {character["attr"]["LEG"]["value"]}/{character["attr"]["LEG"]["max"]} ({character["attr"]["LEG"]["xp"]}/{character["attr"]["LEG"]["max_xp"]}){"+" * character["attr"]["LEG"]["boost"]}'
    message += f'\n:fast_forward: Reflex: {character["attr"]["REF"]["value"]}/{character["attr"]["REF"]["max"]} ({character["attr"]["REF"]["xp"]}/{character["attr"]["REF"]["max_xp"]}){"+" * character["attr"]["REF"]["boost"]}'
    message += f'\n:brain: Intelligence: {character["attr"]["INT"]["value"]}/{character["attr"]["INT"]["max"]} ({character["attr"]["INT"]["xp"]}/{character["attr"]["INT"]["max_xp"]}){"+" * character["attr"]["INT"]["boost"]}'
    message += f'\n:speaking_head: Empathy: {character["attr"]["SOC"]["value"]}/{character["attr"]["SOC"]["max"]} ({character["attr"]["SOC"]["xp"]}/{character["attr"]["SOC"]["max_xp"]}){"+" * character["attr"]["SOC"]["boost"]}'

    #Skills+Languages
    message += f'\n\n**Skills**'
    for skill in character["skills"]:
        message += f'\n{skill}'

    #Possible future error since language is an object not a list
    message += f'Languages: {', '.join(character["language"])}'

    #Equipment+Inventory
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
            item_message += f'({item["amount"]}) '
        item_message += f'({item["name"]}) '
        inventory.append(f'{item_message}')
    message += f'\n{'\n'.join(inventory)}'

    message += f'\n\n'

    return message

async def years(months):
    return [int(months / 12), months % 12]

async def get_item_type(item_id):
    with open(f"./data/items/{item_id}.json", "r") as file:
        item_type = json.load(file)
    
    return item_type

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

async def save_ward(ward_id, ward):
    with open(f"./data/locations/wards/{ward_id}.json", "w") as file:
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

async def save_userinfo(user_id, user):
    with open(f"./data/user_data/{user_id}.json", "w") as file:
        json.dump(user, file, indent=4)

async def get_default_userinfo():
    with open("./default_data/user.json", "r") as file:
        user = json.load(file)
    
    return user

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

async def reply(client, interaction, message):
    try: 
        if len(message) <= 2000:
            await interaction.response.send_message(message)
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
                        await interaction.response.send_message(message_to_send)
                        first_reply_sent = True
                    else:
                        await channel.send(message_to_send)
                    message_to_send = message_fragments[x]
            
            if len(message_to_send) > 0:
                if len(message_to_send) < 2000:
                    if not first_reply_sent:
                        await interaction.response.send_message(message_to_send)
                    else:
                        await channel.send(message_to_send)
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

#Modes: morning_reminder, evening_reminder
async def send_daily_reminder(client, mode, message):
    for filename in os.listdir("./data/user_data"):
        if filename.endswith(".json"):
            user_id = os.path.splitext(filename)[0]
            user = await get_userinfo(user_id)

            if bool(user[mode]) and not bool(user["waffled_today"]):
                await dm(client, user_id, message)
