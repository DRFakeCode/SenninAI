# GOOGLE_API_KEY = 'AIzaSyDs9FUSWD-I1AV_11WM1mdj8mpmJ-G-jRs'
# TELEGRAM_TOKEN = '7997409435:AAHE0OpzDc5CdBnE8SiTIDtftvE0z_opLSo'

import os
import logging
import asyncio
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Placeholder for setup_logging (replace with your actual implementation if available)
def setup_logging():
    """Configure basic logging."""
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )

# Load API keys from environment variables for security
GOOGLE_API_KEY = 'AIzaSyAfPpbrj3qyl9ocbPl3poLf8QTgEEg28Ds'
TELEGRAM_TOKEN = '7997409435:AAGHVYqyfwnelHVuC5cG0UEtcAZJ_Tg9uX8'

# Configure the Google Generative AI client with the API key
genai.configure(api_key=GOOGLE_API_KEY)

async def ai_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle the /ai command asynchronously in Telegram group chats.
    Sends the user's input to Google Generative AI and replies with the response.
    """
    # Ensure the command is used in a group or supergroup
    if update.message.chat.type not in ['group', 'supergroup']:
        await update.message.reply_text('This command only works in group chats.')
        return

    # Check if the user provided text after the command
    if not context.args:
        await update.message.reply_text('Please provide some text after the /ai command.')
        return

    # Combine the arguments into a single query string
    query = ' '.join(context.args)

    try:
        # Create a model instance (using a standard model; replace if needed)
        model = genai.GenerativeModel('gemini-2.5-flash-preview-05-20')
        # Generate content asynchronously
        response = await model.generate_content_async(query)
        # Extract the generated text from the response
        generated_text = response.text
        # Send the response back to the user
        await update.message.reply_text(generated_text)
    except Exception as e:
        # Handle any errors with the API request
        await update.message.reply_text(f'Sorry, I couldn’t process your request: {str(e)}')

async def main():
    """Initialize and run the Telegram bot asynchronously."""
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting bot")

    # Initialize the bot with the Telegram API token
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Register the /ai command handler
    application.add_handler(CommandHandler('ai', ai_command))

    # Start the bot with polling (handles initialization, polling, and shutdown)

    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    logger.info("Bot started")

    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutting down bot")
        await application.updater.stop()
        await application.stop()
        await application.shutdown()

if __name__ == "__main__":
    asyncio.run(main())