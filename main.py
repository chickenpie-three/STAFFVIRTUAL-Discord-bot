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

# AI Libraries - using direct integrations for now
import openai
import anthropic
import google.generativeai as genai

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
            description='SV Brand Assistant Bot - Your AI-powered creative companion with AutoAgent'
        )
        
        # Initialize brand configuration
        self.brand_config = {
            'name': os.getenv('BRAND_NAME', 'SV Brand'),
            'primary_color': int(os.getenv('BRAND_PRIMARY_COLOR', '#1a1a1a').replace('#', ''), 16),
            'secondary_color': int(os.getenv('BRAND_SECONDARY_COLOR', '#ffffff').replace('#', ''), 16),
            'accent_color': int(os.getenv('BRAND_ACCENT_COLOR', '#ff6b6b').replace('#', ''), 16),
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
        
        # Initialize Gemini if API key is available
        gemini_key = os.getenv('GEMINI_API_KEY')
        if gemini_key:
            genai.configure(api_key=gemini_key)
            ai_clients['gemini'] = genai.GenerativeModel('gemini-pro')
        
        # Initialize OpenAI if API key is available
        openai_key = os.getenv('OPENAI_API_KEY')
        if openai_key:
            ai_clients['openai'] = openai.OpenAI(api_key=openai_key)
        
        # Initialize Anthropic if API key is available
        anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        if anthropic_key:
            ai_clients['anthropic'] = anthropic.Anthropic(api_key=anthropic_key)
        
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
                        {"role": "system", "content": system_prompt},
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
                    system=system_prompt,
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

# Slash command groups for different agents
@bot.tree.command(name="image", description="Generate branded images using AI")
async def generate_image(interaction: discord.Interaction, prompt: str, style: str = "default"):
    """Generate branded images using AutoAgent"""
    await interaction.response.defer(thinking=True)
    
    try:
        # Create enhanced prompt with brand context
        enhanced_prompt = f"""
        Create a branded image for {bot.brand_config['name']} with the following requirements:
        
        Original Request: {prompt}
        Style Preference: {style}
        Brand Guidelines: {bot.brand_config['style_guidelines']}
        
        Please generate a detailed image prompt that incorporates our brand aesthetic and the user's request.
        Focus on creating something that would work well for our brand identity.
        """
        
        # Use AI to process the request
        result = await bot._get_ai_response(enhanced_prompt, 'image')
        
        embed = discord.Embed(
            title="🎨 Image Concept Generated!",
            description=f"**Original Request:** {prompt}\n**Style:** {style}",
            color=bot.brand_config['primary_color']
        )
        
        # Add the AI-generated response
        if len(result) > 1024:
            embed.add_field(name="AI Response", value=result[:1021] + "...", inline=False)
        else:
            embed.add_field(name="AI Response", value=result, inline=False)
        
        embed.add_field(
            name="💡 Next Steps", 
            value="Use this concept with your preferred image generation tool (DALL-E, Midjourney, etc.)",
            inline=False
        )
        
        await interaction.followup.send(embed=embed)
            
    except Exception as e:
        logger.error(f"Image generation error: {e}")
        embed = discord.Embed(
            title="❌ Image Generation Failed",
            description=f"An error occurred: {str(e)}",
            color=0xff0000
        )
        await interaction.followup.send(embed=embed)

@bot.tree.command(name="document", description="Create branded documents with AI assistance")
async def create_document(interaction: discord.Interaction, document_type: str, topic: str, length: str = "medium"):
    """Create branded documents using AutoAgent"""
    await interaction.response.defer(thinking=True)
    
    try:
        # Create detailed document request
        document_prompt = f"""
        Create a {length} {document_type} for {bot.brand_config['name']} on the topic: {topic}
        
        Brand Guidelines:
        - Style: {bot.brand_config['style_guidelines']}
        - Voice & Tone: {bot.brand_config['voice_tone']}
        
        Requirements:
        1. Follow professional document structure
        2. Incorporate brand voice and messaging
        3. Ensure content is engaging and well-organized
        4. Include relevant sections and formatting suggestions
        5. Optimize for the intended audience and purpose
        
        Please provide a complete document draft with proper structure and content.
        """
        
        # Use AI to create the document
        result = await bot._get_ai_response(document_prompt, 'document')
        
        embed = discord.Embed(
            title="📄 Document Created!",
            description=f"**Type:** {document_type}\n**Topic:** {topic}\n**Length:** {length}",
            color=bot.brand_config['primary_color']
        )
        
        # Create a text file with the document content
        document_content = f"# {document_type.title()}: {topic}\n\n{result}"
        
        # Create file buffer
        file_buffer = io.StringIO(document_content)
        file = discord.File(
            io.BytesIO(file_buffer.getvalue().encode('utf-8')),
            filename=f"{document_type}_{topic.replace(' ', '_')}.txt"
        )
        
        embed.add_field(
            name="📋 Document Preview",
            value=result[:500] + "..." if len(result) > 500 else result,
            inline=False
        )
        
        await interaction.followup.send(embed=embed, file=file)
            
    except Exception as e:
        logger.error(f"Document creation error: {e}")
        embed = discord.Embed(
            title="❌ Document Creation Failed",
            description=f"An error occurred: {str(e)}",
            color=0xff0000
        )
        await interaction.followup.send(embed=embed)

@bot.tree.command(name="brand", description="Get brand guidance and suggestions")
async def brand_assistance(interaction: discord.Interaction, query: str):
    """Get brand assistance using AutoAgent"""
    await interaction.response.defer(thinking=True)
    
    try:
        # Create brand strategy prompt
        brand_prompt = f"""
        As a brand strategist for {bot.brand_config['name']}, please provide guidance on the following query:
        
        Query: {query}
        
        Current Brand Context:
        - Style Guidelines: {bot.brand_config['style_guidelines']}
        - Voice & Tone: {bot.brand_config['voice_tone']}
        
        Please provide:
        1. Strategic recommendations
        2. Brand alignment considerations
        3. Practical implementation suggestions
        4. Potential risks or considerations
        5. Next steps or action items
        
        Keep the response actionable and specific to our brand identity.
        """
        
        # Use AI for brand guidance
        result = await bot._get_ai_response(brand_prompt, 'brand')
        
        embed = discord.Embed(
            title="🏢 Brand Strategic Guidance",
            description=f"**Your Query:** {query}",
            color=bot.brand_config['primary_color']
        )
        
        # Split long responses into multiple fields
        if len(result) > 1024:
            # Split into chunks
            chunks = [result[i:i+1024] for i in range(0, len(result), 1024)]
            for i, chunk in enumerate(chunks[:3]):  # Limit to 3 chunks
                field_name = "📋 Brand Guidance" if i == 0 else f"📋 Continued ({i+1})"
                embed.add_field(name=field_name, value=chunk, inline=False)
        else:
            embed.add_field(name="📋 Brand Guidance", value=result, inline=False)
        
        embed.set_footer(text=f"Brand Assistant for {bot.brand_config['name']}")
        
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        logger.error(f"Brand assistance error: {e}")
        embed = discord.Embed(
            title="❌ Brand Assistance Failed",
            description=f"An error occurred: {str(e)}",
            color=0xff0000
        )
        await interaction.followup.send(embed=embed)

@bot.tree.command(name="video", description="Generate branded video content strategy")
async def generate_video(interaction: discord.Interaction, prompt: str, duration: int = 10, style: str = "default"):
    """Generate branded video content strategy using AutoAgent"""
    await interaction.response.defer(thinking=True)
    
    try:
        # Create video strategy prompt
        video_prompt = f"""
        Create a comprehensive video content strategy for {bot.brand_config['name']} based on:
        
        Video Concept: {prompt}
        Duration: {duration} seconds
        Style: {style}
        
        Brand Guidelines:
        - Style: {bot.brand_config['style_guidelines']}
        - Voice & Tone: {bot.brand_config['voice_tone']}
        
        Please provide:
        1. Video concept and narrative structure
        2. Visual style recommendations
        3. Script outline or key talking points
        4. Technical specifications and requirements
        5. Brand integration suggestions
        6. Call-to-action recommendations
        
        Focus on creating content that aligns with our brand identity and engages our target audience.
        """
        
        # Use AI for video strategy
        result = await bot._get_ai_response(video_prompt, 'video')
        
        embed = discord.Embed(
            title="🎬 Video Content Strategy",
            description=f"**Concept:** {prompt}\n**Duration:** {duration}s\n**Style:** {style}",
            color=bot.brand_config['primary_color']
        )
        
        # Split long responses appropriately
        if len(result) > 1024:
            chunks = [result[i:i+1024] for i in range(0, len(result), 1024)]
            for i, chunk in enumerate(chunks[:3]):  # Limit to 3 chunks
                field_name = "🎯 Video Strategy" if i == 0 else f"🎯 Continued ({i+1})"
                embed.add_field(name=field_name, value=chunk, inline=False)
        else:
            embed.add_field(name="🎯 Video Strategy", value=result, inline=False)
        
        embed.add_field(
            name="🛠️ Next Steps",
            value="Use this strategy with your preferred video creation tools (Runway, Luma, etc.)",
            inline=False
        )
        
        await interaction.followup.send(embed=embed)
            
    except Exception as e:
        logger.error(f"Video generation error: {e}")
        embed = discord.Embed(
            title="❌ Video Strategy Failed",
            description=f"An error occurred: {str(e)}",
            color=0xff0000
        )
        await interaction.followup.send(embed=embed)

@bot.tree.command(name="blog", description="Create SEO-optimized blog posts")
async def create_blog(interaction: discord.Interaction, topic: str, keywords: str = "", length: str = "medium"):
    """Create blog posts using AI"""
    await interaction.response.defer(thinking=True)
    
    try:
        # Create blog post prompt
        blog_prompt = f"""
        Create a comprehensive blog post for {bot.brand_config['name']} on the topic: {topic}
        
        Requirements:
        - Length: {length}
        - Target Keywords: {keywords if keywords else 'general industry terms'}
        - Include SEO-optimized title and meta description
        - Structure with clear headings and subheadings
        - Include call-to-action at the end
        - Maintain STAFFVIRTUAL brand voice and expertise
        
        Please provide a complete blog post with proper formatting and structure.
        """
        
        # Use AI to create the blog post
        result = await bot._get_ai_response(blog_prompt, 'blog')
        
        embed = discord.Embed(
            title="📝 Blog Post Created!",
            description=f"**Topic:** {topic}\n**Keywords:** {keywords or 'General'}\n**Length:** {length}",
            color=bot.brand_config['primary_color']
        )
        
        # Create blog post file
        blog_content = f"# Blog Post: {topic}\n\n{result}"
        
        # Create file buffer
        file_buffer = io.StringIO(blog_content)
        file = discord.File(
            io.BytesIO(file_buffer.getvalue().encode('utf-8')),
            filename=f"blog_{topic.replace(' ', '_')}.md"
        )
        
        # Add preview
        preview_text = result[:800] + "..." if len(result) > 800 else result
        embed.add_field(name="📋 Blog Preview", value=preview_text, inline=False)
        
        await interaction.followup.send(embed=embed, file=file)
            
    except Exception as e:
        logger.error(f"Blog creation error: {e}")
        embed = discord.Embed(
            title="❌ Blog Creation Failed",
            description=f"An error occurred: {str(e)}",
            color=0xff0000
        )
        await interaction.followup.send(embed=embed)

@bot.tree.command(name="social", description="Create social media posts for different platforms")
async def create_social(interaction: discord.Interaction, platform: str, topic: str, hashtags: str = ""):
    """Create social media posts using AI"""
    await interaction.response.defer(thinking=True)
    
    try:
        # Create social media prompt
        social_prompt = f"""
        Create a social media post for {platform} about: {topic}
        
        Platform: {platform}
        Brand: {bot.brand_config['name']}
        Hashtags to include: {hashtags if hashtags else 'relevant industry hashtags'}
        
        Platform-specific requirements:
        - LinkedIn: Professional, thought leadership tone
        - Instagram: Visual, engaging, story-driven
        - Twitter/X: Concise, impactful, conversation-starting
        - Facebook: Community-focused, engaging
        - TikTok: Trendy, authentic, entertaining
        
        Include relevant hashtags and engagement hooks. Maintain STAFFVIRTUAL brand voice.
        """
        
        # Use AI to create the social post
        result = await bot._get_ai_response(social_prompt, 'social')
        
        embed = discord.Embed(
            title="📱 Social Media Post Created!",
            description=f"**Platform:** {platform.title()}\n**Topic:** {topic}",
            color=bot.brand_config['primary_color']
        )
        
        embed.add_field(name=f"📝 {platform.title()} Post", value=result, inline=False)
        
        if hashtags:
            embed.add_field(name="🏷️ Requested Hashtags", value=hashtags, inline=False)
        
        await interaction.followup.send(embed=embed)
            
    except Exception as e:
        logger.error(f"Social media creation error: {e}")
        embed = discord.Embed(
            title="❌ Social Media Creation Failed",
            description=f"An error occurred: {str(e)}",
            color=0xff0000
        )
        await interaction.followup.send(embed=embed)

@bot.tree.command(name="calendar", description="Create social media content calendar")
async def create_calendar(interaction: discord.Interaction, duration: str = "1 month", focus: str = "general"):
    """Create social media calendar using AI"""
    await interaction.response.defer(thinking=True)
    
    try:
        # Create calendar prompt
        calendar_prompt = f"""
        Create a social media content calendar for {bot.brand_config['name']} with these specifications:
        
        Duration: {duration}
        Focus Area: {focus}
        
        Requirements:
        1. Plan content for major platforms (LinkedIn, Instagram, Twitter/X)
        2. Balance content types: educational, promotional, behind-the-scenes, industry news
        3. Include optimal posting times and frequencies
        4. Suggest content themes for each week
        5. Include relevant hashtags and engagement strategies
        6. Consider STAFFVIRTUAL's business goals and audience
        
        Provide a structured calendar with specific post ideas and scheduling recommendations.
        """
        
        # Use AI to create the calendar
        result = await bot._get_ai_response(calendar_prompt, 'calendar')
        
        embed = discord.Embed(
            title="📅 Social Media Calendar Created!",
            description=f"**Duration:** {duration}\n**Focus:** {focus}",
            color=bot.brand_config['primary_color']
        )
        
        # Create calendar file
        calendar_content = f"# Social Media Calendar - {duration}\n## Focus: {focus}\n\n{result}"
        
        # Create file buffer
        file_buffer = io.StringIO(calendar_content)
        file = discord.File(
            io.BytesIO(file_buffer.getvalue().encode('utf-8')),
            filename=f"social_calendar_{duration.replace(' ', '_')}.md"
        )
        
        # Add preview
        preview_text = result[:800] + "..." if len(result) > 800 else result
        embed.add_field(name="📋 Calendar Preview", value=preview_text, inline=False)
        
        await interaction.followup.send(embed=embed, file=file)
            
    except Exception as e:
        logger.error(f"Calendar creation error: {e}")
        embed = discord.Embed(
            title="❌ Calendar Creation Failed",
            description=f"An error occurred: {str(e)}",
            color=0xff0000
        )
        await interaction.followup.send(embed=embed)

@bot.tree.command(name="ask", description="Ask questions about STAFFVIRTUAL business")
async def ask_business(interaction: discord.Interaction, question: str):
    """Ask business-related questions using AI"""
    await interaction.response.defer(thinking=True)
    
    try:
        # Create knowledge-based prompt
        knowledge_prompt = f"""
        Answer this question about STAFFVIRTUAL based on general business knowledge and context:
        
        Question: {question}
        
        Please provide a helpful response based on:
        1. General business best practices
        2. Industry standards and recommendations
        3. STAFFVIRTUAL's brand positioning as a professional service provider
        4. Practical, actionable advice
        
        If you don't have specific company information, provide general guidance and suggest where to find more specific details.
        """
        
        # Use AI to answer the question
        result = await bot._get_ai_response(knowledge_prompt, 'knowledge')
        
        embed = discord.Embed(
            title="🤔 Business Question Answered",
            description=f"**Your Question:** {question}",
            color=bot.brand_config['primary_color']
        )
        
        # Split long responses
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
        logger.error(f"Business question error: {e}")
        embed = discord.Embed(
            title="❌ Question Processing Failed",
            description=f"An error occurred: {str(e)}",
            color=0xff0000
        )
        await interaction.followup.send(embed=embed)

@bot.tree.command(name="learn_url", description="Add a URL for the bot to learn from")
async def learn_from_url(interaction: discord.Interaction, url: str):
    """Learn from a URL by scraping its content"""
    await interaction.response.defer(thinking=True)
    
    try:
        # Scrape the URL
        content = await bot.knowledge_manager.scrape_url(url)
        
        if content:
            bot.knowledge_manager.save_knowledge_base()
            
            embed = discord.Embed(
                title="🌐 URL Content Learned!",
                description=f"**URL:** {url}",
                color=bot.brand_config['primary_color']
            )
            
            embed.add_field(
                name="📄 Page Title", 
                value=content.get('title', 'No title found')[:1024], 
                inline=False
            )
            
            if content.get('meta_description'):
                embed.add_field(
                    name="📝 Description", 
                    value=content['meta_description'][:1024], 
                    inline=False
                )
            
            embed.add_field(
                name="📊 Content Stats",
                value=f"Headings: {len(content.get('headings', []))}\nParagraphs: {len(content.get('paragraphs', []))}\nLinks: {len(content.get('links', []))}",
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
        embed = discord.Embed(
            title="❌ Learning Failed",
            description=f"An error occurred: {str(e)}",
            color=0xff0000
        )
        await interaction.followup.send(embed=embed)

@bot.tree.command(name="upload_doc", description="Upload a document for the bot to learn from")
async def upload_document(interaction: discord.Interaction, document: discord.Attachment):
    """Learn from an uploaded document"""
    await interaction.response.defer(thinking=True)
    
    try:
        # Check file type
        filename = document.filename.lower()
        if not (filename.endswith('.pdf') or filename.endswith('.docx') or filename.endswith('.doc')):
            embed = discord.Embed(
                title="❌ Unsupported File Type",
                description="Please upload PDF or Word documents only.",
                color=0xff0000
            )
            await interaction.followup.send(embed=embed)
            return
        
        # Download file content
        file_content = await document.read()
        
        # Process based on file type
        if filename.endswith('.pdf'):
            doc_info = bot.knowledge_manager.process_pdf_document(file_content, document.filename)
        elif filename.endswith(('.docx', '.doc')):
            doc_info = bot.knowledge_manager.process_docx_document(file_content, document.filename)
        
        if doc_info:
            bot.knowledge_manager.save_knowledge_base()
            
            embed = discord.Embed(
                title="📄 Document Processed!",
                description=f"**Filename:** {document.filename}",
                color=bot.brand_config['primary_color']
            )
            
            embed.add_field(
                name="📊 Document Stats",
                value=f"Type: {doc_info.get('type', 'Unknown').upper()}\nSize: {len(file_content)} bytes\nContent Length: {len(doc_info.get('content', ''))} characters",
                inline=False
            )
            
            # Add content preview
            content_preview = doc_info.get('content', '')[:500] + "..." if len(doc_info.get('content', '')) > 500 else doc_info.get('content', '')
            if content_preview:
                embed.add_field(
                    name="📝 Content Preview",
                    value=content_preview,
                    inline=False
                )
            
            embed.set_footer(text="This document is now available for all AI agents to reference")
            
        else:
            embed = discord.Embed(
                title="❌ Document Processing Failed",
                description=f"Could not process: {document.filename}",
                color=0xff0000
            )
        
        await interaction.followup.send(embed=embed)
            
    except Exception as e:
        logger.error(f"Document upload error: {e}")
        embed = discord.Embed(
            title="❌ Upload Failed",
            description=f"An error occurred: {str(e)}",
            color=0xff0000
        )
        await interaction.followup.send(embed=embed)

@bot.tree.command(name="knowledge_status", description="Check knowledge base status")
async def knowledge_status(interaction: discord.Interaction):
    """Show knowledge base status and statistics"""
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
        
        # List some sources
        sources = bot.knowledge_manager.knowledge_base.get('sources', [])
        if sources:
            source_list = []
            for source in sources[:10]:  # Show first 10 sources
                source_list.append(f"• {source['type'].title()}: {source['title'][:50]}...")
            
            embed.add_field(
                name="📚 Recent Sources",
                value="\n".join(source_list),
                inline=False
            )
        
        embed.set_footer(text="Use /learn_url and /upload_doc to expand the knowledge base")
        
        await interaction.followup.send(embed=embed)
            
    except Exception as e:
        logger.error(f"Knowledge status error: {e}")
        embed = discord.Embed(
            title="❌ Status Check Failed",
            description=f"An error occurred: {str(e)}",
            color=0xff0000
        )
        await interaction.followup.send(embed=embed)

@bot.tree.command(name="help", description="Show available commands and agent capabilities")
async def help_command(interaction: discord.Interaction):
    """Show help information"""
    embed = discord.Embed(
        title="🤖 SV Brand Assistant Bot",
        description=f"Your AI-powered creative companion for {bot.brand_config['name']} - Powered by AutoAgent",
        color=bot.brand_config['primary_color']
    )
    
    embed.add_field(
        name="🎨 /image",
        value="Generate branded image concepts and detailed prompts\n`/image prompt:\"logo design\" style:\"modern\"`",
        inline=False
    )
    
    embed.add_field(
        name="📄 /document",
        value="Create branded documents with AI assistance\n`/document document_type:\"proposal\" topic:\"new campaign\" length:\"long\"`",
        inline=False
    )
    
    embed.add_field(
        name="🏢 /brand",
        value="Get strategic brand guidance and recommendations\n`/brand query:\"What colors should I use for our new campaign?\"`",
        inline=False
    )
    
    embed.add_field(
        name="🎬 /video",
        value="Generate video content strategies and scripts\n`/video prompt:\"product showcase\" duration:15 style:\"cinematic\"`",
        inline=False
    )
    
    embed.add_field(
        name="📝 /blog",
        value="Create SEO-optimized blog posts\n`/blog topic:\"AI in business\" keywords:\"automation, efficiency\" length:\"long\"`",
        inline=False
    )
    
    embed.add_field(
        name="📱 /social",
        value="Create platform-specific social media posts\n`/social platform:\"LinkedIn\" topic:\"team productivity\" hashtags:\"#productivity #teamwork\"`",
        inline=False
    )
    
    embed.add_field(
        name="📅 /calendar",
        value="Generate social media content calendars\n`/calendar duration:\"2 weeks\" focus:\"product launch\"`",
        inline=False
    )
    
    embed.add_field(
        name="🤔 /ask",
        value="Ask business questions about STAFFVIRTUAL\n`/ask question:\"What are our core service offerings?\"`",
        inline=False
    )
    
    embed.add_field(
        name="🌐 /learn_url",
        value="Teach the bot from website content\n`/learn_url url:\"https://staffvirtual.com/about\"`",
        inline=False
    )
    
    embed.add_field(
        name="📄 /upload_doc",
        value="Upload documents for the bot to learn from\n`/upload_doc document:[attach your PDF/Word file]`",
        inline=False
    )
    
    embed.add_field(
        name="🧠 /knowledge_status",
        value="Check knowledge base status and sources\n`/knowledge_status`",
        inline=False
    )
    
    embed.add_field(
        name="🚀 Enhanced Features",
        value="12 specialized AI agents • Knowledge base learning • Document processing • Web scraping • Cloud deployment ready",
        inline=False
    )
    
    embed.set_footer(text="Use these commands to interact with different AI agents • All responses are brand-optimized for STAFFVIRTUAL")
    
    await interaction.response.send_message(embed=embed)

# Error handling
@bot.event
async def on_command_error(ctx, error):
    """Handle command errors"""
    logger.error(f"Command error: {error}")
    await ctx.send("An error occurred while processing your command.")

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
