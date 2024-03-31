import discord
from discord import app_commands
from discord.ext import commands, tasks
from utilities import *

class Wafflers(commands.Cog):
    def __init__(self, client):
        self.client = client
    
    @commands.Cog.listener()
    async def on_ready(self):
        await self.client.tree.sync()
        print(f'{__name__} loaded successfully!')
    
    @app_commands.command(name="wafflers", description="Check out who are the top wafflers.")
    async def wafflers(self, interaction: discord.Interaction, number: int = 10):
        message = "__**Top Wafflers (:ballot_box_with_check: = waffled today)**__"

        #Build the list of {user_id: waffles}
        waffle_list = []

        for filename in os.listdir("./data/user_data"):
            if filename.endswith(".json"):
                user_id = os.path.splitext(filename)[0]
                user = await get_userinfo(user_id)
                waffle_list.append({user_id: user["waffles"]})
        
        #Sort the list in descending order
        waffle_list.sort(key=lambda x: list(x.values())[0], reverse=True)

        #Get the first number of elements in the list
        waffle_list = waffle_list[:number]

        #For each entry, print the username (user_id) --- waffles (waffled_today)
        for entry in waffle_list:
            user_id = list(entry.keys())[0]
            username = self.client.get_user(int(user_id))
            waffles = list(entry.values())[0]
            user = await get_userinfo(user_id)

            message += f'\n{username} ({user_id}) --- {waffles}'

            if user["waffled_today"]:
                message += f' :ballot_box_with_check:'
            
        await reply(self.client, interaction, message)


async def setup(client):
    await client.add_cog(Wafflers(client))