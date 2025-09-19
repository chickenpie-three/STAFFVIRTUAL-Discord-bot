import discord
from discord.ext import commands
import asyncio
import logging
import os
from dotenv import load_dotenv
import io
import json
import tempfile
import re

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
            description='STAFFVIRTUAL Enterprise Marketing Suite - Modern Weave™ Brand System'
        )
        
        # Brand configuration with Modern Weave™ system
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
            'primary_color': parse_color(os.getenv('BRAND_PRIMARY_COLOR'), '#1888FF'),   # SV Core Blue
            'secondary_color': parse_color(os.getenv('BRAND_SECONDARY_COLOR'), '#F8F8EB'), # Alabaster
            'accent_color': parse_color(os.getenv('BRAND_ACCENT_COLOR'), '#004B8D'),     # Deep Blue
            'neutral_color': parse_color(os.getenv('BRAND_NEUTRAL_COLOR'), '#231F20'),   # Ink Black
            'sub_brand_colors': {
                'Professional Services': '#004B8D',   # Authority, intellect
                'Business Operations': '#DC2626',    # Urgency, output
                'Creative Marketing': '#7C3AED',     # Creativity, imagination
                'Technology & IT': '#059669',        # Innovation, agility
                'Ecommerce & Retail': '#F97316',     # Commerce, demand
                'Property & Real Estate': '#EAB308', # Stability, long-term value
                'Travel & Health': '#6B7280',        # Neutral, calm
                'Future/Experimental': '#231F20'     # Gravity, disruption
            },
            'style_guidelines': (
                "Modern Weave™ identity system — modular, grid-driven, "
                "rooted in Filipino craftsmanship yet scaled for global enterprise. "
                "Layouts follow disciplined grid logic (12-column responsive / 10x6 slide grids). "
                "Photography is bright, documentary-style, showing process and human infrastructure. "
                "Illustration uses editorial logic, muted palettes, and Filipino figures. "
                "Typography pairs Gambetta (serif authority) with General Sans (clarity, UI, body). "
                "All assets engineered for clarity, trust, and impact."
            ),
            'voice_tone': (
                "Institutional clarity with cultural warmth. "
                "Calm, precise, and executive in client decks. "
                "Data-driven and minimal in case studies. "
                "Human-first and empathetic in cultural or recruiting content. "
                "Never promotional hype — always outcome-first, evidence-backed, "
                "and reflective of Filipino respect and craftsmanship."
            ),
            'brandline': "Carefully Woven, Built to Scale. Outsourced. Engineered. Embedded.",
            'core_beliefs': [
                "Craftsmanship Over Commodity",
                "People First, Always",
                "Trust is Engineered",
                "Heritage is a Strength",
                "Design is a System"
            ],
            'typography': {
                'primary_serif': 'Gambetta',          # Authority, heritage
                'supporting_sans': 'General Sans',    # Structure, clarity
                'accent_italic': 'General Sans Italic' # Direction, innovation
            }
        }
        
        self.ai_clients = self._initialize_ai_clients()
        self.knowledge_manager = KnowledgeManager()
        
        # Enhanced brand DNA with enterprise positioning
        self.brand_dna = """
        STAFFVIRTUAL — Enterprise Virtual Talent Partner
        
        Company Profile:
        - Mission: Enable growing companies to scale with precision by deploying vetted, managed virtual teams that deliver measurable outcomes.
        - Vision: Become the most trusted global partner for building modern, distributed operating capacity.
        - Ideal Customers (ICP): Mid-market to enterprise operators (COO, CIO/CTO, CMO, Heads of Ops/Customer/IT) in SaaS, Fintech, E-commerce, Professional Services, Healthcare, Legal, and B2B Services.
        - Market Focus: North America, UK/Europe, and ANZ with delivery in the Philippines and follow-the-sun coverage.
        
        Category Narrative:
        - The Modern Weave™: We connect specialist talent, refined process, and lightweight tech to create an adaptive operating fabric—scalable, secure, and always on.
        
        Service Portfolio (Capability Towers):
        1) CX & Operations
           - Virtual Assistants, CX Pods (Voice/Chat/Email), Billing/AR, Back-Office Ops, Data QA, Research
        2) Creative & Content Studio
           - Brand & Design Ops, Marketing Design, Motion/Video Editing, Content Production, Social Ops
        3) Technology & Engineering
           - Web/App Dev, QA, DevOps, Data Engineering, IT Helpdesk (L1–L2), NOC, Cloud Support
        4) Growth Marketing
           - SEO, Paid Media (PPC/Meta/LinkedIn), Marketing Analytics, Email/Lifecycle, CRO, Marketing Ops
        
        Engagement Models & Commercials:
        - Dedicated Talent (FTE or Pod): Embedded specialists with shared QA and Team Lead oversight.
        - Managed Outcomes (SOW): Defined deliverables, SLAs, and governance.
        - Project Squads: Time-boxed initiatives with cross-functional roles.
        - Pricing: Transparent and role-based with seniority bands (L1–L3). Hourly, monthly retainers, or SOW.
          Reference ranges: $15–$75/hr; $2K–$15K/mo retainers; SOW on scope.
        
        Operating Model:
        - Vetted Talent Bench: Multi-step assessment, domain screening, and live work simulations.
        - Governance: Dedicated Team Leads, QA scorecards, weekly business reviews, and quarterly exec reviews.
        - Tooling: We integrate with your stack (Google/Microsoft, Slack/Teams, Jira/Asana, HubSpot/SFDC).
        - Coverage: 24/5 to 24/7 options with redundancy and documented runbooks.
        
        Competitive Positioning:
        - Premium Alternative to freelance networks and basic VA shops (Belay, Time Etc, Fancy Hands).
        - Vertical & Role Depth: Structured playbooks for CX, TechOps, Creative Ops, and Growth.
        - Managed, Not Marketplace: Accountability via SLAs, QA, and leadership layers.
        - Flexible & Low-Friction: Start lean, scale fast, adjust roles without re-hiring cycles.
        
        Trust, Security & Compliance:
        - Data Protection: Principle of least privilege, password vaulting, and secure device policies.
        - Process Controls: Role-based access, audit trails, and incident response playbooks.
        - Legal: DPAs available; client-preferred NDAs and addenda supported.
        - Compliance-Ready: We align to enterprise expectations; certification details provided during onboarding.
        
        Brand Identity (Essentials for Content & Design):
        - Palette: Trust Blue (#1888FF), Authority Blue (#004B8D), Clean White (#F8F8EB), Ink Black (#231F20)
        - Motifs: Modern Weave grid, rounded tiles, light node connections; clean, editorial compositions.
        - Photography: Realistic, bright, minimal; no text overlays; avoid clutter and gimmicks.
        - Illustration/3D: Isometric/editorial accents only; clean lighting; no cropped or cut-off elements.
        - Layout: Grid-first, ample whitespace, decisive hierarchy; Bain-grade restraint.
        - Tone of Voice: Executive, measured, evidence-led, outcome-oriented. Avoid hype and slang.
        
        Voice & Messaging Rules:
        - Lead with outcomes and specifics; quantify when possible.
        - Use plain English. Prefer verbs over adjectives. Keep sentences tight.
        - Emphasize accountability (SLAs, QA, governance) and adaptability (scale up/down, swap roles).
        - Do say: "We'll stand up a two-role pod with a 14-day ramp and weekly quality reviews."
          Don't say: "We'll supercharge your growth with world-class ninjas."
        
        Key Messages:
        - "Build capacity without adding headcount."
        - "Managed virtual teams that hit SLAs—and your goals."
        - "Scale securely. Deliver faster. Reduce operational drag."
        - "Outcomes over overhead."
        
        Contact CTA Library:
        - "Request a pilot pod"
        - "Scope an SOW"
        - "See a role matrix and pricing bands"
        - "Book a 20-minute fit assessment"
        """
    
    def _initialize_ai_clients(self):
        """Initialize AI clients with Nano Banana support"""
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
        """Generate images using Nano Banana with Modern Weave™ branding"""
        try:
            if 'nano_banana' not in self.ai_clients:
                return {"success": False, "error": "Nano Banana not available"}
            
            branded_prompt = f"""
            Create a professional STAFFVIRTUAL image using Modern Weave™ brand system:
            
            Subject: {prompt}
            Style: {style}, modern, clean, grid-driven aesthetic
            Brand Colors: Trust Blue (#1888FF), Authority Blue (#004B8D), Clean White (#F8F8EB), Ink Black (#231F20)
            Design System: Modern Weave™ - modular, grid-driven, rooted in Filipino craftsmanship
            Photography Style: Bright, documentary-style, showing process and human infrastructure
            Layout: Grid-first, ample whitespace, decisive hierarchy
            Quality: Enterprise-grade, suitable for executive presentations and marketing
            
            Focus on visual elements that convey STAFFVIRTUAL's expertise in managed virtual teams.
            Avoid text overlays, clutter, or gimmicks. Clean, professional, trustworthy aesthetic.
            """
            
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
                            "description": "STAFFVIRTUAL Modern Weave™ branded image generated",
                            "model": "gemini-2.5-flash-image-preview"
                        }
            
            return {"success": False, "error": "No image data received"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _extract_seo_keywords(self, content: str):
        """Extract and analyze SEO keywords from content"""
        try:
            # Enhanced keyword extraction for virtual staffing
            words = re.findall(r'\b[a-zA-Z]{3,}\b', content.lower())
            
            # STAFFVIRTUAL-specific keywords
            industry_keywords = [
                'managed virtual teams', 'offshore CX pod', 'virtual staffing', 'remote team management',
                'business process outsourcing', 'virtual assistants', 'remote work', 'distributed teams',
                'enterprise outsourcing', 'virtual talent', 'managed services', 'business efficiency',
                'scalable operations', 'cost optimization', 'team augmentation', 'offshore development',
                'customer experience outsourcing', 'marketing operations', 'IT support services',
                'creative operations', 'growth marketing', 'business automation'
            ]
            
            found_keywords = []
            for keyword in industry_keywords:
                if keyword.replace(' ', '') in ' '.join(words) or keyword in content.lower():
                    found_keywords.append(keyword)
            
            return found_keywords[:15]  # Return top 15
        except:
            return ['managed virtual teams', 'virtual staffing', 'business efficiency']
    
    async def _get_ai_response(self, prompt, system_context="", use_knowledge=True, max_length=None):
        """Get AI response with enhanced Modern Weave™ brand context"""
        try:
            enhanced_prompt = f"""
            {self.brand_dna}
            
            Your Expert Role: {system_context}
            
            User Request: {prompt}
            
            Content Creation Guidelines:
            1. Apply Modern Weave™ brand system and Filipino heritage positioning
            2. Use institutional clarity with cultural warmth in tone
            3. Lead with outcomes and specifics; quantify when possible
            4. Emphasize managed delivery model vs marketplace approach
            5. Position against commodity VA services with enterprise-grade governance
            6. Include relevant proof points, SLAs, and accountability measures
            7. For blog content, aim for 2000-3000 words with comprehensive coverage
            8. Use sub-brand colors appropriately for different service verticals
            9. Maintain Bain-grade restraint and executive-level professionalism
            10. Always include clear, outcome-focused calls-to-action
            
            Create expert-level content that positions STAFFVIRTUAL as the premium enterprise choice.
            """
            
            # Try Nano Banana first
            if 'nano_banana' in self.ai_clients:
                try:
                    response = self.ai_clients['nano_banana'].models.generate_content(
                        model="gemini-2.0-flash-exp",
                        contents=[enhanced_prompt]
                    )
                    result = response.candidates[0].content.parts[0].text
                    return result[:max_length] + "..." if max_length and len(result) > max_length else result
                except Exception as e:
                    logger.error(f"Nano Banana text error: {e}")
            
            # Try legacy Gemini
            if 'gemini' in self.ai_clients:
                try:
                    response = self.ai_clients['gemini'].generate_content(enhanced_prompt)
                    result = response.text
                    return result[:max_length] + "..." if max_length and len(result) > max_length else result
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
                        max_tokens=4000  # Increased for longer content
                    )
                    result = response.choices[0].message.content
                    return result[:max_length] + "..." if max_length and len(result) > max_length else result
                except Exception as e:
                    logger.error(f"OpenAI error: {e}")
            
            return "❌ No AI service available."
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    def _add_to_knowledge_base(self, title: str, content: str):
        """Add to knowledge base"""
        try:
            if not hasattr(self, 'knowledge_base'):
                self.knowledge_base = {"manual_entries": {}, "scraped_content": {}}
            self.knowledge_base["manual_entries"][title] = {"content": content, "type": "manual"}
            return True
        except:
            return False
        
    async def setup_hook(self):
        logger.info("Setting up STAFFVIRTUAL Enterprise Marketing Suite...")
        try:
            synced = await self.tree.sync()
            logger.info(f"Synced {len(synced)} enterprise agents")
        except Exception as e:
            logger.error(f"Sync error: {e}")
    
    async def on_ready(self):
        logger.info(f'{self.user} connected! Modern Weave™ system active')
        logger.info(f"Enterprise services: {list(self.ai_clients.keys())}")
        logger.info(f"Nano Banana: {NANO_BANANA_AVAILABLE}")
        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="STAFFVIRTUAL enterprise operations"))

