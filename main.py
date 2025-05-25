# GOOGLE_API_KEY = 'AIzaSyDs9FUSWD-I1AV_11WM1mdj8mpmJ-G-jRs' # It's better to use environment variables
# TELEGRAM_TOKEN = '7997409435:AAHE0OpDc5CdBnE8SiTIDtftvE0z_opLSo'

import os
import logging
import asyncio
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Added necessary imports
from PIL import Image # For image processing, though not strictly needed if sending bytes directly
from io import BytesIO # For handling image data in memory
from google.generativeai.types import GenerationConfig # Correct configuration class

# Placeholder for setup_logging (replace with your actual implementation if available)
def setup_logging():
    """Configure basic logging."""
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )

# --- SECURITY WARNING ---
# Hardcoding API keys is a major security risk.
# Load them from environment variables or a secure config file in production.
# Example for environment variables:
# GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
# TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')

# Using placeholder keys from the original code for now.
# REPLACE THESE WITH YOUR ACTUAL KEYS, PREFERABLY LOADED SECURELY.
GOOGLE_API_KEY = 'AIzaSyDs9FUSWD-I1AV_11WM1mdj8mpmJ-G-jRs' # Replace with your key or os.environ.get
TELEGRAM_TOKEN = '951772820:AAH-_6jXhQKE_dmoXS6QZhDytePRshL7L-E' # Replace with your token or os.environ.get
# TELEGRAM_TOKEN = '7997409435:AAGHVYqyfwnelHVuC5cG0UEtcAZJ_Tg9uX8' # Alternative token from comments

if not GOOGLE_API_KEY or GOOGLE_API_KEY == 'YOUR_GOOGLE_API_KEY_HERE': # Added placeholder check
    raise ValueError("GOOGLE_API_KEY not found or is a placeholder. Please set it correctly.")
if not TELEGRAM_TOKEN or TELEGRAM_TOKEN == 'YOUR_TELEGRAM_TOKEN_HERE': # Added placeholder check
    raise ValueError("TELEGRAM_TOKEN not found or is a placeholder. Please set it correctly.")

# Configure the Google Generative AI client with the API key
genai.configure(api_key=GOOGLE_API_KEY)

