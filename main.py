import discord
from discord.ext import commands
import asyncio
import logging
import os
from dotenv import load_dotenv
import io
import json

# AI Libraries with safe imports
try:
    import google.generativeai as genai
except ImportError:
    genai = None

try:
    import openai
except ImportError:
    openai = None

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
            description='STAFFVIRTUAL Brand Assistant Bot - AI-powered content creation'
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
        
        # Simple knowledge base (in-memory for now)
        self.knowledge_base = {
            "company_info": {
                "name": "STAFFVIRTUAL",
                "description": "Professional virtual staffing and business support services",
                "services": ["Virtual Assistants", "Creative Services", "Technical Support", "Marketing Services"],
                "brand_colors": ["#1888FF (Primary Blue)", "#F8F8EB (Secondary Off-white)", "#004B8D (Accent Dark Blue)"]
            },
            "manual_entries": {},
            "scraped_content": {}
        }
    
    def _initialize_ai_clients(self):
        """Initialize AI clients with robust error handling"""
        clients = {}
        
        # Initialize Gemini with stable model
        gemini_key = os.getenv('GEMINI_API_KEY')
        if gemini_key and genai:
            try:
                genai.configure(api_key=gemini_key)
                
                # Try stable models first
                models_to_try = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro']
                
                for model_name in models_to_try:
                    try:
                        clients['gemini'] = genai.GenerativeModel(model_name)
                        logger.info(f"Gemini initialized with model: {model_name}")
                        break
                    except Exception as e:
                        logger.warning(f"Failed to initialize {model_name}: {e}")
                        continue
                        
            except Exception as e:
                logger.error(f"Failed to configure Gemini: {e}")
        
        # Initialize OpenAI
        openai_key = os.getenv('OPENAI_API_KEY')
        if openai_key and openai:
            try:
                clients['openai'] = openai.OpenAI(api_key=openai_key)
                logger.info("OpenAI client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI: {e}")
        
        return clients
    
    async def _get_ai_response(self, prompt, system_context=""):
        """Get AI response using available clients"""
        try:
            # Create brand context
            brand_context = f"""
            You are an AI assistant for {self.brand_config['name']}, a professional virtual staffing company.
            
            Brand Guidelines:
            - Style: {self.brand_config['style_guidelines']}
            - Voice & Tone: {self.brand_config['voice_tone']}
            - Colors: Primary #1888FF, Secondary #F8F8EB, Accent #004B8D
            - Services: Virtual Assistants, Creative Services, Technical Support, Marketing Services
            
            {system_context}
            """
            
            # Try Gemini first
            if 'gemini' in self.ai_clients:
                try:
                    full_prompt = f"{brand_context}\n\nUser Request: {prompt}"
                    response = self.ai_clients['gemini'].generate_content(full_prompt)
                    return response.text
                except Exception as e:
                    logger.error(f"Gemini error: {e}")
            
            # Fallback to OpenAI
            if 'openai' in self.ai_clients:
                try:
                    response = self.ai_clients['openai'].chat.completions.create(
                        model="gpt-4",
                        messages=[
                            {"role": "system", "content": brand_context},
                            {"role": "user", "content": prompt}
                        ],
                        max_tokens=1500
                    )
                    return response.choices[0].message.content
                except Exception as e:
                    logger.error(f"OpenAI error: {e}")
            
            return "❌ No AI service available. Please check your API keys."
                
        except Exception as e:
            logger.error(f"AI response error: {e}")
            return f"❌ Error: {str(e)}"
    
    def _add_to_knowledge_base(self, title: str, content: str, source_type: str = "manual"):
        """Add information to simple knowledge base"""
        try:
            self.knowledge_base["manual_entries"][title] = {
                "content": content,
                "type": source_type,
                "added_at": ""
            }
            logger.info(f"Added to knowledge base: {title}")
            return True
        except Exception as e:
            logger.error(f"Error adding to knowledge base: {e}")
            return False
    
    def _search_knowledge_base(self, query: str) -> str:
        """Simple search through knowledge base"""
        try:
            query_lower = query.lower()
            relevant_info = []
            
            # Search company info
            for key, value in self.knowledge_base["company_info"].items():
                if isinstance(value, str) and query_lower in value.lower():
                    relevant_info.append(f"{key}: {value}")
                elif isinstance(value, list):
                    for item in value:
                        if query_lower in item.lower():
                            relevant_info.append(f"{key}: {item}")
            
            # Search manual entries
            for title, entry in self.knowledge_base["manual_entries"].items():
                if query_lower in title.lower() or query_lower in entry["content"].lower():
                    relevant_info.append(f"{title}: {entry['content'][:200]}...")
            
            if relevant_info:
                return "Relevant STAFFVIRTUAL information:\n" + "\n".join(relevant_info[:3])
            else:
                return "No specific information found in knowledge base."
                
        except Exception as e:
            logger.error(f"Knowledge search error: {e}")
            return "Error searching knowledge base."
        
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
        embed.add_field(name="🧠 Knowledge Base", value="Ready for manual information entry", inline=False)
        embed.add_field(name="🎨 Brand Colors", value=f"Primary: #{bot.brand_config['primary_color']:06x}", inline=False)
        
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        logger.error(f"Test command error: {e}")
        await interaction.response.send_message(f"❌ Test failed: {str(e)}")