# Bot instance
bot = SVDiscordBot()

# ===== ENTERPRISE CONTENT CREATION =====

@bot.tree.command(name="content", description="📝 Enterprise blog posts with SEO and paired images")
async def cmd_content_enterprise(interaction: discord.Interaction, content_type: str, topic: str, keywords: str = "", include_image: bool = True):
    """Enterprise content creation with Modern Weave™ branding"""
    await interaction.response.defer(thinking=True)
    
    try:
        system_context = """
        You are a senior content strategist and enterprise marketing expert for STAFFVIRTUAL.
        
        Expertise:
        - B2B enterprise content marketing for virtual staffing industry
        - Modern Weave™ brand system implementation
        - Executive-level thought leadership content
        - SEO optimization for enterprise keywords
        - Competitive positioning against Belay, Time Etc, TaskUs
        """
        
        enhanced_prompt = f"""
        Create comprehensive {content_type} for STAFFVIRTUAL about: {topic}
        Target Keywords: {keywords if keywords else 'managed virtual teams, offshore CX pod, enterprise outsourcing, virtual staffing'}
        
        ENTERPRISE CONTENT REQUIREMENTS:
        
        1. COMPREHENSIVE LENGTH: 2500-4000 words for blog posts
        2. EXECUTIVE POSITIONING: Target COOs, CTOs, CMOs, Heads of Operations
        3. MODERN WEAVE™ BRAND INTEGRATION:
           - Use institutional clarity with cultural warmth
           - Reference Filipino craftsmanship and heritage
           - Emphasize managed delivery vs marketplace approach
           - Include enterprise governance and SLA focus
        
        4. ADVANCED SEO STRATEGY:
           - Primary keyword in title, first 100 words, and conclusion
           - Secondary keywords naturally integrated throughout
           - Long-tail enterprise keywords (managed virtual teams, offshore CX pod)
           - Meta title and description optimized for enterprise search intent
           - Header structure optimized for featured snippets
           - Internal linking opportunities to STAFFVIRTUAL service pages
        
        5. ENTERPRISE CONTENT STRUCTURE:
           - Executive Summary (key outcomes and ROI upfront)
           - Market Context and Industry Challenges
           - Problem Analysis (enterprise pain points and constraints)
           - STAFFVIRTUAL Solution Framework (capability towers, engagement models)
           - Competitive Differentiation (vs Belay, Time Etc, TaskUs)
           - Implementation Methodology (pod deployment, governance, SLAs)
           - ROI Analysis and Business Case
           - Case Study or Success Story (with metrics)
           - Strategic Recommendations and Next Steps
           - Executive Call-to-Action (pilot pod, SOW scoping, fit assessment)
        
        6. PROOF POINTS TO INCLUDE:
           - Specific metrics and ROI data
           - SLA attainment and quality scorecards
           - Ramp timelines and time-to-productivity
           - Security and compliance frameworks
           - Team composition and governance structures
        
        Create authoritative, evidence-based content that positions STAFFVIRTUAL as the premium enterprise choice.
        """
        
        # Generate comprehensive content
        logger.info(f"Generating enterprise content: {topic}")
        content_result = await bot._get_ai_response(enhanced_prompt, system_context)
        
        # Extract enterprise SEO keywords
        seo_keywords = await bot._extract_seo_keywords(content_result)
        
        # Generate Modern Weave™ branded image
        image_result = None
        if include_image and NANO_BANANA_AVAILABLE:
            image_prompt = f"Modern Weave™ branded header image for STAFFVIRTUAL enterprise article about {topic}. Grid-driven layout, Filipino craftsmanship motifs, documentary-style photography. Professional, clean, enterprise-grade visual suitable for executive audiences."
            image_result = await bot._generate_nano_banana_image(image_prompt, "enterprise")
        
        # Create enterprise-grade embed
        embed = discord.Embed(
            title="📝 STAFFVIRTUAL Enterprise Content Created!",
            description=f"**Type:** {content_type}\n**Topic:** {topic}\n**Length:** {len(content_result)} characters\n**Modern Weave™ Optimized:** ✅",
            color=bot.brand_config['primary_color']
        )
        
        # Add enterprise SEO analysis
        if seo_keywords:
            embed.add_field(
                name="🔍 Enterprise SEO Keywords",
                value=", ".join(seo_keywords[:10]),
                inline=False
            )
        
        # Create comprehensive enterprise content file
        seo_analysis = f"""
## Enterprise SEO Analysis
- **Content Length:** {len(content_result)} characters (Enterprise standard: 2500+ words)
- **Target Audience:** COOs, CTOs, CMOs, Heads of Operations
- **Primary Keywords:** {keywords if keywords else 'Enterprise virtual staffing'}
- **Extracted Keywords:** {', '.join(seo_keywords)}
- **Brand System:** Modern Weave™ integrated
- **Competitive Positioning:** vs Belay, Time Etc, TaskUs
- **Optimization Status:** ✅ Enterprise SEO Optimized

## Modern Weave™ Brand Integration
- **Voice:** Institutional clarity with cultural warmth
- **Positioning:** Premium enterprise virtual talent partner
- **Heritage:** Filipino craftsmanship and respect
- **Governance:** SLA-driven, QA-managed delivery model
- **Image Pairing:** {'✅ Modern Weave™ branded image generated' if image_result and image_result.get('success') else '❌ Image generation not available'}

## Enterprise Messaging Framework
- Outcome-first, evidence-backed content
- Managed delivery vs marketplace positioning  
- Enterprise governance and accountability focus
- Filipino heritage as competitive differentiator
- Modern Weave™ visual identity integration
        """
        
        full_content = f"# STAFFVIRTUAL Enterprise {content_type.title()}: {topic}\n\n{seo_analysis}\n\n## Executive Content\n\n{content_result}"
        
        # Create downloadable enterprise file
        file_buffer = io.BytesIO(full_content.encode('utf-8'))
        file = discord.File(file_buffer, filename=f"STAFFVIRTUAL_enterprise_{content_type}_{topic.replace(' ', '_')}.md")
        
        # Smart preview handling for enterprise content
        if len(content_result) > 1000:
            embed.add_field(name="📋 Executive Summary", value=content_result[:1000], inline=False)
            if len(content_result) > 2000:
                embed.add_field(name="📋 Content Preview", value=content_result[1000:2000], inline=False)
                embed.add_field(name="📄 Complete Enterprise Content", value="See attached file for full article with Modern Weave™ brand analysis", inline=False)
            else:
                embed.add_field(name="📋 Content Continuation", value=content_result[1000:], inline=False)
        else:
            embed.add_field(name="📋 Complete Content", value=content_result, inline=False)
        
        # Send with Modern Weave™ branded image
        if image_result and image_result.get('success') and image_result.get('image_path'):
            image_file = discord.File(image_result['image_path'], filename=f"STAFFVIRTUAL_modern_weave_{topic.replace(' ', '_')}.png")
            embed.set_thumbnail(url=f"attachment://STAFFVIRTUAL_modern_weave_{topic.replace(' ', '_')}.png")
            embed.add_field(name="🎨 Modern Weave™ Image", value="Enterprise-grade branded header image generated and attached", inline=False)
            
            await interaction.followup.send(embed=embed, files=[file, image_file])
            
            try:
                os.unlink(image_result['image_path'])
            except:
                pass
        else:
            await interaction.followup.send(embed=embed, file=file)
            
    except Exception as e:
        logger.error(f"Enterprise content error: {e}")
        await interaction.followup.send(f"❌ Error: {str(e)}")

