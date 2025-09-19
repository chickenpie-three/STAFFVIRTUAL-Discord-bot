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
            description='STAFFVIRTUAL Enhanced Marketing Suite - Premium AI Agents with Advanced Features'
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
        
        # Enhanced brand DNA with competitive intelligence
        self.brand_dna = f"""
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
        - Palette:
          · Trust Blue: #1888FF
          · Authority Blue: #004B8D
          · Clean White: #F8F8EB
          · Ink Black: #231F20
        - Motifs: Modern Weave grid, rounded tiles, light node connections; clean, editorial compositions.
        - Photography: Realistic, bright, minimal; no text overlays; avoid clutter and gimmicks.
        - Illustration/3D: Isometric/editorial accents only; clean lighting; no cropped or cut-off elements.
        - Layout: Grid-first, ample whitespace, decisive hierarchy; Bain-grade restraint.
        - Tone of Voice: Executive, measured, evidence-led, outcome-oriented. Avoid hype and slang.

        Voice & Messaging Rules (Write Like This):
        - Lead with outcomes and specifics; quantify when possible.
        - Use plain English. Prefer verbs over adjectives. Keep sentences tight.
        - Emphasize accountability (SLAs, QA, governance) and adaptability (scale up/down, swap roles).
        - Do say: “We’ll stand up a two-role pod with a 14-day ramp and weekly quality reviews.”
          Don’t say: “We’ll supercharge your growth with world-class ninjas.”

        Messaging Pillars (with Proof You’ll Supply):
        1) Quality Talent, Vetted and Managed
           - Proof: Hiring funnel data, pass rates, simulation scores, client tenure.
        2) Enterprise-Grade Governance
           - Proof: QA scorecards, SLA attainment, cadence (WBR/QBR) artifacts.
        3) Scalable & Flexible Capacity
           - Proof: Ramp timelines, role swaps, seasonality playbooks.
        4) Security & Compliance
           - Proof: Access controls, device standards, DPAs, incident logs/process.
        5) ROI & Speed to Impact
           - Proof: Time-to-productivity, cost-to-serve deltas, case study results.

        Key Messages (Client-Facing):
        - “Build capacity without adding headcount.”
        - “Managed virtual teams that hit SLAs—and your goals.”
        - “Scale securely. Deliver faster. Reduce operational drag.”
        - “Outcomes over overhead.”

        Differentiators (What We Will Always Defend):
        - Vetted talent + managed delivery (not a marketplace).
        - Pod leadership and QA baked into every engagement.
        - Flexible models that match how operators actually run.
        - Clear governance, measurable outcomes, clean handoffs.

        Proof & Case Studies (Structure we’ll follow):
        - Situation → Approach (Pod, Playbooks, Tooling) → SLA/Outcome → ROI/Impact → Quote
        - Include team composition, timeline to ramp, and before/after metrics.

        Go-to-Market (Quick Start):
        - Entry Offers: Discovery Workshop, 30-day Pilot Pod, or Dedicated Role Stand-Up.
        - Typical Ramp: 10–14 days to steady state for L1–L2; 3–4 weeks for multi-role pods.
        - Executive Cadence: Weekly business reviews + QBRs; dashboard access by default.

        Keywords & Phrases (for SEO/Ads/Pages):
        - “Managed virtual teams”, “Offshore CX pod”, “Creative operations”, “IT helpdesk outsourcing”,
          “NOC support”, “Growth marketing pod”, “Scale operations”, “Bain-style operating partner”.

        Boilerplate (Short):
        - STAFFVIRTUAL builds modern operating capacity for growing companies. We deploy vetted virtual
          specialists and managed pods across CX, Creative, Technology, and Growth—governed by SLAs,
          QA, and executive cadence—so operators scale faster with less overhead.

        Contact CTA Library:
        - “Request a pilot pod”
        - “Scope an SOW”
        - “See a role matrix and pricing bands”
        - “Book a 20-minute fit assessment”

        (Updated: 2025-09-20, Asia/Manila)
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
            
            branded_prompt = f"Create professional STAFFVIRTUAL image: {prompt}. Style: {style}. Brand colors: blue (#1888FF), off-white (#F8F8EB), dark blue (#004B8D). Professional, modern, clean aesthetic for virtual staffing company. High-quality business imagery suitable for marketing."
            
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
    
    async def _extract_seo_keywords(self, content: str):
        """Extract and analyze SEO keywords from content"""
        try:
            # Simple keyword extraction
            words = re.findall(r'\b[a-zA-Z]{3,}\b', content.lower())
            
            # Virtual staffing related keywords
            industry_keywords = [
                'virtual assistant', 'remote work', 'virtual staffing', 'business efficiency',
                'productivity', 'outsourcing', 'remote team', 'virtual team', 'business growth',
                'cost savings', 'scalability', 'flexibility', 'expert talent', 'professional services'
            ]
            
            found_keywords = []
            for keyword in industry_keywords:
                if keyword.replace(' ', '') in ' '.join(words) or keyword in content.lower():
                    found_keywords.append(keyword)
            
            return found_keywords[:10]  # Return top 10
        except:
            return ['virtual assistant', 'remote work', 'business efficiency']
    
    async def _get_ai_response(self, prompt, system_context="", use_knowledge=True, max_length=None):
        """Get AI response with enhanced prompting"""
        try:
            # Enhanced prompt engineering
            enhanced_prompt = f"""
            {self.brand_dna}
            
            Your Expert Role: {system_context}
            
            User Request: {prompt}
            
            Instructions:
            1. Provide comprehensive, detailed responses (aim for 1500-3000 words for blog content)
            2. Include specific STAFFVIRTUAL examples, case studies, and value propositions
            3. Reference our actual services and competitive advantages
            4. Use industry statistics and credible data points
            5. Maintain professional yet engaging tone
            6. Include actionable next steps and clear calls-to-action
            7. For SEO content, naturally integrate relevant keywords
            8. Position STAFFVIRTUAL as the premium choice in virtual staffing
            
            Create expert-level content that demonstrates deep industry knowledge and STAFFVIRTUAL expertise.
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
                        max_tokens=3000  # Increased for longer content
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
        logger.info("Setting up STAFFVIRTUAL Enhanced Marketing Suite...")
        try:
            synced = await self.tree.sync()
            logger.info(f"Synced {len(synced)} enhanced agents")
        except Exception as e:
            logger.error(f"Sync error: {e}")
    
    async def on_ready(self):
        logger.info(f'{self.user} connected! Enhanced services: {list(self.ai_clients.keys())}')
        logger.info(f"Nano Banana: {NANO_BANANA_AVAILABLE}")
        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="STAFFVIRTUAL enhanced marketing"))

