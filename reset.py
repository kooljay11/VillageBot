import json
from utilities import *
import os

async def reset(client):
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


    newday_message = f'A new day has arrived. The current season is: {global_info["current_season"]}'
    
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