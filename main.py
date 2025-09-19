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
            description='STAFFVIRTUAL Strategic Marketing Suite - 16 AI Agents'
        )
        
        # Brand configuration with safe parsing
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
                    logger.info("Gemini legacy client initialized")
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
            
            branded_prompt = f"Create professional STAFFVIRTUAL image: {prompt}. Style: {style}. Brand colors: blue (#1888FF), off-white (#F8F8EB), dark blue (#004B8D). Professional, modern, clean aesthetic."
            
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
    
    async def _get_ai_response(self, prompt, system_context="", use_knowledge=True):
        """Get AI response"""
        try:
            knowledge_context = ""
            if use_knowledge:
                try:
                    knowledge_context = self.knowledge_manager.get_context_for_query(prompt)
                    if knowledge_context and knowledge_context != "No specific information found in knowledge base.":
                        knowledge_context = f"\n\nSTAFFVIRTUAL Knowledge: {knowledge_context}\n"
                except:
                    knowledge_context = ""
            
            brand_context = f"""You are an AI for {self.brand_config['name']}, a premium virtual staffing company.
Brand: {self.brand_config['style_guidelines']}. Voice: {self.brand_config['voice_tone']}.
Colors: #1888FF, #F8F8EB, #004B8D. {system_context}"""
            
            full_context = brand_context + knowledge_context
            
            # Try Nano Banana first
            if 'nano_banana' in self.ai_clients:
                try:
                    response = self.ai_clients['nano_banana'].models.generate_content(
                        model="gemini-2.0-flash-exp",
                        contents=[f"{full_context}\n\nRequest: {prompt}"]
                    )
                    return response.candidates[0].content.parts[0].text
                except Exception as e:
                    logger.error(f"Nano Banana text error: {e}")
            
            # Try legacy Gemini
            if 'gemini' in self.ai_clients:
                try:
                    response = self.ai_clients['gemini'].generate_content(f"{full_context}\n\nRequest: {prompt}")
                    return response.text
                except Exception as e:
                    logger.error(f"Gemini error: {e}")
            
            # Try OpenAI
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
            
            return "❌ No AI service available."
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    def _add_to_knowledge_base(self, title: str, content: str):
        """Add to knowledge base"""
        try:
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
        logger.info(f'{self.user} connected! Available services: {list(self.ai_clients.keys())}')
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
            embed = discord.Embed(title="🍌 STAFFVIRTUAL Image Generated!", color=bot.brand_config['primary_color'])
            file = discord.File(result['image_path'], filename=f"staffvirtual_{prompt.replace(' ', '_')[:20]}.png")
            embed.set_image(url=f"attachment://staffvirtual_{prompt.replace(' ', '_')[:20]}.png")
            await interaction.followup.send(embed=embed, file=file)
            try: os.unlink(result['image_path'])
            except: pass
        else:
            concept = await bot._get_ai_response(f"Create detailed image concept: {prompt}, style: {style}", "Image concept designer")
            embed = discord.Embed(title="🎨 Image Concept", color=bot.brand_config['primary_color'])
            embed.add_field(name="🖼️ Concept", value=concept[:1024], inline=False)
            await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {str(e)}")

@bot.tree.command(name="content", description="📝 Blog posts, SEO content, keywords")
async def cmd_content(interaction: discord.Interaction, content_type: str, topic: str, keywords: str = ""):
    await interaction.response.defer(thinking=True)
    try:
        system_context = "Content marketing strategist and SEO specialist for STAFFVIRTUAL."
        prompt = f"Create {content_type} for STAFFVIRTUAL: {topic}. Keywords: {keywords or 'virtual assistants, remote work'}. Include SEO optimization and conversion focus."
        result = await bot._get_ai_response(prompt, system_context)
        
        embed = discord.Embed(title="📝 STAFFVIRTUAL Content Created!", color=bot.brand_config['primary_color'])
        file_buffer = io.BytesIO(f"# STAFFVIRTUAL {content_type}: {topic}\n\n{result}".encode('utf-8'))
        file = discord.File(file_buffer, filename=f"STAFFVIRTUAL_{content_type}_{topic.replace(' ', '_')}.md")
        embed.add_field(name="📋 Preview", value=result[:600] + "..." if len(result) > 600 else result, inline=False)
        
        await interaction.followup.send(embed=embed, file=file)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {str(e)}")

