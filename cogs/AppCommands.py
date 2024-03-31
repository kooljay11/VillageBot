import discord
from discord import app_commands
from discord.ext import commands
import json

class AppCommands(commands.Cog):
    def __init__(self, client):
        self.client = client
    
    @commands.Cog.listener()
    async def on_ready(self):
        await self.client.tree.sync()
        print(f'{__name__} loaded successfully!')

    # @app_commands.command(name="test", description="Sends a test message.")
    # @app_commands.describe(option="Options?")
    # @app_commands.choices(option=[
    #     app_commands.Choice(name="Option 1", value="1"),
    #     app_commands.Choice(name="Option 2", value="2")
    # ])
    # async def test(self, interaction: discord.Interaction, option: app_commands.Choice[str]):
    #     member = None
    #     if member is None:
    #         member = interaction.user
    #     elif member is not None:
    #         member = member
        
    #     avatar_embed = discord.Embed(title=f'{member.name}\'s Avatar', colour=discord.Colour.random())
    #     avatar_embed.set_image(url=member.avatar)
    #     avatar_embed.set_footer(text=f'Requested by {member.name}', icon_url=member.avatar)

    #     await interaction.response.send_message(embed=avatar_embed)
    

    # async def get_servers(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    #     with open(".../data/server_info.json", "r") as file:
    #         server_info = await json.load(file)
        
    #     print(f'server_info: {server_info}')
    #     server_id_list = []

    #     for server_id, server in server_info.items():
    #         server_id_list.append(server_id)
    #         print(f'server_id_list: {server_id_list}')
        
    #     return [
    #         app_commands.Choice(name=server_id, value=server_id)
    #         for server_id in server_id_list if current.lower() in server_id.lower()
    #     ]
    

    # @app_commands.command(name="test2", description="Sends a test message.")
    # @app_commands.autocomplete(option=get_servers)
    # async def test2(self, interaction: discord.Interaction, option: str):
    #     await interaction.response.send_message(f'You chose {option}')
    

    # async def rps_autocomplete(self, interaction: discord.Interaction, current: str,) -> list[app_commands.Choice[str]]:
    #     choices = ['Rock', 'Paper', 'Scissors']
    #     return [
    #         app_commands.Choice(name=choice, value=choice)
    #         for choice in choices if current.lower() in choice.lower()
    #     ]
    

    # play rock paper scissors
    # @app_commands.command(name="rps")
    # @app_commands.autocomplete(choices=rps_autocomplete)
    # async def rps(self, interaction: discord.Interaction, choices:str):
    #     choices = choices.lower()
    #     if (choices == 'rock'):
    #         counter = 'paper'
    #     elif (choices == 'paper'):
    #         counter = 'scissors'
    #     else:
    #         counter = 'rock'
    #     await interaction.response.send_message(f'You chose {choices}')



async def setup(client):
    await client.add_cog(AppCommands(client))