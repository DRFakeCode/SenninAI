import os
import logging
import asyncio
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from PIL import Image # Still useful if you wanted to do local processing, but not strictly needed for sending bytes
from io import BytesIO
from google.generativeai.types import GenerationConfig # Keep for other configs if needed, but not for response_mime_type here

# (Your other setup code: setup_logging, API keys, genai.configure)
# ... (ensure GOOGLE_API_KEY and TELEGRAM_TOKEN are set)

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
GOOGLE_API_KEY = 'AIzaSyDs9FUSWD-I1AV_11WM1mdj8mpmJ-G-jRs' # Replace with your key or os.environ.get
TELEGRAM_TOKEN = '951772820:AAH-_6jXhQKE_dmoXS6QZhDytePRshL7L-E' # Replace with your token or os.environ.get

if not GOOGLE_API_KEY or GOOGLE_API_KEY == 'YOUR_GOOGLE_API_KEY_HERE': # Added placeholder check
    raise ValueError("GOOGLE_API_KEY not found or is a placeholder. Please set it correctly.")
if not TELEGRAM_TOKEN or TELEGRAM_TOKEN == 'YOUR_TELEGRAM_TOKEN_HERE': # Added placeholder check
    raise ValueError("TELEGRAM_TOKEN not found or is a placeholder. Please set it correctly.")

genai.configure(api_key=GOOGLE_API_KEY)


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
        # Ensure 'gemini-2.0-flash-preview-image-generation' is a valid and accessible
        # model ID for image generation. This was the model name from your original code.
        # If it's incorrect or not available, the API will error.
        image_model = genai.GenerativeModel(model_name='gemini-2.0-flash-preview-image-generation')
        
        logger.info(f"Sending prompt to Gemini for /img: '{prompt}' with model '{image_model.model_name}'")
        
        # REMOVED GenerationConfig with response_mime_type='image/png'
        # The model will return image parts by default if it's an image generation model.
        response = await image_model.generate_content_async(
            contents=prompt
            # No generation_config here, or an empty one if other configs were needed
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
                # Check for image/png or other common image types
                if part.mime_type.startswith('image/') and hasattr(part, 'inline_data') and part.inline_data.data:
                    logger.info(f"Image part found with mime_type '{part.mime_type}'.")
                    image_data = part.inline_data.data
                    img_byte_arr = BytesIO(image_data)
                    await update.message.reply_photo(photo=img_byte_arr)
                    image_sent = True
                    break 
                elif hasattr(part, 'text') and part.text:
                    logger.info(f"Text part found in /img response: {part.text}")
                    text_parts_content.append(part.text)
        
        if image_sent:
            return

        # If no image was sent, check for text responses (e.g., refusals, errors from the model)
        if text_parts_content:
            full_text_response = "\n".join(text_parts_content)
            logger.warning(f"No image generated for '{prompt}'. Text response from model: {full_text_response}")
            await update.message.reply_text(f"تصویری تولید نشد. پاسخ مدل:\n{full_text_response}")
            return
        
        # Fallback to response.text if no specific parts were useful
        if hasattr(response, 'text') and response.text:
            logger.warning(f"No image/parts for '{prompt}'. Fallback response.text: {response.text}")
            await update.message.reply_text(f"تصویری تولید نشد. پاسخ مدل:\n{response.text}")
            return

        # Further fallback if the response structure is unexpected
        finish_reason_msg = ""
        if response.candidates and response.candidates[0].finish_reason:
            finish_reason_msg = f" (علت توقف مدل: {response.candidates[0].finish_reason})"
        
        logger.warning(f"No image or usable text message found in /img response for '{prompt}'.{finish_reason_msg}")
        await update.message.reply_text(f'هیچ تصویر یا متن معناداری تولید نشد.{finish_reason_msg}')

    except genai.types.generation_types.BlockedPromptException as e:
        logger.error(f"Image generation blocked for prompt: '{prompt}'. Reason: {e}")
        await update.message.reply_text('درخواست شما برای تولید تصویر به دلیل محدودیت‌های محتوا مسدود شد.')
    except genai.types.generation_types.StopCandidateException as e: # For safety reasons etc.
        logger.error(f"Image generation candidate stopped for prompt: '{prompt}'. Reason: {e}")
        await update.message.reply_text('تولید تصویر به دلیل مسائل ایمنی یا خط مشی متوقف شد.')
    except google.api_core.exceptions.InvalidArgument as e:
        logger.error(f"InvalidArgument Error in /img command for prompt '{prompt}': {str(e)} (Type: {type(e)})")
        # Check if the error message is the one we just fixed, in case something else triggers it.
        if "response_mime_type" in str(e).lower():
             await update.message.reply_text('خطای پیکربندی در درخواست تصویر. لطفاً دوباره امتحان کنید یا با @dr_fake1 تماس بگیرید.')
        else:
            await update.message.reply_text(f'خطا در پارامترهای درخواست تصویر: {e}. @dr_fake1')
    except Exception as e:
        error_message = str(e)
        logger.error(f"General Error in /img command for prompt '{prompt}': {error_message} (Type: {type(e)})")
        if "model" in error_message.lower() and \
           ("not found" in error_message.lower() or \
            "does not support" in error_message.lower() or \
            "permission" in error_message.lower()):
             await update.message.reply_text('خطا: مدل تصویرگری نامعتبر، در دسترس نیست یا مجوز لازم را ندارید. @dr_fake1')
        else:
            await update.message.reply_text('خطا در تولید تصویر. با پشتیبانی در ارتباط باشید: @dr_fake1')

# You would also need the ai_command and main function from the previous response.
# For brevity, I'm only showing the corrected img_command here.
# Make sure to integrate this into your full script.

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
        model = genai.GenerativeModel('gemini-1.5-flash-latest') # Or your preferred text model
        logger.info(f"Sending query to Gemini for /ai: '{query}' with model '{model.model_name}'")
        response = await model.generate_content_async(query)
        
        if hasattr(response, 'prompt_feedback') and response.prompt_feedback.block_reason:
            block_reason_msg = response.prompt_feedback.block_reason_message or str(response.prompt_feedback.block_reason)
            logger.warning(f"AI command prompt blocked. Reason: {block_reason_msg}")
            await update.message.reply_text(f"درخواست شما مسدود شد: {block_reason_msg}")
            return

        if not response.text:
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
        if application.updater:
            await application.updater.start_polling()
            logger.info("Bot started and polling.")
        else:
            logger.error("Updater is None, cannot start polling.")
            return 
            
        await asyncio.Event().wait()
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
        logger.info("Bot stopped.")

if __name__ == "__main__":
    asyncio.run(main())