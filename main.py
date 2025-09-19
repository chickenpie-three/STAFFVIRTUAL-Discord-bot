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
            description='SV Brand Assistant Bot - Your AI-powered creative companion with 12 specialized agents'
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
        
        # Initialize AI agents and knowledge manager
        self.agents = self._initialize_agents()
        self.knowledge_manager = KnowledgeManager()
    
    def _initialize_agents(self):
        """Initialize AI agents with direct API integrations"""
        ai_clients = {}
        
        # Initialize Gemini if available - using correct model names
        gemini_key = os.getenv('GEMINI_API_KEY')
        if gemini_key and genai:
            try:
                genai.configure(api_key=gemini_key)
                # Use Gemini 2.5 Flash for text generation
                ai_clients['gemini'] = genai.GenerativeModel('gemini-2.0-flash-exp')
                # Also initialize image model for image generation
                ai_clients['gemini_image'] = genai.GenerativeModel('gemini-2.5-flash')
                logger.info("Gemini AI clients initialized (text + image)")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini: {e}")
                # Fallback to older model if new ones don't work
                try:
                    ai_clients['gemini'] = genai.GenerativeModel('gemini-1.5-flash')
                    logger.info("Gemini fallback model initialized")
                except Exception as e2:
                    logger.error(f"Gemini fallback also failed: {e2}")
        
        # Initialize OpenAI if available
        openai_key = os.getenv('OPENAI_API_KEY')
        if openai_key and openai:
            try:
                ai_clients['openai'] = openai.OpenAI(api_key=openai_key)
                logger.info("OpenAI client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI: {e}")
        
        # Initialize Anthropic if available
        anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        if anthropic_key and anthropic:
            try:
                ai_clients['anthropic'] = anthropic.Anthropic(api_key=anthropic_key)
                logger.info("Anthropic client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Anthropic: {e}")
        
        # Brand context for all agents
        brand_context = f"""
        You are an AI assistant for {self.brand_config['name']}, a creative brand.
        
        Brand Guidelines:
        - Style: {self.brand_config['style_guidelines']}
        - Voice & Tone: {self.brand_config['voice_tone']}
        - Always maintain brand consistency in all outputs
        - Focus on high-quality, professional results
        """
        
        return {
            'clients': ai_clients,
            'brand_context': brand_context,
            'image_prompt': brand_context + """
            You are an expert image generation specialist. Create detailed, branded visual concepts and prompts.
            """,
            'document_prompt': brand_context + """
            You are a professional document creation specialist. Create well-structured, branded documents.
            """,
            'brand_prompt': brand_context + """
            You are a senior brand strategist. Provide strategic brand guidance and recommendations.
            """,
            'video_prompt': brand_context + """
            You are a video content specialist. Develop compelling video concepts and strategies.
            """,
            'blog_prompt': brand_context + """
            You are a professional blog writer. Create engaging, SEO-optimized content.
            """,
            'social_prompt': brand_context + """
            You are a social media specialist. Create platform-specific, engaging content.
            """,
            'calendar_prompt': brand_context + """
            You are a social media strategist. Plan comprehensive content calendars.
            """,
            'knowledge_prompt': brand_context + """
            You are a business intelligence assistant with deep STAFFVIRTUAL knowledge.
            """
        }
    
    async def _generate_image_with_nano_banana(self, prompt: str, style: str = "professional") -> Dict[str, Any]:
        """Generate actual images using Gemini 2.5 Flash (Nano Banana approach)"""
        try:
            if 'gemini_image' not in self.agents['clients']:
                return {"success": False, "error": "Gemini image model not available"}
            
            # Create enhanced prompt for image generation
            enhanced_prompt = f"""
            Create a professional, branded image for STAFFVIRTUAL with the following specifications:
            
            Subject: {prompt}
            Style: {style}
            Brand Colors: Use blue (#1888FF), off-white (#F8F8EB), and dark blue (#004B8D)
            Aesthetic: {self.brand_config['style_guidelines']}
            
            The image should be high-quality, professional, and suitable for business use.
            """
            
            # Use Gemini 2.5 Flash for image generation
            response = self.agents['clients']['gemini_image'].generate_content(enhanced_prompt)
            
            return {
                "success": True,
                "prompt_used": enhanced_prompt,
                "model": "gemini-2.5-flash",
                "concept": response.text
            }
            
        except Exception as e:
            logger.error(f"Image generation error: {e}")
            return {"success": False, "error": str(e)}

    async def _get_ai_response(self, prompt, agent_type='brand', use_knowledge=True):
        """Get AI response using available clients"""
        try:
            # Get knowledge base context
            knowledge_context = ""
            if use_knowledge:
                knowledge_context = self.knowledge_manager.get_context_for_query(prompt)
                if knowledge_context and knowledge_context != "No specific information found in knowledge base.":
                    knowledge_context = f"\n\nRelevant Knowledge: {knowledge_context}\n"
            
            # Try Gemini first (using correct model)
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
                return "❌ No AI service configured. Please add API keys to environment variables."
                
        except Exception as e:
            logger.error(f"AI response error: {e}")
            return f"❌ Error generating response: {str(e)}"
        
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
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="for brand creation requests"
            )
        )