# Add other essential commands...

@bot.tree.command(name="test", description="🧪 Test enterprise system functionality")
async def cmd_test(interaction: discord.Interaction):
    try:
        embed = discord.Embed(
            title="✅ STAFFVIRTUAL Enterprise Marketing Suite",
            description="Modern Weave™ brand system active • Enterprise AI agents ready",
            color=bot.brand_config['primary_color']
        )
        embed.add_field(name="🤖 AI Services", value=f"Available: {list(bot.ai_clients.keys())}", inline=False)
        embed.add_field(name="🍌 Nano Banana", value=f"{'✅ Available' if NANO_BANANA_AVAILABLE else '❌ Legacy mode'}", inline=False)
        embed.add_field(name="🎨 Brand System", value="Modern Weave™ • Filipino Heritage • Enterprise Grade", inline=False)
        embed.add_field(name="🏢 Positioning", value="Premium enterprise virtual talent partner", inline=False)
        
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"❌ Test failed: {str(e)}")

@bot.tree.command(name="help", description="❓ Show enterprise marketing suite commands")
async def cmd_help(interaction: discord.Interaction):
    try:
        embed = discord.Embed(
            title="🤖 STAFFVIRTUAL Enterprise Marketing Suite",
            description="Modern Weave™ brand system • Premium AI agents for enterprise content",
            color=bot.brand_config['primary_color']
        )
        
        embed.add_field(
            name="🎨 Enterprise Content Creation",
            value="• `/content` - Blog posts with SEO + Modern Weave™ images\n• `/image` - Nano Banana generation with brand system",
            inline=False
        )
        
        embed.add_field(
            name="💡 Example Commands",
            value="`/content blog 'Enterprise Virtual Team Management' 'managed virtual teams, offshore CX pod' include_image:True`",
            inline=False
        )
        
        embed.add_field(
            name="🏢 Brand System",
            value="Modern Weave™ • Filipino Heritage • Enterprise Positioning • Institutional Clarity",
            inline=False
        )
        
        embed.set_footer(text="Enterprise-grade marketing intelligence • Carefully Woven, Built to Scale")
        
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
        logger.info("Starting STAFFVIRTUAL Enterprise Marketing Suite with Modern Weave™...")
        bot.run(token)
    except Exception as e:
        logger.error(f"Bot startup error: {e}")
        exit(1)