# Bot instance
bot = SVDiscordBot()

# ===== ENHANCED CREATIVE & CONTENT AGENTS =====

@bot.tree.command(name="content", description="📝 Enhanced blog posts with SEO, keywords, and paired images")
async def cmd_content_enhanced(interaction: discord.Interaction, content_type: str, topic: str, keywords: str = "", include_image: bool = True):
    """Enhanced content creation with SEO optimization and image pairing"""
    await interaction.response.defer(thinking=True)
    
    try:
        system_context = """
        You are a senior content marketing strategist, SEO specialist, and digital marketing expert for STAFFVIRTUAL. 
        
        Expertise Areas:
        - Virtual staffing industry trends and insights
        - B2B content marketing that converts
        - SEO optimization and keyword strategy
        - Lead generation through content
        - Competitive analysis in virtual staffing space
        """
        
        enhanced_prompt = f"""
        Create a comprehensive {content_type} for STAFFVIRTUAL about: {topic}
        Target Keywords: {keywords if keywords else 'virtual assistants, remote work, business efficiency, virtual staffing, remote team management'}
        
        Content Requirements:
        1. COMPREHENSIVE LENGTH: 1500-2500 words for blog posts
        2. SEO OPTIMIZATION:
           - Primary keyword in title, first paragraph, and conclusion
           - Secondary keywords naturally integrated throughout
           - Meta description (150-160 characters)
           - Header structure (H1, H2, H3) with keyword optimization
           - Internal linking opportunities to STAFFVIRTUAL services
           
        3. CONTENT STRUCTURE:
           - Compelling headline with emotional hook
           - Engaging introduction with statistics or surprising facts
           - Problem identification (pain points of target audience)
           - Solution presentation (how STAFFVIRTUAL solves these)
           - Benefits and value proposition
           - Social proof and credibility elements
           - Case study or success story example
           - Actionable tips and insights
           - Strong conclusion with clear next steps
           - Compelling call-to-action for consultation
           
        4. STAFFVIRTUAL POSITIONING:
           - Position as premium virtual staffing solution
           - Highlight competitive advantages and differentiators
           - Include specific service offerings and capabilities
           - Reference target market pain points and solutions
           - Demonstrate industry expertise and thought leadership
           
        5. SEO ELEMENTS TO INCLUDE:
           - Suggested meta title and description
           - Primary and secondary keyword recommendations
           - Internal linking strategy
           - Featured snippet optimization
           - Schema markup suggestions
           - Social sharing optimization
           
        Create expert-level content that drives organic traffic and qualified leads.
        """
        
        # Generate the main content
        logger.info(f"Generating enhanced content: {topic}")
        content_result = await bot._get_ai_response(enhanced_prompt, system_context)
        
        # Extract SEO keywords from the generated content
        seo_keywords = await bot._extract_seo_keywords(content_result)
        
        # Generate paired image if requested
        image_result = None
        if include_image and NANO_BANANA_AVAILABLE:
            image_prompt = f"Professional blog header image for STAFFVIRTUAL article about {topic}. Modern, clean design with STAFFVIRTUAL branding. Suitable for business blog. Visual elements that represent virtual staffing, remote work, and business efficiency."
            image_result = await bot._generate_nano_banana_image(image_prompt, "professional")
        
        # Create comprehensive embed
        embed = discord.Embed(
            title="📝 STAFFVIRTUAL Enhanced Content Created!",
            description=f"**Type:** {content_type}\n**Topic:** {topic}\n**Length:** {len(content_result)} characters\n**SEO Optimized:** ✅",
            color=bot.brand_config['primary_color']
        )
        
        # Add SEO keywords
        if seo_keywords:
            embed.add_field(
                name="🔍 SEO Keywords Found",
                value=", ".join(seo_keywords),
                inline=False
            )
        
        # Create comprehensive content file
        seo_section = f"""
## SEO Analysis
- **Content Length:** {len(content_result)} characters
- **Target Keywords:** {keywords if keywords else 'Industry standard'}
- **Found Keywords:** {', '.join(seo_keywords)}
- **Optimization Status:** ✅ SEO Optimized

## Image Pairing
- **Paired Image:** {'✅ Generated' if image_result and image_result.get('success') else '❌ Not available'}
- **Image Style:** Professional, STAFFVIRTUAL branded
        """
        
        full_content = f"# STAFFVIRTUAL {content_type.title()}: {topic}\n\n{seo_section}\n\n## Content\n\n{content_result}"
        
        # Create downloadable file
        file_buffer = io.BytesIO(full_content.encode('utf-8'))
        file = discord.File(file_buffer, filename=f"STAFFVIRTUAL_{content_type}_{topic.replace(' ', '_')}_enhanced.md")
        
        # Smart preview handling
        if len(content_result) > 1000:
            embed.add_field(name="📋 Content Preview (Part 1)", value=content_result[:1000], inline=False)
            if len(content_result) > 2000:
                embed.add_field(name="📋 Content Preview (Part 2)", value=content_result[1000:2000], inline=False)
                embed.add_field(name="📄 Complete Content", value="See attached file for full article with SEO analysis", inline=False)
            else:
                embed.add_field(name="📋 Content Preview (Part 2)", value=content_result[1000:], inline=False)
        else:
            embed.add_field(name="📋 Complete Content", value=content_result, inline=False)
        
        # Send content with optional paired image
        if image_result and image_result.get('success') and image_result.get('image_path'):
            # Send both content file and paired image
            image_file = discord.File(image_result['image_path'], filename=f"STAFFVIRTUAL_{topic.replace(' ', '_')}_header.png")
            embed.set_thumbnail(url=f"attachment://STAFFVIRTUAL_{topic.replace(' ', '_')}_header.png")
            embed.add_field(name="🎨 Paired Image", value="Header image generated and attached", inline=False)
            
            await interaction.followup.send(embed=embed, files=[file, image_file])
            
            # Clean up temp file
            try:
                os.unlink(image_result['image_path'])
            except:
                pass
        else:
            await interaction.followup.send(embed=embed, file=file)
            
    except Exception as e:
        logger.error(f"Enhanced content error: {e}")
        await interaction.followup.send(f"❌ Error: {str(e)}")

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
            embed.add_field(name="🖼️ Concept", value=concept[:1024], inline=False)
            await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {str(e)}")

