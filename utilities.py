import json
from copy import deepcopy

async def get_userinfo(self_user, target):
    if str(target).isnumeric():
        target_user_id = target
    else:
        target_user_id = self_user["nicknames"].get(target, 0)
    
    user = await get_userinfo(target)
    
    return user

async def get_userinfo(user_id):
    with open(f"./data/user_data/{user_id}.json", "r") as file:
        user = json.load(file)
    
    return user

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
                if len(message_to_send) + len(message_fragments[x-1]) < 2000:
                    message_to_send += "\n" + message_fragments[x-1]
                else:
                    if not first_reply_sent:
                        await interaction.response.send_message(message_to_send)
                        first_reply_sent = True
                    else:
                        await channel.send(message_to_send)
                    message_to_send = message_fragments[x-1]
            
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