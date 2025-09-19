import discord
from discord.ext import commands
import asyncio
import logging
from typing import Dict, Any
import json
import os
from dotenv import load_dotenv
import tempfile
import io

# AI Libraries - using direct integrations with optional imports
try:
    import openai
except ImportError:
    openai = None
    
try:
    import anthropic
except ImportError:
    anthropic = None
    
try:
    import google.generativeai as genai
except ImportError:
    genai = None

# Knowledge management - simplified for Railway
try:
    from knowledge_manager_simple import SimpleKnowledgeManager as KnowledgeManager
except ImportError:
    from knowledge_manager import KnowledgeManager

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot configuration
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

class SVDiscordBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix='!sv ',
            intents=intents,
            description='SV Brand Assistant Bot - Your AI-powered creative companion with AutoAgent'
        )
        
        # Initialize brand configuration with safe color parsing
        def parse_color(color_str, default):
            try:
                if not color_str or color_str.strip() == '':
                    return int(default.replace('#', ''), 16)
                color_clean = color_str.replace('#', '').strip()
                if len(color_clean) == 6:
                    return int(color_clean, 16)
                else:
                    return int(default.replace('#', ''), 16)
            except (ValueError, AttributeError):
                return int(default.replace('#', ''), 16)
        
        self.brand_config = {
            'name': os.getenv('BRAND_NAME', 'STAFFVIRTUAL'),
            'primary_color': parse_color(os.getenv('BRAND_PRIMARY_COLOR'), '#1888FF'),
            'secondary_color': parse_color(os.getenv('BRAND_SECONDARY_COLOR'), '#F8F8EB'),
            'accent_color': parse_color(os.getenv('BRAND_ACCENT_COLOR'), '#004B8D'),
            'style_guidelines': 'Modern, clean, professional aesthetic with emphasis on clarity and impact',
            'voice_tone': 'Professional yet approachable, confident, and creative'
        }
        
        # Initialize AutoAgent instances for different specializations
        self.agents = self._initialize_agents()
        
        # Initialize knowledge manager
        self.knowledge_manager = KnowledgeManager()
    
    def _initialize_agents(self):
        """Initialize AI agents with direct API integrations"""
        # Initialize AI clients
        ai_clients = {}
        
        # Initialize Gemini if API key is available and library is installed
        gemini_key = os.getenv('GEMINI_API_KEY')
        if gemini_key and genai:
            try:
                genai.configure(api_key=gemini_key)
                ai_clients['gemini'] = genai.GenerativeModel('gemini-pro')
                logger.info("Gemini AI client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini: {e}")
        
        # Initialize OpenAI if API key is available and library is installed
        openai_key = os.getenv('OPENAI_API_KEY')
        if openai_key and openai:
            try:
                ai_clients['openai'] = openai.OpenAI(api_key=openai_key)
                logger.info("OpenAI client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI: {e}")
        
        # Initialize Anthropic if API key is available and library is installed
        anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        if anthropic_key and anthropic:
            try:
                ai_clients['anthropic'] = anthropic.Anthropic(api_key=anthropic_key)
                logger.info("Anthropic client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Anthropic: {e}")
        
        # Brand context that will be injected into all agents
        brand_context = f"""
        You are an AI assistant for {self.brand_config['name']}, a creative brand.
        
        Brand Guidelines:
        - Style: {self.brand_config['style_guidelines']}
        - Voice & Tone: {self.brand_config['voice_tone']}
        - Always maintain brand consistency in all outputs
        - Focus on high-quality, professional results
        """
        
        # Return the AI clients and brand context for use in commands
        return {
            'clients': ai_clients,
            'brand_context': brand_context,
            'image_prompt': brand_context + """
            You are an expert image generation specialist. Your role is to:
            1. Create compelling, branded visual content
            2. Ensure all images align with brand guidelines
            3. Provide detailed, creative prompts that capture the brand essence
            4. Consider composition, color theory, and visual hierarchy
            
            Always ask clarifying questions if the request is ambiguous.
            """,
            'document_prompt': brand_context + """
            You are a professional document creation specialist. Your role is to:
            1. Create well-structured, branded documents
            2. Ensure consistent formatting and style
            3. Use appropriate templates and layouts
            4. Maintain brand voice throughout all content
            5. Optimize for readability and professional presentation
            
            Support various document types: proposals, reports, presentations, marketing materials.
            """,
            'brand_prompt': brand_context + """
            You are a senior brand strategist and consultant. Your role is to:
            1. Provide strategic brand guidance and recommendations
            2. Ensure brand consistency across all touchpoints
            3. Offer creative direction and feedback
            4. Help with brand positioning and messaging
            5. Analyze brand alignment and suggest improvements
            
            Always consider the broader brand strategy when providing advice.
            """,
            'video_prompt': brand_context + """
            You are a video content creation specialist. Your role is to:
            1. Develop video concepts and scripts
            2. Provide direction for branded video content
            3. Ensure visual consistency with brand guidelines
            4. Optimize content for different platforms and audiences
            5. Create engaging, professional video narratives
            
            Focus on storytelling that aligns with brand values.
            """,
            'blog_prompt': brand_context + """
            You are a professional blog writer and content strategist. Your role is to:
            1. Create engaging, SEO-optimized blog posts
            2. Maintain brand voice and messaging consistency
            3. Structure content for readability and engagement
            4. Include relevant keywords and calls-to-action
            5. Optimize for search engines and social sharing
            
            Focus on creating valuable, informative content that establishes thought leadership.
            """,
            'social_prompt': brand_context + """
            You are a social media content specialist. Your role is to:
            1. Create platform-specific social media posts
            2. Optimize content for each platform's best practices
            3. Include relevant hashtags and engagement hooks
            4. Maintain consistent brand voice across platforms
            5. Create content that drives engagement and conversions
            
            Consider platform differences: LinkedIn (professional), Instagram (visual), Twitter (concise), etc.
            """,
            'calendar_prompt': brand_context + """
            You are a social media strategist and calendar planner. Your role is to:
            1. Create comprehensive social media content calendars
            2. Plan content themes and campaigns
            3. Balance promotional and educational content
            4. Consider seasonal trends and industry events
            5. Optimize posting schedules for maximum engagement
            
            Focus on strategic planning that supports business goals and audience engagement.
            """,
            'knowledge_prompt': brand_context + """
            You are a business intelligence assistant with deep knowledge about STAFFVIRTUAL. Your role is to:
            1. Answer questions about company services, processes, and policies
            2. Provide accurate information about business operations
            3. Help with internal knowledge and decision-making
            4. Maintain confidentiality and professional standards
            5. Direct users to appropriate resources when needed
            
            Always provide accurate, helpful information based on available company knowledge.
            """
        }
    
    async def _get_ai_response(self, prompt, agent_type='brand', use_knowledge=True):
        """Get AI response using available clients with knowledge base context"""
        try:
            # Get relevant context from knowledge base
            knowledge_context = ""
            if use_knowledge:
                knowledge_context = self.knowledge_manager.get_context_for_query(prompt)
                if knowledge_context and knowledge_context != "No specific information found in knowledge base.":
                    knowledge_context = f"\n\nRelevant Knowledge Base Information:\n{knowledge_context}\n"
            
            # Try Gemini first (preferred based on user preferences)
            if 'gemini' in self.agents['clients']:
                system_prompt = self.agents[f'{agent_type}_prompt']
                full_prompt = f"{system_prompt}{knowledge_context}\n\nUser Request: {prompt}"
                
                response = self.agents['clients']['gemini'].generate_content(full_prompt)
                return response.text
            
            # Fallback to OpenAI
            elif 'openai' in self.agents['clients']:
                system_prompt = self.agents[f'{agent_type}_prompt']
                
                response = self.agents['clients']['openai'].chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": system_prompt + knowledge_context},
                        {"role": "user", "content": prompt}
                    ]
                )
                return response.choices[0].message.content
            
            # Fallback to Anthropic
            elif 'anthropic' in self.agents['clients']:
                system_prompt = self.agents[f'{agent_type}_prompt']
                
                response = self.agents['clients']['anthropic'].messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=2000,
                    system=system_prompt + knowledge_context,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text
            
            else:
                return "❌ No AI service configured. Please add API keys to your .env file."
                
        except Exception as e:
            logger.error(f"AI response error: {e}")
            return f"❌ Error generating response: {str(e)}"
        
    async def setup_hook(self):
        """Called when the bot is starting up"""
        logger.info("Setting up SV Discord Bot...")
        
        # Sync slash commands
        try:
            synced = await self.tree.sync()
            logger.info(f"Synced {len(synced)} command(s)")
        except Exception as e:
            logger.error(f"Failed to sync commands: {e}")
    
    async def on_ready(self):
        """Called when the bot is ready"""
        logger.info(f'{self.user} has connected to Discord!')
        logger.info(f'Bot is in {len(self.guilds)} guilds')
        
        # Set bot status
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="for brand creation requests"
            )
        )

# Create bot instance
bot = SVDiscordBot()

# Add a simple test command
@bot.tree.command(name="test", description="Test if the bot is working")
async def test_command(interaction: discord.Interaction):
    """Simple test command"""
    embed = discord.Embed(
        title="✅ STAFFVIRTUAL Bot is Working!",
        description="All systems operational. Ready to help with branded content creation.",
        color=bot.brand_config['primary_color']
    )
    await interaction.response.send_message(embed=embed)

# Run the bot
if __name__ == "__main__":
    token = os.getenv('DISCORD_BOT_TOKEN')
    if not token:
        logger.error("DISCORD_BOT_TOKEN not found in environment variables")
        exit(1)
    
    try:
        bot.run(token)
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
