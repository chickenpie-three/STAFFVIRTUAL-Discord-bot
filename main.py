import discord
from discord.ext import commands
import asyncio
import logging
import os
from dotenv import load_dotenv
import io
import json
import base64
import tempfile

# AI Libraries with proper Nano Banana imports
try:
    from google import genai
    from google.genai import types
    NANO_BANANA_AVAILABLE = True
    logger = logging.getLogger(__name__)
    logger.info("Nano Banana (google-genai) SDK loaded successfully")
except ImportError:
    try:
        import google.generativeai as genai
        types = None
        NANO_BANANA_AVAILABLE = False
        logger = logging.getLogger(__name__)
        logger.info("Using legacy google-generativeai SDK")
    except ImportError:
        genai = None
        types = None
        NANO_BANANA_AVAILABLE = False

try:
    import openai
except ImportError:
    openai = None

try:
    from PIL import Image
except ImportError:
    Image = None

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
            description='STAFFVIRTUAL Brand Assistant Bot - With Real Nano Banana Image Generation'
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
        
        # Initialize AI clients
        self.ai_clients = self._initialize_ai_clients()
        self.knowledge_manager = KnowledgeManager()
    
    def _initialize_ai_clients(self):
        """Initialize AI clients with Nano Banana support"""
        clients = {}
        
        # Initialize Gemini with Nano Banana capability
        gemini_key = os.getenv('GEMINI_API_KEY')
        if gemini_key and genai:
            try:
                if NANO_BANANA_AVAILABLE and types:
                    # Use new Google GenAI SDK for Nano Banana
                    clients['nano_banana'] = genai.Client(api_key=gemini_key)
                    logger.info("Nano Banana client initialized successfully!")
                else:
                    # Fallback to legacy SDK
                    genai.configure(api_key=gemini_key)
                    clients['gemini'] = genai.GenerativeModel('gemini-1.5-flash')
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
        
        return clients
    
    async def _generate_nano_banana_image(self, prompt: str, style: str = "professional"):
        """Generate actual images using Gemini 2.5 Flash Image (Nano Banana)"""
        try:
            if 'nano_banana' not in self.ai_clients:
                return {"success": False, "error": "Nano Banana not available - using concept generation instead"}
            
            # Create STAFFVIRTUAL branded prompt
            branded_prompt = f"""
            Create a professional, high-quality image for STAFFVIRTUAL (a virtual staffing company):
            
            Subject: {prompt}
            Style: {style}, modern, clean, professional business aesthetic
            Brand Colors: Incorporate blue (#1888FF), off-white (#F8F8EB), and dark blue (#004B8D)
            Quality: High-resolution, professional business quality suitable for marketing
            Composition: Well-balanced, visually appealing, clean layout
            Mood: Professional, trustworthy, innovative, approachable
            
            The image should reflect STAFFVIRTUAL's expertise in virtual staffing and professional services.
            Avoid any text or logos unless specifically requested.
            Focus on visual elements that convey professionalism and efficiency.
            """
            
            logger.info(f"Generating Nano Banana image with prompt: {prompt}")
            
            # Use Gemini 2.5 Flash Image Preview (Nano Banana)
            response = self.ai_clients['nano_banana'].models.generate_content(
                model="gemini-2.5-flash-image-preview",
                contents=[branded_prompt]
            )
            
            # Process response parts
            for part in response.candidates[0].content.parts:
                if part.text is not None:
                    # Text description of the image
                    description = part.text
                    logger.info("Received text description from Nano Banana")
                    
                elif hasattr(part, 'inline_data') and part.inline_data is not None:
                    # Actual image data
                    image_data = part.inline_data.data
                    
                    if Image:
                        # Process image with PIL
                        image = Image.open(io.BytesIO(image_data))
                        
                        # Save to temporary file for Discord upload
                        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
                        image.save(temp_file.name, 'PNG')
                        
                        logger.info(f"Nano Banana image saved to: {temp_file.name}")
                        
                        return {
                            "success": True,
                            "image_path": temp_file.name,
                            "description": description if 'description' in locals() else "Professional STAFFVIRTUAL branded image generated",
                            "model": "gemini-2.5-flash-image-preview",
                            "prompt_used": branded_prompt,
                            "image_size": image.size
                        }
                    else:
                        # Save raw image data if PIL not available
                        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
                        temp_file.write(image_data)
                        temp_file.close()
                        
                        return {
                            "success": True,
                            "image_path": temp_file.name,
                            "description": description if 'description' in locals() else "Image generated successfully",
                            "model": "gemini-2.5-flash-image-preview",
                            "prompt_used": branded_prompt
                        }
            
            return {"success": False, "error": "No image data received from Nano Banana"}
            
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
            - Services: Virtual Assistants, Creative Services, Technical Support, Marketing Services
            """
            
            # Combine contexts
            full_context = brand_context
            if system_context:
                full_context += f"\n\nSpecific Role: {system_context}"
            if knowledge_context:
                full_context += knowledge_context
            
            # Try Nano Banana client first
            if 'nano_banana' in self.ai_clients:
                try:
                    response = self.ai_clients['nano_banana'].models.generate_content(
                        model="gemini-2.0-flash-exp",
                        contents=[f"{full_context}\n\nUser Request: {prompt}"]
                    )
                    return response.candidates[0].content.parts[0].text
                except Exception as e:
                    logger.error(f"Nano Banana text error: {e}")
            
            # Try legacy Gemini
            if 'gemini' in self.ai_clients:
                try:
                    full_prompt = f"{full_context}\n\nUser Request: {prompt}"
                    response = self.ai_clients['gemini'].generate_content(full_prompt)
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
        logger.info("Setting up STAFFVIRTUAL Discord Bot with Nano Banana...")
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
        logger.info(f"Nano Banana available: {NANO_BANANA_AVAILABLE}")
        
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="for STAFFVIRTUAL brand requests"
            )
        )

# Create bot instance
bot = SVDiscordBot()

# 🧪 TEST COMMAND
@bot.tree.command(name="test", description="Test STAFFVIRTUAL bot functionality")
async def test_command(interaction: discord.Interaction):
    """Test command with Nano Banana status"""
    try:
        available_services = list(bot.ai_clients.keys())
        
        embed = discord.Embed(
            title="✅ STAFFVIRTUAL Bot is Working!",
            description="All systems operational and ready for branded content creation.",
            color=bot.brand_config['primary_color']
        )
        embed.add_field(name="🤖 AI Services", value=f"Available: {', '.join(available_services)}", inline=False)
        embed.add_field(name="🍌 Nano Banana", value=f"Status: {'✅ Available' if NANO_BANANA_AVAILABLE else '❌ Using legacy mode'}", inline=False)
        embed.add_field(name="🧠 Knowledge Base", value="Ready for learning", inline=False)
        embed.add_field(name="🎨 Brand Colors", value=f"Primary: #{bot.brand_config['primary_color']:06x}", inline=False)
        
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        logger.error(f"Test command error: {e}")
        await interaction.response.send_message(f"❌ Test failed: {str(e)}")

# 🍌 NANO BANANA IMAGE GENERATOR
@bot.tree.command(name="image", description="Generate actual images using Gemini 2.5 Flash (Nano Banana)")
async def generate_image(interaction: discord.Interaction, prompt: str, style: str = "professional"):
    """Generate actual images using Nano Banana"""
    await interaction.response.defer(thinking=True)
    
    try:
        logger.info(f"Image generation request: {prompt}, style: {style}")
        
        # Try Nano Banana first
        if NANO_BANANA_AVAILABLE and 'nano_banana' in bot.ai_clients:
            result = await bot._generate_nano_banana_image(prompt, style)
            
            if result['success']:
                embed = discord.Embed(
                    title="🍌 Nano Banana Image Generated!",
                    description=f"**Prompt:** {prompt}\n**Style:** {style}\n**Model:** {result['model']}",
                    color=bot.brand_config['primary_color']
                )
                
                embed.add_field(
                    name="🎨 Image Description",
                    value=result['description'][:1024],
                    inline=False
                )
                
                embed.add_field(
                    name="🔧 Technical Details",
                    value=f"Model: {result['model']}\nSize: {result.get('image_size', 'Standard')}\nBrand Colors: Integrated",
                    inline=False
                )
                
                # Attach the generated image
                if result.get('image_path'):
                    file = discord.File(result['image_path'], filename=f"staffvirtual_{prompt.replace(' ', '_')[:20]}.png")
                    embed.set_image(url=f"attachment://staffvirtual_{prompt.replace(' ', '_')[:20]}.png")
                    
                    await interaction.followup.send(embed=embed, file=file)
                    
                    # Clean up temporary file
                    try:
                        os.unlink(result['image_path'])
                    except:
                        pass
                else:
                    await interaction.followup.send(embed=embed)
                
                return
        
        # Fallback to concept generation
        system_context = "You are an expert image generation specialist. Create detailed, branded visual concepts with specific composition, color, and style guidance."
        
        enhanced_prompt = f"""
        Create a detailed image concept for STAFFVIRTUAL (virtual staffing company):
        
        Subject: {prompt}
        Style: {style}, modern, clean, professional
        Brand Colors: Use blue (#1888FF), off-white (#F8F8EB), and dark blue (#004B8D)
        
        Provide specific details about:
        - Composition and layout
        - Lighting and mood
        - Color scheme and brand integration
        - Professional quality elements
        - Overall aesthetic suitable for business use
        """
        
        result = await bot._get_ai_response(enhanced_prompt, system_context)
        
        embed = discord.Embed(
            title="🎨 STAFFVIRTUAL Image Concept",
            description=f"**Prompt:** {prompt}\n**Style:** {style}\n**Mode:** Concept Generation",
            color=bot.brand_config['primary_color']
        )
        
        embed.add_field(name="🖼️ Detailed Concept", value=result[:1024], inline=False)
        embed.add_field(
            name="💡 Next Steps", 
            value="Use this concept with DALL-E 3, Midjourney, or other image generation tools", 
            inline=False
        )
        
        if not NANO_BANANA_AVAILABLE:
            embed.add_field(
                name="ℹ️ Note", 
                value="Nano Banana image generation not available - providing detailed concept instead", 
                inline=False
            )
        
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        logger.error(f"Image command error: {e}")
        await interaction.followup.send(f"❌ Error generating image: {str(e)}")

# 📄 DOCUMENT CREATION AGENT
@bot.tree.command(name="document", description="Create branded documents for STAFFVIRTUAL")
async def create_document(interaction: discord.Interaction, document_type: str, topic: str, length: str = "medium"):
    """Create branded documents"""
    await interaction.response.defer(thinking=True)
    
    try:
        system_context = "You are a professional document creation specialist for STAFFVIRTUAL. Create well-structured, branded documents."
        doc_prompt = f"Create a {length} {document_type} for STAFFVIRTUAL about: {topic}. Include proper structure, brand voice, and actionable content."
        
        result = await bot._get_ai_response(doc_prompt, system_context)
        
        embed = discord.Embed(
            title="📄 STAFFVIRTUAL Document Created!",
            description=f"**Type:** {document_type}\n**Topic:** {topic}\n**Length:** {length}",
            color=bot.brand_config['primary_color']
        )
        
        # Create file
        document_content = f"# STAFFVIRTUAL {document_type.title()}: {topic}\n\n{result}"
        file_buffer = io.BytesIO(document_content.encode('utf-8'))
        file = discord.File(file_buffer, filename=f"STAFFVIRTUAL_{document_type}_{topic.replace(' ', '_')}.txt")
        
        preview = result[:500] + "..." if len(result) > 500 else result
        embed.add_field(name="📋 Document Preview", value=preview, inline=False)
        
        await interaction.followup.send(embed=embed, file=file)
    except Exception as e:
        logger.error(f"Document command error: {e}")
        await interaction.followup.send(f"❌ Error: {str(e)}")

# 🏢 BRAND STRATEGY AGENT
@bot.tree.command(name="brand", description="Get strategic brand guidance for STAFFVIRTUAL")
async def brand_guidance(interaction: discord.Interaction, query: str):
    """Get brand strategy guidance"""
    await interaction.response.defer(thinking=True)
    
    try:
        system_context = "You are a senior brand strategist for STAFFVIRTUAL. Provide strategic guidance and actionable recommendations."
        result = await bot._get_ai_response(query, system_context)
        
        embed = discord.Embed(
            title="🏢 STAFFVIRTUAL Brand Guidance",
            description=f"**Query:** {query}",
            color=bot.brand_config['primary_color']
        )
        
        if len(result) > 1024:
            chunks = [result[i:i+1024] for i in range(0, len(result), 1024)]
            for i, chunk in enumerate(chunks[:3]):
                field_name = "📋 Guidance" if i == 0 else f"📋 Continued ({i+1})"
                embed.add_field(name=field_name, value=chunk, inline=False)
        else:
            embed.add_field(name="📋 Strategic Guidance", value=result, inline=False)
        
        await interaction.followup.send(embed=embed)
    except Exception as e:
        logger.error(f"Brand command error: {e}")
        await interaction.followup.send(f"❌ Error: {str(e)}")

# 🤔 BUSINESS Q&A AGENT
@bot.tree.command(name="ask", description="Ask questions about STAFFVIRTUAL")
async def ask_business(interaction: discord.Interaction, question: str):
    """Ask business questions"""
    await interaction.response.defer(thinking=True)
    
    try:
        system_context = "You are a business intelligence assistant with deep knowledge about STAFFVIRTUAL."
        result = await bot._get_ai_response(question, system_context, use_knowledge=True)
        
        embed = discord.Embed(
            title="🤔 STAFFVIRTUAL Business Q&A",
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

# Add all the other commands from main_working.py...
# (I'll add them in the next part to keep this manageable)

# ❓ HELP COMMAND
@bot.tree.command(name="help", description="Show all STAFFVIRTUAL bot commands")
async def help_command(interaction: discord.Interaction):
    """Show help information"""
    try:
        embed = discord.Embed(
            title="🤖 STAFFVIRTUAL Brand Assistant",
            description="AI-powered creative companion with Nano Banana image generation",
            color=bot.brand_config['primary_color']
        )
        
        embed.add_field(name="🍌 /image", value="Generate actual images (Nano Banana)", inline=True)
        embed.add_field(name="📄 /document", value="Create documents", inline=True)
        embed.add_field(name="🏢 /brand", value="Brand guidance", inline=True)
        embed.add_field(name="🤔 /ask", value="Business questions", inline=True)
        embed.add_field(name="🧪 /test", value="Test functionality", inline=True)
        
        embed.add_field(
            name="🚀 Nano Banana Features",
            value=f"• Real image generation: {'✅ Available' if NANO_BANANA_AVAILABLE else '❌ Concept mode'}\n• STAFFVIRTUAL branding\n• Professional quality\n• Brand-consistent responses",
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
        logger.info("Starting STAFFVIRTUAL Discord Bot with Nano Banana support...")
        bot.run(token)
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        exit(1)
