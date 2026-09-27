# Bunny - Part 7 (LLM Tool Calling Loop)

This part connects the model to the tools we built in Part 6, allowing Bunny to make autonomous decisions about when and how to read system state!

## The Two-Step Flow
When you send a message like *"What's my RAM usage?"*, the process now works like this:
1. **Model Proposes Tool**: The LLM recognizes it needs real-time data and returns a structured `tool_calls` payload instead of a text reply.
2. **Validation & Execution**: The `chat` endpoint captures this, safely routes it through `dispatcher.execute_tool()` (which internally runs the strict `safety.validate_action()` rules), and retrieves the raw JSON data (e.g., `{"percent": 98.1}`).
3. **Data Feedback**: The backend automatically fires a *second* request to the LLM, appending the raw tool output to the conversation history as a "tool" message.
4. **Natural Language Reply**: The model sees the real-time data and responds naturally to you: *"Your RAM usage is currently at 98.1%."*

Crucially, **the model NEVER executes anything directly**. Its `tool_calls` output is treated purely as an untrusted proposal, and the Python dispatcher handles the actual execution.

## Testing Tool Calling
You can test this end-to-end by sending a Telegram message to your bot, or by using the `/chat` endpoint manually:
- Ask: *"What is my current RAM usage?"*
- Ask: *"Which 5 processes are using the most memory?"*

If the model tries to use a tool that is not in the ALLOWLIST (or tries to hallucinate one), the safety gate will reject it, and the rejection reason is fed back to the model. The model will then truthfully reply that it isn't allowed to do that!

### Note on Model Capabilities
*Tool calling (Function calling) relies heavily on the capabilities of the specific model loaded in LM Studio. While testing with Qwen or Llama-3-instruct variants, they generally format tool calls well natively. If you find the model starts outputting raw JSON code blocks instead of triggering actual tool requests, you may need to add a system prompt enforcing strict function calling adherence, or switch to a model specifically fine-tuned for tool calling.*
