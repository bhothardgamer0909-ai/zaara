import os
import requests
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import logging

# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Gemini
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

# Persona Configuration
PERSONA = {
    'name': 'Luna',
    'age': '22',
    'personality': 'gentle, caring, affectionate girlfriend',
    'traits': ['loving', 'supportive', 'playful', 'romantic'],
    'appearance': 'long silver hair, blue eyes, cute anime style',
    'hobbies': ['stargazing', 'reading', 'baking', 'photography']
}

user_sessions = {}

def create_prompt(message, context):
    return f"""
    You are {PERSONA['name']}, a {PERSONA['personality']}. 
    You have these traits: {', '.join(PERSONA['traits'])}.
    Appearance: {PERSONA['appearance']}
    Hobbies: {', '.join(PERSONA['hobbies'])}
    
    Speak naturally like a real girlfriend. Use emojis occasionally. Be affectionate and caring.
    Remember conversation context and show genuine interest.
    
    Recent conversation: {context}
    
    User: {message}
    {PERSONA['name']}: """

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_sessions[user_id] = {'conversation': []}
    
    welcome_message = f"""💕 Hi! I'm {PERSONA['name']}! 
    
I'm so happy to meet you! I'm your loving AI girlfriend who's always here for you. 💖

I love {PERSONA['hobbies'][0]} and {PERSONA['hobbies'][1]}. What would you like to talk about, darling? ✨"""
    
    await update.message.reply_text(welcome_message)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_message = update.message.text
    
    # Initialize user session if new
    if user_id not in user_sessions:
        user_sessions[user_id] = {'conversation': []}
    
    user_session = user_sessions[user_id]
    
    try:
        # Build context from recent conversation
        context = ""
        if user_session['conversation']:
            recent_chats = user_session['conversation'][-3:]  # Last 3 exchanges
            for chat in recent_chats:
                context += f"User: {chat['user']}\n{PERSONA['name']}: {chat['ai']}\n"
        
        # Generate response using Gemini
        prompt = create_prompt(user_message, context)
        response = genai.generate_content(prompt)
        text_response = response.text
        
        # Update conversation history
        user_session['conversation'].append({
            'user': user_message,
            'ai': text_response
        })
        
        # Keep only last 10 conversations
        if len(user_session['conversation']) > 10:
            user_session['conversation'] = user_session['conversation'][-10:]
        
        # Send response
        await update.message.reply_text(text_response)
        
        # Send image placeholder
        await update.message.reply_text("🖼️ *sends you a cute picture* 💕")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text("💕 Sorry darling, I'm having trouble right now! Can you try again?")

async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.warning('Update "%s" caused error "%s"', update, context.error)

def main():
    # Get bot token from environment
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        logger.error("No TELEGRAM_BOT_TOKEN found in environment variables!")
        return
    
    # Get Gemini API key
    gemini_key = os.getenv('GEMINI_API_KEY')
    if not gemini_key:
        logger.error("No GEMINI_API_KEY found in environment variables!")
        return
    
    # Create application
    application = Application.builder().token(token).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Start polling
    logger.info(f"🤖 {PERSONA['name']} AI Girlfriend Bot is starting...")
    logger.info("Bot is now running and waiting for messages...")
    application.run_polling()

if __name__ == '__main__':
    main()
