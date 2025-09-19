import discord
from discord.ext import commands
import asyncio
import logging
import os
from dotenv import load_dotenv
import io
import json
import tempfile

# AI Libraries with Nano Banana support
try:
    from google import genai
    from google.genai import types
    NANO_BANANA_AVAILABLE = True
except ImportError:
    try:
        import google.generativeai as genai
        types = None
        NANO_BANANA_AVAILABLE = False
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
            description='STAFFVIRTUAL Strategic Marketing Suite - High-Quality AI Agents'
        )
        
        # Brand configuration
        def parse_color(color_str, default):
            try:
                if not color_str or color_str.strip() == '':
                    return int(default.replace('#', ''), 16)
                color_clean = color_str.replace('#', '').strip()
                return int(color_clean, 16) if len(color_clean) == 6 else int(default.replace('#', ''), 16)
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
        
        self.ai_clients = self._initialize_ai_clients()
        self.knowledge_manager = KnowledgeManager()
        
        # Enhanced brand context with specific company details
        self.brand_dna = f"""
        STAFFVIRTUAL Brand DNA:
        
        Company: Premium virtual staffing and business support services
        Mission: Provide high-quality virtual staffing solutions that help businesses scale efficiently
        Target Market: Small to medium businesses, startups, entrepreneurs, growing companies
        Services: Virtual Assistants, Creative Services, Technical Support, Marketing Services
        
        Brand Identity:
        - Colors: Primary #1888FF (Trust Blue), Secondary #F8F8EB (Clean White), Accent #004B8D (Authority Blue)
        - Style: {self.brand_config['style_guidelines']}
        - Voice: {self.brand_config['voice_tone']}
        - Values: Reliability, Professionalism, Innovation, Efficiency, Transparency
        
        Competitive Advantages:
        - Carefully vetted virtual professionals
        - Flexible engagement models (hourly, project, retainer)
        - 24/7 support availability
        - Industry expertise across multiple sectors
        - Scalable solutions that grow with business needs
        
        Key Differentiators:
        - Premium quality over low-cost alternatives
        - Specialized expertise in virtual team management
        - Proven track record of client success
        - Technology-enabled service delivery
        - Focus on long-term partnership relationships
        """
    
    def _initialize_ai_clients(self):
        """Initialize AI clients"""
        clients = {}
        gemini_key = os.getenv('GEMINI_API_KEY')
        
        if gemini_key and genai:
            try:
                if NANO_BANANA_AVAILABLE and types:
                    clients['nano_banana'] = genai.Client(api_key=gemini_key)
                    logger.info("Nano Banana client initialized!")
                else:
                    genai.configure(api_key=gemini_key)
                    clients['gemini'] = genai.GenerativeModel('gemini-1.5-flash')
                    logger.info("Gemini client initialized")
            except Exception as e:
                logger.error(f"Gemini init error: {e}")
        
        openai_key = os.getenv('OPENAI_API_KEY')
        if openai_key and openai:
            try:
                clients['openai'] = openai.OpenAI(api_key=openai_key)
                logger.info("OpenAI client initialized")
            except Exception as e:
                logger.error(f"OpenAI init error: {e}")
        
        return clients
    
    async def _generate_nano_banana_image(self, prompt: str, style: str = "professional"):
        """Generate images using Nano Banana"""
        try:
            if 'nano_banana' not in self.ai_clients:
                return {"success": False, "error": "Nano Banana not available"}
            
            branded_prompt = f"Create professional STAFFVIRTUAL image: {prompt}. Style: {style}. Brand colors: blue (#1888FF), off-white (#F8F8EB), dark blue (#004B8D). Professional, modern, clean aesthetic suitable for virtual staffing company marketing."
            
            response = self.ai_clients['nano_banana'].models.generate_content(
                model="gemini-2.5-flash-image-preview",
                contents=[branded_prompt]
            )
            
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'inline_data') and part.inline_data is not None:
                    image_data = part.inline_data.data
                    
                    if Image:
                        image = Image.open(io.BytesIO(image_data))
                        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
                        image.save(temp_file.name, 'PNG')
                        
                        return {
                            "success": True,
                            "image_path": temp_file.name,
                            "description": "STAFFVIRTUAL branded image generated",
                            "model": "gemini-2.5-flash-image-preview"
                        }
            
            return {"success": False, "error": "No image data received"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _get_ai_response(self, prompt, system_context="", use_knowledge=True, max_length=900):
        """Get AI response with improved prompting and length control"""
        try:
            # Enhanced prompt engineering for better results
            enhanced_prompt = f"""
            {self.brand_dna}
            
            Your Role: {system_context}
            
            User Request: {prompt}
            
            Instructions:
            1. Provide specific, actionable guidance tailored to STAFFVIRTUAL
            2. Reference our actual services, values, and competitive advantages
            3. Keep response under {max_length} characters for optimal display
            4. Focus on practical, implementable recommendations
            5. Maintain our professional yet approachable brand voice
            6. Include specific next steps or action items
            
            Respond with expertise and specificity, not generic advice.
            """
            
            # Try Nano Banana first
            if 'nano_banana' in self.ai_clients:
                try:
                    response = self.ai_clients['nano_banana'].models.generate_content(
                        model="gemini-2.0-flash-exp",
                        contents=[enhanced_prompt]
                    )
                    result = response.candidates[0].content.parts[0].text
                    # Truncate if too long
                    return result[:max_length] + "..." if len(result) > max_length else result
                except Exception as e:
                    logger.error(f"Nano Banana text error: {e}")
            
            # Try legacy Gemini
            if 'gemini' in self.ai_clients:
                try:
                    response = self.ai_clients['gemini'].generate_content(enhanced_prompt)
                    result = response.text
                    return result[:max_length] + "..." if len(result) > max_length else result
                except Exception as e:
                    logger.error(f"Gemini error: {e}")
            
            # Try OpenAI
            if 'openai' in self.ai_clients:
                try:
                    response = self.ai_clients['openai'].chat.completions.create(
                        model="gpt-4",
                        messages=[
                            {"role": "system", "content": self.brand_dna + "\n" + system_context},
                            {"role": "user", "content": prompt}
                        ],
                        max_tokens=1500
                    )
                    result = response.choices[0].message.content
                    return result[:max_length] + "..." if len(result) > max_length else result
                except Exception as e:
                    logger.error(f"OpenAI error: {e}")
            
            return "❌ No AI service available."
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    def _add_to_knowledge_base(self, title: str, content: str):
        """Add to simple knowledge base"""
        try:
            if not hasattr(self, 'knowledge_base'):
                self.knowledge_base = {"manual_entries": {}, "scraped_content": {}}
            self.knowledge_base["manual_entries"][title] = {"content": content, "type": "manual"}
            return True
        except:
            return False
        
    async def setup_hook(self):
        logger.info("Setting up STAFFVIRTUAL Strategic Marketing Suite...")
        try:
            synced = await self.tree.sync()
            logger.info(f"Synced {len(synced)} specialized agents")
        except Exception as e:
            logger.error(f"Sync error: {e}")
    
    async def on_ready(self):
        logger.info(f'{self.user} connected! Services: {list(self.ai_clients.keys())}')
        logger.info(f"Nano Banana: {NANO_BANANA_AVAILABLE}")
        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="STAFFVIRTUAL marketing ops"))

