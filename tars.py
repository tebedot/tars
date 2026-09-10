import os

from openai import APIConnectionError, APIStatusError, APITimeoutError, AuthenticationError, OpenAI
from dotenv import load_dotenv

load_dotenv()

def main():
    print("TARS is online.")

    # Read the key from the terminal's environment, not from this file.
    api_key = os.environ.get("MOONSHOT_API_KEY", "").strip()
    if not api_key:
        print("Set MOONSHOT_API_KEY in your .env file, then run me again.")
        return

    question = "Explain what an API is in two short sentences."
    print(f"You: {question}")

    # The base URL directs this SDK to Kimi.
    with OpenAI(
        api_key=api_key,
        base_url="https://api.moonshot.ai/v1",
        timeout=60.0,
        max_retries=0,
    ) as client:
        try:
            response = client.chat.completions.create(
                model="kimi-k3",
                reasoning_effort="low",
                max_completion_tokens=4096,
                messages=[{"role": "user", "content": question}],
                stream=False,
            )
        except AuthenticationError:
            print("TARS: Authentication failed. Check your Kimi API key.")
            return
        except APITimeoutError:
            print("TARS: The request timed out. Run the program again to retry.")
            return
        except APIConnectionError:
            print("TARS: Could not connect to Kimi. Check your internet connection.")
            return
        except APIStatusError as error:
            print(f"TARS: Kimi returned API error {error.status_code}. Check account access, balance, and rate limits.")
            return

    if not response.choices:
        print("TARS: Incomplete response: no answer was returned.")
        return

    # choices is a list; index 0 selects its first result.
    result = response.choices[0]
    answer = result.message.content
    if result.finish_reason != "stop" or not answer or not answer.strip():
        print("TARS: Incomplete response: generation stopped early or final text is missing.")
        return

    print(f"TARS: {answer}")


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\nTARS signing off.")