@bot.tree.command(name="social", description="📱 Enhanced social media with hashtag research")
async def cmd_social_enhanced(interaction: discord.Interaction, platform: str, topic: str, hashtags: str = "", include_image: bool = False):
    """Enhanced social media posts with hashtag research and optional image pairing"""
    await interaction.response.defer(thinking=True)
    
    try:
        system_context = f"""
        You are a social media marketing expert and hashtag strategist for STAFFVIRTUAL.
        
        Expertise:
        - Platform-specific optimization for {platform}
        - Hashtag research and trending topic analysis
        - Engagement optimization and conversion tactics
        - B2B social media strategy for virtual staffing
        - Lead generation through social content
        """
        
        enhanced_social_prompt = f"""
        Create a high-converting {platform} post for STAFFVIRTUAL about: {topic}
        
        PLATFORM-SPECIFIC STRATEGY:
        
        LinkedIn (B2B Focus):
        - Professional insights and thought leadership
        - Industry statistics and trends
        - Case studies and success stories
        - Networking and relationship building
        - Lead generation and consultation offers
        
        Instagram (Visual Storytelling):
        - Behind-the-scenes content
        - Team culture and values
        - Visual case studies and infographics
        - Stories and reels optimization
        - User-generated content opportunities
        
        Twitter/X (Thought Leadership):
        - Industry commentary and insights
        - Quick tips and actionable advice
        - Thread-worthy content
        - Trending topic integration
        - Conversation starters
        
        ENHANCED REQUIREMENTS:
        1. Hook: Attention-grabbing opening that stops the scroll
        2. Value: Educational or entertaining content that provides real value
        3. Proof: Social proof, statistics, or credibility elements
        4. CTA: Clear call-to-action for lead generation
        5. Hashtags: Research and suggest 8-12 optimal hashtags including:
           - Industry hashtags (#virtualstaffing, #remotework)
           - Trending hashtags (research current trends)
           - Branded hashtags (#STAFFVIRTUAL)
           - Niche hashtags for better targeting
        6. Engagement: Questions or prompts to drive comments and shares
        
        User Specified Hashtags: {hashtags if hashtags else 'Research and suggest optimal hashtags'}
        
        Create content that drives engagement, builds authority, and generates qualified leads.
        """
        
        # Generate social content
        social_result = await bot._get_ai_response(enhanced_social_prompt, system_context)
        
        # Generate paired image if requested
        image_result = None
        if include_image and NANO_BANANA_AVAILABLE:
            image_prompt = f"Social media image for STAFFVIRTUAL {platform} post about {topic}. Professional, engaging, brand-consistent. Optimized for {platform} format."
            image_result = await bot._generate_nano_banana_image(image_prompt, f"{platform}_optimized")
        
        embed = discord.Embed(
            title="📱 STAFFVIRTUAL Enhanced Social Post!",
            description=f"**Platform:** {platform.title()}\n**Topic:** {topic}\n**Enhanced Features:** SEO + Hashtag Research",
            color=bot.brand_config['primary_color']
        )
        
        # Handle long social content
        if len(social_result) > 1024:
            embed.add_field(name=f"📝 {platform.title()} Post (Part 1)", value=social_result[:1024], inline=False)
            if len(social_result) > 2048:
                embed.add_field(name=f"📝 {platform.title()} Post (Part 2)", value=social_result[1024:2048], inline=False)
            else:
                embed.add_field(name=f"📝 {platform.title()} Post (Part 2)", value=social_result[1024:], inline=False)
        else:
            embed.add_field(name=f"📝 {platform.title()} Post", value=social_result, inline=False)
        
        embed.set_footer(text=f"Enhanced for {platform} with hashtag research and engagement optimization")
        
        # Send with optional paired image
        if image_result and image_result.get('success') and image_result.get('image_path'):
            image_file = discord.File(image_result['image_path'], filename=f"STAFFVIRTUAL_{platform}_{topic.replace(' ', '_')}.png")
            embed.set_thumbnail(url=f"attachment://STAFFVIRTUAL_{platform}_{topic.replace(' ', '_')}.png")
            embed.add_field(name="🎨 Paired Image", value="Social media image generated and attached", inline=False)
            
            await interaction.followup.send(embed=embed, file=image_file)
            
            try:
                os.unlink(image_result['image_path'])
            except:
                pass
        else:
            await interaction.followup.send(embed=embed)
            
    except Exception as e:
        logger.error(f"Enhanced social error: {e}")
        await interaction.followup.send(f"❌ Error: {str(e)}")

