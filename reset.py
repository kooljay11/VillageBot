import json
from utilities import *
import os
import random
import discord
import math

async def reset(client):
    with open("./data/bot_status.txt", "r") as file:
        randomresponses = file.readlines()
        response = random.choice(randomresponses)
    await client.change_presence(activity=discord.CustomActivity(name=response, emoji='🦆'))

    global_info = await get_globalinfo()
    world_gen = await get_world_gen()
    print(f'global_info["t_exchange_rate"]: {global_info["t_exchange_rate"]}')

    for filename in os.listdir("./data/user_data"):
        if filename.endswith(".json"):
            user_id = os.path.splitext(filename)[0]
            user = await get_userinfo(user_id)

            # Reset streak counter if the streak is broken
            if not user["waffled_today"]:
                user["waffle_streak"] = 0
            else:
                user["poker_spins"] += 1

            user["waffled_today"] = False
            

            target_rank = await get_waffle_rank(user["waffles"])

            if target_rank != user["waffle_rank"]:
                user["waffle_rank"] = target_rank
            
            await save_userinfo(user_id, user)

    
    # Randomize the w-t exchange rate
    global_info["t_exchange_rate"] = random.randint(int(global_info["t_exchange_rate_range"][0]), int(global_info["t_exchange_rate_range"][1]))
    print(f'global_info["t_exchange_rate"]: {global_info["t_exchange_rate"]}')


    # Run all queued commands in each ward
    for filename in os.listdir("./data/locations/wards"):
        if filename.endswith(".json"):
            ward_id = os.path.splitext(filename)[0]
            ward = await get_ward(ward_id)
            public_stash = ward["stashes"][0]

            # Update the max_capacity of all alive players depending on their ARM and LEG attributes
            for char_user_id in ward["character_ids_user_ids"]:
                # Make sure this player exists
                try:
                    user = await get_userinfo(char_user_id["user_id"])
                except:
                    print(f'user {char_user_id["user_id"]} does not exist.')
                    continue

                # Make sure the character exists and is alive
                try:
                    character = await get_user_character(user, char_user_id["char_id"])
                except:
                    print(f'character {char_user_id["char_id"]} does not exist.')
                    continue

                #print(f'character["status"]: {character["status"]}')

                if "alive" not in character["status"]:
                    print(f'character {char_user_id["char_id"]} is not alive.')
                    continue
                #print(f'character["status"]: {character["status"]}')

                await update_character_max_capacity(character)

                await save_userinfo(char_user_id["user_id"], user)

            index = 0
            while index < len(ward["task_queue"]):
                task_group = ward["task_queue"][index]
                if task_group["task"] == "gather":
                    #print(f'task_group["task"]: {task_group["task"]}')
                    message = f''
                    item_info = await get_item(task_group["item"])

                    for member in task_group["members"]:
                        # Make sure this player exists
                        try:
                            user = await get_userinfo(member["user_id"])
                        except:
                            print(f'user {member["user_id"]} does not exist.')
                            continue

                        # Make sure the character exists and is alive
                        try:
                            character = await get_user_character(user, member["char_id"])
                        except:
                            print(f'character {member["char_id"]} does not exist.')
                            continue

                        if "alive" not in character["status"]:
                            print(f'character {member["char_id"]} is not alive.')
                            continue

                        task_info = await get_task_info("gather", task_group["item"])
                        if task_info == "":
                            task_info = await get_task_info("gather", item_info["material_type"])

                            if task_info == "":
                                print(f'Task info for this item was not found in the task list.')
                                continue
                        
                        # Get the skill modifier
                        skill_modifier = await get_skill_mod(character, task_info["skill"])

                        # Get the ATR modifier
                        ATR_modifier = await get_atr_mod(character, task_info["ATR"])
                        #print(f'ATR_modifier: {ATR_modifier}')

                        # Get the tool modifier
                        tool_and_modifier = await get_best_tool(character, task_info)
                        tool_modifier = tool_and_modifier["tool_modifier"]
                        tool = tool_and_modifier["tool"]

                        #print(f'tool_modifier: {tool_modifier}')

                        amount = math.floor(item_info["base_collection_amount"] * (1 + skill_modifier + ATR_modifier + tool_modifier) * item_info["seasonal_multiplier"][ward["season"]] * item_info["biome_multiplier"][ward["biome"]] * item_info["subbiome_multiplier"][ward["subbiome"]])

                        #print(f'amount: {amount}')

                        # Add random yield modifier +- 30% and then round to closest integer
                        amount = math.floor(amount * random.uniform(global_info["random_yield_multiplier"][0], global_info["random_yield_multiplier"][1]) + 0.5)

                        #print(f'randomized amount: {amount}')

                        # Add partner bonus per 2 people in the group
                        amount += math.floor(amount * task_info["partner_bonus_%"]) * math.floor(len(task_group["members"]) / 2)

                        #print(f'partnered amount: {amount}')

                        # Ensure the amount is not lower than 0
                        amount = max(amount, 0)

                        # Reduce durability of tool
                        if tool != {}:
                            if tool["durability"] > amount:
                                tool["durability"] -= amount
                            else:
                                # Limit the amount to the remaining durability of the tool
                                amount = deepcopy(tool["durability"])
                                tool["durability"] = 0

                                # Break the tool
                                await remove_item_stack_in_inv(tool)
                            
                        overflow_item_stack = {}
                        #print(f'overflow_item_stack: {overflow_item_stack}')

                        # Then add to either the selected dump location or directly to the characters inventory
                        # Prevent the character from overfilling the dump location (overflow goes to character inv) or char inventory (overflow goes to public ward stash)
                        if len(task_group["dump_id"]) == 2:
                            building = await get_building(ward, task_group["dump_id"][0])
                            overflow_item_stack = await add_item_in_building(building, task_group["dump_id"][0], task_group["item"], amount)
                        elif len(task_group["dump_id"]) == 1:
                            stash = ward["stashes"][task_group["dump_id"]]
                            overflow_item_stack = await add_item_in_stash(stash, task_group["item"], amount)
                        #print(f'Checked building/stash')

                        # Add overflow to the character's inventory or add the items directly to the player if no building was specified
                        if overflow_item_stack != {}:
                            overflow_item_stack = await add_item_stack_in_inv(character, overflow_item_stack)
                        elif task_group["dump_id"] == []:
                            overflow_item_stack = await add_item_in_inv(character, task_group["item"], amount)
                        #print(f'Checked character')
                        #print(f'overflow_item_stack: {overflow_item_stack}')
                        
                        if overflow_item_stack != {}:
                            # Add overflow to public ward stash
                            await add_item_stack_in_stash(public_stash, overflow_item_stack)
                        #print(f'Checked public stash')

                        # Give the character skill/atr XP for their action
                        for skill_name in task_info["skill"]:
                            await add_skill_xp(character, skill_name)

                        #print(f'task_info["skill"]: {task_info["skill"]}')
                        
                        for atr_name in task_info["ATR"]:
                            await add_atr_xp(character, atr_name)
                        #print(f'task_info["ATR"]: {task_info["ATR"]}')
                        #print(f'item_info["land_required"]: {item_info["land_required"]}')

                        # If forest or rock land was used then turn a corresponding amount of it into plains if the biome is not 
                        if item_info["land_required"] in ["forest_land", "rocky_land"]:
                            land_converted = math.floor(world_gen["item_amount_to_land_used_ratio"] * amount)
                            #print(f'land_converted: {land_converted}')

                            # Ensure that the amount of land converted cant make the target available land less than 0

                            if ward[f'{item_info["land_required"]}_available'] > land_converted:
                                ward[f'{item_info["land_required"]}_available'] -= land_converted
                                ward[f'{item_info["land_required"]}'] -= land_converted

                                ward["grass_land_available"] += land_converted
                                ward["grass_land"] += land_converted
                        # Otherwise if grass land was used then convert it into rocky land
                        elif item_info["land_required"] == "grass_land":
                            land_converted = math.floor(world_gen["item_amount_to_land_used_ratio"] * amount)
                        
                        # Save user info
                        await save_userinfo(member["user_id"], user)

                        # Build up a result message
                        message += f'{character["name"]} gathered {amount} {task_group["item"]}s in the {item_info["land_required"].replace("_", " ")}. '

                    # Send result message to each user
                    for member in task_group["members"]:
                        # Make sure this player exists
                        try:
                            user = await get_userinfo(member["user_id"])
                        except:
                            print(f'user {member["user_id"]} does not exist.')
                            continue

                        await dm(client, member["user_id"], message)
                    
                    # Remove this task group
                    ward["task_queue"].pop(index)
                else:
                    index += 1

            # Refill energy of all alive characters depending on their hunger, bed available, protein, pregnancy, HP lvl
            for char_user_id in ward["character_ids_user_ids"]:
                # Make sure this player exists
                try:
                    user = await get_userinfo(char_user_id["user_id"])
                except:
                    print(f'user {char_user_id["user_id"]} does not exist.')
                    continue

                # Make sure the character exists and is alive
                try:
                    character = await get_user_character(user, char_user_id["char_id"])
                except:
                    print(f'character {char_user_id["char_id"]} does not exist.')
                    continue

                #print(f'character["status"]: {character["status"]}')

                if "alive" not in character["status"]:
                    print(f'character {char_user_id["char_id"]} is not alive.')
                    continue

                # Make them one month older
                character["age_months"] += 1

                # These don't work because you cannot shallow copy a value of a dictionary
                #hp = character["attr"]["CON"]["value"]
                #max_hp = character["attr"]["CON"]["max"]

                CON = character["attr"]["CON"]

                # If hunger available then check the following conditions
                hunger_consumed = 0
                # HP > 25%: 2 hunger → 2 energy
                if CON["value"] > CON["max"] / 4:
                    hunger_consumed += 2
                # HP > 50%: 1 hunger → 1 energy
                if CON["value"] > CON["max"] / 2:
                    hunger_consumed += 1
                
                # Bed set: 1 hunger → 1 energy NEED TO DO THIS LATER

                # Make sure you can't consume more hunger than they have
                hunger_consumed = min(hunger_consumed, character["hunger"])

                # Make sure you don't consume more hunger than how much energy you need to refill
                hunger_consumed = min(hunger_consumed, character["max_energy"] - character["energy"])

                character["energy"] += hunger_consumed
                #print(f'hunger_consumed: {hunger_consumed}')

                # If no hunger was used then -1 hunger
                # This makes it possible for characters to get negative hunger, which will be returned to 0 a few lines below in the code
                hunger_consumed = max(hunger_consumed, 1)
                #print(f'hunger_consumed inactive: {hunger_consumed}')

                character["hunger"] -= hunger_consumed
                #print(f'character["hunger"]: {character["hunger"]}')

                # If hunger is still negative then refill it using HP: 1 protein → 2 hunger, 1 HP → 1 hunger
                while character["hunger"] < 0:
                    if character["protein"] > 0:
                        character["protein"] -= 1
                        character["hunger"] += 2
                    else:
                        character["hunger"] += 1
                        CON["value"] -= 1
                #print(f'character["hunger"]: {character["hunger"]}')
                #print(f'hp: {hp}')
                #print(f'character["attr"]["CON"]["value"]: {character["attr"]["CON"]["value"]}')

                # Pregnancy: -2 energy NEED TO DO THIS LATER

                # If protein is available then check the following conditions
                protein_consumed = 2

                # If energy < max: 2 protein → 2 energy
                protein_consumed = min(protein_consumed, character["max_energy"] - character["energy"])

                # Make sure they can't consume more protein than they have
                protein_consumed = min(protein_consumed, character["protein"])

                # Make sure protein consumed can't be less than 0
                protein_consumed = max(protein_consumed, 0)

                character["protein"] -= protein_consumed
                character["energy"] += protein_consumed

                # If energy is still 0 or negative: 1 HP → 1 energy until energy == 1
                while character["energy"] < 0:
                    character["energy"] += 1
                    CON["value"] -= 1

                # If HP is less than max, then: 1 protein → 2 HP, 1 hunger → 1 HP
                if CON["value"] < CON["max"] and character["protein"] > 0:
                    CON["value"] += 2
                    character["protein"] -= 1

                if CON["value"] < CON["max"] and character["hunger"] > 0:
                    CON["value"] += 1
                    character["hunger"] -= 1
                    #print(f'hp += 1: {hp}')
                    #print(f'character["hunger"] -= 1: {character["hunger"]}')
                
                #print(f'hp: {hp}')
                #print(f'character["attr"]["CON"]["value"]: {character["attr"]["CON"]["value"]}')

                # If HP is still 0 or less then they are dead
                if CON["value"] <= 0:
                    character["status"].remove("alive")
                    character["status"].append("dead")
                
                await save_userinfo(char_user_id["user_id"], user)

            await save_ward(ward)

    # Set the season for each ward according to biome info

    # Add to the day counter and cycle the season accordingly
    global_info["day_counter"] += 1
    global_info["current_season"] = await get_season(global_info["day_counter"])
    #print(f'global_info["day_counter"]: {global_info["day_counter"]}')

    await save_globalinfo(global_info)

    newday_message = f'A new day has arrived. It is now day {global_info["day_counter"]}. The current season is: {global_info["current_season"]}'
    
    # Tell all users with morning reminder on about the update
    await send_daily_reminder(client, "morning_reminder", newday_message)
    
    # Tell all specified channels about the update
    with open("./data/server_info.json", "r") as file:
        server_info = json.load(file)
    
    for server_id, server in server_info.items():
        for channel_id in server["daily_channels"]:
            try:
                await client.get_channel(channel_id).send(newday_message)
            except:
                #print(f'Error trying to execute the new day to channel {channel_id}.')
                print()