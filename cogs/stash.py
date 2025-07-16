import discord
from discord import app_commands
from discord.ext import commands, tasks
from utilities import *
from datetime import *
import os

class Stash(commands.Cog):
    def __init__(self, client):
        self.client = client
    
    @commands.Cog.listener()
    async def on_ready(self):
        await self.client.tree.sync()
        print(f'{__name__} loaded successfully!')

    # Stashes don't prevent theft, only alert members of it.
    @app_commands.command(name="stash", description="Manage your stash. Permissions depend on stash type (Public, Private, Representative, Communal).")
    @app_commands.describe(mode="Mode")
    @app_commands.choices(mode=[
        app_commands.Choice(name="Show stash info: stash_id", value="info"),
        app_commands.Choice(name="Join a stash: stash_id", value="join"),
        app_commands.Choice(name="Create a stash: stash_type", value="create"),
        app_commands.Choice(name="List stashes (20 per page)", value="list"),
        app_commands.Choice(name="Deposit to the stash (member): stash_id, item_name, num, item_state", value="deposit"),
        app_commands.Choice(name="Withdraw from the stash (member): stash_id, item_name, num, item_state", value="withdraw"),
        app_commands.Choice(name="Expand the stash (member): stash_id", value="expand"),
        app_commands.Choice(name="Leave stash (member): stash_id", value="leave"),
        app_commands.Choice(name="Toggle theft alert (member): stash_id", value="toggle_theft_alert"),
        app_commands.Choice(name="Toggle transaction logs (-OMM): stash_id", value="toggle_transactions"),
        app_commands.Choice(name="Show election progress (--MM): stash_id", value="election"),
        app_commands.Choice(name="Recall the owner (--M-): stash_id", value="recall"),
        app_commands.Choice(name="Vote for a candidate to be stash owner (--M-): stash_id, char_name_or_id", value="vote"),
        app_commands.Choice(name="Remove all your votes in the ongoing election (--M-): stash_id", value="unvote"),
        app_commands.Choice(name="Toggle support for a member to stay in the stash (---M): stash_id, char_name_or_id", value="toggle_support"),
        app_commands.Choice(name="Accept applicant (-OO-): stash_id, char_name_or_id", value="accept"),
        app_commands.Choice(name="Deny applicant (-OOM): stash_id, char_name_or_id", value="deny"),
        app_commands.Choice(name="Kick member (-OOM): stash_id, char_name_or_id", value="kick"),
        app_commands.Choice(name="Ban user (-OO-): stash_id, char_name_or_id", value="ban"),
        app_commands.Choice(name="Unban user (-OO-): stash_id, char_name_or_id", value="unban"),
        app_commands.Choice(name="Rename stash (-OOM): stash_id, stash_name", value="rename"),
        app_commands.Choice(name="Delete stash (-OO-): stash_id", value="del"),
        app_commands.Choice(name="Convert this stash to a different type (-OOM): stash_id, stash_type", value="convert"),
        app_commands.Choice(name="Start an election (--O-): stash_id", value="start_election"),
        app_commands.Choice(name="Set owner (-O--): stash_id, char_name_or_id", value="set_owner")
    ])
    @app_commands.describe(stash_type="Stash type")
    @app_commands.choices(stash_type=[
        app_commands.Choice(name="Private (owner is unelected and makes all decisions)", value="private"),
        app_commands.Choice(name="Representative (owner is elected and makes all decisions)", value="representative"),
        app_commands.Choice(name="Communal (members make decisions democratically)", value="communal")
    ])
    async def manage_stash(self, interaction: discord.Interaction, mode: str = "info", stash_id: int = 0, stash_type: str = "public", num: int = 1, item_name: str = "", item_state: str = "", char_name_or_id: str = "", stash_name: str = ""):
        user_id = interaction.user.id

        # Make sure the user exists
        try:
            user = await get_userinfo(user_id)
        except:
            await reply(self.client, interaction, f'User not found.')
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

        # If the stash is selected then get the stash
        try:
            stash_info = ward["stashes"][stash_id]
        except:
            stash_info = None

        has_perms = False

        ephermeral = False

        # Make sure the character has the proper perms for whatever they are about to do
        if stash_info != None:
            perms = await get_perm_list_by_char_id(stash_info, character["id"])
            if mode in perms:
                has_perms = True
            elif mode not in perms and mode not in ["deposit", "withdraw", "list", "create"]:
                await reply(self.client, interaction, f'You don\'t have the sufficient permissions to use that command.')
                return
        
        message = f''
        
        if mode == "info":
            # Make sure the stash exists
            if stash_info == None:
                await reply(self.client, interaction, f'Stash not found.')
                return

            # Show the stash name, stash type, users for each role (don't show empty lists), capacity, max capacity
            message = f'__**{stash_info["name"]} ({stash_info["type"]})**__'

            # If there is an owner then display it
            if stash_info["owner"] != {}:
                #owner_user = await get_userinfo(stash_info["owner"]["user_id"])
                #owner_char = await get_user_character(owner_user, stash_info["owner"]["char_id"])
                owner_char_id_nick = await get_id_nickname(self.client, user, stash_info["owner"]["char_id"])
                owner_user_id_nick = await get_id_nickname(self.client, user, stash_info["owner"]["user_id"], "user")
                message += f'\nOwner: {owner_char_id_nick["name"]} (id: {owner_char_id_nick["id"]}) - user: {owner_user_id_nick["name"]} (id: {owner_user_id_nick["id"]})'

            if len(stash_info["members"]) > 0:
                message += f'\nTotal members: {len(stash_info["members"])}'
                formatted_member_list = await get_formatted_char_list(self.client, user, stash_info["members"], stash_info["type"])
                message += f'\nMembers: {", ".join(formatted_member_list)}'

            perms = await get_perm_list_by_char_id(stash_info, character["id"])

            # If the character has perms then also show the applicant list
            if "applicant_list" in perms and len(stash_info["waitlist"]) > 0:
                formatted_char_list = await get_formatted_char_list(self.client, user, stash_info["waitlist"])
                if formatted_char_list:
                    message += f'\n\nApplicant list: {", ".join(formatted_char_list)}'

            # If the character has perms then also show the banned list
            if "banned_list" in perms and len(stash_info["ban_list"]) > 0:
                formatted_char_list = await get_formatted_char_list(self.client, user, stash_info["ban_list"])
                if formatted_char_list:
                    message += f'\n\nBanned list: {", ".join(formatted_char_list)}'

            # Stash contents
            message += f'\n\nCapacity: {stash_info["capacity"]}/{stash_info["max_capacity"]}'
            message += f'\nLand usage: {stash_info["land_usage"]}'
            formatted_item_list = await get_formatted_item_list(stash_info["inventory"])
            message += f'\nInventory: \n\t{"\n\t".join(formatted_item_list)}'
        elif mode == "join":
            # Make sure the stash exists
            if stash_info == None:
                await reply(self.client, interaction, f'Stash not found.')
                return
            
            # Make sure the character isn't already the owner or in the member list
            if stash_info["owner"] != {} and stash_info["owner"]["char_id"] == character["id"]:
                await reply(self.client, interaction, f'You are already the owner of this stash.')
                return
            
            member = await get_dict_by_key_value(stash_info["members"], 'char_id', character["id"])

            if member != None:
                await reply(self.client, interaction, f'You are already a member of this stash.')
                return
            
            # If this is a communal stash and they are part of the banlist and are their own critic then move them to the waitlist
            if stash_info["type"] == "communal":
                banned_member = await get_dict_by_key_value(stash_info["ban_list"], 'char_id', character["id"])

                if banned_member != None and banned_member["char_id"] in banned_member["critics"]:
                    banned_member["critics"].remove(banned_member["char_id"])

                # Update any stash informal elections
                await update_stash_informal_elections(self.client, stash_info, stash_id, ward["id"])
            
            # Otherwise make sure the stash hasn't banned this character
            elif await get_dict_by_key_value(stash_info["ban_list"], 'char_id', character["id"]) != None:
                await reply(self.client, interaction, f'You have been banned from rejoining this stash.')
                return
            
            # Make sure the character isn't already on the applicant list
            if await get_dict_by_key_value(stash_info["waitlist"], 'char_id', character["id"]) != None:
                await reply(self.client, interaction, f'You are already on the applicant list for this stash.')
                return
            
            default_stash = await get_default_stash()
            default_stash["template_member"]["char_id"] = character["id"]
            default_stash["template_member"]["user_id"] = user_id

            # Add user to the applicant list
            stash_info["waitlist"].append(default_stash["template_member"])

            await save_ward(ward)

            message = f'You\'ve joined the applicant list for {stash_info["name"]} (id: {stash_id})'
        elif mode == "create":
            default_stash = await get_default_stash()

            # Make sure there is enough space in the ward
            if ward["grass_land_available"] < default_stash["land_usage"]:
                await reply(self.client, interaction, f'There isn\'t enough space in the ward for another stash.')
                return
            

            # Make sure type specified is correct, can't create public stashes
            if stash_type == "public":
                await reply(self.client, interaction, f'You cannot create public stashes.')
                return
            # Depending on type, assign this character as owner or member
            elif stash_type in ["private", "representative"]:
                owner = deepcopy(default_stash["template_member"])
                owner["char_id"] = character["id"]
                owner["user_id"] = user_id
                owner["transaction_log"] = True
                default_stash["owner"] = owner
            elif stash_type == "communal":
                member = deepcopy(default_stash["template_member"])
                member["char_id"] = character["id"]
                member["user_id"] = user_id
                default_stash["members"].append(member)

            # Make sure this character doesn't already own other private stashes
            private_stash = await get_dict_by_key_value(ward["stashes"], 'owner', owner)

            if private_stash != None:
                await reply(self.client, interaction, f'You should use the private stash you already own in this ward.')
                return

            default_stash["type"] = stash_type

            # Remove possible_types, perms, public_perms, private_perms, representative_perms, communal_perms, template_member
            default_stash.pop("possible_types")
            default_stash.pop("perms")
            default_stash.pop("public_perms")
            default_stash.pop("private_perms")
            default_stash.pop("representative_perms")
            default_stash.pop("communal_perms")
            default_stash.pop("template_member")

            # Use up some land
            ward["grass_land_available"] -= default_stash["land_usage"]

            # Add the stash to the ward
            ward["stashes"].append(default_stash)
            await save_ward(ward)

            message = f'You\'ve successfully added a new {stash_type} stash.'
        elif mode == "list":
            message = f'__**Stashes**__'

            # List all available stashes according to index
            stash_list = ward["stashes"]
            
            num_pages = 20

            # Make sure num is a valid page number
            if not(num > 0 and num < len(stash_list) / num_pages + 1):
                await reply(self.client, interaction, f'You must input a valid integer page number.')
                return
            
            # Make sure the index is within what is allowed
            try:
                # Set the index to be searched according to the page number
                index = (num - 1) * num_pages

                if len(stash_list) > index+num_pages:
                    stash_list = stash_list[index:index+num_pages]
                else:
                    stash_list = stash_list[index:]
            except:
                await reply(self.client, interaction, f'Something went wrong with the indexing of the stashes.')
                return

            for stash_info in stash_list:
                message += f'\n{index}) {stash_info["name"]} ({stash_info["type"]}) '
                if stash_info["owner"] != {}:
                    owner_string = str(await get_formatted_char_list(self.client, user, [stash_info["owner"]]))
                    message += f'owner: {owner_string}\t'
                if len(stash_info["members"]) > 0:
                    message += f'members: {len(stash_info["members"])}\t'
                message += f':package: {stash_info["capacity"]}/{stash_info["max_capacity"]}'
                index += 1
        elif mode == "deposit":
            # Make sure the stash exists
            if stash_info == None:
                await reply(self.client, interaction, f'Stash not found.')
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
                
            # Make sure num is a positive number
            if num < 1:
                await reply(self.client, interaction, f'Must be a positive number.')
                return
                
            # Make sure the character actually has the item
            item_stack = await remove_item_in_inv(character, item_name, num, state=item_state)

            # Make sure the stash has space
            if item_stack != {}:
                remaining_item_stack = await add_item_stack_in_stash(stash_info, item_stack)
            else:
                await reply(self.client, interaction, f'There were no items of that type available in the character\'s inventory.')
                return

            # Return any remaining back to the character
            if remaining_item_stack != {}:
                num = num - remaining_item_stack["amount"]
                await add_item_stack_in_stash(stash_info, remaining_item_stack)

            # If this is a donation then message all members with the alert toggled on
            if not has_perms:
                message = f'{character["name"]} donated {num} {item_name} ({item_state}) into the stash.'

                if stash_info["owner"] != {} and stash_info["owner"]["theft_alert"]:
                    await dm(self.client, stash_info["owner"]["user_id"], message)
                for member in stash_info["members"]:
                    if member["theft_alert"]:
                        await dm(self.client, member["user_id"], message)
            else:
                message = f'{character["name"]} deposited {num} {item_name} ({item_state}) into the stash.'

            await save_ward(ward)
            await save_userinfo(user_id, user)
        elif mode == "withdraw":
            # Make sure the stash exists
            if stash_info == None:
                await reply(self.client, interaction, f'Stash not found.')
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
                
            # Make sure num is a positive number
            if num < 1:
                await reply(self.client, interaction, f'Must be a positive number.')
                return

            # Make sure the item actually exists in the stash
            item_stack = await remove_item_in_stash(stash_info, item_name, num)

            # Make sure the character has space for the item
            if item_stack != {}:
                remaining_item_stack = await add_item_stack_in_inv(character, item_stack)
            else:
                await reply(self.client, interaction, f'There were no items of that type available in the stash.')
                return

            # Put the remaining back in the stash
            if remaining_item_stack != {}:
                num = num - remaining_item_stack["amount"]
                await add_item_stack_in_stash(stash_info, remaining_item_stack)

            # If this is stealing then message all members with the alert toggled on
            if not has_perms:
                message = f'{character["name"]} stole {num} {item_name} from the stash.'

                if stash_info["owner"] != {} and stash_info["owner"]["theft_alert"]:
                    await dm(self.client, stash_info["owner"]["user_id"], message)
                for member in stash_info["members"]:
                    if member["theft_alert"]:
                        await dm(self.client, member["user_id"], message)
            else:
                message = f'{character["name"]} withdrew {num} {item_name} from the stash.'

            await save_ward(ward)
            await save_userinfo(user_id, user)
        elif mode == "expand":
            # Make sure the stash exists
            if stash_info == None:
                await reply(self.client, interaction, f'Stash not found.')
                return
            
            default_stash = await get_default_stash()
            
            # Make sure there is enough space in the land
            if ward["grass_land_available"] < default_stash["land_usage"]:
                await reply(self.client, interaction, f'This land has no available grassland left.')
                return
            
            # Make sure the stash actually needs to expand (if the available space is greater than the space provided by 1 land = no need to expand)
            if stash_info["max_capacity"] - stash_info["capacity"] > default_stash["max_capacity"]:
                await reply(self.client, interaction, f'This stash doesn\'t need to expand.')
                return
            
            # Expand the stash
            ward["grass_land_available"] -= default_stash["land_usage"]
            stash_info["max_capacity"] += default_stash["max_capacity"]
            stash_info["land_usage"] += default_stash["land_usage"]
            
            message = f'The stash was expanded by {default_stash["land_usage"]} grassland. The stash is now at :package: {stash_info["capacity"]}/{stash_info["max_capacity"]}, taking up {stash_info["land_usage"]} land.'
            await save_ward(ward)
        elif mode == "leave":
            # Make sure the stash exists
            if stash_info == None:
                await reply(self.client, interaction, f'Stash not found.')
                return

            global_info = await get_globalinfo()

            if stash_info["owner"] != {} and stash_info["owner"]["char_id"] == character["id"]:
                if len(stash_info["members"]) > 1:
                    # If is owner AND stash type = private AND there are more than 1 other members then automatically convert to representative stash and start election
                    if stash_info["type"] == "private":
                        stash_info["type"] = "representative"
                    # If is owner AND stash type = representative AND there are more than 1 other members then start election
                    elif stash_info["type"] == "representative":
                        print()

                    # If no election is happening right now then start one
                    if stash_info["election_days_left"] <= 0:
                        stash_info["election_days_left"] = global_info["election_days_length"]
                        stash_info["recall_voters"] = []

                removed_member = deepcopy(stash_info["owner"])
                stash_info["owner"] = {}

                # If is owner AND stash type = private/representative AND 1 other member left then make the remaining user the owner
                if len(stash_info["members"]) == 1:
                    stash_info["owner"] = deepcopy(stash_info["members"][0])
                    stash_info["members"] = []

                    # Also stop any election/recall election
                    stash_info["election"] = {}
                    stash_info["election_days_left"] = 0
                    stash_info["recall_voters"] = []
            else:
                member = await get_dict_by_key_value(stash_info["members"], 'char_id', character["id"])
                removed_member = deepcopy(member)
                stash_info["members"].remove(member)
            
            # If an election is happening right now then remove them from the candidate list
            if stash_info["election_days_left"] > 0:
                if character["id"] in stash_info["election"].keys():
                    stash_info["election"].pop(character["id"])
                
                # If the person voted in an ongoing election, then remove their vote
                for candidate_id, voter_ids in stash_info["election"]:
                    if character["id"] in voter_ids[candidate_id]:
                        voter_ids[candidate_id].remove(character["id"])
            else:
                # Remove any recall votes the character has made
                if character["id"] in stash_info["recall_voters"]:
                    stash_info["recall_voters"].remove(character["id"])
                
                # If stash type = representative, check whether a recall election can be called
                num_recall_votes_needed = global_info["recall_threshold"] * len(stash_info["members"])

                if stash_info["type"] == "representative" and len(stash_info["recall_voters"]) >= num_recall_votes_needed:
                    stash_info["election_days_left"] = global_info["election_days_length"]
                    stash_info["recall_voters"] = []

            # If stash type = communal, put them on the banlist and have them be one of their own critics
            if stash_info["type"] == "communal":
                removed_member["critics"].append(character["id"])
                stash_info["ban_list"].append(removed_member)

                await remove_all_stash_influence(stash_info, character["id"])

                # Update any stash informal elections
                await update_stash_informal_elections(self.client, stash_info, stash_id, ward["id"])

            public_stash = ward["stashes"][0]

            message = f'You left the stash. '

            # If there are no other members then delete the stash and send all items to public
            if stash_info["owner"] == {} and stash_info["members"] == []:
                message += f'Because there was no one left in the stash, the stash was removed and all items are added to the public stash.'

                for item_stack in stash_info["inventory"]:
                    await add_item_stack_in_stash(public_stash, item_stack, ward)

                # Return the land used back
                ward["grass_land_available"] += stash_info["land_usage"]
                
                ward["stashes"].remove(stash_info)

            await save_ward(ward)
        elif mode == "toggle_theft_alert":
            # Make sure the stash exists
            if stash_info == None:
                await reply(self.client, interaction, f'Stash not found.')
                return
            
            # Toggle the theft alert depending on if they are the owner or a member
            if stash_info["owner"] != {} and stash_info["owner"]["char_id"] == character["id"]:
                member = stash_info["owner"]
            else:
                member = await get_dict_by_key_value(stash_info["members"], 'char_id', character["id"])

            member["theft_alert"] = not stash_info["owner"]["theft_alert"]

            if member["theft_alert"]:
                message = f'This character will now receive theft alerts.'
            else:
                message = f'This character will no longer receive theft alerts.'

            await save_ward(ward)
        elif mode == "toggle_transactions":
            # Make sure the stash exists
            if stash_info == None:
                await reply(self.client, interaction, f'Stash not found.')
                return
            
            # Toggle the transaction log depending on if they are the owner or a member
            if stash_info["owner"] != {} and stash_info["owner"]["char_id"] == character["id"]:
                member = stash_info["owner"]
            else:
                member = await get_dict_by_key_value(stash_info["members"], 'char_id', character["id"])

            member["transaction_log"] = not stash_info["owner"]["transaction_log"]
            
            if member["transaction_log"]:
                message = f'This character will now receive transaction logs.'
            else:
                message = f'This character will no longer receive transaction logs.'

            await save_ward(ward)
        elif mode == "election":
            # Make sure the stash exists
            if stash_info == None:
                await reply(self.client, interaction, f'Stash not found.')
                return
            
            votes = []
            # Show how many votes each candidate has so far in descending order and how many days are left to vote
            if stash_info["election_days_left"] > 0:
                message = f'__**Interim Election Results**__'
                message += f'\nDays left in the vote: {stash_info["election_days_left"]}'

                for candidate_id, voters in stash_info["election"].items():
                    candidate = await get_id_nickname(self.client, user, candidate_id)
                    votes.append((candidate["name"], len(voters)))
                
                # Sort the list of tuples (name, num voters) in descending order
                votes.sort(key=lambda tup: tup[1], reverse=True)

                for candidate_name, num_votes in votes:
                    message += f'\n{candidate_name}: {num_votes}'

            # If there is no election active, then show how many recall voters there are
            else:
                # Calculate the number of recall votes needed to trigger an election
                global_info = await get_globalinfo()
                num_recall_votes_needed = global_info["recall_threshold"] * len(stash_info["members"])
                
                message = f'__**Recall Election Progress**__'
                message += f'\nRecall voters: {len(stash_info["recall_voters"])}'
                message += f'\nTotal members: {len(stash_info["members"])}'
                message += f'\nRecall voters needed: {num_recall_votes_needed}'
        elif mode == "recall":
            # Make sure the stash exists
            if stash_info == None:
                await reply(self.client, interaction, f'Stash not found.')
                return
            
            # Make sure there isn't an active election right now
            if stash_info["election_days_left"] > 0:
                await reply(self.client, interaction, f'You cannot cast a recall vote during an active election.')
                return
            
            # Make sure the character hasn't already voted in the recall election
            if character["id"] in stash_info["recall_voters"]:
                await reply(self.client, interaction, f'You\'ve already cast a recall vote.')
                return
            
            # Add the character id to the recall voters list
            stash_info["recall_voters"].append(character["id"])

            # Calculate the number of recall votes needed to trigger an election
            global_info = await get_globalinfo()
            num_recall_votes_needed = global_info["recall_threshold"] * len(stash_info["members"])

            message = f'You\'ve added a recall vote.'
            message += f'\nRecall voters: {len(stash_info["recall_voters"])}'
            message += f'\nTotal members: {len(stash_info["members"])}'

            message += f'\nRecall voters needed: {num_recall_votes_needed}'

            # If stash type = representative, check whether a recall election can be called
            if stash_info["type"] == "representative" and len(stash_info["recall_voters"]) >= num_recall_votes_needed:
                stash_info["election_days_left"] = global_info["election_days_length"]
                stash_info["recall_voters"] = []

                message += f'\n\nThe recall vote has passed. An election for a new owner has been called.'

            await save_ward(ward)

            ephermeral = True
        elif mode == "vote":
            # Make sure the stash exists
            if stash_info == None:
                await reply(self.client, interaction, f'Stash not found.')
                return
            
            # Make sure there is an active election right now
            if stash_info["election_days_left"] <= 0:
                await reply(self.client, interaction, f'There is no active election right now.')
                return
            
            # If the target is empty then set it to the character id
            if char_name_or_id == "":
                char_name_or_id = character["id"]

            # Get the candidate name
            candidate = await get_id_nickname(self.client, user, char_name_or_id)
            
            # Make sure the character hasn't already voted for this candidate
            try:
                if stash_info["election"].get(candidate["id"], None) != None and character["id"] in stash_info["election"][candidate["id"]]:
                    await reply(self.client, interaction, f'You\'ve already voted for that candidate.')
                    return
            except:
                print()

            # Make sure the candidate they are voting for is an actual member of the stash
            if await get_dict_by_key_value(stash_info["members"], 'char_id', character["id"]) == None and not (stash_info["owner"] != {} and stash_info["owner"]["char_id"] == candidate["id"]):
                await reply(self.client, interaction, f'The candidate must be a member of this stash.')
                return

            # Add their character id to the list of character ids voting for that candidate id
            try:
                stash_info["election"][candidate["id"]].append(character["id"])
            except:
                stash_info["election"][candidate["id"]] = [character["id"]]
                
            await save_ward(ward)

            message = f'You voted for {candidate["name"]}. Use /stash mode=election to see the election progress.'

            ephermeral = True
            # If a majority has been reached then automatically resolve -- NOT REQUIRED
        elif mode == "unvote":
            # Make sure the stash exists
            if stash_info == None:
                await reply(self.client, interaction, f'Stash not found.')
                return
            
            # Make sure there is an active election right now
            if stash_info["election_days_left"] <= 0:
                await reply(self.client, interaction, f'There is no active election right now.')
                return

            removal_ids = []

            # Remove all entries of this character's vote for all candidates
            for candidate_id, voters in stash_info["election"].items():
                if character["id"] in voters:
                    voters.remove(character["id"])
                
                if len(voters) <= 0:
                    removal_ids.append(candidate_id)
            
            # Remove all empty candidate lists
            for candidate_id in removal_ids:
                stash_info["election"].pop(candidate_id)
            
            await save_ward(ward)

            message = f'You\'ve removed all your votes in the current election.'

            ephermeral = True
            # If a majority has been reached then automatically resolve -- NOT REQUIRED
        elif mode == "toggle_support":
            # Make sure the stash exists
            if stash_info == None:
                await reply(self.client, interaction, f'Stash not found.')
                return
            
            # Get the target character id
            target_id_nick = await get_id_nickname(self.client, user, char_name_or_id)
            
            # Figure out whether the target character is in the member list, waitlist, or banlist
            member = await get_dict_by_key_value(stash_info["members"], 'char_id', target_id_nick["id"])

            if member == None:
                member = await get_dict_by_key_value(stash_info["waitlist"], 'char_id', target_id_nick["id"])

            if member == None:
                member = await get_dict_by_key_value(stash_info["ban_list"], 'char_id', target_id_nick["id"])
            
            if member == None:
                await reply(self.client, interaction, f'Target character not found.')
                return
            
            # Make sure the character can't support themselves
            if member["char_id"] == character["id"]:
                await reply(self.client, interaction, f'Character cannot be their own supporter.')
                return

            # See if this character has supported them already
            # If they haven't then add to their supporters
            # Otherwise then remove from their supporters
            if character["id"] in member["supporters"]:
                member["supporters"].remove(character["id"])
                message = f'{character["name"]} is no longer supporting {target_id_nick["name"]}.\n'
            else:

                if character["id"] in member["critics"]:
                    member["critics"].remove(character["id"])

                    message = f'{character["name"]} is no longer a critic of {target_id_nick["name"]}.\n'
                else:
                    member["supporters"].append(character["id"])

                    message = f'{character["name"]} is now supporting {target_id_nick["name"]}.\n'
            
            # Update any stash informal elections
            message += await update_stash_informal_elections(self.client, stash_info, stash_id, ward["id"])
            await save_ward(ward)
        elif mode == "accept":
            # Make sure the stash exists
            if stash_info == None:
                await reply(self.client, interaction, f'Stash not found.')
                return

            # Make sure there isn't an election occuring right now in the stash
            if stash_info["election_days_left"] > 0:
                await reply(self.client, interaction, f'You cannot accept any new members during an active election.')
                return
            
            # Make sure the target applicant exists and is actually in the applicant list
            try:
                applicant_id_nick = await get_id_nickname(self.client, user, char_name_or_id)
            except:
                await reply(self.client, interaction, f'Target applicant doesn\'t exist.')
                return
            
            applicant = await get_dict_by_key_value(stash_info["waitlist"], 'char_id', applicant_id_nick["id"])

            if applicant == None:
                await reply(self.client, interaction, f'The character must be on the applicant list before you can accept them.')
                return

            # Make sure the target applicant hasn't been banned already (if they are then remove them from the applicant list)
            if await get_dict_by_key_value(stash_info["ban_list"], 'char_id', applicant_id_nick["id"]) != None:
                stash_info["waitlist"].remove(applicant)
                await save_ward(ward)
                await reply(self.client, interaction, f'This user has already been banned from the stash.')
                return

            # Add the target applicant to the member list
            stash_info["members"].append(applicant)

            # Remove the target applicant from the waitlist
            stash_info["waitlist"].remove(applicant)

            await save_ward(ward)

            message = f'You have accepted {applicant_id_nick["name"]} into the stash.'

            # DM the applicant that they've been accepted into the stash
            applicant_user = await get_userinfo(applicant["user_id"])
            applicant_char = await get_user_character(applicant_user, applicant_id_nick["id"])
            await dm(self.client, applicant["user_id"], f'{applicant_char["name"]} (id: {applicant_char["id"]}) has been accepted into stash {stash_id} in ward {ward["id"]}.')
        elif mode == "deny":
            # Make sure the stash exists
            if stash_info == None:
                await reply(self.client, interaction, f'Stash not found.')
                return
            
            # Make sure the target applicant exists and is actually in the applicant list
            try:
                applicant_id_nick = await get_id_nickname(self.client, user, char_name_or_id)
            except:
                await reply(self.client, interaction, f'Target applicant doesn\'t exist.')
                return
            
            applicant = await get_dict_by_key_value(stash_info["waitlist"], 'char_id', applicant_id_nick["id"])

            if applicant == None:
                await reply(self.client, interaction, f'The character must be on the applicant list before you can deny them.')
                return
            
            # If communal then add to critics and update roles otherwise remove them from the waitlist
            if stash_info["type"] == "communal":
                if character["id"] in applicant["critics"]:
                    await reply(self.client, interaction, f'You are already a critic against this applicant.')
                    return
                
                if character["id"] in applicant["supporters"]:
                    applicant["supporters"].remove(character["id"])
                
                applicant["critics"].append(character["id"])

                # Update the stash informal elections
                message = await update_stash_informal_elections(self.client, stash_info, stash_id, ward["id"])
            else:
                # Remove the target applicant from the list
                stash_info["waitlist"].remove(applicant)

                message = f'{applicant_id_nick["name"]} (id:{applicant_id_nick["id"]}) was removed from the applicant list.'
            
            await save_ward(ward)
        elif mode == "kick":
            # Make sure the stash exists
            if stash_info == None:
                await reply(self.client, interaction, f'Stash not found.')
                return
            
            # Make sure there isn't an election occuring right now in the stash
            if stash_info["election_days_left"] > 0:
                await reply(self.client, interaction, f'You cannot kick members during an active election.')
                return

            # Make sure the target is a member of the stash
            try:
                member_id_nick = await get_id_nickname(self.client, user, char_name_or_id)
            except:
                await reply(self.client, interaction, f'Target member doesn\'t exist.')
                return
            
            member = await get_dict_by_key_value(stash_info["members"], 'char_id', member_id_nick["id"])

            if member == None:
                await reply(self.client, interaction, f'The character must be a member of the stash.')
                return
            
            if stash_info["type"] == "communal":
                if character["id"] in member["critics"]:
                    await reply(self.client, interaction, f'You are already a critic against this member.')
                    return
                
                if character["id"] in member["supporters"]:
                    member["supporters"].remove(character["id"])
                
                member["critics"].append(character["id"])

                # Update the stash informal elections
                message = await update_stash_informal_elections(self.client, stash_info, stash_id, ward["id"])
                
                await save_ward(ward)
            else:
                member_user = await get_userinfo(member["user_id"])
                member_char = await get_user_character(member_user, member_id_nick["id"])
                
                await dm(self.client, member["user_id"], f'{member_char["name"]} (id: {member_char["id"]}) was kicked from stash {stash_id} in ward {ward["id"]}.')

                # Remove the target member from the member list
                stash_info["members"].remove(member)

                # Remove any recall votes the character has made
                if member["char_id"] in stash_info["recall_voters"]:
                    stash_info["recall_voters"].remove(member["char_id"])

                message = f'{member_id_nick["name"]} (id: {member_id_nick["id"]}) (user id: {member["user_id"]}) was kicked from stash {stash_id} in ward {ward["id"]}.'

                # If stash type = representative, check whether a recall election can be called
                global_info = await get_globalinfo()
                num_recall_votes_needed = global_info["recall_threshold"] * len(stash_info["members"])

                if stash_info["type"] == "representative" and len(stash_info["recall_voters"]) >= num_recall_votes_needed:
                    stash_info["election_days_left"] = global_info["election_days_length"]
                    stash_info["recall_voters"] = []

                    message += f'\n\nThe recall vote has passed. An election for a new owner has been called.'

                await save_ward(ward)
        elif mode == "ban":
            # Make sure the stash exists
            if stash_info == None:
                await reply(self.client, interaction, f'Stash not found.')
                return
            
            # Make sure there isn't an election occuring right now in the stash
            if stash_info["election_days_left"] > 0:
                await reply(self.client, interaction, f'You cannot ban members during an active election.')
                return
            
            # Make sure the target is a member of the stash
            try:
                member_id_nick = await get_id_nickname(self.client, user, char_name_or_id)
            except:
                await reply(self.client, interaction, f'Target member doesn\'t exist.')
                return
            
            member = await get_dict_by_key_value(stash_info["members"], 'char_id', member_id_nick["id"])

            if member == None:
                await reply(self.client, interaction, f'The character must be a member of the stash.')
                return
            
            member_user = await get_userinfo(member["user_id"])
            member_char = await get_user_character(member_user, member_id_nick["id"])
            
            await dm(self.client, member["user_id"], f'{member_char["name"]} (id: {member_char["id"]}) was banned from stash {stash_id} in ward {ward["id"]}.')

            # Add the target user to the ban list
            stash_info["ban_list"].append(member)

            # Remove the target member from the member list
            stash_info["members"].remove(member)

            # Remove any recall votes the character has made
            if member["char_id"] in stash_info["recall_voters"]:
                stash_info["recall_voters"].remove(member["char_id"])
            
            message = f'{member_id_nick["name"]} (id: {member_id_nick["id"]}) (user id: {member["user_id"]}) was banned from stash {stash_id} in ward {ward["id"]}.'

            # If stash type = representative, check whether a recall election can be called INSERT
            global_info = await get_globalinfo()
            num_recall_votes_needed = global_info["recall_threshold"] * len(stash_info["members"])

            if stash_info["type"] == "representative" and len(stash_info["recall_voters"]) >= num_recall_votes_needed:
                stash_info["election_days_left"] = global_info["election_days_length"]
                stash_info["recall_voters"] = []

                message += f'\n\nThe recall vote has passed. An election for a new owner has been called.'

            await save_ward(ward)
        elif mode == "unban":
            # Make sure the stash exists
            if stash_info == None:
                await reply(self.client, interaction, f'Stash not found.')
                return
            
            # Make sure the target user is part of the ban list
            try:
                banned_member_id_nick = await get_id_nickname(self.client, user, char_name_or_id)
            except:
                await reply(self.client, interaction, f'Target member doesn\'t exist.')
                return
            
            banned_member = await get_dict_by_key_value(stash_info["ban_list"], 'char_id', banned_member_id_nick["id"])
            
            if banned_member == None:
                await reply(self.client, interaction, f'The character must be on the banned list.')
                return

            # Remove the target user from the ban list
            stash_info["ban_list"].remove(banned_member)

            await save_ward(ward)

            message = f'{banned_member_id_nick["name"]} (id: {banned_member_id_nick["id"]}) (user id: {banned_member["user_id"]}) was removed from the ban list of stash {stash_id} in ward {ward["id"]}.'
        elif mode == "rename":
            # Make sure the stash exists
            if stash_info == None:
                await reply(self.client, interaction, f'Stash not found.')
                return

            # Make sure the stash name is 1-50 characters long
            if not (len(stash_name) >= 1 and len(stash_name) <= 50):
                await reply(self.client, interaction, f'You must choose a stash name that is 1-50 characters long.')
                return
            
            # Make sure the stash name is different from before
            if stash_name == stash_info["name"]:
                await reply(self.client, interaction, f'The stash is already called {stash_info["name"]}.')
                return
            
            old_stash_name = deepcopy(stash_info["name"])

            stash_info["name"] = stash_name
            await save_ward(ward)

            message = f'The stash has been renamed from {old_stash_name} to {stash_name}.'
        elif mode == "del":
            # Make sure the stash exists
            if stash_info == None:
                await reply(self.client, interaction, f'Stash not found.')
                return

            # Make sure there isn't an election occuring right now in the stash
            if stash_info["election_days_left"] > 0:
                await reply(self.client, interaction, f'You cannot delete a stash during an active election.')
                return
            
            # Make sure there isn't a recall election that has reached the recall threshold
            global_info = await get_globalinfo()
            if len(stash_info["members"]) > 0 and len(stash_info["recall_voters"])/len(stash_info["members"]) >= global_info["recall_threshold"]:
                await reply(self.client, interaction, f'You cannot delete a stash when a recall election has been voted for.')
                return
            
            # Message all members that the stash has been deleted
            for member in stash_info["members"]:
                member_user = await get_userinfo(member["user_id"])
                char_id_nick = await get_id_nickname(self.client, member_user, character["id"])
                await dm(self.client, member["user_id"], f'{stash_info["name"]} (id: {stash_id}) in ward {ward["id"]} has been deleted by {char_id_nick["name"]} (id: {char_id_nick["id"]}) (user id: {user_id}).')

            message = f'Stash {stash_id} ({stash_info["name"]}) has been deleted.'

            public_stash = ward["stashes"][0]

            # Move all items to the public stash
            for item_stack in stash_info["inventory"]:
                await add_item_stack_in_stash(public_stash, item_stack, ward)
            
            # Return the land used back
            ward["grass_land_available"] += stash_info["land_usage"]

            ward["stashes"].remove(stash_info)

            await save_ward(ward)
        elif mode == "convert":
            # Make sure the stash exists
            if stash_info == None:
                await reply(self.client, interaction, f'Stash not found.')
                return

            # Make sure there isn't an election occuring right now in the stash
            if stash_info["election_days_left"] > 0:
                await reply(self.client, interaction, f'You cannot convert a stash during an active election.')
                return
            
            # Make sure there are no recall votes
            global_info = await get_globalinfo()
            if len(stash_info["recall_voters"]) > 0:
                await reply(self.client, interaction, f'You cannot convert a stash when there are recall votes.')
                return
            
            # Make sure this will be a different type of stash than the one already
            if stash_info["type"] == stash_type:
                await reply(self.client, interaction, f'The stash is already a {stash_type} stash.')
                return
            
            old_stash_type = deepcopy(stash_info["type"])
            
            if stash_type == "public":
                # Message all members that the stash has been deleted
                for member in stash_info["members"]:
                    member_user = await get_userinfo(member["user_id"])
                    char_id_nick = await get_id_nickname(self.client, member_user, character["id"])
                    await dm(self.client, member["user_id"], f'{stash_info["name"]} (id: {stash_id}) in ward {ward["id"]} has been deleted by {char_id_nick["name"]} (id: {char_id_nick["id"]}) (user id: {user_id}).')

                message = f'{stash_info["name"]} (id: {stash_id}) has been deleted and all items moved to the public stash.'

                public_stash = ward["stashes"][0]

                # Move all items to the public stash
                for item_stack in stash_info["inventory"]:
                    await add_item_stack_in_stash(public_stash, item_stack, ward)

                ward["stashes"].remove(stash_info)

                await save_ward(ward)
            elif stash_info["type"] in ["representative", "private"]:
                # If turning into a communal stash make the owner a regular member
                if stash_type == "communal" and stash_info["owner"] != {}:
                    prev_owner = deepcopy(stash_info["owner"])
                    stash_info["members"].append(prev_owner)
                    stash_info["owner"] = {}
                
                stash_info["type"] = stash_type

                await save_ward(ward)
            elif stash_info["type"] == "communal":
                # Make sure the stash cannot be converted to private, only representative
                if stash_type != "representative":
                    await reply(self.client, interaction, f'This {stash_info["type"]} stash can only be converted to representative, not {stash_type}.')
                    return

                # Toggle the convert vote
                if character["id"] in stash_info["convert_voters"]:
                    stash_info["convert_voters"].remove(character["id"])
                    message = f'{character["name"]} is no longer voting to convert the stash from {stash_info["type"]} to {stash_type}.'
                else:
                    stash_info["convert_voters"].append(character["id"])
                    message = f'{character["name"]} is now voting to convert the stash from {stash_info["type"]} to {stash_type}.'

                await save_ward(ward)

                # Check if number of converters have reached the threshold
                if len(stash_info["convert_voters"]) < len(stash_info["members"]) * global_info["convert_threshold"]:
                    await reply(self.client, interaction, f'{message} There are not enough convert votes to convert this stash to {stash_type}.')
                    return
                else:
                    stash_info["convert_voters"] = []
                    stash_info["type"] = stash_type

                    # Remove the influence of every member
                    for member in stash_info["members"]:
                        await remove_all_stash_influence(stash_info, member["char_id"])

                    # If there is more than one member, begin an election
                    if len(stash_info["members"]) > 1:
                        await start_stash_election(stash_info)
                    # Otherwise make them the owner
                    else:
                        stash_info["owner"] = deepcopy(stash_info["members"][0])
                        stash_info["members"] = []

                    await save_ward(ward)

            if stash_type != "public" and stash_info["type"] == stash_type:
                message = f'{stash_info["name"]} (id: {stash_id}) has been converted from {old_stash_type} to {stash_type}.'

                # Message all members that the stash has been converted
                for member in stash_info["members"]:
                    member_user = await get_userinfo(member["user_id"])
                    char_id_nick = await get_id_nickname(self.client, member_user, character["id"])
                    await dm(self.client, member["user_id"], f'{stash_info["name"]} (id: {stash_id}) in ward {ward["id"]} has been converted from {old_stash_type} to {stash_type} by {char_id_nick["name"]} (id: {char_id_nick["id"]}) (user id: {user_id}).')
        elif mode == "start_election":
            if stash_info["election_days_left"] > 0:
                await reply(self.client, interaction, f'This stash already has an ongoing election.')
                return

            # Begin an election
            await start_stash_election(stash_info)

            message = f'An election for a new stash leader has begun.'

            # Tell all members that a new election will be called
            for member in stash_info["members"]:
                member_user = await get_userinfo(member["user_id"])
                char_id_nick = await get_id_nickname(self.client, member_user, character["id"])
                await dm(self.client, member["user_id"], f'{char_id_nick["name"]} (id: {char_id_nick["id"]}) (user id: {user_id}) has called for an election for a new leader for {stash_info["name"]} (id: {stash_id}) in ward {ward["id"]}.')

            await save_ward(ward)
        elif mode == "set_owner":
            # Make sure there isn't an election occuring right now in the stash
            if stash_info["election_days_left"] > 0:
                await reply(self.client, interaction, f'Cannot do this during an ongoing election.')
                return
            
            # Make sure the target is a member of the stash
            try:
                new_owner_id_nick = await get_id_nickname(self.client, user, char_name_or_id)
            except:
                await reply(self.client, interaction, f'Target member doesn\'t exist.')
                return
            
            new_owner = await get_dict_by_key_value(stash_info["members"], 'char_id', new_owner_id_nick["id"])

            if new_owner == None:
                await reply(self.client, interaction, f'The character must be a member of the stash.')
                return

            # If this is a private stash then set transaction_log to false for the old owner and true for the new owner
            if stash_info["type"] == "private":
                new_owner["transaction_log"] = True
                stash_info["owner"]["transaction_log"] = False
            
            # Set the new owner
            old_owner = deepcopy(stash_info["owner"])
            
            stash_info["members"].append(old_owner)
            stash_info["owner"] = deepcopy(new_owner)
            stash_info["members"].remove(new_owner)

            message = f'{new_owner_id_nick["name"]} (id: {new_owner_id_nick["id"]}) has been set as the new owner of stash {stash_id} in ward {ward["id"]}.'

            # DM all members of the new ownership change
            for member in stash_info["members"]:
                member_user = await get_userinfo(member["user_id"])
                new_owner_char_id_nick = await get_id_nickname(self.client, member_user, stash_info["owner"]["char_id"])

                old_owner_id_nick = await get_id_nickname(self.client, member_user, character["id"])
                await dm(self.client, member["user_id"], f'{old_owner_id_nick["name"]} (id: {old_owner_id_nick["id"]}) (user id: {user_id}) has set {new_owner_char_id_nick["name"]} (id: {new_owner_char_id_nick["id"]}) (user id: {stash_info["owner"]["user_id"]}) as the new owner for stash {stash_info["name"]} (id: {stash_id}) in ward {ward["id"]}.')

            await save_ward(ward)
        
        # For all successful actions send a message to all members with the transaction_log turned on except info, list, lb, election, recall, support, vote, unvote, applicant_list (and deny, kick if this is a communal stash)
        if mode not in ["info", "list", "lb", "election", "recall", "toggle_support", "vote", "unvote", "toggle_theft_alert", "toggle_transactions", "del", "convert", "start_election", "set_owner"] and not (stash_info["type"] == "communal" and mode in ["deny", "kick"]):
            if stash_info["owner"] != {} and stash_info["owner"]["transaction_log"]:
                owner = await get_userinfo(stash_info["owner"]["user_id"])
                
                #print(f'owner: {owner["points"]}')

                this_char_id_nick = await get_id_nickname(self.client, owner, character["id"])
                #print(f'this_user: {this_user["name"]}')

                await dm(self.client, stash_info["owner"]["user_id"], f'[{stash_info["name"]} | {stash_id}] [{this_char_id_nick["name"]} | {this_char_id_nick["id"]} | {user_id}] : {message}')
            for member in stash_info["members"]:
                if member["transaction_log"]:
                    member_user = await get_userinfo(member["user_id"])
                    #print(f'owner: {owner["points"]}')

                    this_char_id_nick = await get_id_nickname(self.client, member_user, character["id"]) 
                    #print(f'this_user: {this_user["name"]}')

                    await dm(self.client, member["user_id"], f'[{stash_info["name"]} | {stash_id}] [{this_char_id_nick["name"]} | {this_char_id_nick["id"]} | {user_id}] : {message}')

        await reply(self.client, interaction, message, ephemeral=ephermeral)



async def setup(client):
    await client.add_cog(Stash(client))