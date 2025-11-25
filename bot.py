import discord
from discord import app_commands
from discord.ext import commands
import os
from aiohttp import web
import asyncio
import aiohttp_cors

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # Required to assign roles
bot = commands.Bot(command_prefix="!", intents=intents)

# Configuration
PROFILE_WEBSITE = "https://meghaboi.github.io/discord-web-app-page/link-updated.html"
CALLBACK_PORT = 8080  # Port for the web server

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    try:
        guild = discord.Object(id=1440188275909333148)
        bot.tree.copy_global_to(guild=guild)
        synced = await bot.tree.sync(guild=guild)
        print(f"Synced {len(synced)} command(s) to guild {guild.id}")
    except Exception as e:
        print(f"Error syncing commands: {e}")

@bot.tree.command(name="stats", description="View your VR Cricket stats or another user's stats")
@app_commands.describe(user="The user whose stats you want to see (optional)")
async def stats(interaction: discord.Interaction, user: discord.User = None):
    """Display VR Cricket stats for a user"""
    target_user = user if user else interaction.user

    embed = discord.Embed(
        title=f"🏏 VR Cricket Stats for {target_user.display_name}",
        description=f"Profile statistics for {target_user.mention}",
        color=discord.Color.blue()
    )

    embed.set_thumbnail(url=target_user.display_avatar.url)

    embed.add_field(
        name="📊 Player Info",
        value=f"**Discord ID:** `{target_user.id}`\n**Username:** {target_user.name}\n**Display Name:** {target_user.display_name}",
        inline=False
    )

    embed.add_field(
        name="🎮 Game Stats",
        value="*Stats will be available once API integration is complete*",
        inline=False
    )

    embed.add_field(
        name="🏆 Recent Achievements",
        value="*Coming soon...*",
        inline=False
    )

    embed.set_footer(text="VR Cricket Stats • Data synced with your profile")

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="post-link-message", description="Post the profile linking message in this channel")
@app_commands.describe(role="The role to give users after they link (optional)")
@app_commands.checks.has_permissions(administrator=True)
async def post_link_message(interaction: discord.Interaction, role: discord.Role = None):
    """Posts an embed message with a button for users to connect their profile"""
    
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
        value="Click the button below to get your personal linking URL!",
        inline=False
    )
    
    if role:
        embed.add_field(
            name="🎁 Reward",
            value=f"You'll receive the {role.mention} role after linking!",
            inline=False
        )
    
    embed.set_footer(text="VR Cricket • Your data is secure")
    embed.set_thumbnail(url="https://cdn.discordapp.com/embed/avatars/0.png")
    
    # Store role_id in the view if role is provided
    view = LinkButtonView(role_id=role.id if role else None)
    
    await interaction.response.send_message(
        embed=embed,
        view=view
    )

class LinkButtonView(discord.ui.View):
    def __init__(self, role_id=None):
        super().__init__(timeout=None)
        self.role_id = role_id
    
    @discord.ui.button(label="Link Your Profile", style=discord.ButtonStyle.primary, emoji="🔗", custom_id="link_profile_button")
    async def link_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = interaction.user
        user_id = user.id
        username = user.name
        display_name = user.display_name
        avatar_url = user.display_avatar.url
        guild_id = interaction.guild_id
        
        # Create personalized link with user data, guild info, and role_id
        personal_link = f"{PROFILE_WEBSITE}?user_id={user_id}&username={username}&display_name={display_name}&avatar={avatar_url}&guild_id={guild_id}"
        
        if self.role_id:
            personal_link += f"&role_id={self.role_id}"
        
        response_embed = discord.Embed(
            title="🔗 Your Personal Link",
            description=f"Hey {user.mention}! Click the button below to link your profile.",
            color=discord.Color.green()
        )
        
        response_embed.set_thumbnail(url=avatar_url)
        response_embed.set_footer(text="This link is unique to you • Click it to complete linking")
        
        personal_view = discord.ui.View()
        personal_view.add_item(
            discord.ui.Button(
                label="Complete Linking",
                style=discord.ButtonStyle.link,
                url=personal_link,
                emoji="✅"
            )
        )
        
        await interaction.response.send_message(
            embed=response_embed,
            view=personal_view,
            ephemeral=True
        )