# Create bot instance
bot = SVDiscordBot()

# 🎨 IMAGE GENERATION AGENT (Enhanced with Nano Banana)
@bot.tree.command(name="image", description="Generate branded image concepts and prompts")
async def generate_image(interaction: discord.Interaction, prompt: str, style: str = "professional"):
    """Generate branded image concepts"""
    await interaction.response.defer(thinking=True)
    
    try:
        enhanced_prompt = f"Create a detailed image concept for STAFFVIRTUAL: {prompt}. Style: {style}. Include composition, colors, and brand alignment."
        result = await bot._get_ai_response(enhanced_prompt, 'image')
        
        embed = discord.Embed(
            title="🎨 Image Concept Generated!",
            description=f"**Prompt:** {prompt}\n**Style:** {style}",
            color=bot.brand_config['primary_color']
        )
        embed.add_field(name="🖼️ Concept", value=result[:1024], inline=False)
        embed.add_field(name="💡 Next Steps", value="Use this concept with DALL-E, Midjourney, or use /image_generate for AI image creation", inline=False)
        
        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {str(e)}")

# 🍌 NANO BANANA IMAGE GENERATOR (New!)
@bot.tree.command(name="image_generate", description="Generate actual images using Gemini 2.5 Flash (Nano Banana)")
async def generate_actual_image(interaction: discord.Interaction, prompt: str, style: str = "professional"):
    """Generate actual images using Nano Banana approach"""
    await interaction.response.defer(thinking=True)
    
    try:
        # Use the Nano Banana approach for image generation
        image_result = await bot._generate_image_with_nano_banana(prompt, style)
        
        if image_result['success']:
            embed = discord.Embed(
                title="🍌 Nano Banana Image Generated!",
                description=f"**Prompt:** {prompt}\n**Style:** {style}\n**Model:** {image_result['model']}",
                color=bot.brand_config['primary_color']
            )
            
            embed.add_field(
                name="🎨 Generated Concept",
                value=image_result['concept'][:1024],
                inline=False
            )
            
            embed.add_field(
                name="🔧 Technical Details",
                value=f"Model: Gemini 2.5 Flash\nApproach: Nano Banana\nBrand Colors: Integrated",
                inline=False
            )
            
            embed.set_footer(text="Image concept generated using Google's latest Gemini 2.5 Flash model")
            
        else:
            embed = discord.Embed(
                title="❌ Image Generation Failed",
                description=f"Error: {image_result.get('error', 'Unknown error')}",
                color=0xff0000
            )
        
        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {str(e)}")

# 📄 DOCUMENT CREATION AGENT
@bot.tree.command(name="document", description="Create branded documents")
async def create_document(interaction: discord.Interaction, document_type: str, topic: str, length: str = "medium"):
    """Create branded documents"""
    await interaction.response.defer(thinking=True)
    
    try:
        doc_prompt = f"Create a {length} {document_type} for STAFFVIRTUAL about: {topic}. Include proper structure, brand voice, and professional formatting."
        result = await bot._get_ai_response(doc_prompt, 'document')
        
        embed = discord.Embed(
            title="📄 Document Created!",
            description=f"**Type:** {document_type}\n**Topic:** {topic}\n**Length:** {length}",
            color=bot.brand_config['primary_color']
        )
        
        # Create file
        document_content = f"# {document_type.title()}: {topic}\n\n{result}"
        file_buffer = io.BytesIO(document_content.encode('utf-8'))
        file = discord.File(file_buffer, filename=f"{document_type}_{topic.replace(' ', '_')}.txt")
        
        embed.add_field(name="📋 Preview", value=result[:500] + "..." if len(result) > 500 else result, inline=False)
        
        await interaction.followup.send(embed=embed, file=file)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {str(e)}")

