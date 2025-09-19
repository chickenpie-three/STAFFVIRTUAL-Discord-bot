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
import base64
from PIL import Image

# AI Libraries with proper imports
try:
    from google import genai
    from google.genai import types
except ImportError:
    try:
        import google.generativeai as genai
        types = None
    except ImportError:
        genai = None
        types = None

try:
    import openai
except ImportError:
    openai = None
    
try:
    import anthropic
except ImportError:
    anthropic = None

# Knowledge management
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
            description='STAFFVIRTUAL Brand Assistant Bot - AI-powered with Nano Banana image generation'
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
        
        # Initialize AI clients and knowledge manager
        self.ai_clients = self._initialize_ai_clients()
        self.knowledge_manager = KnowledgeManager()
    
    def _initialize_ai_clients(self):
        """Initialize AI clients with proper error handling"""
        clients = {}
        
        # Initialize Gemini with new API approach
        gemini_key = os.getenv('GEMINI_API_KEY')
        if gemini_key and genai:
            try:
                if types:  # New Google GenAI SDK
                    clients['gemini'] = genai.Client(api_key=gemini_key)
                    logger.info("Gemini client initialized with new SDK")
                else:  # Fallback to old SDK
                    genai.configure(api_key=gemini_key)
                    clients['gemini_legacy'] = genai.GenerativeModel('gemini-1.5-flash')
                    logger.info("Gemini legacy client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini: {e}")
        
        # Initialize OpenAI
        openai_key = os.getenv('OPENAI_API_KEY')
        if openai_key and openai:
            try:
                clients['openai'] = openai.OpenAI(api_key=openai_key)
                logger.info("OpenAI client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI: {e}")
        
        # Initialize Anthropic
        anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        if anthropic_key and anthropic:
            try:
                clients['anthropic'] = anthropic.Anthropic(api_key=anthropic_key)
                logger.info("Anthropic client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Anthropic: {e}")
        
        return clients
    
    async def _generate_nano_banana_image(self, prompt: str, style: str = "professional"):
        """Generate images using Gemini 2.5 Flash Image (Nano Banana)"""
        try:
            if 'gemini' not in self.ai_clients:
                return {"success": False, "error": "Gemini client not available"}
            
            # Create STAFFVIRTUAL branded prompt
            branded_prompt = f"""
            Create a professional, high-quality image for STAFFVIRTUAL (a virtual staffing company) with these specifications:
            
            Subject: {prompt}
            Style: {style}, modern, clean, professional
            Brand Colors: Incorporate blue (#1888FF), off-white (#F8F8EB), and dark blue (#004B8D)
            Quality: High-resolution, professional business quality
            Composition: Well-balanced, visually appealing, suitable for business use
            
            The image should reflect STAFFVIRTUAL's professional, innovative, and trustworthy brand identity.
            """
            
            # Use new Gemini API for image generation
            response = self.ai_clients['gemini'].models.generate_content(
                model="gemini-2.5-flash-image-preview",
                contents=[branded_prompt]
            )
            
            # Process response
            for part in response.candidates[0].content.parts:
                if part.text is not None:
                    return {
                        "success": True,
                        "description": part.text,
                        "model": "gemini-2.5-flash-image-preview",
                        "prompt_used": branded_prompt
                    }
                elif part.inline_data is not None:
                    # Save the generated image
                    image_data = part.inline_data.data
                    image = Image.open(io.BytesIO(image_data))
                    
                    # Save to temporary file
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
                    image.save(temp_file.name)
                    
                    return {
                        "success": True,
                        "image_path": temp_file.name,
                        "description": "Image generated successfully",
                        "model": "gemini-2.5-flash-image-preview",
                        "prompt_used": branded_prompt
                    }
            
            return {"success": False, "error": "No image data in response"}
            
        except Exception as e:
            logger.error(f"Nano Banana image generation error: {e}")
            return {"success": False, "error": str(e)}
    
    async def _get_ai_response(self, prompt, system_context="", use_knowledge=True):
        """Get AI text response using available clients"""
        try:
            # Get knowledge base context
            knowledge_context = ""
            if use_knowledge:
                try:
                    knowledge_context = self.knowledge_manager.get_context_for_query(prompt)
                    if knowledge_context and knowledge_context != "No specific information found in knowledge base.":
                        knowledge_context = f"\n\nRelevant STAFFVIRTUAL Knowledge: {knowledge_context}\n"
                except Exception as e:
                    logger.error(f"Knowledge base error: {e}")
                    knowledge_context = ""
            
            # Brand context
            brand_context = f"""
            You are an AI assistant for {self.brand_config['name']}, a professional virtual staffing company.
            
            Brand Guidelines:
            - Style: {self.brand_config['style_guidelines']}
            - Voice & Tone: {self.brand_config['voice_tone']}
            - Colors: Primary #1888FF, Secondary #F8F8EB, Accent #004B8D
            - Always maintain brand consistency in all outputs
            """
            
            # Combine contexts
            full_context = brand_context
            if system_context:
                full_context += f"\n\nSpecific Role: {system_context}"
            if knowledge_context:
                full_context += knowledge_context
            
            # Try Gemini first
            if 'gemini' in self.ai_clients:
                try:
                    full_prompt = f"{full_context}\n\nUser Request: {prompt}"
                    response = self.ai_clients['gemini'].models.generate_content(
                        model="gemini-2.0-flash-exp",
                        contents=[full_prompt]
                    )
                    return response.candidates[0].content.parts[0].text
                except Exception as e:
                    logger.error(f"Gemini error: {e}")
            
            # Try legacy Gemini
            if 'gemini_legacy' in self.ai_clients:
                try:
                    full_prompt = f"{full_context}\n\nUser Request: {prompt}"
                    response = self.ai_clients['gemini_legacy'].generate_content(full_prompt)
                    return response.text
                except Exception as e:
                    logger.error(f"Gemini legacy error: {e}")
            
            # Fallback to OpenAI
            if 'openai' in self.ai_clients:
                try:
                    response = self.ai_clients['openai'].chat.completions.create(
                        model="gpt-4",
                        messages=[
                            {"role": "system", "content": full_context},
                            {"role": "user", "content": prompt}
                        ],
                        max_tokens=2000
                    )
                    return response.choices[0].message.content
                except Exception as e:
                    logger.error(f"OpenAI error: {e}")
            
            return "❌ No AI service available. Please check your API keys."
                
        except Exception as e:
            logger.error(f"AI response error: {e}")
            return f"❌ Error: {str(e)}"
        
    async def setup_hook(self):
        """Called when the bot is starting up"""
        logger.info("Setting up STAFFVIRTUAL Discord Bot...")
        try:
            synced = await self.tree.sync()
            logger.info(f"Synced {len(synced)} command(s)")
        except Exception as e:
            logger.error(f"Failed to sync commands: {e}")
    
    async def on_ready(self):
        """Called when the bot is ready"""
        logger.info(f'{self.user} has connected to Discord!')
        logger.info(f'Bot is in {len(self.guilds)} guilds')
        logger.info(f"Available AI services: {list(self.ai_clients.keys())}")
        
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="for STAFFVIRTUAL brand requests"
            )
        )

