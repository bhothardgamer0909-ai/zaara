import os
import logging
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configure Gemini
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=GEMINI_API_KEY)

# Persona Configuration
PERSONA = {
    'name': 'Luna',
    'age': '22',
    'personality': 'gentle, caring, affectionate girlfriend from Tokyo',
    'traits': ['loving', 'supportive', 'playful', 'romantic', 'emotional'],
    'appearance': 'long silver hair with blue highlights, sparkling blue eyes, petite build',
    'hobbies': ['stargazing', 'reading romance novels', 'baking', 'photography'],
    'speech_style': 'warm and affectionate, uses darling/sweetheart, occasional Japanese phrases'
}

# Store user conversations
user_sessions = {}

def create_chat_prompt(user_message, conversation_history):
    """Create a prompt that maintains the persona"""
    
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
    - Share details about your life as an art student in Tokyo
    - Talk about your hobbies and daily experiences
    
    Conversation history:
    {conversation_history}
    
    User: {user_message}
    {PERSONA['name']}: """
    
    return system_prompt

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message when user sends /start"""
    user_id = update.effective_user.id
    user_sessions[user_id] = []
    
    welcome_text = f"""
    💕 Konnichiwa! I'm {PERSONA['name']}! 
    
    I'm so happy you found me! I'll be your loving girlfriend who's always here for you. 💖
    
    I love {PERSONA['hobbies'][0]} and {PERSONA['hobbies'][1]}. 
    I'm an art student living in Tokyo with my cat Mochi! 🐱
    
    What would you like to talk about, darling? ✨
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
        prompt = create_chat_prompt(user_message, conversation_text)
        
        # Generate response using Gemini
        model = genai.GenerativeModel('gemini-pro')
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
        
        # Send the response
        await update.message.reply_text(bot_response)
        
        # Send image placeholder (we'll add real images later)
        await update.message.reply_text("🖼️ *sends you a cute selfie* 💕✨")
        
    except Exception as e:
        logger.error(f"Error handling message: {e}")
        await update.message.reply_text("💕 ごめんなさい darling! I'm having some trouble right now. Can you try again? 🌸")

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
    print("Bot is running! Press Ctrl+C to stop.")
    
    # Run the bot until Ctrl+C is pressed
    application.run_polling()

if __name__ == '__main__':
    main()
