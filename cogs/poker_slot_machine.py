import discord
from discord import app_commands
from discord.ext import commands, tasks
from utilities import *
import random

class PokerSlotMachine(commands.Cog):
    def __init__(self, client):
        self.client = client
    
    @commands.Cog.listener()
    async def on_ready(self):
        await self.client.tree.sync()
        print(f'{__name__} loaded successfully!')
    
    @app_commands.command(name="pokerslotmachine", description="Spin the slot machine for a chance to win the jackpot!")
    async def pokerslotmachine(self, interaction: discord.Interaction):
        user_id = interaction.user.id

        # Make sure this player exists in user_info
        try:
            user = await get_userinfo(user_id)
        except:
            await reply(self.client, interaction, "You aren't part of the game yet! Do /waffle first.")
            return
        
        # Make sure the player has at least one spin available
        if user["poker_spins"] < 1:
            await reply(self.client, interaction, "You don't have enough poker spins for that.")
            return
    
        result = []
        slots_info = await get_poker_slots()
        
        # Spin the slot machine
        while len(result) < 5:
            card = [random.choice(slots_info["card"]["number"]), random.choice(slots_info["card"]["suit"])]

            if card not in result:
                result.append(card)
        
        # Sort the result
        # Get the reward (isFlush(), is4Kind(), is3Kind() = return true/false, remainder cards, isStraight(), hasAce(), isPair() = return true/false, remainder cards)
        # Get the result code as a list of emojis
        # Give rewards
        # Save to database
        
        message = f'.'
        await reply(self.client, interaction, message)
    

    async def isFlush(hand):
        

        return False

# 1 pair = 1/1.37 * 1t
# 2 pair = 1/20 * 3 spins
# 3 kind = 1/46.3 * 4s, 5t
# straight = 1/254 * 5s, 50t
# flush = 1/508 * 10s, 150t
# full house = 1/693 * 300t
# 4 kind = 1/4164 * 1500t
# st flush = 1/72192 * 20,000t
# royal flush = 1/649739 * 100,000t
# Average reward = 3.93293813t(equivalent)/spin

async def setup(client):
    await client.add_cog(PokerSlotMachine(client))