# 🎨 IMAGE CONCEPT GENERATOR
@bot.tree.command(name="image", description="Generate detailed image concepts for STAFFVIRTUAL")
async def generate_image(interaction: discord.Interaction, prompt: str, style: str = "professional"):
    """Generate branded image concepts"""
    await interaction.response.defer(thinking=True)
    
    try:
        system_context = "You are an expert image generation specialist. Create detailed, branded visual concepts with specific composition, color, and style guidance for professional use."
        
        enhanced_prompt = f"""
        Create a detailed image concept for STAFFVIRTUAL (virtual staffing company):
        
        Subject: {prompt}
        Style: {style}, modern, clean, professional
        Brand Colors: Use blue (#1888FF), off-white (#F8F8EB), and dark blue (#004B8D)
        
        Provide specific details about:
        - Composition and layout
        - Lighting and mood
        - Color scheme and brand integration
        - Typography or text elements (if any)
        - Overall aesthetic and professional quality
        
        Make it suitable for business use and brand consistency.
        """
        
        result = await bot._get_ai_response(enhanced_prompt, system_context)
        
        embed = discord.Embed(
            title="🎨 STAFFVIRTUAL Image Concept",
            description=f"**Prompt:** {prompt}\n**Style:** {style}",
            color=bot.brand_config['primary_color']
        )
        
        # Split long responses
        if len(result) > 1024:
            embed.add_field(name="🖼️ Concept (Part 1)", value=result[:1024], inline=False)
            if len(result) > 1024:
                embed.add_field(name="🖼️ Concept (Part 2)", value=result[1024:2048], inline=False)
        else:
            embed.add_field(name="🖼️ Detailed Concept", value=result, inline=False)
        
        embed.add_field(
            name="💡 Next Steps", 
            value="Use this detailed concept with:\n• DALL-E 3\n• Midjourney\n• Stable Diffusion\n• Adobe Firefly\n• Or any image generation tool", 
            inline=False
        )
        
        embed.set_footer(text="Concept optimized for STAFFVIRTUAL brand consistency")
        
        await interaction.followup.send(embed=embed)
    except Exception as e:
        logger.error(f"Image command error: {e}")
        await interaction.followup.send(f"❌ Error generating image concept: {str(e)}")

# 📄 DOCUMENT CREATION AGENT
@bot.tree.command(name="document", description="Create branded documents")
async def create_document(interaction: discord.Interaction, document_type: str, topic: str, length: str = "medium"):
    """Create branded documents"""
    await interaction.response.defer(thinking=True)
    
    try:
        system_context = "You are a professional document creation specialist for STAFFVIRTUAL. Create well-structured, branded documents with proper formatting and professional presentation."
        
        doc_prompt = f"""
        Create a {length} {document_type} for STAFFVIRTUAL about: {topic}
        
        Include:
        - Professional structure and formatting
        - STAFFVIRTUAL brand voice and messaging
        - Actionable content and clear next steps
        - Appropriate tone for business audience
        - Call-to-action where relevant
        
        Make it comprehensive and ready for business use.
        """
        
        result = await bot._get_ai_response(doc_prompt, system_context)
        
        embed = discord.Embed(
            title="📄 STAFFVIRTUAL Document Created!",
            description=f"**Type:** {document_type}\n**Topic:** {topic}\n**Length:** {length}",
            color=bot.brand_config['primary_color']
        )
        
        # Create downloadable file
        document_content = f"# STAFFVIRTUAL {document_type.title()}: {topic}\n\n{result}"
        file_buffer = io.BytesIO(document_content.encode('utf-8'))
        file = discord.File(file_buffer, filename=f"STAFFVIRTUAL_{document_type}_{topic.replace(' ', '_')}.txt")
        
        preview = result[:500] + "..." if len(result) > 500 else result
        embed.add_field(name="📋 Document Preview", value=preview, inline=False)
        
        await interaction.followup.send(embed=embed, file=file)
    except Exception as e:
        logger.error(f"Document command error: {e}")
        await interaction.followup.send(f"❌ Error creating document: {str(e)}")