# Bot instance
bot = SVDiscordBot()

# ===== CREATIVE & CONTENT AGENTS =====

@bot.tree.command(name="image", description="🎨 Generate branded images (Nano Banana)")
async def cmd_image(interaction: discord.Interaction, prompt: str, style: str = "professional"):
    await interaction.response.defer(thinking=True)
    try:
        result = await bot._generate_nano_banana_image(prompt, style)
        if result['success'] and result.get('image_path'):
            embed = discord.Embed(
                title="🍌 STAFFVIRTUAL Image Generated!",
                description=f"**Prompt:** {prompt}\n**Style:** {style}",
                color=bot.brand_config['primary_color']
            )
            file = discord.File(result['image_path'], filename=f"staffvirtual_{prompt.replace(' ', '_')[:20]}.png")
            embed.set_image(url=f"attachment://staffvirtual_{prompt.replace(' ', '_')[:20]}.png")
            await interaction.followup.send(embed=embed, file=file)
            try: os.unlink(result['image_path'])
            except: pass
        else:
            concept = await bot._get_ai_response(f"Create detailed STAFFVIRTUAL image concept: {prompt}, style: {style}", "Expert image concept designer specializing in virtual staffing company branding")
            embed = discord.Embed(title="🎨 STAFFVIRTUAL Image Concept", color=bot.brand_config['primary_color'])
            embed.add_field(name="🖼️ Concept", value=concept, inline=False)
            await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {str(e)}")