# Web server to handle callbacks from your website
async def handle_verification(request):
    """Handle verification callback from your website"""
    try:
        data = await request.json()
        user_id = int(data.get('user_id'))
        guild_id = int(data.get('guild_id'))
        role_id = data.get('role_id')  # Can be None
        success = data.get('success', False)
        
        if not success:
            return web.json_response({'status': 'error', 'message': 'Verification failed'}, status=400)
        
        # Get the guild and member
        guild = bot.get_guild(guild_id)
        if not guild:
            return web.json_response({'status': 'error', 'message': 'Guild not found'}, status=404)
        
        member = guild.get_member(user_id)
        if not member:
            return web.json_response({'status': 'error', 'message': 'Member not found'}, status=404)
        
        # Assign role only if role_id is provided
        role_assigned = False
        role_name = None

        print(f"[DEBUG] Received role_id: {role_id} (type: {type(role_id)})")

        if role_id and role_id != "null" and role_id != "undefined":
            try:
                role_id_int = int(role_id)
                verified_role = guild.get_role(role_id_int)

                print(f"[DEBUG] Looking for role with ID: {role_id_int}")
                print(f"[DEBUG] Found role: {verified_role}")

                if verified_role:
                    await member.add_roles(verified_role, reason="Profile linked successfully")
                    role_assigned = True
                    role_name = verified_role.name
                    print(f"✅ Assigned {role_name} role to {member.name}")
                else:
                    print(f"❌ Role with ID {role_id_int} not found in guild {guild.name}")
                    print(f"[DEBUG] Available roles: {[f'{r.name} (ID: {r.id})' for r in guild.roles]}")
            except ValueError as e:
                print(f"❌ Error converting role_id to int: {e}")
            except Exception as e:
                print(f"❌ Error assigning role: {e}")
        else:
            print(f"[DEBUG] No role_id provided or invalid value")
        
        # Send a DM to the user
        try:
            dm_embed = discord.Embed(
                title="✅ Profile Linked Successfully!",
                description=f"Your profile has been linked successfully!",
                color=discord.Color.green()
            )
            
            if role_assigned:
                dm_embed.add_field(
                    name="🎁 Role Assigned",
                    value=f"You've been given the **{role_name}** role!",
                    inline=False
                )
            
            dm_embed.add_field(
                name="What's Next?",
                value="You can now access exclusive features and tournaments!",
                inline=False
            )
            
            await member.send(embed=dm_embed)
        except discord.Forbidden:
            print(f"Could not send DM to {member.name}")
        
        return web.json_response({
            'status': 'success',
            'message': 'Profile linked successfully',
            'role_assigned': role_assigned,
            'role_name': role_name
        })
        
    except Exception as e:
        print(f"Error handling verification: {e}")
        return web.json_response({'status': 'error', 'message': str(e)}, status=500)

async def start_webserver():
    """Start the web server for callbacks"""
    app = web.Application()
    app.router.add_post('/verify', handle_verification)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', CALLBACK_PORT)
    await site.start()
    print(f"Web server started on port {CALLBACK_PORT}")

# Error handling
@post_link_message.error
async def post_link_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.errors.MissingPermissions):
        await interaction.response.send_message(
            "❌ You need Administrator permissions to use this command!",
            ephemeral=True
        )

# Run the bot
async def main():
    async with bot:
        # Start web server
        await start_webserver()
        # Start bot
        await bot.start(os.getenv("DISCORD_BOT_TOKEN"))

if __name__ == "__main__":
    BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
    if not BOT_TOKEN:
        print("Error: DISCORD_BOT_TOKEN not found in environment variables!")
        print("Set it using: $env:DISCORD_BOT_TOKEN='your_token_here'")
    else:
        asyncio.run(main())