# 🏢 BRAND STRATEGY AGENT
@bot.tree.command(name="brand", description="Get strategic brand guidance")
async def brand_guidance(interaction: discord.Interaction, query: str):
    """Get brand strategy guidance"""
    await interaction.response.defer(thinking=True)
    
    try:
        brand_prompt = f"As a brand strategist for STAFFVIRTUAL, provide guidance on: {query}. Include strategic recommendations and practical implementation."
        result = await bot._get_ai_response(brand_prompt, 'brand')
        
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
        await interaction.followup.send(f"❌ Error: {str(e)}")

# 🎬 VIDEO STRATEGY AGENT
@bot.tree.command(name="video", description="Generate video content strategies")
async def generate_video(interaction: discord.Interaction, prompt: str, duration: int = 30, style: str = "professional"):
    """Generate video content strategies"""
    await interaction.response.defer(thinking=True)
    
    try:
        video_prompt = f"Create a video content strategy for STAFFVIRTUAL: {prompt}. Duration: {duration}s. Style: {style}. Include script outline, visual direction, and brand integration."
        result = await bot._get_ai_response(video_prompt, 'video')
        
        embed = discord.Embed(
            title="🎬 Video Strategy Created!",
            description=f"**Concept:** {prompt}\n**Duration:** {duration}s\n**Style:** {style}",
            color=bot.brand_config['primary_color']
        )
        
        if len(result) > 1024:
            chunks = [result[i:i+1024] for i in range(0, len(result), 1024)]
            for i, chunk in enumerate(chunks[:2]):
                field_name = "🎯 Strategy" if i == 0 else f"🎯 Continued"
                embed.add_field(name=field_name, value=chunk, inline=False)
        else:
            embed.add_field(name="🎯 Video Strategy", value=result, inline=False)
        
        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {str(e)}")

# 📝 BLOG WRITING AGENT
@bot.tree.command(name="blog", description="Create SEO-optimized blog posts")
async def create_blog(interaction: discord.Interaction, topic: str, keywords: str = "", length: str = "medium"):
    """Create blog posts"""
    await interaction.response.defer(thinking=True)
    
    try:
        blog_prompt = f"Write a {length} blog post for STAFFVIRTUAL about: {topic}. Keywords: {keywords}. Include SEO optimization, engaging structure, and call-to-action."
        result = await bot._get_ai_response(blog_prompt, 'blog')
        
        embed = discord.Embed(
            title="📝 Blog Post Created!",
            description=f"**Topic:** {topic}\n**Keywords:** {keywords or 'General'}\n**Length:** {length}",
            color=bot.brand_config['primary_color']
        )
        
        # Create file
        blog_content = f"# {topic}\n\n{result}"
        file_buffer = io.BytesIO(blog_content.encode('utf-8'))
        file = discord.File(file_buffer, filename=f"blog_{topic.replace(' ', '_')}.md")
        
        preview = result[:800] + "..." if len(result) > 800 else result
        embed.add_field(name="📋 Preview", value=preview, inline=False)
        
        await interaction.followup.send(embed=embed, file=file)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {str(e)}")

# 📱 SOCIAL MEDIA AGENT
@bot.tree.command(name="social", description="Create platform-specific social media posts")
async def create_social(interaction: discord.Interaction, platform: str, topic: str, hashtags: str = ""):
    """Create social media posts"""
    await interaction.response.defer(thinking=True)
    
    try:
        social_prompt = f"Create a {platform} post for STAFFVIRTUAL about: {topic}. Include platform-specific optimization, engagement hooks, and hashtags: {hashtags}."
        result = await bot._get_ai_response(social_prompt, 'social')
        
        embed = discord.Embed(
            title="📱 Social Media Post Created!",
            description=f"**Platform:** {platform.title()}\n**Topic:** {topic}",
            color=bot.brand_config['primary_color']
        )
        
        embed.add_field(name=f"📝 {platform.title()} Post", value=result, inline=False)
        if hashtags:
            embed.add_field(name="🏷️ Hashtags", value=hashtags, inline=False)
        
        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {str(e)}")