# Create bot instance
bot = SVDiscordBot()

# 🧪 TEST COMMAND
@bot.tree.command(name="test", description="Test if the bot is working")
async def test_command(interaction: discord.Interaction):
    """Test command"""
    try:
        available_services = list(bot.ai_clients.keys())
        
        embed = discord.Embed(
            title="✅ STAFFVIRTUAL Bot is Working!",
            description="All systems operational and ready for branded content creation.",
            color=bot.brand_config['primary_color']
        )
        embed.add_field(name="🤖 AI Services", value=f"Available: {', '.join(available_services) if available_services else 'None configured'}", inline=False)
        embed.add_field(name="🧠 Knowledge Base", value="Ready to learn from URLs and documents", inline=False)
        embed.add_field(name="🎨 Brand Colors", value=f"Primary: #{bot.brand_config['primary_color']:06x}", inline=False)
        
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        logger.error(f"Test command error: {e}")
        await interaction.response.send_message(f"❌ Test failed: {str(e)}")

# 🍌 NANO BANANA IMAGE GENERATOR (Using official Gemini API)
@bot.tree.command(name="image", description="Generate actual images using Gemini 2.5 Flash (Nano Banana)")
async def generate_image(interaction: discord.Interaction, prompt: str, style: str = "professional"):
    """Generate actual images using Nano Banana approach"""
    await interaction.response.defer(thinking=True)
    
    try:
        # Generate image using Nano Banana approach
        result = await bot._generate_nano_banana_image(prompt, style)
        
        if result['success']:
            embed = discord.Embed(
                title="🍌 Nano Banana Image Generated!",
                description=f"**Prompt:** {prompt}\n**Style:** {style}\n**Model:** {result['model']}",
                color=bot.brand_config['primary_color']
            )
            
            embed.add_field(
                name="🎨 Generated Description",
                value=result['description'][:1024],
                inline=False
            )
            
            embed.add_field(
                name="🔧 Technical Details",
                value=f"Model: Gemini 2.5 Flash Image Preview\nApproach: Official Nano Banana API\nBrand Colors: Integrated",
                inline=False
            )
            
            # If we have an actual image file, attach it
            if result.get('image_path'):
                file = discord.File(result['image_path'], filename=f"staffvirtual_{prompt.replace(' ', '_')[:20]}.png")
                await interaction.followup.send(embed=embed, file=file)
                
                # Clean up temporary file
                try:
                    os.unlink(result['image_path'])
                except:
                    pass
            else:
                await interaction.followup.send(embed=embed)
            
        else:
            embed = discord.Embed(
                title="❌ Image Generation Failed",
                description=f"Error: {result.get('error', 'Unknown error')}",
                color=0xff0000
            )
            await interaction.followup.send(embed=embed)
        
    except Exception as e:
        logger.error(f"Image generation error: {e}")
        await interaction.followup.send(f"❌ Error generating image: {str(e)}")

