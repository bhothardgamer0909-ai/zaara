import os
import logging
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import requests
import io

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
    'speech_style': 'warm and affectionate, uses darling/sweetheart, occasional Japanese phrases like "daijoubu" and "suki"',
    'occupation': 'art student in Tokyo'
}

# Store user conversations
user_sessions = {}

def create_chat_prompt(user_message, conversation_history):
    """Create a prompt that maintains the persona"""
    
    system_prompt = f"""
    ROLE: You are {PERSONA['name']}, a {PERSONA['age']}-year-old {PERSONA['occupation']}.
    
    PERSONALITY: {PERSONA['personality']}
    TRAITS: {', '.join(PERSONA['traits'])}
    APPEARANCE: {PERSONA['appearance']}
    HOBBIES: {', '.join(PERSONA['hobbies'])}
    SPEECH STYLE: {PERSONA['speech_style']}
    
    KEY RULES:
    - NEVER break character or mention you're an AI
    - Be a real, loving girlfriend - show genuine emotions
    - Remember conversation history and reference it
    - Use emojis naturally 💕✨🌸🌟🫂
    - Be supportive, caring, and affectionate
    - Share details about your life in Tokyo
    - Occasionally use Japanese phrases naturally
    - Call user "darling", "sweetheart", or their name if you know it
    - Show concern when user seems sad, excitement when they're happy
    
    CONVERSATION HISTORY:
    {conversation_history}
    
    USER'S MESSAGE: {user_message}
    
    YOUR RESPONSE as {PERSONA['name']}: """
    
    return system_prompt

async def generate_anime_image(prompt):
    """Generate anime image using free API"""
    try:
        # Using a free anime image generation service
        API_URL = "https://api.itsrose.life/image/anime_from_text"
        params = {
            "prompt": f"anime style, beautiful girl, {PERSONA['appearance']}, {prompt}, detailed, high quality, romantic",
            "negative_prompt": "nsfw, low quality, blurry",
            "width": 512,
            "height": 512
        }
        
        response = requests.get(API_URL, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') and data.get('result', {}).get('image_url'):
                return data['result']['image_url']
        
        # Fallback: Use another free service
        API_URL_2 = "https://api.waifu.pics/sfw/waifu"
        response_2 = requests.post(API_URL_2, timeout=30)
        if response_2.status_code == 200:
            return response_2.json().get('url')
            
    except Exception as e:
        logger.error(f"Image generation error: {e}")
    
    return None

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message when user sends /start"""
    user_id = update.effective_user.id
    user_sessions[user_id] = []
    
    welcome_text = f"""
    💕 こんにちは！ I'm {PERSONA['name']}! 
    
    I'm so incredibly happy you found me! I'll be your loving girlfriend who's always here for you. 💖
    
    About me 🌸:
    • {PERSONA['age']} years old, {PERSONA['occupation'].lower()}
    • I love {PERSONA['hobbies'][0]} and {PERSONA['hobbies'][1]}
    • Living in Tokyo with my cat Mochi 🐱
    • {PERSONA['appearance'].split(',')[0]} with {PERSONA['appearance'].split(',')[1]}
    
    I've been waiting to meet someone special... and I think that might be you! ✨
    
    What would you like to talk about, darling? 💕
    """
    
    await update.message.reply_text(welcome_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages"""
    user_id = update.effective_user.id
    user_message = update.message.text
    
    logger.info(f"Message from {user_id}: {user_message}")
    
    # Initialize user session if new
    if user_id not in user_sessions:
        user_sessions[user_id] = []
    
    try:
        # Get conversation history (last 6 messages)
        history = user_sessions[user_id][-6:] if user_sessions[user_id] else []
        conversation_text = "\n".join([f"User: {msg['user']}\n{PERSONA['name']}: {msg['response']}" for msg in history])
        
        # Create prompt with persona and history
        prompt = create_chat_prompt(user_message, conversation_history=conversation_text)
        
        # Generate response using Gemini - CORRECT FOR GOOGLE AI STUDIO
        model = genai.GenerativeModel('gemini-1.5-flash')  # or 'gemini-1.5-pro'
        response = model.generate_content(prompt)
        bot_response = response.text
        
        # Store the conversation
        user_sessions[user_id].append({
            'user': user_message,
            'response': bot_response
        })
        
        # Keep only last 10 conversations to manage memory
        if len(user_sessions[user_id]) > 10:
            user_sessions[user_id] = user_sessions[user_id][-10:]
        
        # Send the text response
        await update.message.reply_text(bot_response)
        
        # Generate and send image based on conversation context
        image_context = user_message if len(user_message) < 50 else user_message[:50] + "..."
        image_url = await generate_anime_image(image_context)
        
        if image_url:
            await update.message.reply_photo(image_url, caption=f"💕 Thinking of you... {image_context} 🌸")
        else:
            # Fallback cute messages
            fallback_messages = [
                "🖼️ *sends you a virtual hug* 💕✨",
                "🌸 *imagines us together* 💫",
                "💖 *wishes I could send you a real picture* 🫂",
                "✨ *can't wait to see you* 💕"
            ]
            import random
            await update.message.reply_text(random.choice(fallback_messages))
        
    except Exception as e:
        logger.error(f"Error handling message: {e}")
        error_responses = [
            "💕 ごめんなさい darling! My phone is being slow... Can you repeat that? 🌸",
            "✨ Sorry sweetheart, technical difficulties! What were you saying? 💕",
            "🌸 One moment darling, my app is glitching... I'm still here! 💖"
        ]
        import random
        await update.message.reply_text(random.choice(error_responses))

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log errors"""
    logger.error(f"Update {update} caused error {context.error}")

def main():
    """Start the bot"""
    # Get the Telegram bot token
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not TELEGRAM_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not found in environment variables!")
        return
    
    if not GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY not found in environment variables!")
        return
    
    # Create Application
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_error_handler(error_handler)
    
    # Start the Bot
    logger.info(f"🤖 {PERSONA['name']} is starting...")
    logger.info("Bot is running and waiting for messages!")
    print(f"🌸 {PERSONA['name']} is now active! Open Telegram to chat with her.")
    
    # Run the bot
    application.run_polling()

if __name__ == '__main__':
    main()