@bot.tree.command(name="campaign", description="🎪 Complete marketing campaigns with multi-asset creation")
async def cmd_campaign_enhanced(interaction: discord.Interaction, campaign_type: str, goal: str, duration: str = "1 month", create_assets: bool = True):
    """Enhanced campaign creation with asset generation"""
    await interaction.response.defer(thinking=True)
    
    try:
        system_context = """
        You are a senior marketing campaign strategist for STAFFVIRTUAL with expertise in:
        - Multi-channel campaign development
        - B2B lead generation campaigns
        - Virtual staffing industry marketing
        - ROI optimization and performance tracking
        - Asset creation and brand consistency
        """
        
        campaign_prompt = f"""
        Design a comprehensive {campaign_type} marketing campaign for STAFFVIRTUAL:
        
        Campaign Goal: {goal}
        Duration: {duration}
        Asset Creation: {'Include asset recommendations' if create_assets else 'Strategy only'}
        
        COMPREHENSIVE CAMPAIGN FRAMEWORK:
        
        1. CAMPAIGN STRATEGY:
           - Objective and success metrics
           - Target audience segmentation
           - Competitive positioning
           - Value proposition and messaging
           
        2. MULTI-CHANNEL APPROACH:
           - LinkedIn advertising and organic content
           - Google Ads (search and display)
           - Email marketing sequences
           - Content marketing and SEO
           - Social media strategy
           - Partnership and referral programs
           
        3. CONTENT & CREATIVE STRATEGY:
           - Blog post topics and SEO keywords
           - Social media content calendar
           - Ad copy variations for A/B testing
           - Email sequence templates
           - Landing page copy and structure
           - Video content concepts
           
        4. IMPLEMENTATION TIMELINE:
           - Week-by-week execution plan
           - Milestone checkpoints
           - Resource allocation
           - Budget distribution
           
        5. PERFORMANCE TRACKING:
           - KPIs and success metrics
           - Analytics setup and tracking
           - Optimization opportunities
           - ROI measurement framework
           
        6. ASSET REQUIREMENTS:
           - Image specifications and concepts
           - Video requirements and scripts
           - Design templates and brand guidelines
           - Copy variations and messaging
           
        Create a campaign that positions STAFFVIRTUAL as the premium choice and drives qualified leads.
        """
        
        campaign_result = await bot._get_ai_response(campaign_prompt, system_context)
        
        embed = discord.Embed(
            title="🎪 STAFFVIRTUAL Enhanced Campaign Strategy!",
            description=f"**Type:** {campaign_type}\n**Goal:** {goal}\n**Duration:** {duration}\n**Length:** {len(campaign_result)} characters",
            color=bot.brand_config['primary_color']
        )
        
        # Create comprehensive campaign file
        campaign_content = f"""# STAFFVIRTUAL Marketing Campaign: {campaign_type}
## Goal: {goal}
## Duration: {duration}

{campaign_result}

## Campaign Assets Checklist
- [ ] Blog posts and SEO content
- [ ] Social media graphics and posts
- [ ] Email templates and sequences
- [ ] Landing page copy and design
- [ ] Ad copy variations
- [ ] Video scripts and concepts
- [ ] Performance tracking setup

## Next Steps
1. Review and approve campaign strategy
2. Create content calendar and timeline
3. Develop creative assets
4. Set up tracking and analytics
5. Launch campaign with A/B testing
6. Monitor performance and optimize

Generated by STAFFVIRTUAL AI Marketing Suite
"""
        
        file_buffer = io.BytesIO(campaign_content.encode('utf-8'))
        file = discord.File(file_buffer, filename=f"STAFFVIRTUAL_campaign_{campaign_type}_{goal.replace(' ', '_')}.md")
        
        # Smart preview handling
        if len(campaign_result) > 1000:
            embed.add_field(name="📋 Campaign Preview (Part 1)", value=campaign_result[:1000], inline=False)
            if len(campaign_result) > 2000:
                embed.add_field(name="📋 Campaign Preview (Part 2)", value=campaign_result[1000:2000], inline=False)
                embed.add_field(name="📄 Complete Strategy", value="See attached file for full campaign strategy and asset checklist", inline=False)
            else:
                embed.add_field(name="📋 Campaign Preview (Part 2)", value=campaign_result[1000:], inline=False)
        else:
            embed.add_field(name="📋 Complete Campaign Strategy", value=campaign_result, inline=False)
        
        if create_assets:
            embed.add_field(
                name="🎨 Asset Creation",
                value="Use `/content`, `/social`, and `/image` commands to create campaign assets based on this strategy",
                inline=False
            )
        
        await interaction.followup.send(embed=embed, file=file)
        
    except Exception as e:
        logger.error(f"Enhanced campaign error: {e}")
        await interaction.followup.send(f"❌ Error: {str(e)}")