# 🏢 BRAND STRATEGY AGENT
@bot.tree.command(name="brand", description="Get strategic brand guidance for STAFFVIRTUAL")
async def brand_guidance(interaction: discord.Interaction, query: str):
    """Get brand strategy guidance"""
    await interaction.response.defer(thinking=True)
    
    try:
        system_context = "You are a senior brand strategist and consultant for STAFFVIRTUAL. Provide strategic brand guidance, creative direction, and actionable recommendations."
        
        # Include knowledge base context
        knowledge_context = bot._search_knowledge_base(query)
        
        brand_prompt = f"""
        As a brand strategist for STAFFVIRTUAL, provide guidance on: {query}
        
        {knowledge_context}
        
        Please provide:
        - Strategic recommendations
        - Brand alignment considerations  
        - Practical implementation steps
        - Potential risks or considerations
        - Next steps or action items
        
        Keep the response actionable and specific to STAFFVIRTUAL's brand identity.
        """
        
        result = await bot._get_ai_response(brand_prompt, system_context)
        
        embed = discord.Embed(
            title="🏢 STAFFVIRTUAL Brand Guidance",
            description=f"**Query:** {query}",
            color=bot.brand_config['primary_color']
        )
        
        if len(result) > 1024:
            chunks = [result[i:i+1024] for i in range(0, len(result), 1024)]
            for i, chunk in enumerate(chunks[:3]):
                field_name = "📋 Strategic Guidance" if i == 0 else f"📋 Continued ({i+1})"
                embed.add_field(name=field_name, value=chunk, inline=False)
        else:
            embed.add_field(name="📋 Strategic Guidance", value=result, inline=False)
        
        await interaction.followup.send(embed=embed)
    except Exception as e:
        logger.error(f"Brand command error: {e}")
        await interaction.followup.send(f"❌ Error generating brand guidance: {str(e)}")

# 🤔 BUSINESS Q&A AGENT
@bot.tree.command(name="ask", description="Ask questions about STAFFVIRTUAL")
async def ask_business(interaction: discord.Interaction, question: str):
    """Ask business questions with knowledge base integration"""
    await interaction.response.defer(thinking=True)
    
    try:
        system_context = "You are a business intelligence assistant with deep knowledge about STAFFVIRTUAL's services, processes, and operations."
        
        # Get relevant knowledge
        knowledge_context = bot._search_knowledge_base(question)
        
        knowledge_prompt = f"""
        Answer this question about STAFFVIRTUAL: {question}
        
        {knowledge_context}
        
        Provide a helpful, accurate response based on available information. If specific details aren't available, provide general guidance and suggest where to find more information.
        """
        
        result = await bot._get_ai_response(knowledge_prompt, system_context)
        
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
        
        embed.set_footer(text="💡 For specific company policies, consult internal documentation")
        
        await interaction.followup.send(embed=embed)
    except Exception as e:
        logger.error(f"Ask command error: {e}")
        await interaction.followup.send(f"❌ Error processing question: {str(e)}")

# 📝 ADD INFORMATION TO KNOWLEDGE BASE
@bot.tree.command(name="add_info", description="Add information to STAFFVIRTUAL knowledge base")
async def add_info(interaction: discord.Interaction, title: str, content: str):
    """Add text information to knowledge base"""
    await interaction.response.defer(thinking=True)
    
    try:
        success = bot._add_to_knowledge_base(title, content)
        
        if success:
            embed = discord.Embed(
                title="📝 Information Added to Knowledge Base!",
                description=f"**Title:** {title}",
                color=bot.brand_config['primary_color']
            )
            
            embed.add_field(name="📄 Content Added", value=content[:800] + "..." if len(content) > 800 else content, inline=False)
            embed.set_footer(text="This information is now available for all AI agents to reference")
            
        else:
            embed = discord.Embed(
                title="❌ Failed to Add Information",
                description="Could not add information to knowledge base",
                color=0xff0000
            )
        
        await interaction.followup.send(embed=embed)
    except Exception as e:
        logger.error(f"Add info error: {e}")
        await interaction.followup.send(f"❌ Error: {str(e)}")