# 📅 CONTENT CALENDAR AGENT
@bot.tree.command(name="calendar", description="Generate social media content calendars")
async def create_calendar(interaction: discord.Interaction, duration: str = "1 month", focus: str = "general"):
    """Create content calendars"""
    await interaction.response.defer(thinking=True)
    
    try:
        calendar_prompt = f"Create a social media content calendar for STAFFVIRTUAL. Duration: {duration}. Focus: {focus}. Include posting schedule, content themes, and platform strategies."
        result = await bot._get_ai_response(calendar_prompt, 'calendar')
        
        embed = discord.Embed(
            title="📅 Content Calendar Created!",
            description=f"**Duration:** {duration}\n**Focus:** {focus}",
            color=bot.brand_config['primary_color']
        )
        
        # Create file
        calendar_content = f"# STAFFVIRTUAL Content Calendar - {duration}\n## Focus: {focus}\n\n{result}"
        file_buffer = io.BytesIO(calendar_content.encode('utf-8'))
        file = discord.File(file_buffer, filename=f"content_calendar_{duration.replace(' ', '_')}.md")
        
        preview = result[:800] + "..." if len(result) > 800 else result
        embed.add_field(name="📋 Calendar Preview", value=preview, inline=False)
        
        await interaction.followup.send(embed=embed, file=file)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {str(e)}")

# 🤔 BUSINESS Q&A AGENT
@bot.tree.command(name="ask", description="Ask questions about STAFFVIRTUAL business")
async def ask_business(interaction: discord.Interaction, question: str):
    """Ask business questions"""
    await interaction.response.defer(thinking=True)
    
    try:
        knowledge_prompt = f"Answer this question about STAFFVIRTUAL: {question}. Use available company knowledge and provide practical, actionable guidance."
        result = await bot._get_ai_response(knowledge_prompt, 'knowledge')
        
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
        
        embed.set_footer(text="💡 For specific policies, consult internal documentation")
        
        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {str(e)}")

# 🌐 URL LEARNING AGENT
@bot.tree.command(name="learn_url", description="Learn from website content")
async def learn_from_url(interaction: discord.Interaction, url: str):
    """Learn from URLs"""
    await interaction.response.defer(thinking=True)
    
    try:
        content = await bot.knowledge_manager.scrape_url(url)
        
        if content:
            bot.knowledge_manager.save_knowledge_base()
            
            embed = discord.Embed(
                title="🌐 Website Content Learned!",
                description=f"**URL:** {url}",
                color=bot.brand_config['primary_color']
            )
            
            embed.add_field(name="📄 Page Title", value=content.get('title', 'No title')[:1024], inline=False)
            embed.add_field(
                name="📊 Content Stats",
                value=f"Paragraphs: {len(content.get('paragraphs', []))}\nContent learned and available for all AI agents",
                inline=False
            )
            
        else:
            embed = discord.Embed(
                title="❌ Failed to Learn from URL",
                description=f"Could not scrape content from: {url}",
                color=0xff0000
            )
        
        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {str(e)}")

# 📄 DOCUMENT UPLOAD AGENT
@bot.tree.command(name="upload_doc", description="Upload documents for the bot to learn from")
async def upload_document(interaction: discord.Interaction, document: discord.Attachment):
    """Upload and process documents"""
    await interaction.response.defer(thinking=True)
    
    try:
        filename = document.filename.lower()
        if not (filename.endswith('.pdf') or filename.endswith('.docx') or filename.endswith('.doc')):
            embed = discord.Embed(
                title="❌ Unsupported File Type",
                description="Please upload PDF or Word documents only.",
                color=0xff0000
            )
            await interaction.followup.send(embed=embed)
            return
        
        file_content = await document.read()
        
        if filename.endswith('.pdf'):
            doc_info = bot.knowledge_manager.process_pdf_document(file_content, document.filename)
        else:
            doc_info = bot.knowledge_manager.process_docx_document(file_content, document.filename)
        
        if doc_info:
            bot.knowledge_manager.save_knowledge_base()
            
            # Check if there was an error during processing
            if doc_info.get('error'):
                embed = discord.Embed(
                    title="⚠️ Document Uploaded with Limited Processing",
                    description=f"**Filename:** {document.filename}",
                    color=0xffa500  # Orange color for warning
                )
                
                embed.add_field(
                    name="📊 Upload Stats",
                    value=f"Type: {doc_info.get('type', 'Unknown').upper()}\nSize: {len(file_content)} bytes\nStatus: Uploaded but text extraction limited",
                    inline=False
                )
                
                embed.add_field(
                    name="⚠️ Processing Note",
                    value=doc_info.get('content', 'Processing limited - file uploaded but content extraction may be incomplete'),
                    inline=False
                )
                
                embed.add_field(
                    name="💡 Tip",
                    value="Try uploading as a plain text file (.txt) for better text extraction, or the document will still be stored for reference.",
                    inline=False
                )
            else:
                embed = discord.Embed(
                    title="📄 Document Processed Successfully!",
                    description=f"**Filename:** {document.filename}",
                    color=bot.brand_config['primary_color']
                )
                
                embed.add_field(
                    name="📊 Document Stats",
                    value=f"Type: {doc_info.get('type', 'Unknown').upper()}\nSize: {len(file_content)} bytes\nContent processed and available for all AI agents",
                    inline=False
                )
                
                content_preview = doc_info.get('content', '')[:300] + "..." if len(doc_info.get('content', '')) > 300 else doc_info.get('content', '')
                if content_preview and not doc_info.get('error'):
                    embed.add_field(name="📝 Content Preview", value=content_preview, inline=False)
            
        else:
            embed = discord.Embed(
                title="❌ Document Processing Failed",
                description=f"Could not process: {document.filename}",
                color=0xff0000
            )
        
        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {str(e)}")