@bot.tree.command(name="social", description="📱 Platform-specific social media posts")
async def cmd_social(interaction: discord.Interaction, platform: str, topic: str, hashtags: str = ""):
    await interaction.response.defer(thinking=True)
    try:
        system_context = "Social media marketing expert for STAFFVIRTUAL."
        prompt = f"Create {platform} post for STAFFVIRTUAL: {topic}. Include engagement hooks, CTAs, hashtags: {hashtags or 'suggest optimal'}."
        result = await bot._get_ai_response(prompt, system_context)
        
        embed = discord.Embed(title="📱 STAFFVIRTUAL Social Post!", color=bot.brand_config['primary_color'])
        embed.add_field(name=f"📝 {platform.title()}", value=result, inline=False)
        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {str(e)}")

@bot.tree.command(name="calendar", description="📅 Strategic content calendars")
async def cmd_calendar(interaction: discord.Interaction, duration: str = "1 month", focus: str = "lead_generation"):
    await interaction.response.defer(thinking=True)
    try:
        system_context = "Content marketing strategist for STAFFVIRTUAL."
        prompt = f"Create strategic content calendar for {duration}, focus: {focus}. Multi-platform, lead generation optimized."
        result = await bot._get_ai_response(prompt, system_context)
        
        embed = discord.Embed(title="📅 STAFFVIRTUAL Calendar!", color=bot.brand_config['primary_color'])
        file_buffer = io.BytesIO(f"# STAFFVIRTUAL Calendar - {duration}\n{result}".encode('utf-8'))
        file = discord.File(file_buffer, filename=f"STAFFVIRTUAL_calendar_{duration.replace(' ', '_')}.md")
        embed.add_field(name="📋 Preview", value=result[:600] + "..." if len(result) > 600 else result, inline=False)
        
        await interaction.followup.send(embed=embed, file=file)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {str(e)}")

@bot.tree.command(name="newsletter", description="📰 Email campaigns and newsletters")
async def cmd_newsletter(interaction: discord.Interaction, newsletter_type: str, topic: str, audience: str = "prospects"):
    await interaction.response.defer(thinking=True)
    try:
        system_context = "Email marketing specialist for STAFFVIRTUAL."
        prompt = f"Create {newsletter_type} newsletter for STAFFVIRTUAL: {topic}. Audience: {audience}. Include subject lines, CTAs."
        result = await bot._get_ai_response(prompt, system_context)
        
        embed = discord.Embed(title="📰 STAFFVIRTUAL Newsletter!", color=bot.brand_config['primary_color'])
        embed.add_field(name="📧 Preview", value=result[:800] + "..." if len(result) > 800 else result, inline=False)
        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {str(e)}")

@bot.tree.command(name="document", description="📄 Business documents and proposals")
async def cmd_document(interaction: discord.Interaction, document_type: str, topic: str, length: str = "medium"):
    await interaction.response.defer(thinking=True)
    try:
        system_context = "Professional document specialist for STAFFVIRTUAL."
        prompt = f"Create {length} {document_type} for STAFFVIRTUAL: {topic}. Professional structure and brand voice."
        result = await bot._get_ai_response(prompt, system_context)
        
        embed = discord.Embed(title="📄 STAFFVIRTUAL Document!", color=bot.brand_config['primary_color'])
        file_buffer = io.BytesIO(f"# STAFFVIRTUAL {document_type}: {topic}\n\n{result}".encode('utf-8'))
        file = discord.File(file_buffer, filename=f"STAFFVIRTUAL_{document_type}_{topic.replace(' ', '_')}.txt")
        embed.add_field(name="📋 Preview", value=result[:500] + "..." if len(result) > 500 else result, inline=False)
        
        await interaction.followup.send(embed=embed, file=file)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {str(e)}")

# ===== GROWTH & CAMPAIGNS =====

@bot.tree.command(name="brand", description="🏢 Strategic brand guidance")
async def cmd_brand(interaction: discord.Interaction, query: str):
    await interaction.response.defer(thinking=True)
    try:
        system_context = "Senior brand strategist for STAFFVIRTUAL."
        result = await bot._get_ai_response(query, system_context)
        
        embed = discord.Embed(title="🏢 STAFFVIRTUAL Brand Strategy", color=bot.brand_config['primary_color'])
        embed.add_field(name="📋 Guidance", value=result[:1024], inline=False)
        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {str(e)}")