# 🌐 SIMPLE WEB LEARNING
@bot.tree.command(name="learn_url", description="Learn basic information from a website")
async def learn_from_url(interaction: discord.Interaction, url: str):
    """Learn from URLs with simple scraping"""
    await interaction.response.defer(thinking=True)
    
    try:
        import requests
        from bs4 import BeautifulSoup
        
        # Simple web scraping
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract basic content
            title = soup.find('title').text.strip() if soup.find('title') else "No title"
            paragraphs = [p.text.strip() for p in soup.find_all('p') if p.text.strip() and len(p.text.strip()) > 20]
            
            # Store in knowledge base
            content_summary = "\n".join(paragraphs[:5])  # First 5 paragraphs
            bot._add_to_knowledge_base(f"Website: {title}", content_summary, "url")
            
            embed = discord.Embed(
                title="🌐 Website Content Learned!",
                description=f"**URL:** {url}",
                color=bot.brand_config['primary_color']
            )
            
            embed.add_field(name="📄 Page Title", value=title[:500], inline=False)
            embed.add_field(name="📊 Content Stats", value=f"Paragraphs extracted: {len(paragraphs)}", inline=False)
            
            if content_summary:
                preview = content_summary[:500] + "..." if len(content_summary) > 500 else content_summary
                embed.add_field(name="📝 Content Preview", value=preview, inline=False)
            
            embed.set_footer(text="This information is now available for all AI agents")
            
        else:
            embed = discord.Embed(
                title="❌ Failed to Learn from URL",
                description=f"Could not access: {url} (Status: {response.status_code})",
                color=0xff0000
            )
        
        await interaction.followup.send(embed=embed)
    except Exception as e:
        logger.error(f"Learn URL error: {e}")
        await interaction.followup.send(f"❌ Error learning from URL: {str(e)}")

# 🧠 KNOWLEDGE STATUS
@bot.tree.command(name="knowledge_status", description="Check STAFFVIRTUAL knowledge base status")
async def knowledge_status(interaction: discord.Interaction):
    """Show knowledge base status"""
    await interaction.response.defer(thinking=True)
    
    try:
        manual_entries = len(bot.knowledge_base["manual_entries"])
        scraped_content = len(bot.knowledge_base["scraped_content"])
        
        embed = discord.Embed(
            title="🧠 STAFFVIRTUAL Knowledge Base",
            description="Current knowledge base status",
            color=bot.brand_config['primary_color']
        )
        
        embed.add_field(
            name="📊 Statistics",
            value=f"Manual Entries: {manual_entries}\nScraped Content: {scraped_content}\nTotal Sources: {manual_entries + scraped_content}",
            inline=False
        )
        
        # Show recent entries
        if bot.knowledge_base["manual_entries"]:
            recent_entries = list(bot.knowledge_base["manual_entries"].keys())[-3:]
            embed.add_field(
                name="📚 Recent Entries",
                value="\n".join([f"• {entry}" for entry in recent_entries]),
                inline=False
            )
        
        embed.add_field(
            name="💡 How to Add Knowledge",
            value="• `/add_info` - Add text information manually\n• `/learn_url` - Learn from websites",
            inline=False
        )
        
        await interaction.followup.send(embed=embed)
    except Exception as e:
        logger.error(f"Knowledge status error: {e}")
        await interaction.followup.send(f"❌ Error: {str(e)}")

# ❓ HELP COMMAND
@bot.tree.command(name="help", description="Show all available STAFFVIRTUAL bot commands")
async def help_command(interaction: discord.Interaction):
    """Show help information"""
    try:
        embed = discord.Embed(
            title="🤖 STAFFVIRTUAL Brand Assistant",
            description="AI-powered creative companion for professional content creation",
            color=bot.brand_config['primary_color']
        )
        
        embed.add_field(name="🎨 /image", value="Generate detailed image concepts", inline=True)
        embed.add_field(name="📄 /document", value="Create branded documents", inline=True)
        embed.add_field(name="🏢 /brand", value="Get brand guidance", inline=True)
        embed.add_field(name="🤔 /ask", value="Ask business questions", inline=True)
        embed.add_field(name="🌐 /learn_url", value="Learn from websites", inline=True)
        embed.add_field(name="📝 /add_info", value="Add information manually", inline=True)
        embed.add_field(name="🧠 /knowledge_status", value="Check knowledge base", inline=True)
        embed.add_field(name="🧪 /test", value="Test bot functionality", inline=True)
        
        embed.add_field(
            name="🚀 STAFFVIRTUAL Features",
            value="• Professional brand consistency\n• Smart knowledge base\n• Document generation\n• Strategic guidance",
            inline=False
        )
        
        embed.set_footer(text="All responses optimized for STAFFVIRTUAL brand consistency")
        
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        logger.error(f"Help command error: {e}")
        await interaction.response.send_message(f"❌ Error showing help: {str(e)}")

# Run the bot
if __name__ == "__main__":
    token = os.getenv('DISCORD_BOT_TOKEN')
    if not token:
        logger.error("DISCORD_BOT_TOKEN not found in environment variables")
        exit(1)
    
    try:
        logger.info("Starting STAFFVIRTUAL Discord Bot...")
        bot.run(token)
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        exit(1)
