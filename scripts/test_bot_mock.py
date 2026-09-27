import asyncio
import os
from unittest.mock import AsyncMock, MagicMock

# Set mock env vars BEFORE importing telegram_bot
os.environ["TELEGRAM_BOT_TOKEN"] = "mock_token"
os.environ["ALLOWED_TELEGRAM_CHAT_ID"] = "12345"

from app.telegram_bot import handle_message

async def main():
    print("--- Testing Authorized User ---")
    mock_update = MagicMock()
    mock_update.message.chat_id = 12345
    mock_update.message.text = "Hello Bunny!"
    mock_update.message.reply_text = AsyncMock()
    
    mock_context = MagicMock()
    
    await handle_message(mock_update, mock_context)
    mock_update.message.reply_text.assert_called_once()
    print("Authorized user received a reply!")
    
    print("\n--- Testing Unauthorized User ---")
    mock_update_unauth = MagicMock()
    mock_update_unauth.message.chat_id = 99999
    mock_update_unauth.message.text = "I am a hacker!"
    mock_update_unauth.message.reply_text = AsyncMock()
    
    await handle_message(mock_update_unauth, mock_context)
    mock_update_unauth.message.reply_text.assert_not_called()
    print("Unauthorized user was silently ignored (no reply sent)!")

if __name__ == "__main__":
    asyncio.run(main())
