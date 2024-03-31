import json
from utilities import *
import os
import random
import discord

async def reset(client):
    with open("./data/bot_status.txt", "r") as file:
        randomresponses = file.readlines()
        response = random.choice(randomresponses)
    await client.change_presence(activity=discord.CustomActivity(name=response, emoji='🦆'))

    global_info = await get_globalinfo()

    for filename in os.listdir("./data/user_data"):
        if filename.endswith(".json"):
            user_id = os.path.splitext(filename)[0]
            user = await get_userinfo(user_id)

            # Reset streak counter if the streak is broken
            if not bool(user["waffled_today"]):
                user["waffle_streak"] = 0
            else:
                user["spins"] += 1

            user["waffled_today"] = False
            

            target_rank = await get_waffle_rank(user["waffles"])

            if target_rank != user["waffle_rank"]:
                user["waffle_rank"] = target_rank
            
            await save_userinfo(user_id, user)

    
    # Randomize the w-t exchange rate
    global_info["t_exchange_rate"] = random.randint(int(global_info["t_exchange_rate_range"][0]), int(global_info["t_exchange_rate_range"][1]))

    # Add to the day counter and cycle the season accordingly
    global_info["day_counter"] += 1
    global_info["current_season"] = await get_season(global_info["day_counter"])

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