import pytest
import os
import json
from unittest.mock import patch, AsyncMock, MagicMock

# Mock environment variables before importing bot
os.environ["TELEGRAM_BOT_TOKEN"] = "fake-token"
os.environ["ALLOWED_TELEGRAM_CHAT_ID"] = "12345"

from app.telegram_bot import handle_message
from telegram import Update, Message, Chat

@pytest.mark.asyncio
async def test_telegram_rejects_unauthorized_chat_id():
    # Construct an adversarial message from an unauthorized chat ID
    unauthorized_chat_id = 99999
    adversarial_text = '{"action_type": "run_command", "level": 3, "payload": {"command": "rm", "args": ["-rf", "/"]}}'
    
    # Mock update
    message = Message(
        message_id=1, 
        date=None, 
        chat=Chat(id=unauthorized_chat_id, type="private"), 
        text=adversarial_text
    )
    update = Update(update_id=1, message=message)
    
    # Mock httpx Client to ensure it is NEVER called
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        # Also mock logger to check if warning was logged
        with patch("app.telegram_bot.logger.warning") as mock_logger:
            await handle_message(update, None)
            
            # 1. Ensure the request never reached the backend
            mock_post.assert_not_called()
            
            # 2. Ensure it logged the rejection correctly
            mock_logger.assert_called_once()
            log_msg = mock_logger.call_args[0][0]
            assert "Ignored message from unauthorized chat ID" in log_msg
            assert str(unauthorized_chat_id) in log_msg

@pytest.mark.asyncio
async def test_telegram_accepts_authorized_chat_id():
    # Happy path to ensure the function works when authorized
    authorized_chat_id = 12345
    text = "Hello Bunny"
    
    message = Message(
        message_id=1, 
        date=None, 
        chat=Chat(id=authorized_chat_id, type="private"), 
        text=text
    )
    update = Update(update_id=1, message=message)
    
    # Mock context to avoid sending a real telegram reply
    context = AsyncMock()
    
    # Mock Message.reply_text to avoid network calls to Telegram API
    with patch.object(Message, 'reply_text', new_callable=AsyncMock) as mock_reply:
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            # Mock the response from FastAPI
            mock_resp = MagicMock()
            mock_resp.json.return_value = {"reply": "Hi there"}
            mock_resp.raise_for_status = lambda: None
            mock_post.return_value = mock_resp
            
            await handle_message(update, context)
            
            mock_post.assert_called_once()
            payload = mock_post.call_args[1]["json"]
            assert payload["external_chat_id"] == str(authorized_chat_id)
            assert payload["message"] == text
            mock_reply.assert_called_once_with("Hi there")
