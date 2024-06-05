import discord
from discord import app_commands
from discord.ext import commands, tasks
from utilities import *

class Waitlist(commands.Cog):
    def __init__(self, client):
        self.client = client
    
    @commands.Cog.listener()
    async def on_ready(self):
        await self.client.tree.sync()
        print(f'{__name__} loaded successfully!')
    
    async def char_mode_autocomplete(self, interaction: discord.Interaction, current: str,) -> list[app_commands.Choice[str]]:
        choices = ['view', 'join', 'edit', 'leave']
        return [
            app_commands.Choice(name=choice, value=choice)
            for choice in choices if current.lower() in choice.lower()
        ]

    @app_commands.command(name="waitlist", description="View/join/edit/leave the waitlist")
    @app_commands.autocomplete(mode=char_mode_autocomplete)
    async def waitlist(self, interaction: discord.Interaction, mode: str = "view", character_id: int = -1, migrant: bool = False, ward_id: int = -1):
        user_id = interaction.user.id

        # Make sure this player exists
        try:
            user = await get_userinfo(user_id)
        except:
            await reply(self.client, interaction, "That user has not waffled yet.")
            return
        
        #Get character
        try:
            if character_id < 0:
                #Get the user's selected character
                character = await get_selected_character(user)
            else:
                character = await get_user_character(user, character_id)
        except:
            await reply(self.client, interaction, "Character not found or does not belong to you.")
            return
        
        #If ward is specified, make sure it exists
        if ward_id >= 0:
            try:
                await get_ward(ward_id)
            except:
                await reply(self.client, interaction, "Specified ward does not exist.")
                return
        
        #Get the waitlist
        waitlist = await get_waitlist()

        message = f'Mode incorrectly specified.'

        if mode == "view":
            message = f'**Waitlist**'
            for attr, value in waitlist.items():
                char_list = []

                for entry in value:
                    char = await get_character(entry["id"])
                    msg = f'{char["name"]} [{entry["id"]}]'
                    if entry["migrant"]:
                        msg += f' (possible migrant)'
                    char_list.append(msg)

                message += f'\n{attr}: {", ".join(char_list)}'
            
        elif mode == "join":
            #Make sure this character isn't on the waitlist already
            for attr, value in waitlist.items():
                for entry in value:
                    if character["id"] == entry["id"]:
                        await reply(self.client, interaction, "This character is already on the waitlist.")
                        return
            
            #Make sure this character isn't already alive or dead
            if "alive" in character["status"]:
                await reply(self.client, interaction, "This character is already alive.")
                return
            elif "dead" in character["status"]:
                await reply(self.client, interaction, "This character is already dead.")
                return

            #Make sure the user hasn't reached their maximum waitlist character count yet
            num_waitlist = 0
            global_info = await get_globalinfo()

            for char in user["characters"]:
                if "waitlist" in char["status"]:
                    num_waitlist += 1
            
            if num_waitlist > global_info["max_waitlist_characters"]:
                await reply(self.client, interaction, "You have already reached your maximum waitlisted characters.")
                return
            
            waitlist_entry = {
                "id": character["id"],
                "migrant": migrant
            }

            #Add character to the waitlist depending on their specified ward
            if ward_id < 0:
                waitlist["global"].append(waitlist_entry)
            else:
                if waitlist.get(str(ward_id), []) == []:
                    waitlist[str(ward_id)] = [waitlist_entry]
                else:
                    waitlist[str(ward_id)].append(waitlist_entry)

            #Save waitlist
            await save_waitlist(waitlist)
            
            #Add waitlist status to character
            character["status"].append("waitlist")

            await save_userinfo(user_id, user)

            message = f'{character["name"]} [{character["id"]}] was added to the waitlist.'
        elif mode == "edit":
            #Make sure character is already on the waitlist
            if "waitlist" not in character["status"]:
                await reply(self.client, interaction, "This character is not on the waitlist yet. Use waitlist mode:join to add them.")
                return

            #Add character to the specific ward if not already or remove them from the specific ward if already present and matching migrant bool
            if ward_id >= 0:
                waitlist_entry = ""

                for entry in waitlist.get(str(ward_id), []):
                    if entry["id"] == character["id"]:
                        waitlist_entry = entry
                        break
                
                if waitlist_entry == "":
                    waitlist_entry = {
                        "id": character["id"],
                        "migrant": migrant
                    }

                    if waitlist.get(str(ward_id), []) == []:
                        waitlist[str(ward_id)] = [waitlist_entry]
                    else:
                        waitlist[str(ward_id)].append(waitlist_entry)

                    message = f'{character["name"]} [{character["id"]}] was added to the waitlist for ward_id {ward_id}.'

                    waitlist_entry = ""
                    
                    #Remove waitlist entry from global
                    for entry in waitlist["global"]:
                        if entry["id"] == character["id"]:
                            waitlist_entry = entry
                            break
                    
                    if waitlist_entry != "":
                        waitlist["global"].remove(waitlist_entry)
                        message += f' They were also taken off the global waitlist.'
                elif waitlist_entry["migrant"] != migrant:
                    waitlist_entry["migrant"] = migrant
                    message = f' Migrant was set to {migrant} for {character["name"]} [{character["id"]}]\'s waitlist entry in ward {ward_id}.'
                else:
                    waitlist[str(ward_id)].remove(waitlist_entry)

                    message = f'{character["name"]} [{character["id"]}] was removed from the waitlist for ward_id {ward_id}.'

                    waitlist_entry = ""
                    
                    #If the character doesn't exist in the waitlist anymore, then add them back to global
                    for attr, value in waitlist.items():
                        for entry in value:
                            if entry["id"] == character["id"]:
                                waitlist_entry = entry
                                break
                    
                    if waitlist_entry == "":
                        waitlist_entry = {
                            "id": character["id"],
                            "migrant": migrant
                        }
                        waitlist["global"].append(waitlist_entry)
                        message += f' They were also added back to the global waitlist.'
            #If ward id not specified, then set migrant for all waitlist entries
            else:
                for attr, value in waitlist.items():
                    for entry in value:
                        if entry["id"] == character["id"]:
                            entry["migrant"] = migrant
                message = f'{character["name"]} [{character["id"]}]\' migrant status was set to {migrant} for all waitlist entries.'

            #Save waitlist
            await save_waitlist(waitlist)
        elif mode == "leave":
            #Make sure character is already on the waitlist
            if "waitlist" not in character["status"]:
                await reply(self.client, interaction, "This character is not on the waitlist.")
                return

            #Remove all of this character's entries from the waitlist
            for attr, value in waitlist.items():
                index = 0
                while index < len(value):
                    if value[index]["id"] == character["id"]:
                        value.pop(index)
                    else:
                        index += 1

            #Save waitlist
            await save_waitlist(waitlist)

            #Remove waitlist status from the character
            character["status"].remove("waitlist")
            await save_userinfo(user_id, user)

            message = f'All entries for {character["name"]} [{character["id"]}] were removed from the waitlist.'

        await reply(self.client, interaction, message)


async def setup(client):
    await client.add_cog(Waitlist(client))