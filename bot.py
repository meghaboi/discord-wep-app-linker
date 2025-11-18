import discord
from discord import app_commands
from discord.ext import commands
import os

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Your OAuth2 URL - Replace CLIENT_ID and REDIRECT_URI with your actual values
CLIENT_ID = "1440189661929672714"
REDIRECT_URI = "http://localhost:3000/auth/discord/callback"  # Change for production
OAUTH_URL = f"https://discord.com/api/oauth2/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&scope=identify"

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    try:
        # Replace with your server ID
        guild = discord.Object(id=1440188275909333148)
        bot.tree.copy_global_to(guild=guild)
        synced = await bot.tree.sync(guild=guild)
        print(f"Synced {len(synced)} command(s) to server")
    except Exception as e:
        print(f"Error syncing commands: {e}")

@bot.tree.command(name="post-link-message", description="Post the profile linking message in this channel")
@app_commands.checks.has_permissions(administrator=True)  # Only admins can use this
async def post_link_message(interaction: discord.Interaction):
    """Posts an embed message with a link button for users to connect their profile"""
    
    # Create the embed
    embed = discord.Embed(
        title="🏏 Link Your VR Cricket Profile",
        description="Connect your Discord account with your VR Cricket game profile to unlock exclusive features!",
        color=discord.Color.purple()
    )
    
    embed.add_field(
        name="📋 Why Link?",
        value="• See your stats on Discord\n• Get exclusive roles\n• Join tournaments\n• Access leaderboards",
        inline=False
    )
    
    embed.add_field(
        name="🔗 How to Link",
        value="1. Click the button below\n2. Authorize the connection\n3. Your profile will be linked instantly!",
        inline=False
    )
    
    embed.set_footer(text="VR Cricket • Secure linking via Discord OAuth2")
    embed.set_thumbnail(url="https://cdn.discordapp.com/embed/avatars/0.png")  # Replace with your game logo URL
    
    # Create the button view
    view = LinkButton()
    
    # Send the message
    await interaction.response.send_message(
        embed=embed,
        view=view
    )

class LinkButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)  # Button never expires
        
        # Add the link button
        button = discord.ui.Button(
            label="Link Your Profile",
            style=discord.ButtonStyle.link,
            url=OAUTH_URL,
            emoji="🔗"
        )
        self.add_item(button)

# Error handling for permission issues
@post_link_message.error
async def post_link_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.errors.MissingPermissions):
        await interaction.response.send_message(
            "❌ You need Administrator permissions to use this command!",
            ephemeral=True
        )

# Run the bot
if __name__ == "__main__":
    BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")  # Store token in environment variable
    if not BOT_TOKEN:
        print("Error: DISCORD_BOT_TOKEN not found in environment variables!")
        print("Set it using: export DISCORD_BOT_TOKEN='your_token_here'")
    else:
        bot.run(BOT_TOKEN)