@bot.tree.command(name="content", description="📝 Blog posts, SEO content, keywords")
async def cmd_content(interaction: discord.Interaction, content_type: str, topic: str, keywords: str = ""):
    await interaction.response.defer(thinking=True)
    try:
        system_context = "Senior content marketing strategist and SEO specialist for STAFFVIRTUAL. Expert in virtual staffing industry content that drives qualified leads and establishes thought leadership."
        
        prompt = f"""
        Create high-converting {content_type} for STAFFVIRTUAL about: {topic}
        Target Keywords: {keywords or 'virtual assistants, remote work, business efficiency'}
        
        Requirements:
        - Position STAFFVIRTUAL as the premium virtual staffing solution
        - Include specific benefits of our services
        - Address common pain points of our target market (SMBs, startups)
        - Include compelling statistics and industry insights
        - End with clear call-to-action for consultation or service inquiry
        - Optimize for search engines and lead generation
        """
        
        result = await bot._get_ai_response(prompt, system_context, max_length=2000)
        
        embed = discord.Embed(
            title="📝 STAFFVIRTUAL Content Created!",
            description=f"**Type:** {content_type}\n**Topic:** {topic}",
            color=bot.brand_config['primary_color']
        )
        
        # Create file
        file_buffer = io.BytesIO(f"# STAFFVIRTUAL {content_type.title()}: {topic}\n\n{result}".encode('utf-8'))
        file = discord.File(file_buffer, filename=f"STAFFVIRTUAL_{content_type}_{topic.replace(' ', '_')}.md")
        
        # Safe preview length
        preview = result[:800] + "..." if len(result) > 800 else result
        embed.add_field(name="📋 Content Preview", value=preview, inline=False)
        
        await interaction.followup.send(embed=embed, file=file)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {str(e)}")

@bot.tree.command(name="social", description="📱 Platform-specific social media posts")
async def cmd_social(interaction: discord.Interaction, platform: str, topic: str, hashtags: str = ""):
    await interaction.response.defer(thinking=True)
    try:
        system_context = f"Expert social media strategist for STAFFVIRTUAL specializing in {platform} marketing for virtual staffing companies. Focus on lead generation and engagement."
        
        prompt = f"""
        Create a high-engagement {platform} post for STAFFVIRTUAL about: {topic}
        
        STAFFVIRTUAL Context:
        - We provide premium virtual assistants and remote staff
        - Target audience: Business owners, entrepreneurs, growing companies
        - Key benefits: Cost savings, flexibility, expertise, scalability
        
        Platform Strategy for {platform}:
        - LinkedIn: B2B professional content, thought leadership, case studies
        - Instagram: Behind-the-scenes, team culture, visual storytelling
        - Twitter: Industry insights, quick tips, trending topics
        - Facebook: Community building, educational content, testimonials
        
        Include:
        - Attention-grabbing hook
        - Specific STAFFVIRTUAL value proposition
        - Clear call-to-action
        - Strategic hashtags: {hashtags or 'research and suggest 5-10 optimal hashtags'}
        """
        
        result = await bot._get_ai_response(prompt, system_context, max_length=900)
        
        embed = discord.Embed(
            title="📱 STAFFVIRTUAL Social Media Post!",
            description=f"**Platform:** {platform.title()}\n**Topic:** {topic}",
            color=bot.brand_config['primary_color']
        )
        
        embed.add_field(name=f"📝 {platform.title()} Post", value=result, inline=False)
        embed.set_footer(text=f"Optimized for {platform} engagement and STAFFVIRTUAL lead generation")
        
        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {str(e)}")

