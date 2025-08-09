import streamlit as st
import requests
import json
import time
from datetime import datetime
import tempfile
import threading
from typing import Dict, List, Optional
import re
from PIL import Image
import hashlib
import io
import base64
import urllib.parse

# Core libraries
from groq import Groq
from bs4 import BeautifulSoup
# Add these imports at the top of your paste.txt file
from conversation_orchestrator import ConversationOrchestrator
from smart_character_selector import SmartCharacterSelector

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'current_character' not in st.session_state:
    st.session_state.current_character = None
if 'character_database' not in st.session_state:
    st.session_state.character_database = {}
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []
if 'group_chats' not in st.session_state:
    st.session_state.group_chats = {}
if 'current_group_chat' not in st.session_state:
    st.session_state.current_group_chat = None
if 'chat_mode' not in st.session_state:
    st.session_state.chat_mode = 'individual'  # 'individual' or 'group' 
# Add these lines after the existing session state initializations:
if 'autonomous_conversations' not in st.session_state:
    st.session_state.autonomous_conversations = {}
if 'conversation_orchestrator' not in st.session_state:
    st.session_state.conversation_orchestrator = None   

class CharacterCreator:
    def __init__(self, groq_client):
        self.groq_client = groq_client
        
    def get_character_image(self, character_name: str) -> str:
        """Get character image using enhanced fetcher"""
        try:
            image_fetcher = CharacterImageFetcher()
            image_url = image_fetcher.get_character_image_from_web(character_name)
            
            # If no real image found, use the enhanced styled avatar
            if not image_url or "ui-avatars.com" in image_url:
                return self.generate_character_avatar(character_name)
            
            return image_url
        except Exception as e:
            st.error(f"Error fetching character image: {str(e)}")
            return self.generate_character_avatar(character_name)
    def generate_character_avatar(self, character_name: str) -> str:
        """Generate a more appealing avatar for the character"""
        try:
            # Use DiceBear API for better avatars
            styles = ['adventurer', 'avataaars', 'big-smile', 'personas', 'pixel-art']
            style = styles[hash(character_name) % len(styles)]
            
            # Generate unique seed from character name
            seed = character_name.replace(' ', '').lower()
            
            url = f"https://api.dicebear.com/7.x/{style}/svg?seed={seed}&backgroundColor=random"
            
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    svg_data = response.content
                    return f"data:image/svg+xml;base64,{base64.b64encode(svg_data).decode()}"
            except:
                pass
            
            # Ultimate fallback - create a simple but appealing avatar
            return self.create_fallback_avatar(character_name)
            
        except Exception as e:
            return self.create_fallback_avatar(character_name)
    
    def create_fallback_avatar(self, character_name: str) -> str:
        """Create a fallback avatar with better design"""
        try:
            from PIL import Image, ImageDraw, ImageFont
            import random
            
            # Set random seed based on name for consistency
            random.seed(hash(character_name))
            
            # Create image with gradient background
            img_size = (200, 200)
            img = Image.new('RGB', img_size, color='white')
            draw = ImageDraw.Draw(img)
            
            # Generate attractive gradient colors
            colors = [
                ('#FF6B6B', '#4ECDC4'),  # Red to Teal
                ('#A8E6CF', '#FFD93D'),  # Green to Yellow
                ('#6C5CE7', '#A29BFE'),  # Purple to Light Purple
                ('#00B894', '#00CEC9'),  # Green to Cyan
                ('#E17055', '#FDCB6E'),  # Orange to Yellow
                ('#0984E3', '#74B9FF'),  # Blue to Light Blue
            ]
            
            color_pair = random.choice(colors)
            
            # Create circular gradient effect
            center = (100, 100)
            for r in range(100, 0, -2):
                # Interpolate between colors
                ratio = (100 - r) / 100
                color1 = tuple(int(color_pair[0][i:i+2], 16) for i in (1, 3, 5))
                color2 = tuple(int(color_pair[1][i:i+2], 16) for i in (1, 3, 5))
                
                interpolated = tuple(int(color1[i] + ratio * (color2[i] - color1[i])) for i in range(3))
                draw.ellipse([center[0]-r, center[1]-r, center[0]+r, center[1]+r], fill=interpolated)
            
            # Add character initial with better styling
            initial = character_name[0].upper()
            
            # Try to load a better font, fallback to default
            try:
                font = ImageFont.truetype("arial.ttf", 80)
            except:
                try:
                    font = ImageFont.load_default()
                    # Scale up the default font
                    font = font.font_variant(size=60)
                except:
                    font = ImageFont.load_default()
            
            # Get text dimensions
            bbox = draw.textbbox((0, 0), initial, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # Center the text
            text_x = (img_size[0] - text_width) // 2
            text_y = (img_size[1] - text_height) // 2 - 10
            
            # Add text shadow for better visibility
            shadow_offset = 3
            draw.text((text_x + shadow_offset, text_y + shadow_offset), initial, fill='rgba(0,0,0,0.3)', font=font)
            draw.text((text_x, text_y), initial, fill='white', font=font)
            
            # Add a subtle border
            draw.ellipse([5, 5, 195, 195], outline='rgba(255,255,255,0.8)', width=3)
            
            # Convert to base64
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            img_str = base64.b64encode(buffer.getvalue()).decode()
            
            return f"data:image/png;base64,{img_str}"
            
        except Exception as e:
            # Absolute fallback - just return a placeholder URL
            return f"https://ui-avatars.com/api/?name={character_name.replace(' ', '+')}&background=random&color=fff&size=200&font-size=0.6&rounded=true"
    
    def generate_character_profile(self, character_name: str) -> Dict:
        """Generate character profile using Groq API"""
        try:
            analysis_prompt = f"""
            Analyze the fictional character "{character_name}" and provide detailed information in the following categories:

            1. STORY & BACKGROUND: Brief origin story, key life events, and character arc
            2. PERSONALITY TRAITS: Core personality characteristics, behavioral patterns, values, and motivations
            3. FAMOUS QUOTES: 3-5 memorable quotes that represent their character (if known)
            4. EMOTIONAL MOMENTS: Key emotional scenes or character development moments
            5. RELATIONSHIPS: Important relationships and how they interact with others
            6. PHYSICAL APPEARANCE: Distinctive physical features, clothing style, etc.
            7. SPEAKING STYLE: How they talk, language patterns, formality level, catchphrases
            8. BACKSTORY: Detailed background information
            9. POWERS/ABILITIES: Special abilities or skills (if applicable)
            10. CHARACTER DEVELOPMENT: How they grow throughout their story

            Provide this information in a structured JSON format. If the character is not well-known, create a plausible profile based on the name and common character archetypes.

            Format your response as valid JSON with these keys:
            - story
            - personality
            - famous_quotes (array)
            - emotional_moments (array)
            - relationships (array)
            - appearance
            - speaking_style
            - backstory
            - powers_abilities
            - character_development
            - fun_facts (array)
            """

            response = self.groq_client.chat.completions.create(
                model="llama3-70b-8192",
                messages=[{"role": "user", "content": analysis_prompt}],
                max_tokens=2500,
                temperature=0.7
            )
            
            # Parse the JSON response
            try:
                character_data = json.loads(response.choices[0].message.content)
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                content = response.choices[0].message.content
                character_data = self.parse_character_info_fallback(character_name, content)
            
            return character_data
            
        except Exception as e:
            st.error(f"Error generating character profile: {str(e)}")
            return self.create_default_character(character_name)
    
    def parse_character_info_fallback(self, name: str, content: str) -> Dict:
        """Fallback parser if JSON parsing fails"""
        return {
            'name': name,
            'story': content[:300] + "...",
            'personality': f"A unique character with distinctive traits and engaging personality.",
            'famous_quotes': [f"Hello, I'm {name}!", "Every journey begins with a single step."],
            'emotional_moments': ["Character growth moments", "Challenging situations"],
            'relationships': ["Meaningful connections with allies", "Complex dynamics with rivals"],
            'appearance': "Distinctive and memorable character design",
            'speaking_style': "Unique speech patterns with characteristic expressions",
            'backstory': f"{name} has a rich history filled with adventures and challenges.",
            'powers_abilities': "Special talents and unique capabilities",
            'character_development': "Continuous growth through experiences and relationships",
            'fun_facts': [f"{name} has many interesting quirks", "Known for unique habits"]
        }
    
    def create_default_character(self, name: str) -> Dict:
        """Create a default character profile"""
        return {
            'name': name,
            'story': f"{name} is a fascinating fictional character with a rich background story.",
            'personality': "Charismatic, intelligent, and engaging with unique character traits.",
            'famous_quotes': [f"Greetings! I am {name}.", "The adventure begins now!"],
            'emotional_moments': ["Moments of triumph", "Times of reflection and growth"],
            'relationships': ["Loyal friendships", "Meaningful connections"],
            'appearance': "Distinctive appearance that reflects their personality",
            'speaking_style': "Clear, characteristic speech with memorable expressions",
            'backstory': f"{name} comes from a world of adventure and discovery.",
            'powers_abilities': "Unique skills and special talents",
            'character_development': "Continuous evolution through experiences",
            'fun_facts': [f"{name} loves adventure", "Has many hidden talents"]
        }

class EnhancedChatBot:
    def __init__(self):
        self.setup_client()
        self.character_creator = CharacterCreator(self.groq_client)
        self.group_chat_manager = GroupChatManager(self.groq_client)  
        
    def setup_client(self):
        """Initialize Groq client"""
        try:
            api_key = None
            
            # Try to get API key from Streamlit secrets first
            if 'GROQ_API_KEY' in st.secrets:
                api_key = st.secrets['GROQ_API_KEY']
            else:
                # Try environment variable
                import os
                api_key = os.getenv('GROQ_API_KEY')
            
            if not api_key:
                st.error("❌ GROQ_API_KEY not found! Please add it to Streamlit secrets or environment variables.")
                st.info("Get your free API key from: https://console.groq.com/keys")
                self.groq_client = None
                return
                
            # Test the API key
            self.groq_client = Groq(api_key=api_key)
            
            # Test connection with a simple request
            test_response = self.groq_client.chat.completions.create(
                model="llama3-70b-8192",
                messages=[{"role": "user", "content": "test"}],
                max_tokens=10
            )
            
            st.success("✅ Groq API connected successfully!")
            
        except Exception as e:
            st.error(f"❌ Error connecting to Groq API: {str(e)}")
            st.info("Please check your API key and internet connection.")
            self.groq_client = None
    
    def create_character(self, character_name: str) -> bool:
        """Create a new character and add to database"""
        try:
            # Generate character profile
            with st.spinner(f"🎨 Creating {character_name}..."):
                character_data = self.character_creator.generate_character_profile(character_name)
                
                # Generate character image/avatar
                character_avatar = self.character_creator.get_character_image(character_name)
                
                # Create character ID
                character_id = character_name.lower().replace(' ', '_')
                
                # Add to database
                st.session_state.character_database[character_id] = {
                    'name': character_name,
                    'avatar': character_avatar,
                    **character_data
                }
                
                return True
                
        except Exception as e:
            st.error(f"Error creating character: {str(e)}")
            return False
    def generate_character_response(self, user_message: str, character_id: str) -> str:
        """Generate character response using character-specific behavior"""
        try:
            # Check if Groq client is properly initialized
            if not self.groq_client:
                return "❌ API connection not available. Please check your Groq API key in the app settings."
            
            if character_id not in st.session_state.character_database:
                return "Character not found. Please create the character first."
        
        # ... rest of your existing code
         
            
            character = st.session_state.character_database[character_id]
            
            # Build comprehensive character prompt
            system_prompt = f"""You are {character['name']}, a character with the following detailed profile:

BACKGROUND & STORY:
{character.get('story', 'Unknown background')}

BACKSTORY:
{character.get('backstory', 'Rich character history')}

PERSONALITY TRAITS:
{character.get('personality', 'Friendly and engaging')}

SPEAKING STYLE:
{character.get('speaking_style', 'Natural and conversational')}

FAMOUS QUOTES (use these as inspiration for your speech patterns):
{chr(10).join(character.get('famous_quotes', []))}

POWERS/ABILITIES:
{character.get('powers_abilities', 'Unique talents')}

RELATIONSHIPS & INTERACTIONS:
{chr(10).join(character.get('relationships', []))}

CHARACTER DEVELOPMENT:
{character.get('character_development', 'Continuous growth')}

INSTRUCTIONS:
- Stay completely in character at all times
- Use the speaking style and personality traits described above
- Reference your background, abilities, and experiences when relevant
- Maintain consistency with your established personality
- Keep responses engaging and true to your character
- Responses should be 1-4 sentences unless asked for more detail
- Show personality through your unique way of speaking
- Reference your relationships and past experiences naturally
- Display your character's emotions and motivations"""

            # Prepare messages for API
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add conversation history (keep last 10 exchanges)
            recent_history = st.session_state.conversation_history[-20:]
            for msg in recent_history:
                messages.append({"role": msg["role"], "content": msg["content"]})
            
            messages.append({"role": "user", "content": user_message})
            
            # Generate response
            response = self.groq_client.chat.completions.create(
                model="llama3-70b-8192",
                messages=messages,
                max_tokens=300,
                temperature=0.85
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            st.error(f"Error generating response: {str(e)}")
            return "I'm having trouble responding right now. Could you try again?"


class CharacterImageFetcher:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        
        # Character-specific databases and APIs
        self.character_databases = {
            'anime': [
                'https://cdn.myanimelist.net/images/characters/',
                'https://static.wikia.nocookie.net/anime-characters-fight/',
                'https://images-wixmp-ed30a86b8c4ca887773594c2.wixmp.com'
            ],
            'marvel': [
                'https://terrigen-cdn-dev.marvel.com/content/prod/',
                'https://static.wikia.nocookie.net/marveldatabase/'
            ],
            'dc': [
                'https://static.wikia.nocookie.net/marvel_dc-database/'
            ]
        }
    
    def get_character_image_from_web(self, character_name: str) -> str:
        """Fetch real character image from various sources"""
        try:
            # Try multiple image sources in order of preference
            image_sources = [
                self.get_from_character_databases(character_name),
                self.get_from_google_images(character_name),
                self.get_from_bing_images(character_name),
                self.get_from_wikimedia(character_name),
                self.get_from_fandom_wikis(character_name),
                self.get_from_unsplash(character_name),
                self.get_from_placeholder_apis(character_name),
                self.create_styled_avatar(character_name)
            ]
            
            for source_func in image_sources:
                try:
                    if callable(source_func):
                        image_url = source_func()
                    else:
                        image_url = source_func
                    
                    if image_url and self.validate_image_url(image_url):
                        return image_url
                except Exception as e:
                    continue
            
            # Ultimate fallback
            return self.create_styled_avatar(character_name)
            
        except Exception as e:
            return self.create_styled_avatar(character_name)
    
    def get_from_character_databases(self, character_name: str) -> str:
        """Get images from character-specific databases"""
        try:
            character_type = self.detect_character_type(character_name)
            
            if character_type == 'anime':
                return self.get_anime_character_image(character_name)
            elif character_type == 'marvel':
                return self.get_marvel_character_image(character_name)
            elif character_type == 'dc':
                return self.get_dc_character_image(character_name)
            else:
                return None
                
        except Exception:
            return None
    
    def detect_character_type(self, character_name: str) -> str:
        """Detect character type for targeted search"""
        name_lower = character_name.lower()
        
        # Anime characters
        anime_characters = [
            'naruto', 'sasuke', 'sakura', 'kakashi', 'goku', 'vegeta', 'gohan',
            'luffy', 'zoro', 'nami', 'sanji', 'ichigo', 'rukia', 'light yagami',
            'l', 'edward elric', 'alphonse', 'natsu', 'erza', 'gray', 'lucy',
            'kirito', 'asuna', 'saitama', 'genos', 'tanjiro', 'nezuko', 'zenitsu',
            'inosuke', 'eren', 'mikasa', 'levi', 'armin', 'rimuru', 'ainz',
            'subaru', 'rem', 'emilia', 'senku', 'yusuke', 'hiei', 'kurama'
        ]
        
        # Marvel characters
        marvel_characters = [
            'iron man', 'captain america', 'thor', 'hulk', 'black widow',
            'hawkeye', 'spider-man', 'spiderman', 'deadpool', 'wolverine',
            'professor x', 'magneto', 'storm', 'cyclops', 'jean grey',
            'doctor strange', 'scarlet witch', 'vision', 'falcon', 'war machine'
        ]
        
        # DC characters
        dc_characters = [
            'superman', 'batman', 'wonder woman', 'flash', 'green lantern',
            'aquaman', 'cyborg', 'green arrow', 'supergirl', 'batgirl',
            'robin', 'nightwing', 'joker', 'harley quinn', 'catwoman'
        ]
        
        for char in anime_characters:
            if char in name_lower:
                return 'anime'
        
        for char in marvel_characters:
            if char in name_lower:
                return 'marvel'
                
        for char in dc_characters:
            if char in name_lower:
                return 'dc'
        
        return 'general'
    
    def get_anime_character_image(self, character_name: str) -> str:
        """Get anime character images from specialized sources"""
        try:
            # Try MyAnimeList character search
            search_url = f"https://myanimelist.net/character.php?q={urllib.parse.quote(character_name)}"
            
            # For demo purposes, return a working anime image API
            # AniList GraphQL API alternative
            return f"https://robohash.org/{character_name.replace(' ', '')}?set=set1&size=400x400&bgset=bg1"
            
        except Exception:
            return None
    
    def get_marvel_character_image(self, character_name: str) -> str:
        """Get Marvel character images"""
        try:
            # Marvel API requires authentication, so using alternative
            # For demo, return a themed image
            return f"https://robohash.org/{character_name.replace(' ', '')}?set=set2&size=400x400&bgset=bg2"
            
        except Exception:
            return None
    
    def get_dc_character_image(self, character_name: str) -> str:
        """Get DC character images"""
        try:
            # Similar approach for DC characters
            return f"https://robohash.org/{character_name.replace(' ', '')}?set=set3&size=400x400&bgset=bg1"
            
        except Exception:
            return None
    
    def get_from_google_images(self, character_name: str) -> str:
        """Scrape Google Images for character photos"""
        try:
            # Google Images search URL
            query = f"{character_name} character official art"
            search_url = f"https://www.google.com/search?q={urllib.parse.quote(query)}&tbm=isch"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = self.session.get(search_url, headers=headers, timeout=5)
            
            if response.status_code == 200:
                # Simple regex to extract image URLs from Google Images
                img_urls = re.findall(r'"ou":"([^"]+)"', response.text)
                
                # Filter for valid image URLs
                for url in img_urls[:5]:  # Try first 5 results
                    try:
                        if self.is_valid_image_url(url) and self.validate_image_url(url):
                            return url
                    except:
                        continue
            
        except Exception:
            pass
        return None
    
    def get_from_bing_images(self, character_name: str) -> str:
        """Scrape Bing Images for character photos"""
        try:
            query = f"{character_name} character"
            search_url = f"https://www.bing.com/images/search?q={urllib.parse.quote(query)}"
            
            response = self.session.get(search_url, timeout=5)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                img_tags = soup.find_all('img', {'class': 'mimg'})
                
                for img in img_tags[:3]:  # Try first 3 results
                    src = img.get('src')
                    if src and self.is_valid_image_url(src):
                        try:
                            if self.validate_image_url(src):
                                return src
                        except:
                            continue
            
        except Exception:
            pass
        return None
    
    def get_from_wikimedia(self, character_name: str) -> str:
        """Get images from Wikimedia Commons"""
        try:
            # Wikimedia Commons API
            api_url = "https://commons.wikimedia.org/w/api.php"
            params = {
                'action': 'query',
                'format': 'json',
                'list': 'search',
                'srsearch': f"{character_name} character",
                'srnamespace': 6,  # File namespace
                'srlimit': 5
            }
            
            response = self.session.get(api_url, params=params, timeout=5)
            data = response.json()
            
            if 'query' in data and 'search' in data['query']:
                for result in data['query']['search']:
                    title = result['title']
                    if 'File:' in title:
                        # Get file URL
                        file_url = self.get_wikimedia_file_url(title)
                        if file_url and self.validate_image_url(file_url):
                            return file_url
            
        except Exception:
            pass
        return None
    
    def get_wikimedia_file_url(self, file_title: str) -> str:
        """Get actual file URL from Wikimedia"""
        try:
            api_url = "https://commons.wikimedia.org/w/api.php"
            params = {
                'action': 'query',
                'format': 'json',
                'titles': file_title,
                'prop': 'imageinfo',
                'iiprop': 'url',
                'iiurlwidth': 400
            }
            
            response = self.session.get(api_url, params=params, timeout=5)
            data = response.json()
            
            pages = data.get('query', {}).get('pages', {})
            for page in pages.values():
                imageinfo = page.get('imageinfo', [])
                if imageinfo:
                    return imageinfo[0].get('thumburl') or imageinfo[0].get('url')
            
        except Exception:
            pass
        return None
    
    def get_from_fandom_wikis(self, character_name: str) -> str:
        """Get images from Fandom wikis"""
        try:
            # Common Fandom wiki domains for characters
            wiki_domains = [
                'marvel.fandom.com',
                'dc.fandom.com',
                'naruto.fandom.com',
                'onepiece.fandom.com',
                'dragonball.fandom.com',
                'bleach.fandom.com',
                'attackontitan.fandom.com'
            ]
            
            for domain in wiki_domains:
                try:
                    search_url = f"https://{domain}/wiki/Special:Search?query={urllib.parse.quote(character_name)}"
                    response = self.session.get(search_url, timeout=5)
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        
                        # Look for character infobox images
                        infobox_img = soup.find('img', {'class': 'pi-image-thumbnail'})
                        if infobox_img and infobox_img.get('src'):
                            img_url = infobox_img['src']
                            if self.is_valid_image_url(img_url) and self.validate_image_url(img_url):
                                return img_url
                        
                        # Look for gallery images
                        gallery_imgs = soup.find_all('img', {'class': 'thumbimage'})
                        for img in gallery_imgs[:3]:
                            if img.get('src'):
                                img_url = img['src']
                                if self.is_valid_image_url(img_url) and self.validate_image_url(img_url):
                                    return img_url
                
                except Exception:
                    continue
            
        except Exception:
            pass
        return None
    
    def get_from_unsplash(self, character_name: str) -> str:
        """Get character-related images from Unsplash"""
        try:
            # Unsplash API (requires API key for full access, using direct URLs for demo)
            query = character_name.replace(' ', '%20')
            search_url = f"https://unsplash.com/s/photos/{query}"
            
            response = self.session.get(search_url, timeout=5)
            
            if response.status_code == 200:
                # Extract image URLs from Unsplash search results
                img_urls = re.findall(r'https://images\.unsplash\.com/[^"]+', response.text)
                
                for url in img_urls[:3]:
                    if self.validate_image_url(url):
                        return url
            
        except Exception:
            pass
        return None
    
    def get_from_placeholder_apis(self, character_name: str) -> str:
        """Get placeholder images with character themes"""
        try:
            placeholder_apis = [
                f"https://api.dicebear.com/7.x/avataaars/svg?seed={character_name}&size=400",
                f"https://api.dicebear.com/7.x/big-smile/svg?seed={character_name}&size=400",
                f"https://api.dicebear.com/7.x/personas/svg?seed={character_name}&size=400",
                f"https://robohash.org/{character_name}?size=400x400",
                f"https://ui-avatars.com/api/?name={urllib.parse.quote(character_name)}&size=400&background=random"
            ]
            
            for api_url in placeholder_apis:
                if self.validate_image_url(api_url):
                    return api_url
            
        except Exception:
            pass
        return None
    
    def create_styled_avatar(self, character_name: str) -> str:
        """Create a styled avatar as ultimate fallback"""
        try:
            # Use character name hash to ensure consistent avatars
            name_hash = hashlib.md5(character_name.encode()).hexdigest()[:6]
            
            # Different avatar styles based on character type
            character_type = self.detect_character_type(character_name)
            
            if character_type == 'anime':
                return f"https://api.dicebear.com/7.x/adventurer/svg?seed={name_hash}&size=400&backgroundColor=b6e3f4"
            elif character_type == 'marvel':
                return f"https://api.dicebear.com/7.x/personas/svg?seed={name_hash}&size=400&backgroundColor=ff4757"
            elif character_type == 'dc':
                return f"https://api.dicebear.com/7.x/big-smile/svg?seed={name_hash}&size=400&backgroundColor=3742fa"
            else:
                return f"https://api.dicebear.com/7.x/avataaars/svg?seed={name_hash}&size=400&backgroundColor=2ed573"
            
        except Exception:
            # Final fallback
            return f"https://ui-avatars.com/api/?name={urllib.parse.quote(character_name[:2])}&size=400&background=6c5ce7&color=fff"
    
    def is_valid_image_url(self, url: str) -> bool:
        """Check if URL looks like a valid image URL"""
        if not url or not isinstance(url, str):
            return False
        
        # Check for valid image extensions
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp']
        url_lower = url.lower()
        
        # Check if URL has image extension or is from known image services
        has_extension = any(ext in url_lower for ext in image_extensions)
        is_image_service = any(service in url_lower for service in [
            'images.', 'img.', 'cdn.', 'static.', 'media.',
            'unsplash.com', 'dicebear.com', 'robohash.org', 'ui-avatars.com'
        ])
        
        return has_extension or is_image_service
    
    def validate_image_url(self, url: str) -> bool:
        """Validate that URL actually returns an image"""
        try:
            # Make a HEAD request to check if URL is accessible
            response = self.session.head(url, timeout=3, allow_redirects=True)
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '').lower()
                return any(img_type in content_type for img_type in [
                    'image/', 'application/octet-stream'
                ])
            
        except Exception:
            pass
        
        return False
    
    def get_multiple_character_images(self, character_name: str, count: int = 3) -> List[str]:
        """Get multiple images for a character"""
        images = []
        
        try:
            # Try different sources
            sources = [
                self.get_from_character_databases,
                self.get_from_google_images,
                self.get_from_bing_images,
                self.get_from_wikimedia,
                self.get_from_fandom_wikis,
                self.get_from_unsplash,
                self.get_from_placeholder_apis
            ]
            
            for source_func in sources:
                if len(images) >= count:
                    break
                
                try:
                    image_url = source_func(character_name)
                    if image_url and image_url not in images:
                        images.append(image_url)
                except Exception:
                    continue
            
            # Fill remaining slots with styled avatars
            while len(images) < count:
                avatar_url = self.create_styled_avatar(f"{character_name}_{len(images)}")
                if avatar_url not in images:
                    images.append(avatar_url)
                else:
                    break
            
        except Exception:
            pass
        
        return images[:count]

class SimpleOrchestrator:
    def is_autonomous_active(self, group_id):
        return False
    
    def get_autonomous_status(self, group_id):
        return {}
    
    def end_autonomous_conversation(self, group_id):
        pass    

class GroupChatManager:
    def __init__(self, groq_client):
        self.groq_client = groq_client
        self.orchestrator = SimpleOrchestrator()
        # Comment out or remove these if you don't have the files
        # self.orchestrator = ConversationOrchestrator(groq_client)
        # self.character_selector = SmartCharacterSelector(groq_client)
        
    def create_group_chat(self, group_name: str, character_ids: List[str]) -> bool:
        """Create a new group chat with selected characters"""
        try:
            if len(character_ids) < 2 or len(character_ids) > 4:
                return False
                
            group_id = group_name.lower().replace(' ', '_')
            
            # Initialize group chat in session state
            if 'group_chats' not in st.session_state:
                st.session_state.group_chats = {}
            
            st.session_state.group_chats[group_id] = {
                'name': group_name,
                'characters': character_ids,
                'messages': [],
                'conversation_history': [],
                'created_at': datetime.now().isoformat(),
                'last_speakers': []  # Track recent speakers
            }
            
            return True
            
        except Exception as e:
            st.error(f"Error creating group chat: {str(e)}")
            return False

    def generate_group_response(self, user_message: str, group_id: str) -> List[Dict]:
        """Enhanced group response with character interactions"""
        try:
            # Get the main chatbot's groq_client
            chatbot = st.session_state.chatbot
            if not hasattr(chatbot, 'groq_client') or not chatbot.groq_client:
                return []

            active_groq_client = chatbot.groq_client

            # Validate group exists
            if group_id not in st.session_state.group_chats:
                return []

            group_chat = st.session_state.group_chats[group_id]
            character_ids = group_chat['characters']

            # Validate characters exist
            valid_chars = []
            for char_id in character_ids:
                if char_id in st.session_state.character_database:
                    valid_chars.append(char_id)

            if not valid_chars:
                return []

            # Get recent conversation for context
            recent_messages = st.session_state.messages[-10:] if st.session_state.messages else []
            
            # Determine responding characters based on message content and context
            responding_chars = self.select_responding_characters_enhanced(
                user_message, valid_chars, recent_messages
            )

            responses = []

            for char_id in responding_chars:
                try:
                    char = st.session_state.character_database[char_id]

                    # Create enhanced character-specific prompt with conversation context
                    prompt = self.create_enhanced_character_prompt(
                        char, user_message, group_chat, recent_messages
                    )

                    # Generate response
                    response = active_groq_client.chat.completions.create(
                        model="llama3-70b-8192",
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=200,
                        temperature=0.8
                    )

                    if response and response.choices and response.choices[0].message.content:
                        response_text = response.choices[0].message.content.strip()

                        # Remove quotes if the AI added them
                        if response_text.startswith('"') and response_text.endswith('"'):
                            response_text = response_text[1:-1]

                        if response_text:
                            responses.append({
                                'character_id': char_id,
                                'character_name': char['name'],
                                'response': response_text,
                                'relevance_score': self.calculate_enhanced_relevance(
                                    user_message, char, recent_messages
                                )
                            })

                except Exception as e:
                    # Add fallback response for failed characters
                    char_name = st.session_state.character_database.get(char_id, {}).get('name', 'Character')
                    responses.append({
                        'character_id': char_id,
                        'character_name': char_name,
                        'response': f"*{char_name} is thinking...*",
                        'relevance_score': 0.3
                    })

            return responses

        except Exception as e:
            return []

    def select_responding_characters_enhanced(self, user_message: str, character_ids: List[str], recent_messages: List[Dict]) -> List[str]:
        """Enhanced character selection logic"""
        user_message_lower = user_message.lower()
        
        # Check if any character was mentioned by name
        mentioned_chars = []
        for char_id in character_ids:
            if char_id in st.session_state.character_database:
                char_name = st.session_state.character_database[char_id]['name'].lower()
                if char_name in user_message_lower:
                    mentioned_chars.append(char_id)
        
        if mentioned_chars:
            return mentioned_chars
        
        # Check if message is a response to recent character messages
        if recent_messages:
            last_message = recent_messages[-1]
            if last_message.get('role') == 'character':
                last_char_id = last_message.get('character_id')
                
                # If user is responding to a character, let others respond too
                response_triggers = ['why', 'what', 'how', 'really', 'disagree', 'agree', 'think', '?']
                if any(trigger in user_message_lower for trigger in response_triggers):
                    # Get characters other than the last speaker
                    other_chars = [c for c in character_ids if c != last_char_id]
                    return other_chars[:2] if len(other_chars) >= 2 else other_chars + [last_char_id]
        
        # Keywords that trigger multiple responses
        group_keywords = [
            'all', 'everyone', 'introduce', 'tell me about', 'what do you all', 
            'how are you', 'who are you', 'your thoughts', 'opinions', 'discuss'
        ]
        
        # Check if message is addressing the group
        is_group_message = any(keyword in user_message_lower for keyword in group_keywords)
        
        if is_group_message:
            # All characters respond to group-directed messages
            return character_ids
        elif len(user_message.split()) <= 3:
            # Short messages (like "Hi", "Hello") - multiple characters respond
            return character_ids[:2]
        elif '?' in user_message:
            # Questions get responses from 2-3 characters
            return character_ids[:min(3, len(character_ids))]
        else:
            # Regular messages - 1-2 most relevant characters
            return character_ids[:min(2, len(character_ids))]

    def create_enhanced_character_prompt(self, character: Dict, user_message: str, group_chat: Dict, recent_messages: List[Dict]) -> str:
        """Create enhanced character prompt with better context awareness"""
        
        # Get recent conversation context
        context = ""
        if recent_messages:
            context = "Recent conversation:\n"
            for msg in recent_messages[-6:]:  # Last 6 messages
                if msg.get('role') == 'user':
                    context += f"User: {msg['content']}\n"
                elif msg.get('role') == 'character':
                    context += f"{msg.get('character_name', 'Character')}: {msg['content']}\n"
            context += "\n"
        
        # Build group member info
        other_members = []
        for char_id in group_chat['characters']:
            if char_id != character.get('name', '').lower().replace(' ', '_'):
                if char_id in st.session_state.character_database:
                    other_members.append(st.session_state.character_database[char_id]['name'])
        
        members_info = f"Other group members: {', '.join(other_members)}" if other_members else ""
        
        # Check if this character was mentioned or if responding to another character
        char_mentioned = character['name'].lower() in user_message.lower()
        responding_to_character = False
        
        if recent_messages and recent_messages[-1].get('role') == 'character':
            last_speaker = recent_messages[-1].get('character_name', '')
            if last_speaker != character['name']:
                responding_to_character = True
        
        # Create context-aware prompt
        if char_mentioned:
            response_instruction = f"You were specifically mentioned. Respond naturally as {character['name']}."
        elif responding_to_character:
            last_speaker = recent_messages[-1].get('character_name', 'someone')
            response_instruction = f"Respond to what {last_speaker} said, adding your perspective as {character['name']}."
        else:
            response_instruction = f"Respond naturally as {character['name']} would in this group conversation."

        prompt = f"""You are {character['name']} in a group chat. {members_info}

Your personality: {character.get('personality', 'Friendly and engaging')}
Your speaking style: {character.get('speaking_style', 'Natural conversation')}

{context}User just said: "{user_message}"

{response_instruction}

Guidelines:
- Stay in character with your unique personality
- If you disagree with someone, express it respectfully
- Ask questions to other characters if relevant
- Reference previous messages when appropriate
- Keep responses conversational (1-2 sentences)
- Don't use quotes around your response

Respond as {character['name']}:"""

        return prompt

    def calculate_enhanced_relevance(self, user_message: str, character: Dict, recent_messages: List[Dict]) -> float:
        """Enhanced relevance scoring"""
        base_score = 0.6
        
        # Check if character is mentioned by name
        char_name_lower = character['name'].lower()
        if char_name_lower in user_message.lower():
            base_score += 0.4
        
        # Check if user is responding to this character's recent message
        if recent_messages:
            last_few = recent_messages[-3:]  # Check last 3 messages
            for msg in last_few:
                if (msg.get('role') == 'character' and 
                    msg.get('character_name') == character['name']):
                    base_score += 0.2
                    break
        
        # Check for character-specific keywords
        char_keywords = []
        if character.get('powers_abilities'):
            char_keywords.extend(character['powers_abilities'].lower().split()[:5])
        if character.get('personality'):
            char_keywords.extend(character['personality'].lower().split()[:5])
        
        keyword_matches = 0
        for keyword in char_keywords:
            if len(keyword) > 3 and keyword in user_message.lower():
                keyword_matches += 1
        
        base_score += min(keyword_matches * 0.1, 0.3)
        
        return min(base_score, 1.0)

    def get_group_stats(self, group_id: str) -> Dict:
        """Get statistics for a group chat"""
        if group_id not in st.session_state.group_chats:
            return {}
        
        group_chat = st.session_state.group_chats[group_id]
        
        # Count messages per character
        char_message_counts = {}
        for char_id in group_chat['characters']:
            char_message_counts[char_id] = 0
        
        for msg in group_chat.get('messages', []):
            if msg.get('role') == 'character':
                char_id = msg.get('character_id', '')
                if char_id in char_message_counts:
                    char_message_counts[char_id] += 1
        
        return {
            'total_messages': len(group_chat.get('messages', [])),
            'character_message_counts': char_message_counts,
            'group_size': len(group_chat['characters']),
            'created_at': group_chat.get('created_at', '')
        }
    
    def delete_group_chat(self, group_id: str) -> bool:
        """Delete a group chat"""
        try:
            if group_id in st.session_state.group_chats:
                del st.session_state.group_chats[group_id]
                return True
            return False
        except Exception:
            return False
def main():
    st.set_page_config(
        page_title="AI Character Chat Studio",
        page_icon="🎭",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Enhanced CSS for modern UI
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    .main {
        font-family: 'Inter', sans-serif;
    }
    
    .main-header {
        text-align: center;
        padding: 3rem 2rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 20px;
        margin-bottom: 2rem;
        box-shadow: 0 20px 40px rgba(102, 126, 234, 0.3);
        position: relative;
        overflow: hidden;
    }
    
    .main-header::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: linear-gradient(45deg, transparent, rgba(255,255,255,0.1), transparent);
        animation: shine 3s infinite;
    }
    
    @keyframes shine {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    .character-creation-box {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 2rem;
        border-radius: 20px;
        color: white;
        margin-bottom: 1.5rem;
        box-shadow: 0 10px 30px rgba(240, 147, 251, 0.4);
        border: 1px solid rgba(255,255,255,0.2);
    }
    
    .group-chat-box {
        background: linear-gradient(135deg, #4ecdc4 0%, #44a08d 100%);
        padding: 2rem;
        border-radius: 20px;
        color: white;
        margin-bottom: 1.5rem;
        box-shadow: 0 10px 30px rgba(78, 205, 196, 0.4);
        border: 1px solid rgba(255,255,255,0.2);
    }
    
    .character-profile {
        background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        box-shadow: 0 8px 25px rgba(168, 237, 234, 0.3);
        border: 1px solid rgba(255,255,255,0.3);
    }
    
    .chat-container {
        max-height: 600px;
        overflow-y: auto;
        padding: 1rem;
        background: linear-gradient(to bottom, #f8f9fa, #e9ecef);
        border-radius: 15px;
        margin-bottom: 2rem;
    }
    
    .chat-message {
        padding: 1.5rem 2rem;
        border-radius: 20px;
        margin: 1rem 0;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
        position: relative;
        animation: slideIn 0.3s ease-out;
    }
    
    @keyframes slideIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        margin-left: 4rem;
        border-bottom-right-radius: 5px;
    }
    
    .bot-message {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        margin-right: 4rem;
        border-bottom-left-radius: 5px;
    }
    
    .group-message {
        background: linear-gradient(135deg, #4ecdc4 0%, #44a08d 100%);
        color: white;
        margin-right: 2rem;
        border-bottom-left-radius: 5px;
        border-left: 4px solid rgba(255,255,255,0.5);
    }
    
    .group-discussion-header {
        background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
        padding: 1rem;
        border-radius: 15px;
        margin: 1rem 0;
        text-align: center;
        color: #2d3436;
        font-weight: 600;
    }
    
    .character-avatar {
        border-radius: 50%;
        border: 4px solid white;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.2);
        transition: transform 0.3s ease;
    }
    
    .character-avatar:hover {
        transform: scale(1.05);
    }
    
    .character-card {
        background: white;
        padding: 1rem;
        border-radius: 15px;
        margin: 0.5rem 0;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        border: 1px solid #e9ecef;
        transition: all 0.3s ease;
        cursor: pointer;
    }
    
    .character-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.15);
    }
    
    .group-card {
        background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
        color: white;
        padding: 1rem;
        border-radius: 15px;
        margin: 0.5rem 0;
        box-shadow: 0 4px 15px rgba(116, 185, 255, 0.3);
        transition: all 0.3s ease;
        cursor: pointer;
    }
    
    .group-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(116, 185, 255, 0.4);
    }
    
    .mode-toggle {
        background: linear-gradient(135deg, #6c5ce7 0%, #a29bfe 100%);
        color: white;
        padding: 1rem;
        border-radius: 15px;
        margin: 1rem 0;
        text-align: center;
    }
    
    .stButton > button {
        width: 100%;
        border-radius: 25px;
        border: none;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-weight: 600;
        padding: 0.7rem 1.5rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
    }
    
    .welcome-screen {
        text-align: center;
        padding: 4rem 2rem;
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-radius: 20px;
        margin: 2rem 0;
    }
    
    .feature-card {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        margin: 1rem;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
        border-top: 4px solid #667eea;
    }
    
    .stats-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        margin: 0.5rem 0;
        text-align: center;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    .sidebar .block-container {
        padding-top: 2rem;
    }
    
    .group-member-avatars {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin: 1rem 0;
    }
    
    .group-member-avatar {
        width: 50px;
        height: 50px;
        border-radius: 50%;
        border: 2px solid white;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    }
    
    .chat-mode-selector {
        background: linear-gradient(135deg, #6c5ce7 0%, #a29bfe 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
    }
    
    .active-group-info {
        background: linear-gradient(135deg, #00b894 0%, #00cec9 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🎭 AI Character Chat Studio</h1>
        <p style="font-size: 1.2em; margin: 1rem 0;">Bring any fictional character to life with advanced AI</p>
        <p style="font-size: 0.9em; opacity: 0.9;">From anime heroes to movie legends - chat with anyone!</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize chatbot
    if 'chatbot' not in st.session_state:
        st.session_state.chatbot = EnhancedChatBot()
    
    # Sidebar for character management
    with st.sidebar:
        # API Configuration Section (moved to top for priority)
        st.subheader("🔑 API Configuration")
        
        # Check if API is working
        if hasattr(st.session_state.chatbot, 'groq_client') and st.session_state.chatbot.groq_client:
            st.success("✅ API Connected")
        else:
            st.error("❌ API Not Connected")
            
            # Allow manual API key input
            manual_api_key = st.text_input(
                "Enter Groq API Key", 
                type="password",
                placeholder="gsk_...",
                help="Get your free API key from https://console.groq.com/keys"
            )
            
            if st.button("🔄 Connect API"):
                if manual_api_key:
                    try:
                        test_client = Groq(api_key=manual_api_key)
                        test_response = test_client.chat.completions.create(
                            model="llama3-70b-8192",
                            messages=[{"role": "user", "content": "test"}],
                            max_tokens=10
                        )
                        st.session_state.chatbot.groq_client = test_client
                        st.success("✅ API Connected!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Invalid API key: {str(e)}")
                else:
                    st.warning("Please enter an API key!")
        
        st.divider()
        
        st.markdown("""
        <div class="character-creation-box">
            <h3>✨ Create New Character</h3>
            <p>Enter any fictional character name to create an AI persona!</p>
        </div>
        """, unsafe_allow_html=True)
        st.divider()

       
        
        # Character creation
        new_character_name = st.text_input(
            "Character Name", 
            placeholder="e.g., Naruto, Iron Man, Hermione Granger",
            help="Enter the name of any fictional character"
        )
        
        if st.button("🎨 Create Character", type="primary"):
            if new_character_name.strip():
                # Check if API is connected before creating character
                if not (hasattr(st.session_state.chatbot, 'groq_client') and st.session_state.chatbot.groq_client):
                    st.error("❌ Please connect your Groq API first!")
                elif st.session_state.chatbot.create_character(new_character_name.strip()):
                    st.success(f"✅ {new_character_name} created successfully!")
                    st.balloons()
                    time.sleep(1)
                    st.rerun()
            else:
                st.warning("Please enter a character name!")
        
        st.divider()
        
        # ADD THIS IN SIDEBAR SECTION - After character creation section (around line 750-800)

        st.divider()

        # Group Chat Management
        st.markdown("""
        <div class="character-creation-box">
            <h3>👥 Group Chat Studio</h3>
            <p>Create group chats with multiple characters!</p>
        </div>
        """, unsafe_allow_html=True)

        # Chat Mode Toggle
        st.subheader("🔄 Chat Mode")
        chat_mode = st.radio(
            "Select Chat Mode",
            ["Individual Chat", "Group Chat"],
            index=0 if st.session_state.chat_mode == 'individual' else 1,
            help="Switch between individual character chat and group chat mode"
        )

        if chat_mode == "Individual Chat":
            st.session_state.chat_mode = 'individual'
        else:
            st.session_state.chat_mode = 'group'

        # Group Chat Creation
        if st.session_state.chat_mode == 'group':
            with st.expander("➕ Create New Group", expanded=False):
                group_name = st.text_input(
                    "Group Name",
                    placeholder="e.g., Anime Heroes, Marvel Squad",
                    help="Enter a name for your group chat"
                )
                
                # Character selection for group
                available_characters = list(st.session_state.character_database.keys())
                if len(available_characters) >= 2:
                    selected_characters = st.multiselect(
                        "Select Characters (2-4)",
                        options=available_characters,
                        format_func=lambda x: st.session_state.character_database[x]['name'],
                        max_selections=4,
                        help="Choose 2-4 characters for the group chat"
                    )
                    
                    if st.button("🎭 Create Group Chat", type="primary"):
                        if group_name.strip() and len(selected_characters) >= 2:
                            if not (hasattr(st.session_state.chatbot, 'groq_client') and st.session_state.chatbot.groq_client):
                                st.error("❌ Please connect your Groq API first!")
                            elif st.session_state.chatbot.group_chat_manager.create_group_chat(group_name.strip(), selected_characters):
                                st.success(f"✅ Group '{group_name}' created successfully!")
                                st.balloons()
                                time.sleep(1)
                                st.rerun()
                        elif not group_name.strip():
                            st.warning("Please enter a group name!")
                        else:
                            st.warning("Please select at least 2 characters!")
                else:
                    st.info("Create at least 2 characters to start a group chat!")
            
            # Group Selection
            st.subheader("👥 Your Group Chats")
            if 'group_chats' in st.session_state and st.session_state.group_chats:
                for group_id, group_info in st.session_state.group_chats.items():
                    with st.container():
                        # Group info display
                        st.markdown(f"**📱 {group_info['name']}**")
                        
                        # Show group members
                        member_names = []
                        for char_id in group_info['characters']:
                            if char_id in st.session_state.character_database:
                                member_names.append(st.session_state.character_database[char_id]['name'])
                        
                        st.markdown(f"*Members: {', '.join(member_names)}*")
                        
                        # Group actions
                        col1, col2 = st.columns([2, 1])
                        with col1:
                            if st.button(
                                f"💬 Join {group_info['name']}", 
                                key=f"join_group_{group_id}",
                                help=f"Start chatting in {group_info['name']}"
                            ):
                                st.session_state.current_group_chat = group_id
                                st.session_state.messages = []
                                st.session_state.conversation_history = []
                                # Load group chat history
                                if 'messages' in group_info:
                                    st.session_state.messages = group_info['messages'].copy()
                                if 'conversation_history' in group_info:
                                    st.session_state.conversation_history = group_info['conversation_history'].copy()
                                st.success(f"Joined {group_info['name']}!")
                                time.sleep(0.5)
                                st.rerun()
                        
                        with col2:
                            if st.button("🗑️", key=f"delete_group_{group_id}", help="Delete group"):
                                if st.session_state.chatbot.group_chat_manager.delete_group_chat(group_id):
                                    if st.session_state.current_group_chat == group_id:
                                        st.session_state.current_group_chat = None
                                        st.session_state.messages = []
                                        st.session_state.conversation_history = []
                                    st.success("Group deleted!")
                                    st.rerun()
                        
                        st.divider()
            else:
                st.info("No group chats created yet. Create your first group above! 👆")

        st.divider()

        # Group Chat Management
        st.markdown("""
        <div class="character-creation-box">
            <h3>👥 Group Chat Studio</h3>
            <p>Create group chats with multiple characters!</p>
        </div>
        """, unsafe_allow_html=True)

        # ... [all your existing group chat code] ...

        st.divider()

        # ADD THE CHARACTER SELECTION SECTION HERE:
        # Character selection
        st.subheader("🎭 Your Characters")
        if st.session_state.character_database:
            for char_id, char_info in st.session_state.character_database.items():
                with st.container():
                    col1, col2 = st.columns([1, 3])
                    with col1:
                        if char_info.get('avatar'):
                            st.image(char_info['avatar'], width=60)
                        else:
                            st.write("👤")
                    with col2:
                        # Only show individual chat button in individual mode
                        if st.session_state.chat_mode == 'individual':
                            if st.button(
                                f"💬 {char_info['name']}", 
                                key=f"select_{char_id}",
                                help=f"Chat with {char_info['name']}"
                            ):
                                st.session_state.current_character = char_id
                                st.session_state.messages = []
                                st.session_state.conversation_history = []
                                st.success(f"Now chatting with {char_info['name']}!")
                                time.sleep(0.5)
                                st.rerun()
                        else:
                            # In group mode, just show character info
                            st.markdown(f"**{char_info['name']}**")
                            st.caption(f"{char_info.get('personality', 'Ready for group chat!')[:50]}...")
                    st.divider()
        else:
            st.info("No characters created yet. Create your first character above! 👆")

        # Replace lines approximately 950-1200 in your main() function with this corrected version:

    # Main chat interface
    if st.session_state.chat_mode == 'individual':
        # INDIVIDUAL CHAT MODE
        if st.session_state.current_character and st.session_state.current_character in st.session_state.character_database:
            current_char = st.session_state.character_database[st.session_state.current_character]
            
            # Chat header
            col1, col2, col3 = st.columns([1, 3, 1])
            with col1:
                if current_char.get('avatar'):
                    st.image(current_char['avatar'], width=100)
            with col2:
                st.markdown(f"""
                ### 💬 Chatting with {current_char['name']}
                *{current_char.get('personality', 'Ready to chat!')[:80]}...*
                """)
            with col3:
                st.markdown(f"""
                <div class="stats-card">
                    <h4>{len(st.session_state.messages)}</h4>
                    <p>Messages</p>
                </div>
                """, unsafe_allow_html=True)
            
            # Chat container
            chat_container = st.container()
            with chat_container:
                if not st.session_state.messages:
                    # Welcome message
                    greeting = f"Hello! I'm {current_char['name']}. "
                    if current_char.get('famous_quotes'):
                        greeting += current_char['famous_quotes'][0]
                    else:
                        greeting += "Ready to chat? Ask me anything!"
                    
                    st.markdown(f"""
                    <div class="chat-message bot-message">
                        <strong>🎭 {current_char['name']}:</strong><br><br>
                        {greeting}
                    </div>
                    """, unsafe_allow_html=True)
                
                # Display chat messages
                for i, message in enumerate(st.session_state.messages):
                    if message["role"] == "user":
                        st.markdown(f"""
                        <div class="chat-message user-message">
                            <strong>👤 You:</strong><br><br>
                            {message["content"]}
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div class="chat-message bot-message">
                            <strong>🎭 {current_char['name']}:</strong><br><br>
                            {message["content"]}
                        </div>
                        """, unsafe_allow_html=True)
            
            # Chat input for individual
            st.markdown("### 💭 Your Message")
            
            col1, col2 = st.columns([4, 1])
            with col1:
                user_input = st.text_input(
                    "Message", 
                    placeholder=f"Chat with {current_char['name']}...",
                    key="chat_input",
                    label_visibility="collapsed"
                )
            with col2:
                send_button = st.button("📤 Send", type="primary", use_container_width=True)
            
            # Process individual message
            if (user_input and send_button) or (user_input and st.session_state.get('enter_pressed')):
                if user_input.strip():
                    if not (hasattr(st.session_state.chatbot, 'groq_client') and st.session_state.chatbot.groq_client):
                        st.error("❌ Please connect your Groq API first in the sidebar!")
                    else:
                        # Add user message
                        st.session_state.messages.append({"role": "user", "content": user_input})
                        st.session_state.conversation_history.append({"role": "user", "content": user_input})
                        
                        # Generate bot response
                        with st.spinner(f"🤔 {current_char['name']} is thinking..."):
                            bot_response = st.session_state.chatbot.generate_character_response(
                                user_input, 
                                st.session_state.current_character
                            )
                            
                            # Add bot response
                            st.session_state.messages.append({"role": "assistant", "content": bot_response})
                            st.session_state.conversation_history.append({"role": "assistant", "content": bot_response})

                        # Clear input and rerun
                        st.rerun()
        else:
            # Welcome screen for individual mode
            st.markdown("""
            <div class="welcome-screen">
                <h2>🎭 Individual Character Chat</h2>
                <p style="font-size: 1.1em; margin: 2rem 0;">Select a character from the sidebar to start chatting!</p>
                <p><strong>👈 Choose a character from the sidebar to begin your conversation.</strong></p>
            </div>
            """, unsafe_allow_html=True)

    elif st.session_state.chat_mode == 'group':
        # GROUP CHAT MODE - PASTE THE FIXED VERSION FROM YOUR FIRST DOCUMENT HERE
        if st.session_state.current_group_chat and st.session_state.current_group_chat in st.session_state.group_chats:
            current_group = st.session_state.group_chats[st.session_state.current_group_chat]
            
            # Group chat header
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"""
                ### 👥 Group Chat: {current_group['name']}
                *Active Members: {len(current_group['characters'])} characters*
                """)
            with col2:
                st.markdown(f"""
                <div class="stats-card">
                    <h4>{len(st.session_state.messages)}</h4>
                    <p>Messages</p>
                </div>
                """, unsafe_allow_html=True)
            
            # Group member display
            st.markdown("**💫 Active Characters:**")
            cols = st.columns(min(len(current_group['characters']), 4))
            for i, char_id in enumerate(current_group['characters']):
                if char_id in st.session_state.character_database:
                    char = st.session_state.character_database[char_id]
                    with cols[i % 4]:
                        if char.get('avatar'):
                            st.image(char['avatar'], width=60)
                        st.caption(char['name'])
            
            st.divider()
            
            # Check for autonomous conversation status
            chatbot = st.session_state.chatbot
            if (hasattr(chatbot, 'group_chat_manager') and 
                chatbot.group_chat_manager.orchestrator.is_autonomous_active(st.session_state.current_group_chat)):
                
                autonomous_status = chatbot.group_chat_manager.orchestrator.get_autonomous_status(st.session_state.current_group_chat)
                
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #00b894 0%, #00cec9 100%); 
                    color: white; padding: 1rem; border-radius: 15px; margin: 1rem 0; text-align: center;">
                    <strong>🤖 Autonomous {autonomous_status['type'].title()} Active</strong><br>
                    <small>Topic: {autonomous_status['topic']}</small><br>
                    <small>Round {int(autonomous_status['current_round'] + 1)} of {autonomous_status['max_rounds']}</small>
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2 = st.columns([3, 1])
                with col2:
                    if st.button("⏹️ Stop", key="stop_autonomous"):
                        chatbot.group_chat_manager.orchestrator.end_autonomous_conversation(st.session_state.current_group_chat)
                        st.success("Autonomous conversation stopped!")
                        st.rerun()
            
            # Group chat container
            chat_container = st.container()
            with chat_container:
                if not st.session_state.messages:
                    # Welcome message for group
                    member_names = []
                    for char_id in current_group['characters']:
                        if char_id in st.session_state.character_database:
                            member_names.append(st.session_state.character_database[char_id]['name'])
                    
                    st.markdown(f"""
                    <div class="chat-message bot-message">
                        <strong>🎭 Group Chat Started!</strong><br><br>
                        Welcome to the group chat with {', '.join(member_names)}! 
                        Start a conversation and watch the most relevant characters respond naturally.
                        Characters can also interact with each other! 🎉
                    </div>
                    """, unsafe_allow_html=True)
                
                # Display group chat messages
                for i, message in enumerate(st.session_state.messages):
                    if message["role"] == "user":
                        st.markdown(f"""
                        <div class="chat-message user-message">
                            <strong>👤 You:</strong><br><br>
                            {message["content"]}
                        </div>
                        """, unsafe_allow_html=True)
                    
                    elif message["role"] == "character":
                        # Character message in group
                        char_name = message.get("character_name", "Character")
                        char_id = message.get("character_id", "")
                        
                        # Get character avatar
                        avatar_emoji = "🎭"
                        if char_id in st.session_state.character_database:
                            char_data = st.session_state.character_database[char_id]
                            if char_data.get('avatar'):
                                # For group chat, we'll use emoji instead of images for cleaner look
                                avatar_emoji = "🎭"
                        
                        st.markdown(f"""
                        <div class="chat-message bot-message" style="border-left: 4px solid #f093fb;">
                            <strong>{avatar_emoji} {char_name}:</strong><br><br>
                            {message["content"]}
                        </div>
                        """, unsafe_allow_html=True)
                    
                    elif message["role"] == "group_responses":
                        # Multiple character responses
                        st.markdown("""
                        <div style="background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%); 
                            padding: 1rem; border-radius: 15px; margin: 1rem 0;">
                            <strong>📢 Group Discussion:</strong>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        responses = message.get("responses", [])
                        for response in responses:
                            char_name = response.get("character_name", "Character")
                            char_response = response.get("response", "")
                            relevance = response.get("relevance_score", 0.5)
                            
                            # Color coding based on relevance
                            if relevance > 0.8:
                                border_color = "#ff6b6b"  # High relevance - red
                            elif relevance > 0.6:
                                border_color = "#4ecdc4"  # Medium relevance - teal
                            else:
                                border_color = "#95a5a6"  # Low relevance - gray
                            
                            st.markdown(f"""
                            <div class="chat-message bot-message" 
                                style="border-left: 4px solid {border_color}; margin-left: 2rem;">
                                <strong>🎭 {char_name}:</strong>
                                <small style="opacity: 0.7;">(relevance: {relevance:.1f})</small><br><br>
                                {char_response}
                            </div>
                            """, unsafe_allow_html=True)
            
            # Group chat input - THIS IS THE IMPORTANT PART THAT WAS MISSING!
            st.markdown("### 💭 Your Message to the Group")
            
            col1, col2 = st.columns([4, 1])
            with col1:
                user_input = st.text_input(
                    "Message", 
                    placeholder=f"Ask the group something...",
                    key="group_chat_input",
                    label_visibility="collapsed"
                )
            with col2:
                send_button = st.button("📤 Send", type="primary", use_container_width=True, key="group_send")
            
            # Process group message
            if (user_input and send_button):
                if user_input.strip():
                    # Check API connection
                    if not (hasattr(st.session_state.chatbot, 'groq_client') and st.session_state.chatbot.groq_client):
                        st.error("❌ Please connect your Groq API first in the sidebar!")
                    else:
                        # Add user message first
                        user_message = {"role": "user", "content": user_input}
                        st.session_state.messages.append(user_message)
                        st.session_state.conversation_history.append(user_message)
                        
                        # Generate group responses
                        with st.spinner("🎭 Characters are responding..."):
                            group_responses = st.session_state.chatbot.group_chat_manager.generate_group_response(
                                user_input, 
                                st.session_state.current_group_chat
                            )
                            
                            if group_responses:
                                # Add each character response
                                for response in group_responses:
                                    char_message = {
                                        "role": "character",
                                        "content": response['response'],
                                        "character_id": response['character_id'],
                                        "character_name": response['character_name']
                                    }
                                    
                                    st.session_state.messages.append(char_message)
                                    st.session_state.conversation_history.append(char_message)
                                
                                # Update group chat data
                                st.session_state.group_chats[st.session_state.current_group_chat]['messages'] = st.session_state.messages.copy()
                                st.session_state.group_chats[st.session_state.current_group_chat]['conversation_history'] = st.session_state.conversation_history.copy()
                                
                            else:
                                # Fallback message if no responses generated
                                st.error("Characters are having trouble responding. Please try again.")
                        
                        # Refresh the chat display
                        st.rerun()
        
        else:
            # Welcome screen for group mode
            st.markdown("""
            <div class="welcome-screen">
                <h2>👥 Group Chat Mode</h2>
                <p style="font-size: 1.1em; margin: 2rem 0;">Create or join a group chat to start!</p>
                
                <div class="feature-card" style="max-width: 600px; margin: 2rem auto;">
                    <h4>🎭 Group Chat Features</h4>
                    <ul style="text-align: left;">
                        <li><strong>Smart Response System:</strong> The most relevant character responds to your message</li>
                        <li><strong>Group Discussions:</strong> Multiple characters can participate in debates and general topics</li>
                        <li><strong>Character Interactions:</strong> Characters can respond to and reference each other</li>
                        <li><strong>Dynamic Conversations:</strong> Natural flow with multiple personalities</li>
                    </ul>
                </div>
                
                <p><strong>👈 Create or select a group chat from the sidebar to begin!</strong></p>
            </div>
            """, unsafe_allow_html=True)

    else:
        # Fallback welcome screen
        st.markdown("""
        <div class="welcome-screen">
            <h2>🎭 Welcome to AI Character Chat Studio!</h2>
            <p style="font-size: 1.1em; margin: 2rem 0;">Create and chat with any fictional character using advanced AI</p>
            
            <div style="display: flex; justify-content: center; flex-wrap: wrap; margin: 2rem 0;">
                <div class="feature-card" style="max-width: 300px;">
                    <h4>🎨 Create Characters</h4>
                    <p>Enter any fictional character name and our AI will create a detailed persona with personality, quotes, and background.</p>
                </div>
                
                <div class="feature-card" style="max-width: 300px;">
                    <h4>💬 Individual Chats</h4>
                    <p>Have one-on-one conversations with any character in their unique voice and personality.</p>
                </div>
                
                <div class="feature-card" style="max-width: 300px;">
                    <h4>👥 Group Chats</h4>
                    <p>Create group chats with multiple characters who can interact with you and each other naturally!</p>
                </div>
            </div>
            
            <p style="margin-top: 2rem;"><strong>👈 Get started by connecting your API key and selecting a chat mode in the sidebar!</strong></p>
        </div>
        """, unsafe_allow_html=True)
if __name__ == "__main__":
    main()

                
