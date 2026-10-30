# Assignment 4 — LLM API Integration: CLI Bullet-Point Summarizer

**Course Outcome:** CO2  
**Assignment:** Build a Python CLI tool that accepts a paragraph, calls an LLM API, and prints a concise bullet-point summary.  
**Provider:** Groq (OpenAI-compatible Chat Completions API)

## Features
- Accept a paragraph interactively, from `--text`, or from a `.txt` file.
- Call an LLM API and print a concise bullet-point summary.
- Configure model and secret API key through environment variables.
- Set number of bullet points and generation temperature.
- Handle missing keys, bad input, network issues, and API errors.
- Uses Python standard library plus macOS built-in `curl` — no pip installation needed.

## Setup (macOS / VS Code)

1. Open the `Assignment_04_LLM_API_Integration` folder in VS Code.
2. Open **Terminal > New Terminal**.
3. Make sure Python 3.10+ is available: `python3 --version`.
4. Copy the example configuration:
   ```bash
   cp .env.example .env
   ```
5. Open `.env` and replace `replace_with_your_groq_api_key` with your actual key from https://console.groq.com/keys . **Never publish `.env` or your API key to GitHub.**
6. Run:
   ```bash
   python3 main.py --file sample_input.txt
   ```

### Other ways to run

```bash
# Direct paragraph
python3 main.py --text "Machine learning helps identify patterns in data and automate predictions." --bullets 2

# Adjust generation parameters
python3 main.py --file sample_input.txt --bullets 4 --temperature 0.1

# Interactive mode (press Enter twice after your paragraph)
python3 main.py

# Help
python3 main.py --help
```

## Environment variables and API parameters

| Setting | Purpose | Default |
| --- | --- | --- |
| `GROQ_API_KEY` | Authenticates API requests; required | none |
| `GROQ_MODEL` / `--model` | Chooses chat model | `openai/gpt-oss-20b` |
| `--temperature` | Controls sampling variability | `0.2` |
| `--bullets` | Requested bullet count | `3` |
| `max_tokens` | Maximum generated tokens | `500` |

The script uses the system `curl` for HTTPS calls (matching the successful direct Groq test), and calls `POST https://api.groq.com/openai/v1/chat/completions`. The JSON request includes `model`, `messages`, `temperature`, and `max_tokens`. Output text is read from `choices[0].message.content`.

## Illustrative terminal example

> The following summary is illustrative, not a verified live API response. Run with a valid key and capture your own terminal screenshot for submission.

```text
$ python3 main.py --file sample_input.txt

=== BULLET-POINT SUMMARY ===
- AI tools help farmers access weather forecasts, crop prices, and crop-disease warnings.
- Digital agriculture can improve planning and reduce uncertainty.
- Poor connectivity, language barriers, and limited digital skills remain challenges.
```

## Evidence for grading and submission

- **Code:** `main.py`
- **README:** This file contains setup, parameters, and usage.
- **Input sample:** `sample_input.txt`
- **Sample terminal transcript:** `sample_terminal_output.txt` (illustrative until replaced with a real run)
- **Required actual screenshot:** After successful execution, take a screenshot showing the terminal command and returned bullets. Save it in `screenshots/`.
- **GitHub repository link:** Create a repository, push this folder, and submit the URL. No repository has been created automatically.

## Troubleshooting

- `GROQ_API_KEY is missing`: check `.env` was created and contains the key.
- `HTTP 401`: key is incorrect or revoked.
- `HTTP 429`: API usage/rate limit reached; retry later.
- `model_not_found` / `HTTP 400`: update `GROQ_MODEL` using a current supported model ID from Groq documentation.
- Connection error: verify internet access and the service status.

## Data safety

Do not paste private information into inputs. Input paragraphs are sent to the configured external LLM provider for summarization.

## Note for previous users
If you already have a `.env` file, update `GROQ_MODEL=openai/gpt-oss-20b` in that file. The `.env` is not included in this ZIP. If an old model is exported in your shell, run `unset GROQ_MODEL` before using the new default.
