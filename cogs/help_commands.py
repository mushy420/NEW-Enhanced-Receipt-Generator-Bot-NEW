import discord
from discord import app_commands
from discord.ext import commands
import logging
from typing import Optional

# Update import to use relative path
from ..config import EMBED_COLOR, PREFIX

class HelpCog(commands.Cog):
    """Cog for handling help commands."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.logger = logging.getLogger('help_commands')
        self._original_help_command = bot.help_command
        bot.help_command = None  # Remove the default help command
    
    def cog_unload(self):
        """Restore the original help command when the cog is unloaded."""
        self.bot.help_command = self._original_help_command
    
    @commands.Cog.listener()
    async def on_ready(self):
        """Log when the cog is loaded."""
        self.logger.info("Help Commands cog is ready")
    
    @app_commands.command(name="help", description="Shows help information about all commands")
    async def help_slash(self, interaction: discord.Interaction):
        """Show help information about commands."""
        await self._send_general_help(interaction)
    
    async def _send_general_help(self, interaction: discord.Interaction):
        """Send general help information."""
        embed = discord.Embed(
            title="Enhanced Receipt Generator Help",
            description="Here are the available commands:",
            color=discord.Color(EMBED_COLOR)
        )
        
        # Get all slash commands
        app_commands_list = self.bot.tree.get_commands()
        
        # Filter out admin commands for non-admins
        if not interaction.guild or not interaction.user.guild_permissions.administrator:
            app_commands_list = [cmd for cmd in app_commands_list if cmd.name != "admin"]
        
        # Sort commands by name
        app_commands_list.sort(key=lambda x: x.name)
        
        # Add slash commands to embed
        for cmd in app_commands_list:
            embed.add_field(
                name=f"/{cmd.name}",
                value=cmd.description or "No description provided",
                inline=False
            )
        
        # Add note about prefix commands
        embed.add_field(
            name="Note",
            value=f"Legacy prefix commands with `{PREFIX}` are deprecated and will be removed in a future update. Please use slash commands instead.",
            inline=False
        )
        
        # Add receipt command usage
        embed.add_field(
            name="Receipt Generator Usage",
            value="1. Use `/receipt` to start the generator\n"
                  "2. Select a store from the dropdown menu\n"
                  "3. Fill in the product details\n"
                  "4. Fill in your personal information\n"
                  "5. Review all details and generate your receipt\n"
                  "6. Your receipt will be sent to you",
            inline=False
        )
        
        # Add footer
        embed.set_footer(text="Enhanced Receipt Generator")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        self.logger.info(f"Help requested by {interaction.user.id}")
    
    @commands.command(name="help", hidden=True)
    async def help_legacy(self, ctx):
        """Legacy help command with prefix, hidden from help."""
        embed = discord.Embed(
            title="Command Deprecated",
            description="⚠️ The prefix command is deprecated. Please use the slash command `/help` instead.",
            color=discord.Color(EMBED_COLOR)
        )
        await ctx.send(embed=embed)

async def setup(bot: commands.Bot):
    """Add the cog to the bot."""
    await bot.add_cog(HelpCog(bot))
