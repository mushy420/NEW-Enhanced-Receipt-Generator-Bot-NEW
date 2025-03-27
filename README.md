# HEADS UP

This has been pushed to a website currently apple is the only good option

https://instantreceipt.netlify.app


# Discord Receipt Generator Bot

<div align="center">
  <br>
  <b>Generate realistic receipt images for various popular retailers</b>
  <br>
  <br>
</div>

A powerful Discord bot designed to generate high-quality, realistic-looking receipts for various popular stores. Perfect for educational purposes and digital organization.

## 📋 Features

- **Multiple Store Support**: Create receipts for Amazon, Apple, Best Buy, Walmart, GOAT, StockX, Louis Vuitton, and more
- **Interactive UI**: User-friendly Discord modals for inputting receipt information
- **Realistic Designs**: High-quality receipt templates that closely mimic real store receipts
- **Customization**: Control over product details, pricing, shipping information, and more
- **Instant Delivery**: Receipts delivered directly to users via Discord
- **Daily Limits**: Built-in request limiting to prevent abuse
- **Admin Controls**: Special commands for server administrators
- **Detailed Help System**: Comprehensive command documentation

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- Discord Bot Token ([Discord Developer Portal](https://discord.com/developers/applications))
- Required Python packages (listed in requirements.txt)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/discord-receipt-generator.git
   cd discord-receipt-generator
   ```

2. **Set up a virtual environment (recommended)**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure the bot**
   - Create a `.env` file in the project root with the following:
   ```
   BOT_TOKEN=your_discord_bot_token_here
   ADMIN_ROLE_ID=your_admin_role_id_here
   ```

5. **Run the bot**
   ```bash
   python bot.py
   ```

### Discord Bot Setup

1. Create a new application at the [Discord Developer Portal](https://discord.com/developers/applications)
2. Navigate to the Bot section and create a bot
3. Enable the following Privileged Gateway Intents:
   - Presence Intent
   - Server Members Intent
   - Message Content Intent
4. Copy your bot token and add it to the `.env` file
5. Generate an OAuth2 URL with the following permissions:
   - `applications.commands` (for slash commands)
   - `bot` with permissions:
     - Send Messages
     - Embed Links
     - Attach Files
     - Use Slash Commands
6. Invite the bot to your server using the generated URL

## 📝 Usage

### Commands

- `/receipt` - Start the receipt generation process
- `/help` - View general help information
- `/help [command]` - View detailed help for a specific command
- `/admin sync` - Sync slash commands (admin only)
- `/admin status` - View bot status information (admin only)
- `/admin restart` - Restart the bot (admin only)

### Receipt Generation

1. Use the `/receipt` command to start the generator
2. Select a store from the dropdown menu
3. Fill in basic product information (name, price, etc.)
4. Add shipping details and customer information
5. Receive your generated receipt as an image

## 📁 Project Structure

```
discord-receipt-generator/
├── assets/              # Static assets like fonts and templates
│   ├── fonts/           # Font files for receipt generation
│   └── templates/       # Receipt template images
├── cogs/                # Command modules
│   ├── admin_commands.py       # Admin-only commands
│   ├── help_commands.py        # Help system commands
│   └── receipt_commands.py     # Receipt generation commands
├── core/                # Core functionality
│   ├── config.py               # Configuration settings
│   └── receipt_generator.py    # Receipt image generation logic
├── ui/                  # User interface components
│   ├── receipt_modals.py       # Modal forms for receipt information
│   └── receipt_views.py        # Views and components for interaction
├── utils/               # Utility modules
│   ├── logging_setup.py        # Logging configuration
│   └── validators.py           # Input validation helpers
├── .env                 # Environment variables (not tracked by git)
├── .env.example         # Example environment file
├── .gitignore           # Git ignore file
├── bot.py               # Main bot file
├── README.md            # This documentation
└── requirements.txt     # Python dependencies
```

## 🛠️ Customization

### Adding New Stores

To add a new store template:

1. Add the store information to `core/config.py` in the `STORES` dictionary:
   ```python
   "your_store_id": {
       "name": "Your Store Name",
       "logo_url": "https://example.com/logo.png",
       "template_path": "templates/your_store_receipt.png",
       "color": 0xHEXCOLOR,  # Hex color code
   },
   ```

2. Create a generator method in `core/receipt_generator.py` named `_generate_your_store_id_receipt`

3. Add any store-specific modal classes in `ui/receipt_modals.py` if needed

### Modifying Templates

Edit the receipt generation methods in `core/receipt_generator.py` to change the appearance and layout of each store's receipt.

## 📊 Technical Details

- Built with [discord.py](https://github.com/Rapptz/discord.py) v2.0+
- Uses [Pillow](https://python-pillow.org/) for image manipulation
- Implements the Discord slash commands API
- Uses modal forms for data input
- Stores configuration in environment variables

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Disclaimer

This bot is designed for educational purposes only. The receipts generated should not be used for fraudulent activities, returns, or any illegal purposes. The developers are not responsible for any misuse of this software.

## 🙏 Acknowledgements

- [discord.py](https://github.com/Rapptz/discord.py) for the Discord API wrapper
- [Pillow](https://python-pillow.org/) for image processing capabilities
- All contributors to the project
mushy420 on github

I will only be updating the website and this github repository has been discontinued. Please visit the website for free usage of this.
---

<div align="center">
  Made with ❤️ for the Discord community
</div>
