# Bunny - Part 4 (Integration & Verification)

This section ensures the end-to-end integration across FastAPI, LM Studio, and Telegram is robust and working smoothly.

## Full Run Order
To bring Bunny completely online, you need to start these three services in order:
1. **LM Studio**: Open the app, load your desired model, and start the **Local Server** on port `1234`.
2. **FastAPI Backend**: Open a terminal in the `bunny/` folder, activate the virtual environment (`venv\Scripts\activate`), and run:
   ```cmd
   uvicorn app.main:app --host 127.0.0.1 --port 8000
   ```
3. **Telegram Bot**: Open a *second* terminal in the `bunny/` folder, activate the virtual environment, and run:
   ```cmd
   python -m app.telegram_bot
   ```

## What "Fully Working" Looks Like
- You send a message from your phone in Telegram.
- The `telegram_bot.py` securely verifies your Chat ID and forwards it to `http://127.0.0.1:8000/chat`.
- `main.py` saves the message to `bunny.db` and requests a completion from `llm_client.py`.
- `llm_client.py` retrieves a response from your local LM Studio model.
- The reply is saved to the database, passed back up the chain, and instantly appears on your phone in Telegram!

*(You can verify the conversation logs by navigating to `http://127.0.0.1:8000/docs` and using the `/conversations/{id}/history` endpoint.)*

## Troubleshooting Guide

| Symptom | Likely Cause | Fix |
|---|---|---|
| **Telegram bot returns: "Sorry, Bunny's backend is currently unavailable."** | LM Studio isn't running, or model isn't loaded. | Open LM Studio and start the Local Server on port `1234`. |
| **Telegram bot ignores you completely** | Chat ID mismatch in `.env`. | Message `@RawDataBot` on Telegram to get your true Chat ID, then update the `.env` file and restart the bot. |
| **Uvicorn throws `[WinError 10013]`** | Port 8000 is already in use by another instance. | Close any other terminals running the backend or kill python processes running on port 8000. |
| **Bot replies with empty messages** | Model in LM Studio crashed or isn't generating text. | Eject the model in LM Studio and reload it, or try a smaller model. |

## Manual Error Testing
To test that error handling cascades cleanly without crashing the bot:
1. Ensure the Telegram bot and FastAPI backend are running.
2. **Stop the local server** in LM Studio (or close LM Studio entirely).
3. Send a message to your Telegram bot.
4. You should smoothly receive the friendly error: *"Sorry, Bunny's backend is currently unavailable."* (or *"Bunny's local AI engine isn't responding right now."*), proving the fallback chain works!