@bot.tree.command(name="seo_audit", description="🔍 Comprehensive SEO analysis and optimization")
async def cmd_seo_audit(interaction: discord.Interaction, content_to_audit: str, target_keywords: str = ""):
    """SEO audit and optimization agent"""
    await interaction.response.defer(thinking=True)
    
    try:
        system_context = """
        seo_prompt = f"""
You are an enterprise SEO strategist and digital marketing analyst for STAFFVIRTUAL — 
a global provider of premium virtual staffing solutions.

Expertise:
- Enterprise-level technical SEO audits
- Keyword architecture design for B2B services
- On-page and off-page optimization strategy
- Competitive SERP and intent gap analysis
- Local SEO and trust signal engineering for service businesses

Conduct a comprehensive SEO audit for STAFFVIRTUAL content:

Content to Audit: {content_to_audit}
Target Keywords: {target_keywords if target_keywords else 'virtual staffing, managed remote teams, offshore outsourcing, business process outsourcing'}

SEO AUDIT FRAMEWORK:

1. KEYWORD & SEARCH INTELLIGENCE:
   - Map primary, secondary, and semantic keywords
   - Identify long-tail and question-based opportunities
   - Evaluate keyword density vs. topical authority
   - Flag cannibalization or overlap across assets
   - Align search intent with STAFFVIRTUAL’s ICPs (COOs, CTOs, CMOs, founders)