@bot.tree.command(name="growth", description="🎯 Ads, funnels, landing pages")
async def cmd_growth(interaction: discord.Interaction, growth_type: str, objective: str, audience: str = "SMBs"):
    await interaction.response.defer(thinking=True)
    try:
        system_context = "Growth marketing specialist for STAFFVIRTUAL."
        prompt = f"Create {growth_type} for STAFFVIRTUAL. Objective: {objective}. Audience: {audience}. Focus on conversion optimization."
        result = await bot._get_ai_response(prompt, system_context)
        
        embed = discord.Embed(title="🎯 STAFFVIRTUAL Growth Strategy!", color=bot.brand_config['primary_color'])
        embed.add_field(name="🚀 Strategy", value=result[:1024], inline=False)
        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {str(e)}")

@bot.tree.command(name="campaign", description="🎪 Comprehensive marketing campaigns")
async def cmd_campaign(interaction: discord.Interaction, campaign_type: str, goal: str, budget: str = "medium"):
    await interaction.response.defer(thinking=True)
    try:
        system_context = "Marketing campaign strategist for STAFFVIRTUAL."
        prompt = f"Design {campaign_type} campaign for STAFFVIRTUAL. Goal: {goal}. Budget: {budget}. Multi-channel approach."
        result = await bot._get_ai_response(prompt, system_context)
        
        embed = discord.Embed(title="🎪 STAFFVIRTUAL Campaign!", color=bot.brand_config['primary_color'])
        file_buffer = io.BytesIO(f"# STAFFVIRTUAL Campaign: {campaign_type}\n{result}".encode('utf-8'))
        file = discord.File(file_buffer, filename=f"STAFFVIRTUAL_campaign_{campaign_type}.md")
        embed.add_field(name="📋 Preview", value=result[:600] + "..." if len(result) > 600 else result, inline=False)
        
        await interaction.followup.send(embed=embed, file=file)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {str(e)}")

@bot.tree.command(name="roi", description="📈 ROI analysis and business cases")
async def cmd_roi(interaction: discord.Interaction, scenario: str, timeframe: str = "1 year"):
    await interaction.response.defer(thinking=True)
    try:
        system_context = "Business analyst and ROI specialist for STAFFVIRTUAL."
        prompt = f"Create ROI analysis for STAFFVIRTUAL scenario: {scenario}. Timeframe: {timeframe}. Include specific metrics and business case."
        result = await bot._get_ai_response(prompt, system_context)
        
        embed = discord.Embed(title="📈 STAFFVIRTUAL ROI Analysis!", color=bot.brand_config['primary_color'])
        embed.add_field(name="💰 Analysis", value=result[:1024], inline=False)
        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {str(e)}")

# ===== RESEARCH & INSIGHTS =====

@bot.tree.command(name="research", description="📊 Market research and competitor analysis")
async def cmd_research(interaction: discord.Interaction, research_type: str, topic: str):
    await interaction.response.defer(thinking=True)
    try:
        system_context = "Market research analyst for STAFFVIRTUAL."
        prompt = f"Conduct {research_type} research for STAFFVIRTUAL on: {topic}. Provide actionable insights and strategic recommendations."
        result = await bot._get_ai_response(prompt, system_context)
        
        embed = discord.Embed(title="📊 STAFFVIRTUAL Research!", color=bot.brand_config['primary_color'])
        embed.add_field(name="🔍 Findings", value=result[:1024], inline=False)
        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {str(e)}")

@bot.tree.command(name="audience", description="👥 Target audience analysis and personas")
async def cmd_audience(interaction: discord.Interaction, audience_type: str, industry: str = "general"):
    await interaction.response.defer(thinking=True)
    try:
        system_context = "Audience research specialist for STAFFVIRTUAL."
        prompt = f"Analyze {audience_type} audience for STAFFVIRTUAL in {industry}. Create detailed personas and targeting strategies."
        result = await bot._get_ai_response(prompt, system_context)
        
        embed = discord.Embed(title="👥 STAFFVIRTUAL Audience Analysis!", color=bot.brand_config['primary_color'])
        embed.add_field(name="🎯 Insights", value=result[:1024], inline=False)
        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {str(e)}")

@bot.tree.command(name="pulse", description="🔔 Industry trends and competitive intelligence")
async def cmd_pulse(interaction: discord.Interaction, focus_area: str = "virtual_staffing"):
    await interaction.response.defer(thinking=True)
    try:
        system_context = "Market intelligence analyst for STAFFVIRTUAL."
        prompt = f"Create market pulse report for STAFFVIRTUAL focused on: {focus_area}. Include trends, opportunities, threats."
        result = await bot._get_ai_response(prompt, system_context)
        
        embed = discord.Embed(title="🔔 STAFFVIRTUAL Market Pulse!", color=bot.brand_config['primary_color'])
        embed.add_field(name="📈 Intelligence", value=result[:1024], inline=False)
        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {str(e)}")

