# SV Brand Assistant Discord Bot

A powerful Discord bot powered by [AutoAgent](https://github.com/HKUDS/AutoAgent) that helps create branded content with multiple specialized AI agents.

## 🚀 Features

- **🎨 Image Agent**: Generate branded image concepts and detailed prompts
- **📄 Document Agent**: Create professional branded documents
- **🏢 Brand Agent**: Get strategic brand guidance and recommendations  
- **🎬 Video Agent**: Develop video content strategies and scripts
- **🤖 AutoAgent Integration**: Fully-automated, zero-code LLM agent framework
- **🎯 Brand Consistency**: All agents maintain your brand guidelines and voice

## 🛠️ Setup Instructions

### Prerequisites

- Python 3.8 or higher
- Discord Bot Token
- AI Model API Key (Gemini, OpenAI, Anthropic, etc.)

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment Configuration

Copy `env_template.txt` to `.env` and configure your settings:

```bash
cp env_template.txt .env
```

Edit `.env` with your credentials:

```env
# Discord Bot Configuration
DISCORD_BOT_TOKEN=your_discord_bot_token_here

# AI Model API Keys (choose one or more)
GEMINI_API_KEY=your_gemini_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# AutoAgent Configuration
COMPLETION_MODEL=gemini/gemini-2.0-flash-exp

# Brand Configuration
BRAND_NAME=Your Brand Name
BRAND_PRIMARY_COLOR=#1a1a1a
BRAND_SECONDARY_COLOR=#ffffff
BRAND_ACCENT_COLOR=#ff6b6b
```

### 3. Discord Bot Setup

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application
3. Go to "Bot" section and create a bot
4. Copy the bot token to your `.env` file
5. Enable the following bot permissions:
   - Send Messages
   - Use Slash Commands
   - Embed Links
   - Attach Files
   - Read Message History

### 4. Invite Bot to Server

Generate an invite link with the required permissions:
```
https://discord.com/api/oauth2/authorize?client_id=YOUR_BOT_CLIENT_ID&permissions=274877976576&scope=bot%20applications.commands
```

### 5. Run the Bot

```bash
python main.py
```

## 🎯 Usage

### Available Commands

#### `/image` - Generate Image Concepts
Generate branded image concepts and detailed prompts.
```
/image prompt:"modern logo design" style:"minimalist"
```

#### `/document` - Create Documents
Create branded documents with AI assistance.
```
/document document_type:"proposal" topic:"new marketing campaign" length:"long"
```

#### `/brand` - Brand Guidance
Get strategic brand guidance and recommendations.
```
/brand query:"What colors should I use for our social media posts?"
```

#### `/video` - Video Strategy
Generate video content strategies and scripts.
```
/video prompt:"product showcase" duration:30 style:"cinematic"
```

#### `/help` - Show Help
Display all available commands and their usage.

## 🤖 AutoAgent Integration

This bot leverages the powerful [AutoAgent framework](https://github.com/HKUDS/AutoAgent) to provide:

- **Fully Automated**: Zero-code agent creation and management
- **Multiple LLM Support**: Works with various AI models (Gemini, OpenAI, Anthropic, etc.)
- **Specialized Agents**: Each agent is optimized for specific creative tasks
- **Brand Consistency**: All agents maintain your brand guidelines

### Supported AI Models

- **Gemini**: `gemini/gemini-2.0-flash-exp`, `gemini/gemini-2.5-nano-banana`
- **OpenAI**: `gpt-4o`, `gpt-4-turbo`
- **Anthropic**: `claude-3-5-sonnet-20241022`
- **And many more via LiteLLM**

## 🎨 Brand Customization

### Brand Configuration

Customize your brand settings in the `.env` file:

```env
BRAND_NAME=Your Brand Name
BRAND_PRIMARY_COLOR=#1a1a1a
BRAND_SECONDARY_COLOR=#ffffff
BRAND_ACCENT_COLOR=#ff6b6b
```

### Brand Guidelines

Each agent is pre-configured with brand context:
- **Style Guidelines**: Modern, clean, professional aesthetic
- **Voice & Tone**: Professional yet approachable, confident, and creative
- **Consistency**: All outputs maintain brand alignment

## 📁 Project Structure

```
SV Discord Bot/
├── main.py                 # Main bot file with AutoAgent integration
├── requirements.txt        # Python dependencies
├── env_template.txt        # Environment variables template
├── README.md              # This file
└── output/                # Generated content output (created automatically)
    ├── documents/
    └── videos/
```

## 🔧 Advanced Configuration

### Custom AI Models

To use different AI models, update the `COMPLETION_MODEL` in your `.env`:

```env
# For OpenAI
COMPLETION_MODEL=gpt-4o

# For Anthropic  
COMPLETION_MODEL=claude-3-5-sonnet-20241022

# For Mistral
COMPLETION_MODEL=mistral/mistral-large-2407
```

### Debug Mode

Enable debug mode for detailed logs:

```env
DEBUG=True
```

### Brand Voice Customization

Modify the brand context in `main.py` to customize how agents respond:

```python
brand_context = f"""
You are an AI assistant for {self.brand_config['name']}, a creative brand.

Brand Guidelines:
- Style: {self.brand_config['style_guidelines']}
- Voice & Tone: {self.brand_config['voice_tone']}
- Always maintain brand consistency in all outputs
- Focus on high-quality, professional results
"""
```

## 🐛 Troubleshooting

### Common Issues

1. **Bot not responding**: Check if bot token is correct and bot is online
2. **API errors**: Verify your AI model API keys are valid
3. **Permission errors**: Ensure bot has required Discord permissions
4. **Import errors**: Make sure all dependencies are installed

### Logs

Check console output for detailed error messages and debugging information.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- [AutoAgent](https://github.com/HKUDS/AutoAgent) - The powerful LLM agent framework powering our bots
- [Discord.py](https://discordpy.readthedocs.io/) - Discord API wrapper for Python
- [LiteLLM](https://litellm.ai/) - Universal LLM API interface

---

**Made with ❤️ for creative brand teams**