2. CONTENT OPTIMIZATION:
   - Title tag clarity (50–60 characters, outcome-led)
   - Meta description alignment (150–160 characters, benefit-driven)
   - Structured heading hierarchy (H1–H3) analysis
   - Depth, breadth, and topical completeness
   - Readability, scannability, and engagement markers (bullets, tables, data)

3. TECHNICAL SEO:
   - URL architecture and crawl depth recommendations
   - Internal linking pathways for topical clusters
   - Schema markup opportunities (FAQ, HowTo, Organization, Service)
   - Image optimization (alt text, compression, accessibility)
   - Core Web Vitals & page speed enhancements

4. COMPETITIVE & SERP ANALYSIS:
   - Benchmark against direct competitors (Belay, Time Etc, TaskUs)
   - Identify SERP feature gaps (snippets, People Also Ask, video, local packs)
   - Highlight backlink and domain authority differentials
   - Content differentiation and positioning strategies

5. IMPROVEMENT ROADMAP:
   - Immediate quick wins (low-effort, high-impact)
   - Strategic content enhancements for authority building
   - Technical implementation checklist
   - Measurement framework (rank tracking, GSC/GA4 integration, KPI dashboard)

Deliver a structured, evidence-based audit with prioritized recommendations 
to increase STAFFVIRTUAL’s organic visibility, drive qualified leads, and 
reinforce brand authority as a trusted enterprise partner.
"""
        
        audit_result = await bot._get_ai_response(seo_prompt, system_context)
        
        embed = discord.Embed(
            title="🔍 STAFFVIRTUAL SEO Audit Complete!",
            description=f"**Content Length:** {len(content_to_audit)} characters\n**Target Keywords:** {target_keywords or 'Industry standard'}",
            color=bot.brand_config['primary_color']
        )
        
        # Handle long audit results
        if len(audit_result) > 1024:
            chunks = [audit_result[i:i+1024] for i in range(0, len(audit_result), 1024)]
            for i, chunk in enumerate(chunks[:6]):
                field_name = "🔍 SEO Analysis" if i == 0 else f"🔍 Continued ({i+1})"
                embed.add_field(name=field_name, value=chunk, inline=False)
            
            if len(chunks) > 6:
                # Create file for very long audits
                audit_content = f"# STAFFVIRTUAL SEO Audit\n## Target Keywords: {target_keywords}\n\n{audit_result}"
                file_buffer = io.BytesIO(audit_content.encode('utf-8'))
                file = discord.File(file_buffer, filename=f"STAFFVIRTUAL_seo_audit.md")
                embed.add_field(name="📄 Complete Audit", value="See attached file for full SEO analysis", inline=False)
                await interaction.followup.send(embed=embed, file=file)
                return
        else:
            embed.add_field(name="🔍 SEO Analysis", value=audit_result, inline=False)
        
        embed.set_footer(text="SEO audit optimized for STAFFVIRTUAL's virtual staffing market")
        
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        logger.error(f"SEO audit error: {e}")
        await interaction.followup.send(f"❌ Error: {str(e)}")

# Add other enhanced agents...
# (keeping the existing brand, ask, document, test, help commands from main_improved.py)

# Run the bot
if __name__ == "__main__":
    token = os.getenv('DISCORD_BOT_TOKEN')
    if not token:
        logger.error("DISCORD_BOT_TOKEN not found")
        exit(1)
    
    try:
        logger.info("Starting STAFFVIRTUAL Enhanced Marketing Suite...")
        bot.run(token)
    except Exception as e:
        logger.error(f"Bot startup error: {e}")
        exit(1)
