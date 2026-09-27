import os
import logging
import asyncio
import httpx
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Config
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
ALLOWED_CHAT_ID = os.environ.get("ALLOWED_TELEGRAM_CHAT_ID")
API_URL = "http://127.0.0.1:8000/chat"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return

    chat_id = str(update.message.chat_id)
    text = update.message.text

    # Authorization Check
    if chat_id != ALLOWED_CHAT_ID:
        logger.warning(f"Ignored message from unauthorized chat ID: {chat_id}. Message: {text}")
        return
    
    logger.info(f"Received authorized message from {chat_id}: {text}")
    
    # Internal HTTP Request to FastAPI backend
    payload = {
        "source": "telegram",
        "external_chat_id": chat_id,
        "message": text
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(API_URL, json=payload, timeout=65.0)
            response.raise_for_status()
            data = response.json()
            reply_text = data.get("reply", "No reply received from backend.")
            
        await update.message.reply_text(reply_text)
        logger.info("Successfully replied to user.")
    except Exception as e:
        logger.error(f"Error communicating with backend: {e}")
        error_msg = "Sorry, Bunny's backend is currently unavailable."
        await update.message.reply_text(error_msg)

def main() -> None:
    if not TOKEN or not ALLOWED_CHAT_ID:
        logger.error("TELEGRAM_BOT_TOKEN and ALLOWED_TELEGRAM_CHAT_ID must be set in environment.")
        return

    application = Application.builder().token(TOKEN).build()
    
    # Listen to all text messages
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("Starting Bunny Telegram bot polling...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
