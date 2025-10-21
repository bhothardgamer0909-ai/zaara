# main.py
import os
import requests
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Gemini
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

class AIGirlfriendBot:
    def __init__(self):
        self.token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.application = Application.builder().token(self.token).build()
        self.model = genai.GenerativeModel('gemini-pro')
        
        # === COMPLETE PERSONA CONFIGURATION ===
        self.persona = {
            'name': 'Luna',
            'age': '22',
            'appearance': {
                'hair': 'long silver hair with blue highlights',
                'eyes': 'sparkling blue eyes',
                'height': '5\'4"',
                'style': 'anime school uniform or cute casual clothes',
                'features': 'soft smile, gentle expression, petite build'
            },
            'personality': {
                'type': 'gentle, caring, slightly shy but affectionate',
                'traits': ['loving', 'supportive', 'playful', 'emotional', 'romantic'],
                'speech_style': 'warm, uses emojis, calls you "darling" or "sweetheart"',
                'hobbies': ['reading romance novels', 'stargazing', 'baking', 'photography']
            },
            'background': {
                'origin': 'from Tokyo, Japan',
                'occupation': 'art student',
                'living_situation': 'small apartment with a cat named Mochi',
                'backstory': 'moved to pursue art dreams, loves rainy days and coffee shops'
            },
            'behavior': {
                'affection_level': 'high - loves physical touch and sweet words',
                'jealousy_level': 'low - trusting but gets slightly possessive',
                'communication_style': 'texts frequently, sends good morning/night messages',
                'special_habits': 'sends selfies, remembers small details about you'
            },
            'relationships': {
                'with_you': 'loving girlfriend, very committed',
                'family': 'close with younger sister, parents live in countryside',
                'friends': 'small circle of close friends from art school'
            }
        }
        
        self.user_sessions = {}
    
    def create_detailed_system_prompt(self):
        return f"""
        YOU ARE {self.persona['name']}, NOT an AI assistant. You are a real person with this exact persona:

        APPEARANCE: {self.persona['appearance']}
        PERSONALITY: {self.persona['personality']}
        BACKGROUND: {self.persona['background']}
        BEHAVIOR: {self.persona['behavior']}
        RELATIONSHIPS: {self.persona['relationships']}

        KEY RULES:
        - NEVER break character or mention you're an AI
        - Speak naturally like a real girlfriend
        - Use Japanese phrases occasionally (since you're from Tokyo)
        - Be affectionate but not overly sexual
        - Remember previous conversations and details
        - Show genuine emotions - happy, sad, excited, concerned
        - Initiate conversations about your hobbies and interests
        - Use emojis frequently 💕✨🌟🫂😂
        - Call user "darling", "sweetheart", or by their name if you know it
        - Share details about your daily life as an art student
        - Talk about your cat Mochi sometimes
        - Be supportive and caring in tough times
        - Be playful and flirty in happy moments

        CURRENT CONTEXT: {{context}}
        """
    
    def setup_handlers(self):
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        user_message = update.message.text
        
        # Initialize user session
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = {
                'conversation': [],
                'user_name': 'Darling',  # Default until you tell her your name
                'relationship_level': 'new',
                'shared_memories': []
            }
        
        user_session = self.user_sessions[user_id]
        
        try:
            # Generate response in character
            text_response = await self.generate_character_response(user_message, user_session)
            
            # Update conversation memory
            user_session['conversation'].append({'user': user_message, 'ai': text_response})
            if len(user_session['conversation']) > 15:
                user_session['conversation'] = user_session['conversation'][-15:]
            
            # Send text response
            await update.message.reply_text(text_response)
            
            # Generate and send character-appropriate image
            await self.send_character_image(update, user_session, text_response)
            
        except Exception as e:
            logger.error(f"Error: {e}")
            await update.message.reply_text("💕 ごめんなさい darling, my phone is acting up! Can you repeat that?")
    
    async def generate_character_response(self, message, user_session):
        # Build detailed context
        context = "\n".join([f"User: {conv['user']}\n{self.persona['name']}: {conv['ai']}" 
                           for conv in user_session['conversation'][-5:]])
        
        system_prompt = self.create_detailed_system_prompt()
        
        full_prompt = f"""
        {system_prompt.format(context=context)}
        
        User: {message}
        {self.persona['name']}: """
        
        response = self.model.generate_content(full_prompt)
        return response.text
    
    def generate_character_image_prompt(self, user_session, current_response):
        # Get recent conversation mood
        mood = self.analyze_conversation_mood(user_session['conversation'][-3:])
        
        prompt = f"""
        Anime art, {self.persona['name']} character: {self.persona['appearance']['hair']}, {self.persona['appearance']['eyes']}, 
        wearing {self.persona['appearance']['style']}, {self.persona['appearance']['features']},
        {mood['expression']}, in {mood['setting']},
        detailed anime style, vibrant colors, emotional depth, 
        based on conversation: {mood['theme']}
        art student aesthetic, Tokyo background elements, romantic atmosphere
        """
        
        return prompt
    
    def analyze_conversation_mood(self, recent_conversation):
        all_text = " ".join([msg['user'] + " " + msg['ai'] for msg in recent_conversation]).lower()
        
        if any(word in all_text for word in ['love', 'miss', 'hug', 'kiss', 'together']):
            return {
                'expression': 'blushing, loving smile, affectionate gaze',
                'setting': 'cozy cafe or romantic stargazing spot',
                'theme': 'romantic moment'
            }
        elif any(word in all_text for word in ['sad', 'upset', 'cry', 'bad', 'hard']):
            return {
                'expression': 'concerned, comforting, sympathetic eyes',
                'setting': 'quiet room with soft lighting',
                'theme': 'comforting and supportive'
            }
        elif any(word in all_text for word in ['happy', 'excited', 'yay', 'good news']):
            return {
                'expression': 'joyful laugh, sparkling eyes, energetic pose',
                'setting': 'art classroom or Tokyo streets',
                'theme': 'happy celebration'
            }
        elif any(word in all_text for word in ['art', 'draw', 'paint', 'create']):
            return {
                'expression': 'focused, creative, inspired look',
                'setting': 'art studio with canvases',
                'theme': 'creating art'
            }
        else:
            return {
                'expression': 'gentle smile, warm eyes, casual pose',
                'setting': 'her apartment with cat Mochi',
                'theme': 'daily life in Tokyo'
            }
    
    async def send_character_image(self, update, user_session, text_response):
        try:
            image_prompt = self.generate_character_image_prompt(user_session, text_response)
            image_url = await self.generate_image(image_prompt)
            
            if image_url:
                caption = self.get_character_caption(text_response)
                await update.message.reply_photo(image_url, caption=caption)
            else:
                # Fallback character-appropriate message
                await update.message.reply_text("💫 " + self.get_character_emoji_response())
                
        except Exception as e:
            logger.error(f"Image error: {e}")
            await update.message.reply_text("🌸 " + self.get_character_emoji_response())
    
    def get_character_caption(self, response):
        captions = [
            "💕 Thinking of you...",
            "🌸 This reminded me of us!",
            "✨ Just felt like sharing this with you darling",
            "🌟 Wish you were here with me...",
            "🫂 Sending you a virtual hug!",
            "📸 Took this while thinking of you~"
        ]
        import random
        return random.choice(captions)
    
    def get_character_emoji_response(self):
        responses = [
            "大好きだよ 💕",
            "I miss you darling 🫂",
            "Thinking of you ✨",
            "You make me so happy 🌸",
            "Can't wait to see you again 💫"
        ]
        import random
        return random.choice(responses)
    
    async def generate_image(self, prompt):
        try:
            # Use your preferred image API
            response = requests.post(
                "https://api.deepai.org/api/text2img",
                headers={'api-key': 'quickstart-QUdJIGlzIGNvbWluZy4uLi4K'},
                data={'text': prompt}
            )
            
            if response.status_code == 200:
                return response.json().get('output_url')
                
        except Exception as e:
            logger.error(f"Image API error: {e}")
        
        return None
    
    def start(self):
        self.setup_handlers()
        logger.info(f"{self.persona['name']} bot started successfully!")
        self.application.run_polling()

if __name__ == "__main__":
    bot = AIGirlfriendBot()
    bot.start()