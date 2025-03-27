import discord
from discord import app_commands
from discord.ext import commands
import logging
from typing import Optional

from config import EMBED_COLOR, PREFIX

# Setup logging
logger = logging.getLogger('help_commands')

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
    
    @app_commands.command(name="help", description="Shows help information about commands")
    @app_commands.describe(command="Get help for a specific command")
    async def help_slash(self, interaction: discord.Interaction, command: Optional[str] = None):
        """Show help information about commands."""
        if command:
            await self._send_command_help(interaction, command)
        else:
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
        embed.set_footer(text="For detailed help on a specific command, use /help [command]")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        self.logger.info(f"General help requested by {interaction.user.id}")
    
    async def _send_command_help(self, interaction: discord.Interaction, command_name: str):
        """Send help information for a specific command."""
        # Remove leading slash or prefix if present
        command_name = command_name.lstrip('/')
        command_name = command_name.lstrip(PREFIX)
        
        # Look for the command in app commands
        app_cmd = None
        for cmd in self.bot.tree.get_commands():
            if cmd.name == command_name:
                app_cmd = cmd
                break
        
        if app_cmd:
            # Create embed for app command
            embed = discord.Embed(
                title=f"Command: /{app_cmd.name}",
                description=app_cmd.description or "No description provided",
                color=discord.Color(EMBED_COLOR)
            )
            
            # Add parameters if any
            if hasattr(app_cmd, 'parameters') and app_cmd.parameters:
                params_text = ""
                for param in app_cmd.parameters:
                    param_desc = param.description or "No description"
                    required = "Required" if param.required else "Optional"
                    params_text += f"**{param.name}** ({required}): {param_desc}\n"
                
                if params_text:
                    embed.add_field(name="Parameters", value=params_text, inline=False)
            
            # Add usage example
            usage = f"/{app_cmd.name}"
            if hasattr(app_cmd, 'parameters') and app_cmd.parameters:
                for param in app_cmd.parameters:
                    if param.required:
                        usage += f" <{param.name}>"
                    else:
                        usage += f" [{param.name}]"
            
            embed.add_field(name="Usage", value=f"`{usage}`", inline=False)
            
            # Add receipt specific instructions
            if command_name == "receipt":
                embed.add_field(
                    name="How to use the Receipt Generator",
                    value="1. Use `/receipt` to start the generator\n"
                          "2. Select a store from the dropdown menu\n"
                          "3. Fill in the product details in the modal\n"
                          "4. The receipt will be generated and sent to you\n\n"
                          "Note: All receipts are for educational purposes only!",
                    inline=False
                )
                
                # Add available stores
                from config import STORES
                stores_list = ", ".join([store_info["name"] for store_id, store_info in STORES.items()])
                embed.add_field(
                    name="Available Stores",
                    value=stores_list,
                    inline=False
                )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            self.logger.info(f"Help for /{command_name} requested by {interaction.user.id}")
            return
        
        # If we get here, command was not found
        embed = discord.Embed(
            title="Command Not Found",
            description=f"The command `{command_name}` was not found. Use `/help` to see available commands.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        self.logger.warning(f"Help requested for unknown command '{command_name}' by {interaction.user.id}")
    
    @commands.command(name="help", hidden=True)
    async def help_legacy(self, ctx, command: str = None):
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