@bot.tree.command(name="brand", description="🏢 Strategic brand guidance")
async def cmd_brand(interaction: discord.Interaction, query: str):
    await interaction.response.defer(thinking=True)
    try:
        system_context = "Senior brand strategist and consultant specifically for STAFFVIRTUAL. Expert in virtual staffing industry positioning, competitive differentiation, and premium service branding."
        
        prompt = f"""
        Provide strategic brand guidance for STAFFVIRTUAL regarding: {query}
        
        Context: STAFFVIRTUAL is a premium virtual staffing company competing against both low-cost offshore providers and traditional staffing agencies.
        
        Consider:
        - Our premium positioning and quality focus
        - Target market of growing SMBs and startups
        - Competitive landscape in virtual staffing
        - Our core values: reliability, professionalism, innovation
        - Need to differentiate from commodity virtual assistant services
        
        Provide specific, actionable recommendations that strengthen our market position.
        """
        
        result = await bot._get_ai_response(prompt, system_context, max_length=900)
        
        embed = discord.Embed(
            title="🏢 STAFFVIRTUAL Brand Strategy",
            description=f"**Query:** {query}",
            color=bot.brand_config['primary_color']
        )
        
        embed.add_field(name="📋 Strategic Guidance", value=result, inline=False)
        
        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {str(e)}")

@bot.tree.command(name="document", description="📄 Business documents and proposals")
async def cmd_document(interaction: discord.Interaction, document_type: str, topic: str, length: str = "medium"):
    await interaction.response.defer(thinking=True)
    try:
        system_context = "Professional business document specialist for STAFFVIRTUAL. Expert in creating compelling proposals, case studies, and business documents for virtual staffing services."
        
        prompt = f"""
        Create a {length} {document_type} for STAFFVIRTUAL about: {topic}
        
        Document should:
        - Clearly articulate STAFFVIRTUAL's value proposition
        - Address specific client pain points and challenges
        - Include relevant case studies or success metrics
        - Maintain professional tone while being approachable
        - Include clear next steps and call-to-action
        - Reflect our premium positioning in the virtual staffing market
        """
        
        result = await bot._get_ai_response(prompt, system_context, max_length=2000)
        
        embed = discord.Embed(
            title="📄 STAFFVIRTUAL Document Created!",
            description=f"**Type:** {document_type}\n**Topic:** {topic}",
            color=bot.brand_config['primary_color']
        )
        
        # Create file
        file_buffer = io.BytesIO(f"# STAFFVIRTUAL {document_type.title()}: {topic}\n\n{result}".encode('utf-8'))
        file = discord.File(file_buffer, filename=f"STAFFVIRTUAL_{document_type}_{topic.replace(' ', '_')}.txt")
        
        preview = result[:500] + "..." if len(result) > 500 else result
        embed.add_field(name="📋 Document Preview", value=preview, inline=False)
        
        await interaction.followup.send(embed=embed, file=file)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {str(e)}")