# 📄 DOCUMENT CREATION AGENT
@bot.tree.command(name="document", description="Create branded documents")
async def create_document(interaction: discord.Interaction, document_type: str, topic: str, length: str = "medium"):
    """Create branded documents"""
    await interaction.response.defer(thinking=True)
    
    try:
        system_context = "You are a professional document creation specialist. Create well-structured, branded documents with proper formatting."
        doc_prompt = f"Create a {length} {document_type} for STAFFVIRTUAL about: {topic}. Include proper structure, brand voice, and actionable content."
        
        result = await bot._get_ai_response(doc_prompt, system_context)
        
        embed = discord.Embed(
            title="📄 Document Created!",
            description=f"**Type:** {document_type}\n**Topic:** {topic}\n**Length:** {length}",
            color=bot.brand_config['primary_color']
        )
        
        # Create file
        document_content = f"# STAFFVIRTUAL {document_type.title()}: {topic}\n\n{result}"
        file_buffer = io.BytesIO(document_content.encode('utf-8'))
        file = discord.File(file_buffer, filename=f"staffvirtual_{document_type}_{topic.replace(' ', '_')}.txt")
        
        preview = result[:500] + "..." if len(result) > 500 else result
        embed.add_field(name="📋 Document Preview", value=preview, inline=False)
        
        await interaction.followup.send(embed=embed, file=file)
    except Exception as e:
        logger.error(f"Document command error: {e}")
        await interaction.followup.send(f"❌ Error creating document: {str(e)}")

