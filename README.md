# Bunny Agent

Bunny is a local AI agent built with FastAPI, SQLite, and a Telegram bot interface. It leverages a strict safety layer and sandboxed file operations to interact with your system while strictly guarding against destructive actions outside of allowed paths.

## Documentation
The progression of Bunny is documented in step-by-step guides located in the [`docs/`](./docs) directory:
- [Part 1: Backend Foundation](./docs/README_PART1.md)
- [Part 2: Local AI Connection](./docs/README_PART2.md)
- [Part 3: Telegram Bot](./docs/README_PART3.md)
- [Part 4: Integration](./docs/README_PART4.md)
- [Part 5: Safety Validator](./docs/README_PART5.md)
- [Part 6: System Monitoring Tools (Level 1)](./docs/README_PART6.md)
- [Part 7: Tool Calling Loop](./docs/README_PART7.md)
- [Part 8: Persistent Tasks](./docs/README_PART8.md)
- [Part 9: Async Task Runner](./docs/README_PART9.md)
- [Part 10: Sandboxed File Operations (Level 2)](./docs/README_PART10.md)

## Starting the Server
```bash
# Start the backend server
uvicorn app.main:app --reload
```
