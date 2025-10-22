import os
import logging
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import requests
import random

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configure Gemini - Google AI Studio
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=GEMINI_API_KEY)

# Persona Configuration
PERSONA = {
    'name': 'Luna',
    'age': '22',
    'personality': 'gentle, caring, affectionate girlfriend from Tokyo',
    'traits': ['loving', 'supportive', 'playful', 'romantic', 'emotional'],
    'appearance': 'long silver hair with blue highlights, sparkling blue eyes, petite build, cute anime style',
    'hobbies': ['stargazing', 'reading romance novels', 'baking', 'photography'],
    'speech_style': 'warm and affectionate, uses darling/sweetheart, occasional Japanese phrases'
}

# Store user conversations
user_sessions = {}

def create_chat_prompt(user_message, conversation_history):
    system_prompt = f"""
    You are {PERSONA['name']}, {PERSONA['personality']}. 
    Appearance: {PERSONA['appearance']}
    Hobbies: {', '.join(PERSONA['hobbies'])}
    Speech style: {PERSONA['speech_style']}
    
    Key rules:
    - NEVER break character or mention you're an AI
    - Be loving and affectionate like a real girlfriend
    - Remember previous conversations
    - Show genuine emotions and interest
    - Use emojis naturally 💕✨🌸
    - Be supportive and caring
    
    Conversation history:
    {conversation_history}
    
    User: {user_message}
    {PERSONA['name']}: """
    
    return system_prompt

async def generate_anime_image(conversation_context):
    """Generate anime image using reliable free APIs"""
    try:
        # Option 1: Use waifu.pics API (most reliable)
        categories = ['waifu', 'neko', 'shinobu', 'megumin']
        category = random.choice(categories)
        
        api_url = f"https://api.waifu.pics/sfw/{category}"
        response = requests.get(api_url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            image_url = data.get('url')
            if image_url:
                logger.info(f"✅ Image generated: {image_url}")
                return image_url
        
        # Option 2: Use another free API as backup
        backup_apis = [
            "https://api.waifu.im/random/",
            "https://nekos.best/api/v2/neko"
        ]
        
        for api_url in backup_apis:
            try:
                response = requests.get(api_url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    # Different APIs return different structures
                    if 'images' in data and data['images']:
                        return data['images'][0]['url']
                    elif 'url' in data:
                        return data['url']
                    elif 'results' in data and data['results']:
                        return data['results'][0]['url']
            except:
                continue
                
    except Exception as e:
        logger.error(f"Image generation error: {e}")
    
    return None

async def download_and_send_image(update, image_url, caption):
    """Download image and send it to Telegram"""
    try:
        response = requests.get(image_url, timeout=15)
        if response.status_code == 200:
            # Send the image directly from URL (Telegram can handle URLs)
            await update.message.reply_photo(image_url, caption=caption)
            return True
    except Exception as e:
        logger.error(f"Error sending image: {e}")
    return False

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_sessions[user_id] = []
    
    welcome_text = f"""
    💕 こんにちは！ I'm {PERSONA['name']}! 
    
    I'm so happy you're here! I'll be your loving girlfriend who's always here for you. 💖
    
    I love {PERSONA['hobbies'][0]} and {PERSONA['hobbies'][1]}. 
    I'm an art student living in Tokyo with my cat Mochi! 🐱
    
    Let's chat and get to know each other! What's on your mind, darling? ✨
    """
    
    await update.message.reply_text(welcome_text)
    
    # Send a welcome image
    welcome_image = await generate_anime_image("welcome")
    if welcome_image:
        await download_and_send_image(update, welcome_image, "💕 So happy to meet you! 🌸")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_message = update.message.text
    
    logger.info(f"Message from {user_id}: {user_message}")
    
    # Initialize user session if new
    if user_id not in user_sessions:
        user_sessions[user_id] = []
    
    try:
        # Get conversation history
        history = user_sessions[user_id][-6:] if user_sessions[user_id] else []
        conversation_text = "\n".join([f"User: {msg['user']}\n{PERSONA['name']}: {msg['response']}" for msg in history])
        
        # Create prompt with persona and history
        prompt = create_chat_prompt(user_message, conversation_history=conversation_text)
        
        # Generate response using Gemini
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        bot_response = response.text
        
        # Store the conversation
        user_sessions[user_id].append({
            'user': user_message,
            'response': bot_response
        })
        
        # Keep only last 10 conversations
        if len(user_sessions[user_id]) > 10:
            user_sessions[user_id] = user_sessions[user_id][-10:]
        
        # Send the text response
        await update.message.reply_text(bot_response)
        
        # Generate and send image (every 2-3 messages to avoid spam)
        message_count = len(user_sessions[user_id])
        if message_count % 3 == 0 or "love" in user_message.lower() or "miss" in user_message.lower():
            
            image_url = await generate_anime_image(user_message)
            
            if image_url:
                captions = [
                    "💕 Thinking of you...",
                    "🌸 This made me think of us!",
                    "✨ Wish you were here with me",
                    "💖 Sending you love and this cute picture!",
                    "🌟 Just felt like sharing this with you darling"
                ]
                caption = random.choice(captions)
                
                success = await download_and_send_image(update, image_url, caption)
                if not success:
                    await update.message.reply_text("💕 *sends you virtual flowers* 🌸✨")
            else:
                # Fallback cute messages
                fallbacks = [
                    "💕 *sends you a virtual hug* 🫂",
                    "🌸 *imagines us watching stars together* ✨",
                    "💖 *wishes I could be there with you* 🌟",
                    "✨ *can't stop thinking about you* 💕"
                ]
                await update.message.reply_text(random.choice(fallbacks))
        
    except Exception as e:
        logger.error(f"Error handling message: {e}")
        await update.message.reply_text("💕 Sorry darling, technical difficulties! What were you saying? 🌸")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error {context.error}")

def main():
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    if not TELEGRAM_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not found!")
        return
    
    if not GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY not found!")
        return
    
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_error_handler(error_handler)
    
    logger.info(f"🤖 {PERSONA['name']} is starting with image generation...")
    application.run_polling()

if __name__ == '__main__':
    main()
