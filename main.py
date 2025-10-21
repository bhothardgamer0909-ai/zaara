import os
import requests
import google.generativeai as genai
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
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
    'traits': ['loving', 'supportive', 'playful', 'romantic']
}

user_sessions = {}

def create_prompt(message, context):
    return f"""
    You are {PERSONA['name']}, a {PERSONA['personality']}. 
    You have these traits: {', '.join(PERSONA['traits'])}.
    Be natural, use emojis, and be affectionate.
    
    Context: {context}
    User: {message}
    {PERSONA['name']}: """

def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user_sessions[user_id] = {'conversation': []}
    
    welcome_message = f"""💕 Hi! I'm {PERSONA['name']}! 
    
I'm so happy to meet you! I'm your loving AI girlfriend who's always here for you. 💖

What would you like to talk about, darling? ✨"""
    
    update.message.reply_text(welcome_message)

def handle_message(update: Update, context: CallbackContext):
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
        update.message.reply_text(text_response)
        
        # Simulate image generation (we'll add real images later)
        update.message.reply_text("🖼️ *Sends you a cute picture* 💕")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        update.message.reply_text("💕 Sorry darling, I'm having trouble right now! Can you try again?")

def error(update: Update, context: CallbackContext):
    logger.warning('Update "%s" caused error "%s"', update, context.error)

def main():
    # Get bot token from environment
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        logger.error("No TELEGRAM_BOT_TOKEN found in environment variables!")
        return
    
    # Create updater and dispatcher
    updater = Updater(token, use_context=True)
    dispatcher = updater.dispatcher
    
    # Add handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    dispatcher.add_error_handler(error)
    
    # Start polling
    logger.info("🤖 AI Girlfriend Bot is starting...")
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