async def ai_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle the /ai command asynchronously in Telegram group chats.
    Sends the user's input to Google Generative AI and replies with the response.
    """
    logger = logging.getLogger(__name__)
    if not update.message:
        logger.warning("/ai command received without a message object.")
        return
        
    if update.message.chat.type not in ['group', 'supergroup']:
        await update.message.reply_text('این دستور فقط در گروه‌ها کار می‌کند.')
        return

    if not context.args:
        logger.info("User did not provide text for /ai command")
        await update.message.reply_text('لطفاً متنی پس از دستور /ai وارد کنید.')
        return

    query = ' '.join(context.args)

    try:
        # Using a common, recent model. You can change this back to 'gemini-2.5-flash-preview-05-20'
        # if you have specific access or reasons.
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        logger.info(f"Sending query to Gemini for /ai: '{query}' with model '{model.model_name}'")
        response = await model.generate_content_async(query)
        
        # Check for blocking or safety issues
        if hasattr(response, 'prompt_feedback') and response.prompt_feedback.block_reason:
            block_reason_msg = response.prompt_feedback.block_reason_message or str(response.prompt_feedback.block_reason)
            logger.warning(f"AI command prompt blocked. Reason: {block_reason_msg}")
            await update.message.reply_text(f"درخواست شما مسدود شد: {block_reason_msg}")
            return

        if not response.text:
             # This can happen if the response was empty or blocked at candidate level
            finish_reason_msg = ""
            if response.candidates and response.candidates[0].finish_reason:
                finish_reason_msg = f" (علت توقف مدل: {response.candidates[0].finish_reason})"
            logger.warning(f"AI command produced no text. {finish_reason_msg}")
            await update.message.reply_text(f"پاسخی از مدل دریافت نشد.{finish_reason_msg}")
            return
            
        generated_text = response.text
        await update.message.reply_text(generated_text)

    except genai.types.generation_types.BlockedPromptException as e:
        logger.error(f"AI command blocked for prompt '{query}'. Reason: {e}")
        await update.message.reply_text('درخواست شما به دلیل محدودیت‌های محتوا مسدود شد.')
    except Exception as e:
        logger.error(f"Error in /ai command for query '{query}': {str(e)} (Type: {type(e)})")
        await update.message.reply_text('خطا در دریافت اطلاعات. با پشتیبانی در ارتباط باشید: @dr_fake1')


async def img_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle the /img command asynchronously in Telegram group chats.
    Generates an image based on user input using Google Generative AI and sends it to the chat.
    """
    logger = logging.getLogger(__name__)
    if not update.message:
        logger.warning("/img command received without a message object.")
        return

    if update.message.chat.type not in ['group', 'supergroup']:
        await update.message.reply_text('این دستور فقط در گروه‌ها کار می‌کند.')
        return

    if not context.args:
        logger.info("User did not provide text for /img command")
        await update.message.reply_text('لطفاً متنی پس از دستور /img وارد کنید.')
        return

    prompt = ' '.join(context.args)

    try:
        # IMPORTANT: Ensure 'gemini-2.0-flash-preview-image-generation' is a valid and accessible
        # model ID for image generation in your Google Cloud project / API key permissions.
        # If not, this will fail. Example alternatives: 'gemini-1.5-flash-latest' (if image gen enabled)
        # or specific Imagen models (though they might use a different API pattern).
        image_model = genai.GenerativeModel(model_name='gemini-2.0-flash-preview-image-generation')
        
        config = GenerationConfig(
            response_mime_type='image/png'  # Request PNG image output
        )

        logger.info(f"Sending prompt to Gemini for /img: '{prompt}' with model '{image_model.model_name}'")
        
        response = await image_model.generate_content_async(
            contents=prompt,
            generation_config=config
        )

        if hasattr(response, 'prompt_feedback') and response.prompt_feedback.block_reason:
            block_reason_msg = response.prompt_feedback.block_reason_message or str(response.prompt_feedback.block_reason)
            logger.warning(f"Image generation prompt blocked for '{prompt}'. Reason: {block_reason_msg}")
            await update.message.reply_text(f"درخواست تصویر شما مسدود شد: {block_reason_msg}")
            return

        image_sent = False
        text_parts_content = []

        if response.parts:
            for part in response.parts:
                if part.mime_type == 'image/png' and hasattr(part, 'inline_data') and part.inline_data.data:
                    logger.info("Image part found with mime_type 'image/png'.")
                    image_data = part.inline_data.data
                    img_byte_arr = BytesIO(image_data)
                    # img_byte_arr.name = 'generated_image.png' # Good practice for Telegram
                    await update.message.reply_photo(photo=img_byte_arr)
                    image_sent = True
                    break 
                elif hasattr(part, 'text') and part.text:
                    logger.info(f"Text part found in /img response: {part.text}")
                    text_parts_content.append(part.text)
        
        if image_sent:
            return

        if text_parts_content:
            full_text_response = "\n".join(text_parts_content)
            logger.warning(f"No image generated for '{prompt}'. Text response from model: {full_text_response}")
            await update.message.reply_text(f"تصویری تولید نشد. پاسخ مدل:\n{full_text_response}")
            return
        
        if hasattr(response, 'text') and response.text:
            logger.warning(f"No image/parts for '{prompt}'. Fallback response.text: {response.text}")
            await update.message.reply_text(f"تصویری تولید نشد. پاسخ مدل:\n{response.text}")
            return

        finish_reason_msg = ""
        if response.candidates and response.candidates[0].finish_reason:
            finish_reason_msg = f" (علت توقف مدل: {response.candidates[0].finish_reason})"
        
        logger.warning(f"No image or usable text message found in /img response for '{prompt}'.{finish_reason_msg}")
        await update.message.reply_text(f'هیچ تصویر یا متن معناداری تولید نشد.{finish_reason_msg}')

    except genai.types.generation_types.BlockedPromptException as e:
        logger.error(f"Image generation blocked for prompt: '{prompt}'. Reason: {e}")
        await update.message.reply_text('درخواست شما برای تولید تصویر به دلیل محدودیت‌های محتوا مسدود شد.')
    except genai.types.generation_types.StopCandidateException as e:
        logger.error(f"Image generation stopped (e.g. safety filter) for prompt: '{prompt}'. Reason: {e}")
        await update.message.reply_text('تولید تصویر به دلیل مسائل ایمنی یا خط مشی متوقف شد.')
    except Exception as e:
        error_message = str(e)
        logger.error(f"Error in /img command for prompt '{prompt}': {error_message} (Type: {type(e)})")
        if "model" in error_message.lower() and \
           ("not found" in error_message.lower() or \
            "does not support" in error_message.lower() or \
            "permission" in error_message.lower()):
             await update.message.reply_text('خطا: مدل تصویرگری نامعتبر، در دسترس نیست یا مجوز لازم را ندارید. @dr_fake1')
        else:
            await update.message.reply_text('خطا در تولید تصویر. با پشتیبانی در ارتباط باشید: @dr_fake1')


async def main():
    """Initialize and run the Telegram bot asynchronously."""
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting bot...")

    application = Application.builder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler('ai', ai_command))
    application.add_handler(CommandHandler('img', img_command))

    try:
        await application.initialize()
        await application.start()
        # Ensure updater is not None before trying to start polling
        if application.updater:
            await application.updater.start_polling()
            logger.info("Bot started and polling.")
        else:
            logger.error("Updater is None, cannot start polling.")
            return 
            
        await asyncio.Event().wait()  # Keep the bot running until interrupted
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot shutting down due to interrupt...")
    except Exception as e:
        logger.critical(f"Critical error in main loop: {e}", exc_info=True)
    finally:
        logger.info("Stopping bot application...")
        if application.updater and application.updater.running:
            await application.updater.stop()
        if application.running: # type: ignore
            await application.stop()
        # application.shutdown() is part of application.stop() implicitly in recent versions
        # if hasattr(application, 'shutdown') and callable(application.shutdown):
        #    await application.shutdown()
        logger.info("Bot stopped.")

if __name__ == "__main__":
    asyncio.run(main())