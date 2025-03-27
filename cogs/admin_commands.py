import discord
from discord import app_commands
from discord.ext import commands
import logging
import os
import sys
from typing import List, Optional

from config import ADMIN_ROLE_ID, EMBED_COLOR, ERROR_COLOR

# Setup logging
logger = logging.getLogger('admin_commands')

def is_admin(interaction: discord.Interaction) -> bool:
    """Check if user has admin role or is server owner."""
    if not interaction.guild:
        return False
    
    # Server owner is always admin
    if interaction.guild.owner_id == interaction.user.id:
        return True
    
    # Check for admin role
    if ADMIN_ROLE_ID:
        role = interaction.guild.get_role(ADMIN_ROLE_ID)
        if role and role in interaction.user.roles:
            return True
    
    # Check for administrator permission
    return interaction.user.guild_permissions.administrator


class AdminCog(commands.Cog):
    """Cog for admin commands."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.logger = logging.getLogger('admin_commands')
    
    @commands.Cog.listener()
    async def on_ready(self):
        """Log when the cog is loaded."""
        self.logger.info("Admin Commands cog is ready")
    
    @app_commands.command(name="admin", description="Admin commands for bot management")
    @app_commands.describe(
        action="Action to perform: sync, restart, or status",
        target="Optional parameter depending on the action"
    )
    async def admin(self, interaction: discord.Interaction, action: str, target: Optional[str] = None):
        """Admin commands for bot management."""
        # Check if user is admin
        if not is_admin(interaction):
            embed = discord.Embed(
                title="Permission Denied",
                description="❌ You do not have permission to use admin commands.",
                color=discord.Color(ERROR_COLOR)
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Process admin command
        action = action.lower()
        
        if action == "sync":
            await self._sync_commands(interaction, target)
        elif action == "restart":
            await self._restart_bot(interaction)
        elif action == "status":
            await self._show_status(interaction)
        else:
            embed = discord.Embed(
                title="Invalid Action",
                description="❌ Invalid action. Available actions: `sync`, `restart`, `status`.",
                color=discord.Color(ERROR_COLOR)
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    async def _sync_commands(self, interaction: discord.Interaction, guild_id: Optional[str] = None):
        """Sync application commands."""
        try:
            # Defer the response as syncing might take time
            await interaction.response.defer(ephemeral=True, thinking=True)
            
            # Sync commands globally or to a specific guild
            if guild_id:
                try:
                    guild_id_int = int(guild_id)
                    guild = self.bot.get_guild(guild_id_int)
                    if not guild:
                        await interaction.followup.send(f"❌ Could not find guild with ID {guild_id}", ephemeral=True)
                        return
                    
                    synced = await self.bot.tree.sync(guild=guild)
                    embed = discord.Embed(
                        title="Commands Synced",
                        description=f"✅ Successfully synced {len(synced)} command(s) to guild {guild.name}.",
                        color=discord.Color(EMBED_COLOR)
                    )
                    self.logger.info(f"Commands synced to guild {guild.name} ({guild.id}) by {interaction.user.id}: {len(synced)} commands")
                except ValueError:
                    await interaction.followup.send("❌ Invalid guild ID. Please provide a valid integer ID.", ephemeral=True)
                    return
            else:
                # Sync globally
                synced = await self.bot.tree.sync()
                embed = discord.Embed(
                    title="Commands Synced",
                    description=f"✅ Successfully synced {len(synced)} command(s) globally.",
                    color=discord.Color(EMBED_COLOR)
                )
                self.logger.info(f"Commands synced globally by {interaction.user.id}: {len(synced)} commands")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            self.logger.error(f"Error syncing commands: {e}", exc_info=True)
            embed = discord.Embed(
                title="Sync Failed",
                description=f"❌ Failed to sync commands: {str(e)}",
                color=discord.Color(ERROR_COLOR)
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
    
    async def _restart_bot(self, interaction: discord.Interaction):
        """Restart the bot."""
        embed = discord.Embed(
            title="Restarting Bot",
            description="🔄 Bot is restarting...",
            color=discord.Color(EMBED_COLOR)
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
        self.logger.warning(f"Bot restart initiated by {interaction.user.id}")
        
        # We're using sys.exit(0) to indicate a clean exit for restart
        # This should be caught by the process manager (if any) to restart the bot
        await self.bot.close()
        sys.exit(0)
    
    async def _show_status(self, interaction: discord.Interaction):
        """Show bot status information."""
        # Collect status information
        uptime = discord.utils.utcnow() - self.bot.user.created_at
        days, remainder = divmod(int(uptime.total_seconds()), 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        uptime_str = f"{days}d {hours}h {minutes}m {seconds}s"
        
        guild_count = len(self.bot.guilds)
        member_count = sum(g.member_count for g in self.bot.guilds)
        
        # Get memory usage
        import psutil
        process = psutil.Process(os.getpid())
        memory_usage = process.memory_info().rss / 1024 / 1024  # Convert to MB
        
        # Create embed
        embed = discord.Embed(
            title="Bot Status",
            description="ℹ️ Current status information",
            color=discord.Color(EMBED_COLOR)
        )
        
        embed.add_field(name="Bot Version", value="1.0.0", inline=True)
        embed.add_field(name="Python Version", value=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}", inline=True)
        embed.add_field(name="Discord.py Version", value=discord.__version__, inline=True)
        
        embed.add_field(name="Uptime", value=uptime_str, inline=True)
        embed.add_field(name="Memory Usage", value=f"{memory_usage:.2f} MB", inline=True)
        embed.add_field(name="Latency", value=f"{round(self.bot.latency * 1000)}ms", inline=True)
        
        embed.add_field(name="Servers", value=str(guild_count), inline=True)
        embed.add_field(name="Members", value=str(member_count), inline=True)
        embed.add_field(name="Commands", value=str(len(self.bot.tree.get_commands())), inline=True)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        self.logger.info(f"Status requested by {interaction.user.id}")


async def setup(bot: commands.Bot):
    """Add the cog to the bot."""
    await bot.add_cog(AdminCog(bot))
