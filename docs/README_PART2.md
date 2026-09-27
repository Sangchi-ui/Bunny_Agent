# Bunny - Part 2 (LM Studio Integration)

This part replaces the placeholder replies with a real connection to an OpenAI-compatible local API server (LM Studio).

## Prerequisites
1. **LM Studio must be running**.
2. A model must be loaded in LM Studio.
3. The **Local Server** in LM Studio must be started (running on port `1234`).

## Verifying LM Studio is Up
Before running the Bunny backend, verify that LM Studio's server is responding. You can do this by opening your browser and visiting:
[http://localhost:1234/v1/models](http://localhost:1234/v1/models)

Or by running this curl command in your terminal:
```cmd
curl http://localhost:1234/v1/models
```
If you get a JSON response with model details, the server is ready.

## Security & Network Scope
- This backend **only ever talks to `localhost`**. 
- It makes **no external network calls**.
- Nothing is exposed beyond `127.0.0.1`.
