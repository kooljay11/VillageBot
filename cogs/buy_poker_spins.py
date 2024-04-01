import discord
from discord import app_commands
from discord.ext import commands, tasks
from utilities import *

class BuyPokerSpins(commands.Cog):
    def __init__(self, client):
        self.client = client
    
    @commands.Cog.listener()
    async def on_ready(self):
        await self.client.tree.sync()
        print(f'{__name__} loaded successfully!')
    
    @app_commands.command(name="buypokerspins", description="Buy spins to use on the poker slot machine (5qq each).")
    async def buypokerspins(self, interaction: discord.Interaction, number: int):
        slots = await get_poker_slots()

        user_id = interaction.user.id

        # Make sure this player exists in user_info
        try:
            user = await get_userinfo(user_id)
        except:
            await reply(self.client, interaction, "You aren't part of the game yet! Do /waffle first.")
            return
        
        cost = slots["spin_cost"] * number

        # Make sure the player can't spend more tetra than they have
        try:
            if int(user["tetra"]) < cost:
                await reply(self.client, interaction, "You don't have enough tetra for that.")
                return
        except:
            await reply(self.client, interaction, "You don't have enough tetra for that.")
            return
        
        #Add spins to the user
        user["poker_spins"] += number
        user["tetra"] -= cost
        
        message = f'You bought {number} poker spins for a total of {cost} tetra. You now have {user["tetra"]} tetra and {user["poker_spins"]} poker spins.'

        # Save to database
        await save_userinfo(user_id, user)

        await reply(self.client, interaction, message)


async def setup(client):
    await client.add_cog(BuyPokerSpins(client))