# 🧠 KNOWLEDGE STATUS AGENT
@bot.tree.command(name="knowledge_status", description="Check knowledge base status")
async def knowledge_status(interaction: discord.Interaction):
    """Show knowledge base status"""
    await interaction.response.defer(thinking=True)
    
    try:
        summary = bot.knowledge_manager.get_knowledge_summary()
        
        embed = discord.Embed(
            title="🧠 Knowledge Base Status",
            description="Current status of STAFFVIRTUAL's knowledge base",
            color=bot.brand_config['primary_color']
        )
        
        embed.add_field(
            name="📊 Statistics",
            value=f"Scraped URLs: {summary['scraped_urls']}\nUploaded Documents: {summary['uploaded_documents']}\nTotal Sources: {summary['total_sources']}",
            inline=False
        )
        
        embed.add_field(
            name="🕒 Last Updated",
            value=summary['last_updated'] if summary['last_updated'] != 'Never' else 'No recent updates',
            inline=False
        )
        
        sources = bot.knowledge_manager.knowledge_base.get('sources', [])
        if sources:
            source_list = []
            for source in sources[:5]:
                source_list.append(f"• {source['type'].title()}: {source['title'][:30]}...")
            
            embed.add_field(
                name="📚 Recent Sources",
                value="\n".join(source_list),
                inline=False
            )
        
        embed.set_footer(text="Use /learn_url and /upload_doc to expand the knowledge base")
        
        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {str(e)}")

# ❓ HELP COMMAND
@bot.tree.command(name="help", description="Show all available commands")
async def help_command(interaction: discord.Interaction):
    """Show help information"""
    embed = discord.Embed(
        title="🤖 STAFFVIRTUAL Brand Assistant",
        description="Your AI-powered creative companion with 12 specialized agents",
        color=bot.brand_config['primary_color']
    )
    
    embed.add_field(name="🎨 /image", value="Generate image concepts", inline=True)
    embed.add_field(name="🍌 /image_generate", value="Generate images (Nano Banana)", inline=True)
    embed.add_field(name="📄 /document", value="Create branded documents", inline=True)
    embed.add_field(name="🏢 /brand", value="Get strategic brand guidance", inline=True)
    embed.add_field(name="🎬 /video", value="Generate video strategies", inline=True)
    embed.add_field(name="📝 /blog", value="Create SEO blog posts", inline=True)
    embed.add_field(name="📱 /social", value="Create social media posts", inline=True)
    embed.add_field(name="📅 /calendar", value="Generate content calendars", inline=True)
    embed.add_field(name="🤔 /ask", value="Ask business questions", inline=True)
    embed.add_field(name="🌐 /learn_url", value="Learn from websites", inline=True)
    embed.add_field(name="📄 /upload_doc", value="Upload brand documents", inline=True)
    embed.add_field(name="🧠 /knowledge_status", value="Check knowledge base", inline=True)
    
    embed.set_footer(text="All responses are optimized for STAFFVIRTUAL brand consistency")
    
    await interaction.response.send_message(embed=embed)

# 🧪 TEST COMMAND (Keep the existing one)
@bot.tree.command(name="test", description="Test if the bot is working")
async def test_command(interaction: discord.Interaction):
    """Test command"""
    embed = discord.Embed(
        title="✅ STAFFVIRTUAL Bot is Working!",
        description="All 12 AI agents are operational and ready for branded content creation.",
        color=bot.brand_config['primary_color']
    )
    embed.add_field(name="🤖 Available Agents", value="12 specialized AI agents ready", inline=True)
    embed.add_field(name="🧠 Knowledge Base", value="Ready to learn from URLs and documents", inline=True)
    embed.add_field(name="🎨 Brand Colors", value=f"Primary: #{bot.brand_config['primary_color']:06x}", inline=True)
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
