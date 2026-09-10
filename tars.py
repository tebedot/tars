import json
import os

from httpx2 import TransportError

from openai import APIConnectionError, APIStatusError, APITimeoutError, AuthenticationError, OpenAI
from dotenv import load_dotenv

def ask_kimi(client, messages):
    """Send the supplied conversation and return a streaming-response context manager."""
    return client.chat.completions.with_streaming_response.create(
        model="kimi-k3",
        reasoning_effort="low",
        max_completion_tokens=4096,
        messages=messages,
        stream=True,
    )


class StreamReplyError(Exception):
    """A received stream cannot be used as a complete conversation turn."""


def iter_sse_data(lines):
    """Yield data from events terminated by a blank line."""
    data_lines = []
    for line in lines:
        if line == "":
            if data_lines:
                yield "\n".join(data_lines)
                data_lines = []
        elif line == "data" or line.startswith("data:"):
            value = line[5:] if line.startswith("data:") else ""
            if value.startswith(" "):
                value = value[1:]
            data_lines.append(value)
        # Comments and metadata are ignored. An unfinished event at EOF is not yielded.


def read_reply(lines):
    """Display answer fragments and return a message only after valid completion."""
    assistant_message = {"role": "assistant"}
    finish_reason = None
    done = False
    printing_started = False
    try:
        for data in iter_sse_data(lines):
            if data == "[DONE]":
                done = True
                break
            event = json.loads(data)
            if not isinstance(event, dict):
                raise StreamReplyError("Expected a JSON object in the stream.")
            if "error" in event:
                raise StreamReplyError("Kimi reported an error event.")
            choices = event.get("choices")
            if not isinstance(choices, list):
                raise StreamReplyError("The stream has missing or invalid choices.")
            if not choices:
                continue
            choice = choices[0]
            if not isinstance(choice, dict):
                raise StreamReplyError("The stream contains an invalid choice.")
            delta = choice.get("delta")
            if not isinstance(delta, dict):
                raise StreamReplyError("The stream contains an invalid message delta.")
            for field, fragment in delta.items():
                if fragment is None:
                    continue
                if field not in {"role", "content", "reasoning_content", "refusal"}:
                    raise StreamReplyError(f"Unsupported message field: {field}.")
                if not isinstance(fragment, str):
                    raise StreamReplyError(f"Invalid text in message field: {field}.")
                if field == "role":
                    if fragment != "assistant":
                        raise StreamReplyError("Unexpected message role.")
                    assistant_message["role"] = fragment
                    continue
                # Never strip fragments: spaces and newlines belong to the answer.
                assistant_message[field] = assistant_message.get(field, "") + fragment
                if field == "content" and fragment:
                    if not printing_started:
                        print("TARS: ", end="", flush=True)
                        printing_started = True
                    print(fragment, end="", flush=True)
            reason = choice.get("finish_reason")
            if reason is not None:
                if not isinstance(reason, str):
                    raise StreamReplyError("Invalid finish reason.")
                finish_reason = reason
    finally:
        # Also end partial output cleanly on a transport error or Ctrl+C.
        if printing_started:
            print()

    if not done:
        raise StreamReplyError("Transmission ended before [DONE].")
    if finish_reason == "length":
        raise StreamReplyError("The generation token limit was reached.")
    if finish_reason != "stop":
        raise StreamReplyError(f"Unexpected finish reason: {finish_reason!r}.")
    if not assistant_message.get("content", "").strip():
        raise StreamReplyError("Final answer text is missing or blank.")
    return assistant_message


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
            print("TARS: Thinking...", flush=True)
            failure = None
            try:
                with ask_kimi(client, candidate_messages) as response:
                    assistant_message = read_reply(response.iter_lines())
            except AuthenticationError:
                failure = "Authentication failed. Check your key; restart after changing .env."
            except APITimeoutError:
                failure = "The request timed out."
            except APIConnectionError:
                failure = "Could not connect to Kimi. Check your connection."
            except APIStatusError as error:
                failure = f"Kimi returned API error {error.status_code}. Check account access, balance, and rate limits."
            except TransportError:
                failure = "The connection failed while reading the reply."
            except json.JSONDecodeError:
                failure = "The stream contained malformed JSON."
            except StreamReplyError as error:
                failure = str(error)

            if failure is not None:
                print(f"TARS: Incomplete reply: {failure} This turn was not added to history. Re-enter your message to retry.")
                continue

            # Only a fully received and validated reply becomes conversation history.
            messages = candidate_messages + [assistant_message]


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\nTARS signing off.")