# 🏢 BRAND STRATEGY AGENT
@bot.tree.command(name="brand", description="Get strategic brand guidance")
async def brand_guidance(interaction: discord.Interaction, query: str):
    """Get brand strategy guidance"""
    await interaction.response.defer(thinking=True)
    
    try:
        system_context = "You are a senior brand strategist for STAFFVIRTUAL. Provide strategic guidance, creative direction, and actionable recommendations."
        result = await bot._get_ai_response(query, system_context)
        
        embed = discord.Embed(
            title="🏢 Brand Strategic Guidance",
            description=f"**Query:** {query}",
            color=bot.brand_config['primary_color']
        )
        
        if len(result) > 1024:
            chunks = [result[i:i+1024] for i in range(0, len(result), 1024)]
            for i, chunk in enumerate(chunks[:3]):
                field_name = "📋 Guidance" if i == 0 else f"📋 Continued ({i+1})"
                embed.add_field(name=field_name, value=chunk, inline=False)
        else:
            embed.add_field(name="📋 Brand Guidance", value=result, inline=False)
        
        await interaction.followup.send(embed=embed)
    except Exception as e:
        logger.error(f"Brand command error: {e}")
        await interaction.followup.send(f"❌ Error: {str(e)}")

# 🤔 BUSINESS Q&A AGENT
@bot.tree.command(name="ask", description="Ask questions about STAFFVIRTUAL")
async def ask_business(interaction: discord.Interaction, question: str):
    """Ask business questions with knowledge base integration"""
    await interaction.response.defer(thinking=True)
    
    try:
        system_context = "You are a business intelligence assistant with deep knowledge about STAFFVIRTUAL's services, processes, and operations."
        result = await bot._get_ai_response(question, system_context, use_knowledge=True)
        
        embed = discord.Embed(
            title="🤔 Business Question Answered",
            description=f"**Question:** {question}",
            color=bot.brand_config['primary_color']
        )
        
        if len(result) > 1024:
            chunks = [result[i:i+1024] for i in range(0, len(result), 1024)]
            for i, chunk in enumerate(chunks[:3]):
                field_name = "💡 Answer" if i == 0 else f"💡 Continued ({i+1})"
                embed.add_field(name=field_name, value=chunk, inline=False)
        else:
            embed.add_field(name="💡 Answer", value=result, inline=False)
        
        await interaction.followup.send(embed=embed)
    except Exception as e:
        logger.error(f"Ask command error: {e}")
        await interaction.followup.send(f"❌ Error: {str(e)}")

# 🌐 URL LEARNING AGENT
@bot.tree.command(name="learn_url", description="Learn from website content")
async def learn_from_url(interaction: discord.Interaction, url: str):
    """Learn from URLs"""
    await interaction.response.defer(thinking=True)
    
    try:
        content = await bot.knowledge_manager.scrape_url(url)
        
        if content and not content.get('error'):
            bot.knowledge_manager.save_knowledge_base()
            
            embed = discord.Embed(
                title="🌐 Website Content Learned!",
                description=f"**URL:** {url}",
                color=bot.brand_config['primary_color']
            )
            
            embed.add_field(name="📄 Page Title", value=content.get('title', 'No title')[:500], inline=False)
            embed.add_field(
                name="📊 Content Stats",
                value=f"Paragraphs: {len(content.get('paragraphs', []))}\nContent learned and available for all AI agents",
                inline=False
            )
            embed.set_footer(text="This information is now available for all AI agents to reference")
            
        else:
            embed = discord.Embed(
                title="❌ Failed to Learn from URL",
                description=f"Could not scrape content from: {url}",
                color=0xff0000
            )
        
        await interaction.followup.send(embed=embed)
    except Exception as e:
        logger.error(f"Learn URL error: {e}")
        await interaction.followup.send(f"❌ Error: {str(e)}")

