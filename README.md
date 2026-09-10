# TARS

TARS is a terminal conversation assistant powered by Kimi. It displays answers
progressively, remembers successful turns during the current session, and speaks
with a concise, occasionally dry personality.

## Requirements

- Python 3.14.6 is the tested interpreter version.
- A Kimi account with K3 API access, an API key, and internet connectivity.
- Run the commands below from the project folder in a macOS or Linux terminal.

## Setup

Create and activate a project environment:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip check
```

If `python` is unavailable, use your Python 3 executable for the first command.
After activation, `python` selects the project environment.

Copy the configuration example (only if you do not already have a `.env`):

```bash
cp .env.example .env
```

Open `.env` in your editor and enter your own Kimi key after the equals sign:

```dotenv
MOONSHOT_API_KEY=your_kimi_key_here
```

Keep the real key private. `.gitignore` excludes `.env` and `.venv/`.
An existing terminal environment variable takes precedence over `.env`; restart
TARS after changing configuration.

## Run

```bash
source .venv/bin/activate
python tars.py
```

Type a message after `You:` and press Enter. `TARS: Thinking...` appears before
answer fragments arrive. Reasoning is retained for conversation continuity but
is not printed. Requests use your Kimi account's API allowance.

## Commands

- `/new`: discard the session history and start with the original personality.
- `/quit`: exit cleanly.
- Ctrl+C: exit, including during a reply. End-of-input also exits.
- Blank input: prompt again without sending a request.

Commands are lowercase and must match exactly after surrounding whitespace is removed.

## Dependencies and settings

Direct dependencies are packages this program imports: `openai==3.11.0` for the
Kimi-compatible client, `python-dotenv==1.2.3` for `.env` loading, and
`httpx2==2.12.0` for transport exceptions. Indirect dependencies are packages those
libraries need. `requirements.txt` records both, captured from the working environment
with `python -m pip freeze > requirements.txt`. The `>` replaces that file with
the installed version list. It does not record Python itself, source code, or keys.

Current settings: `kimi-k3`, reasoning effort `low`, a 4,096-token generation
allowance, streaming enabled, a 60-second SDK timeout, and no automatic retries.
The endpoint is `https://api.moonshot.ai/v1`. The token allowance is a generation
ceiling, not a promised answer length.

## Current limits

History lives only in memory and disappears on exit or `/new`. Every ordinary
request sends the successful conversation history again. Voice, persistent memory,
and external actions are future features. This version supports text conversation;
unexpected message fields such as tool calls cause the turn to fail explicitly.

## Troubleshooting

- Missing credentials: fill in `MOONSHOT_API_KEY` in `.env` and restart.
- Authentication failure: check the Kimi key and restart after correcting it.
- Connection failure or timeout: restore connectivity and re-enter the message.
  TARS remains at the input prompt and does not retry automatically.
- Other API errors: check account access, balance, and rate limits using the
  displayed HTTP status code.
- Incomplete reply: partial output may remain visible, but that entire turn is
  excluded from history. Missing `[DONE]`, an unexpected finish reason, malformed
  data, or blank final text all fail the turn. If the generation limit was reached,
  try a shorter request. Otherwise re-enter the message when the issue is resolved.
- Import errors: activate `.venv` and install `requirements.txt` in that environment.

## Verification

Verification date: 2026-09-10. Existing and temporary interpreter: Python 3.14.6.

- Recorded the working environment's 15 pinned packages in `requirements.txt`.
- Existing environment: `python -m pip check` passed; source syntax, empty
  configuration example, and ignore rules passed local checks.
- Earlier synthetic streaming checks passed: exact fragment reconstruction,
  hidden reasoning preservation, empty choices, valid completion, missing `[DONE]`,
  generation limit, malformed JSON, error events, and transport interruption.
  These are simulated checks, not evidence of live Kimi behavior.
- Created `/tmp/tars-phase1-check` using `/opt/miniconda3/bin/python` without
  changing the working `.venv`. Installation was blocked by sandbox DNS resolution
  of PyPI, and permission for a network-enabled retry was declined. Installation
  from the recorded list and `pip check` in that temporary environment remain unverified.
- Live streaming, fact recall, blank input, `/new`, disconnect/reconnect recovery,
  and `/quit` followed by a fresh restart have not been verified in the temporary
  environment. No paid API requests were made during this verification step.

Phase 1 remains incomplete pending isolated installation and the live checks.
To resume from the project folder:

```bash
/tmp/tars-phase1-check/bin/python -m pip install -r requirements.txt
/tmp/tars-phase1-check/bin/python -m pip check
/tmp/tars-phase1-check/bin/python tars.py
```

Ask a simple question; state a distinctive fact and ask about it; enter blank
input; use `/new` and ask about the fact again. Disconnect the network, send a
message, then reconnect and send another. Finally use `/quit`, restart, and confirm
the earlier fact is unavailable. A passing live check should show incremental
answers once, correct session recall, a usable prompt after failure, and fresh
history after reset or restart.
