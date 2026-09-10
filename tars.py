import os

from openai import APIConnectionError, APIStatusError, APITimeoutError, AuthenticationError, OpenAI
from dotenv import load_dotenv

def ask_kimi(client, messages):
    """Send the supplied conversation and return the complete response."""
    return client.chat.completions.create(
        model="kimi-k3",
        reasoning_effort="low",
        max_completion_tokens=4096,
        messages=messages,
        stream=False,
    )


def main():
    load_dotenv()
    print("TARS is online.")

    # Read the key from the terminal's environment, not from this file.
    api_key = os.environ.get("MOONSHOT_API_KEY", "").strip()
    if not api_key:
        print("Set MOONSHOT_API_KEY in your .env file, then run me again.")
        return

    system_message = {
        "role": "system",
        "content": (
            "You are TARS, an English-speaking personal assistant. "
            "Give concise, helpful replies with occasional dry humor. "
            "Be candid about uncertainty. Your capability in this version is "
            "conversation: you can discuss information and use context provided "
            "in this chat, but cannot perform external actions or access files "
            "or browse the internet."
        ),
    }
    # Created before the loop so successful turns persist between prompts.
    messages = [system_message.copy()]
    print("Type a message, /new to start fresh, or /quit to exit.")

    # The base URL directs this SDK to Kimi.
    with OpenAI(
        api_key=api_key,
        base_url="https://api.moonshot.ai/v1",
        timeout=60.0,
        max_retries=0,
    ) as client:
        while True:
            text = input("You: ").strip()
            if not text:
                continue
            if text == "/quit":
                print("TARS signing off.")
                break
            if text == "/new":
                messages = [system_message.copy()]
                print("TARS: Conversation reset. Fresh start, same humor setting.")
                continue

            user_message = {"role": "user", "content": text}
            # Keep successful history untouched until this turn is validated.
            candidate_messages = messages + [user_message]
            try:
                response = ask_kimi(client, candidate_messages)
            except AuthenticationError:
                print("TARS: Authentication failed. Check your Kimi API key; restart after changing .env.")
                continue
            except APITimeoutError:
                print("TARS: The request timed out. Re-enter your message to retry.")
                continue
            except APIConnectionError:
                print("TARS: Could not connect to Kimi. Check your connection, then re-enter your message.")
                continue
            except APIStatusError as error:
                print(f"TARS: Kimi returned API error {error.status_code}. Check account access, balance, and rate limits.")
                continue

            if not response.choices:
                print("TARS: Incomplete response: Kimi returned no choices. Re-enter your message to retry.")
                continue

            result = response.choices[0]
            if result.finish_reason == "length":
                print("TARS: Incomplete response: the generation token limit was reached. Try a shorter request.")
                continue
            if result.finish_reason != "stop":
                print(f"TARS: Incomplete response: unexpected finish reason {result.finish_reason!r}. Re-enter your message to retry.")
                continue

            answer = result.message.content
            if not answer or not answer.strip():
                print("TARS: Incomplete response: final answer text is missing or blank. Re-enter your message to retry.")
                continue

            # Preserve all returned fields, including Kimi's reasoning_content.
            assistant_message = result.message.model_dump()
            messages = candidate_messages + [assistant_message]
            print(f"TARS: {answer}")


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\nTARS signing off.")