@bot.tree.command(name="ask", description="🤔 Ask questions about STAFFVIRTUAL")
async def cmd_ask(interaction: discord.Interaction, question: str):
    await interaction.response.defer(thinking=True)
    try:
        system_context = "Business intelligence assistant with comprehensive knowledge of STAFFVIRTUAL's services, processes, competitive advantages, and market positioning."
        
        prompt = f"""
        Answer this question about STAFFVIRTUAL: {question}
        
        Provide accurate information about:
        - Our virtual staffing services and capabilities
        - Competitive advantages and differentiators
        - Target market and ideal clients
        - Pricing models and service packages
        - Success stories and client outcomes
        - Company values and approach
        
        If specific information isn't available, provide general guidance based on virtual staffing industry best practices.
        """
        
        result = await bot._get_ai_response(prompt, system_context, use_knowledge=True, max_length=900)
        
        embed = discord.Embed(
            title="🤔 STAFFVIRTUAL Business Q&A",
            description=f"**Question:** {question}",
            color=bot.brand_config['primary_color']
        )
        
        embed.add_field(name="💡 Answer", value=result, inline=False)
        embed.set_footer(text="Based on STAFFVIRTUAL knowledge base and industry expertise")
        
        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {str(e)}")

# ===== UTILITY =====

@bot.tree.command(name="test", description="🧪 Test system functionality")
async def cmd_test(interaction: discord.Interaction):
    try:
        embed = discord.Embed(
            title="✅ STAFFVIRTUAL Strategic Marketing Suite",
            description="High-quality AI agents ready for professional content creation",
            color=bot.brand_config['primary_color']
        )
        embed.add_field(name="🤖 AI Services", value=f"Available: {list(bot.ai_clients.keys())}", inline=False)
        embed.add_field(name="🍌 Nano Banana", value=f"{'✅ Available' if NANO_BANANA_AVAILABLE else '❌ Legacy mode'}", inline=False)
        embed.add_field(name="🧠 Knowledge", value="Enhanced brand DNA and context loaded", inline=False)
        embed.add_field(name="🎨 Brand", value=f"#{bot.brand_config['primary_color']:06x} • {bot.brand_config['voice_tone'][:30]}...", inline=False)
        
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"❌ Test failed: {str(e)}")

@bot.tree.command(name="help", description="❓ Show all commands")
async def cmd_help(interaction: discord.Interaction):
    try:
        embed = discord.Embed(
            title="🤖 STAFFVIRTUAL Strategic Marketing Suite",
            description="High-quality AI agents for professional content creation",
            color=bot.brand_config['primary_color']
        )
        
        embed.add_field(
            name="🎨 Creative & Content",
            value="• `/image` - Nano Banana generation\n• `/content` - Blog + SEO + keywords\n• `/social` - Social media posts\n• `/document` - Business documents",
            inline=False
        )
        
        embed.add_field(
            name="🏢 Business & Strategy", 
            value="• `/brand` - Strategic guidance\n• `/ask` - Business Q&A",
            inline=False
        )
        
        embed.add_field(
            name="🛠️ Utility",
            value="• `/test` - System status\n• `/help` - This menu",
            inline=False
        )
        
        embed.add_field(
            name="💡 Examples",
            value="`/brand 'How should we position against competitors?'`\n`/content blog 'Future of Remote Work' 'virtual assistants'`\n`/social LinkedIn 'productivity tips' '#productivity #remotework'`",
            inline=False
        )
        
        embed.set_footer(text="Enhanced AI with STAFFVIRTUAL brand DNA for superior results")
        
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"❌ Error: {str(e)}")

# Run the bot
if __name__ == "__main__":
    token = os.getenv('DISCORD_BOT_TOKEN')
    if not token:
        logger.error("DISCORD_BOT_TOKEN not found")
        exit(1)
    
    try:
        logger.info("Starting STAFFVIRTUAL Strategic Marketing Suite...")
        bot.run(token)
    except Exception as e:
        logger.error(f"Bot startup error: {e}")
        exit(1)