# 📄 SIMPLE DOCUMENT UPLOAD (Text-based for now)
@bot.tree.command(name="add_info", description="Add text information to knowledge base")
async def add_info(interaction: discord.Interaction, title: str, content: str):
    """Add text information directly to knowledge base"""
    await interaction.response.defer(thinking=True)
    
    try:
        # Add to knowledge base directly
        info_entry = {
            "title": title,
            "content": content,
            "type": "manual",
            "added_by": str(interaction.user),
            "added_at": ""
        }
        
        if "manual_entries" not in bot.knowledge_manager.knowledge_base:
            bot.knowledge_manager.knowledge_base["manual_entries"] = {}
        
        bot.knowledge_manager.knowledge_base["manual_entries"][title] = info_entry
        bot.knowledge_manager.knowledge_base["sources"].append({
            "type": "manual",
            "source": title,
            "title": title
        })
        
        bot.knowledge_manager.save_knowledge_base()
        
        embed = discord.Embed(
            title="📝 Information Added!",
            description=f"**Title:** {title}",
            color=bot.brand_config['primary_color']
        )
        
        embed.add_field(name="📄 Content Added", value=content[:500] + "..." if len(content) > 500 else content, inline=False)
        embed.set_footer(text="This information is now available for all AI agents to reference")
        
        await interaction.followup.send(embed=embed)
    except Exception as e:
        logger.error(f"Add info error: {e}")
        await interaction.followup.send(f"❌ Error: {str(e)}")

# 🧠 KNOWLEDGE STATUS
@bot.tree.command(name="knowledge_status", description="Check knowledge base status")
async def knowledge_status(interaction: discord.Interaction):
    """Show knowledge base status"""
    await interaction.response.defer(thinking=True)
    
    try:
        summary = bot.knowledge_manager.get_knowledge_summary()
        
        embed = discord.Embed(
            title="🧠 STAFFVIRTUAL Knowledge Base",
            description="Current knowledge base status",
            color=bot.brand_config['primary_color']
        )
        
        embed.add_field(
            name="📊 Statistics",
            value=f"Scraped URLs: {summary['scraped_urls']}\nUploaded Documents: {summary['uploaded_documents']}\nTotal Sources: {summary['total_sources']}",
            inline=False
        )
        
        sources = bot.knowledge_manager.knowledge_base.get('sources', [])
        if sources:
            source_list = []
            for source in sources[-5:]:  # Show last 5 sources
                source_list.append(f"• {source['type'].title()}: {source['title'][:40]}...")
            
            embed.add_field(
                name="📚 Recent Sources",
                value="\n".join(source_list),
                inline=False
            )
        
        embed.add_field(
            name="💡 How to Add Knowledge",
            value="• `/learn_url` - Learn from websites\n• `/add_info` - Add text information manually\n• Upload docs as text files for now",
            inline=False
        )
        
        await interaction.followup.send(embed=embed)
    except Exception as e:
        logger.error(f"Knowledge status error: {e}")
        await interaction.followup.send(f"❌ Error: {str(e)}")

# ❓ HELP COMMAND
@bot.tree.command(name="help", description="Show all available commands")
async def help_command(interaction: discord.Interaction):
    """Show help information"""
    try:
        embed = discord.Embed(
            title="🤖 STAFFVIRTUAL Brand Assistant",
            description="AI-powered creative companion with Nano Banana image generation",
            color=bot.brand_config['primary_color']
        )
        
        embed.add_field(name="🍌 /image", value="Generate images (Nano Banana)", inline=True)
        embed.add_field(name="📄 /document", value="Create documents", inline=True)
        embed.add_field(name="🏢 /brand", value="Brand guidance", inline=True)
        embed.add_field(name="🤔 /ask", value="Business questions", inline=True)
        embed.add_field(name="🌐 /learn_url", value="Learn from websites", inline=True)
        embed.add_field(name="📝 /add_info", value="Add text information", inline=True)
        embed.add_field(name="🧠 /knowledge_status", value="Check knowledge", inline=True)
        embed.add_field(name="🧪 /test", value="Test functionality", inline=True)
        
        embed.add_field(
            name="🚀 Features",
            value="• Nano Banana image generation\n• Smart knowledge base\n• Brand-consistent responses\n• Document processing",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        logger.error(f"Help command error: {e}")
        await interaction.response.send_message(f"❌ Error: {str(e)}")

# Run the bot
if __name__ == "__main__":
    token = os.getenv('DISCORD_BOT_TOKEN')
    if not token:
        logger.error("DISCORD_BOT_TOKEN not found in environment variables")
        exit(1)
    
    try:
        logger.info("Starting STAFFVIRTUAL Discord Bot with Nano Banana...")
        bot.run(token)
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        exit(1)
