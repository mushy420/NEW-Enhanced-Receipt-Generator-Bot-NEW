# Enhanced Receipt Generator Discord Bot

A feature-rich Discord bot for generating realistic-looking receipts for various popular stores.

## Features

- Interactive receipt generation via slash commands
- Support for multiple popular stores (Amazon, Apple, Best Buy, Walmart, GOAT, StockX, Louis Vuitton)
- Customizable receipt details through intuitive forms
- High-quality receipt images sent via direct messages
- Comprehensive error handling and user guidance
- Admin commands for bot management
- Detailed help system

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- A Discord bot token
- Required Python packages (see requirements.txt)

### Installation

1. **Clone the repository:**

```bash
git clone https://github.com/yourusername/receipt-generator-bot.git
cd receipt-generator-bot
```

2. **Install dependencies:**

```bash
pip install -r requirements.txt
```

3. **Configure the bot:**

- Copy `.env.example` to `.env` and fill in your Discord bot token:

```bash
cp .env.example .env
```

- Edit the `.env` file with your details:

```
BOT_TOKEN=your_discord_bot_token_here
ADMIN_ROLE_ID=your_admin_role_id_here
```

4. **Create required directories:**

```bash
mkdir -p templates fonts
```

5. **Run the bot:**

```bash
python main.py
```

### Discord Bot Setup

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application and set up a bot
3. Enable the "Message Content Intent" under the Bot settings
4. Invite the bot to your server with the appropriate permissions:
   - `applications.commands` (for slash commands)
   - `bot` with permissions:
     - Send Messages
     - Embed Links
     - Attach Files
     - Use Slash Commands

## Usage

### Commands

- `/receipt` - Start the receipt generation process
- `/help` - Show help information
- `/help [command]` - Show detailed help for a specific command
- `/admin sync` - Sync slash commands (admin only)
- `/admin restart` - Restart the bot (admin only)
- `/admin status` - Show bot status information (admin only)

### Receipt Generation Process

1. Use `/receipt` to start the generator
2. Select a store from the dropdown menu
3. Fill in the product details in the form
4. Fill in customer information in the next form
5. Review all details and make any necessary edits
6. Click "Generate Receipt" to create and receive your receipt

## Customization

### Adding New Stores

To add a new store, edit the `config.py` file and add your store to the `STORES` dictionary:

```python
"yourstore": {
    "name": "Your Store",
    "logo_url": "https://example.com/logo.png",
    "template_path": "templates/yourstore_receipt.png",
    "color": 0xFF0000,  # Hex color code
},
```

Then create a corresponding modal class in `cogs/receipt_generator.py` and a template generator method in `receipt_generator.py`.

### Customizing Receipt Templates

Edit the appropriate template generator method in `receipt_generator.py` to modify the layout and appearance of each store's receipt.

## Troubleshooting

### Slash Commands Not Appearing

If slash commands don't appear:

1. Make sure you've invited the bot with the `applications.commands` scope
2. Try running `/admin sync` if you have admin permissions
3. Wait up to an hour for Discord to cache the commands globally

### Bot Not Responding

1. Check your `.env` file has the correct bot token
2. Make sure all required dependencies are installed
3. Check the bot's permissions in your Discord server
4. Look at the console output for any error messages

### DM Not Received

1. Make sure your DMs are open for the server (Server Privacy Settings)
2. Check if the bot has permission to send messages to you

## License

This project is licensed under the Apache 2.0 License - see the LICENSE file for details.

## Acknowledgements

- [discord.py](https://github.com/Rapptz/discord.py) for the Discord API wrapper
- [Pillow](https://python-pillow.org/) for image manipulation