# ===== KNOWLEDGE & OPS =====

@bot.tree.command(name="knowledge", description="🧠 Q&A, learning, knowledge management")
async def cmd_knowledge(interaction: discord.Interaction, action: str, query: str = "", content: str = ""):
    await interaction.response.defer(thinking=True)
    try:
        if action == "ask":
            result = await bot._get_ai_response(query, "Business intelligence assistant", use_knowledge=True)
            embed = discord.Embed(title="🤔 STAFFVIRTUAL Q&A", color=bot.brand_config['primary_color'])
            embed.add_field(name="💡 Answer", value=result[:1024], inline=False)
        elif action == "add":
            bot._add_to_knowledge_base(query, content)
            embed = discord.Embed(title="📝 Info Added!", color=bot.brand_config['primary_color'])
            embed.add_field(name="📄 Content", value=content[:500], inline=False)
        elif action == "status":
            embed = discord.Embed(title="🧠 Knowledge Status", color=bot.brand_config['primary_color'])
            embed.add_field(name="📊 Stats", value="Knowledge base operational", inline=False)
        else:
            embed = discord.Embed(title="❌ Invalid Action", description="Use: ask, add, or status", color=0xff0000)
        
        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {str(e)}")

@bot.tree.command(name="case_study", description="🧩 Structured case studies")
async def cmd_case_study(interaction: discord.Interaction, client_type: str, challenge: str):
    await interaction.response.defer(thinking=True)
    try:
        system_context = "Case study specialist for STAFFVIRTUAL."
        prompt = f"Create professional case study for {client_type} with challenge: {challenge}. Include results and ROI."
        result = await bot._get_ai_response(prompt, system_context)
        
        embed = discord.Embed(title="🧩 STAFFVIRTUAL Case Study!", color=bot.brand_config['primary_color'])
        embed.add_field(name="📋 Preview", value=result[:800], inline=False)
        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {str(e)}")

@bot.tree.command(name="brand_guardian", description="🧑‍💻 Brand compliance review")
async def cmd_brand_guardian(interaction: discord.Interaction, content_to_review: str):
    await interaction.response.defer(thinking=True)
    try:
        system_context = "Brand guardian for STAFFVIRTUAL. Review for compliance."
        prompt = f"Review for STAFFVIRTUAL brand compliance: {content_to_review}"
        result = await bot._get_ai_response(prompt, system_context)
        
        embed = discord.Embed(title="🧑‍💻 Brand Review", color=bot.brand_config['primary_color'])
        embed.add_field(name="✅ Compliance", value=result[:1024], inline=False)
        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {str(e)}")

# ===== UTILITY =====

@bot.tree.command(name="test", description="🧪 Test system functionality")
async def cmd_test(interaction: discord.Interaction):
    try:
        embed = discord.Embed(title="✅ STAFFVIRTUAL Strategic Marketing Suite", color=bot.brand_config['primary_color'])
        embed.add_field(name="🤖 AI", value=f"Services: {list(bot.ai_clients.keys())}", inline=False)
        embed.add_field(name="🍌 Nano Banana", value=f"{'✅ Available' if NANO_BANANA_AVAILABLE else '❌ Legacy'}", inline=False)
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"❌ Error: {str(e)}")

@bot.tree.command(name="help", description="❓ Show all commands organized by function")
async def cmd_help(interaction: discord.Interaction):
    try:
        embed = discord.Embed(title="🤖 STAFFVIRTUAL Strategic Marketing Suite", description="16 specialized AI agents", color=bot.brand_config['primary_color'])
        
        embed.add_field(name="🎨 Creative & Content", value="• `/image` `/content` `/social` `/calendar` `/newsletter` `/document`", inline=False)
        embed.add_field(name="🚀 Growth & Campaigns", value="• `/brand` `/growth` `/campaign` `/roi`", inline=False)
        embed.add_field(name="🔍 Research & Insights", value="• `/research` `/audience` `/pulse`", inline=False)
        embed.add_field(name="🧠 Knowledge & Ops", value="• `/knowledge` `/case_study` `/brand_guardian`", inline=False)
        embed.add_field(name="🛠️ Utility", value="• `/test` `/help`", inline=False)
        
        embed.set_footer(text="Strategic AI agents for institutional clarity and business results")
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
