import discord
from discord import app_commands
from discord.ext import commands, tasks
from utilities import *

class DailyChannel(commands.Cog):
    def __init__(self, client):
        self.client = client
    
    @commands.Cog.listener()
    async def on_ready(self):
        await self.client.tree.sync()
        print(f'{__name__} loaded successfully!')
    
    @app_commands.command(name="dailychannel", description="Sends a test message.")
    @commands.has_permissions(administrator=True)
    @app_commands.describe(mode="Mode")
    @app_commands.choices(mode=[
        app_commands.Choice(name="view", value="view"),
        app_commands.Choice(name="set", value="set"),
        app_commands.Choice(name="remove", value="remove")
    ])
    async def daily_channel(self, interaction: discord.Interaction, mode: app_commands.Choice[str], channel_id: str = None):
        server_info = await get_serverinfo()

        server_id = interaction.guild_id

        # Make sure this server exists in user_info
        server = server_info.get(str(server_id), None)

        if server == None:
            server = {
                "daily_channels": []
            }
            server_info[server_id] = server
        
        if mode.value == "view":
            print()
        elif mode.value == "set":
            server["daily_channels"].append(int(channel_id))
        elif mode.value == "remove":
            server["daily_channels"].remove(int(channel_id))
        
        message = f'__**{self.client.get_guild(server_id)} - Daily Channels**__'

        #Give the name and id for each channel in this server
        for channel_id in server["daily_channels"]:
            message += f'\n{self.client.get_channel(channel_id)} (id:{channel_id})'

        # Save to database
        await save_serverinfo(server_info)

        await reply(self.client, interaction, message)


async def setup(client):
    await client.add_cog(DailyChannel(client))