import discord
from discord import app_commands
from discord.ext import commands, tasks
from utilities import *

class DailyReminder(commands.Cog):
    def __init__(self, client):
        self.client = client
    
    @commands.Cog.listener()
    async def on_ready(self):
        await self.client.tree.sync()
        print(f'{__name__} loaded successfully!')
    
    @app_commands.command(name="dailyreminder", description="Sends a test message.")
    @app_commands.describe(mode="Mode")
    @app_commands.choices(mode=[
        app_commands.Choice(name="Morning reminder", value="morning_reminder"),
        app_commands.Choice(name="Evening reminder", value="evening_reminder")
    ])
    async def daily_reminder(self, interaction: discord.Interaction, mode: app_commands.Choice[str]):
        user_id = interaction.user.id

        # Make sure this player exists
        try:
            user = await get_userinfo(user_id)
        except:
            await reply(interaction, "You have not waffled yet.")
            return
        
        user[mode.value] = not bool(user[mode.value])

        await save_userinfo(user_id, user)

        message = f'{mode.value} is now: {user[mode.value]}'
        
        await reply(self.client, interaction, message)


async def setup(client):
    await client.add_cog(DailyReminder(client))