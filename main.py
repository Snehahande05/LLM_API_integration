"""CLI paragraph-to-bullets summarizer using the Groq chat completions API."""
import argparse
import json
import os
import sys
import subprocess
import tempfile
from pathlib import Path

API_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODEL = "openai/gpt-oss-20b"


def load_env_file(path: Path) -> None:
    """Load basic KEY=VALUE entries from .env without overriding existing variables."""
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        name = name.strip()
        value = value.strip().strip('"').strip("'")
        if name:
            os.environ.setdefault(name, value)


def summarize(text: str, key: str, model: str, bullets: int, temperature: float, timeout: int = 30) -> str:
    if not text.strip():
        raise ValueError("The input paragraph cannot be empty.")
    payload = {
        "model": model,
        "temperature": temperature,
        "max_tokens": 500,
        "messages": [
            {"role": "system", "content": (
                "You are a concise summarization assistant. Summarize the provided text "
                f"into exactly {bullets} short bullet points. Each line must begin with '- '. "
                "Preserve factual meaning. Do not invent details. Output only bullet points."
            )},
            {"role": "user", "content": text},
        ],
    }
    # Use macOS curl: it has already been verified to work with this Groq account.
    # Pass the secret header through curl's stdin config, not command-line arguments.
    # Store the nonsecret JSON body in a temporary file for reliable quoting.
    try:
        with tempfile.TemporaryDirectory(prefix="groq_cli_") as temp_dir:
            payload_path = Path(temp_dir) / "request.json"
            payload_path.write_text(json.dumps(payload), encoding="utf-8")
            # Groq API keys consist of alphanumeric characters, hyphens and underscores.
            if any(ch in key for ch in ('\n', '\r', '"', '\\')):
                raise RuntimeError("Invalid API key format in .env")
            config = f'header = "Authorization: Bearer {key}"\n'
            completed = subprocess.run(
                ["curl", "--silent", "--show-error", "--location", 
                 "--request", "POST", API_URL,
                 "--header", "Content-Type: application/json",
                 "--data-binary", f"@{payload_path}",
                 "--connect-timeout", "15", "--max-time", str(timeout),
                 "--write-out", "\n__HTTP_STATUS__:%{http_code}",
                 "--config", "-"],
                input=config, capture_output=True, text=True, timeout=timeout + 5,
                check=False,
            )
        if completed.returncode != 0:
            raise RuntimeError(f"Connection error: {completed.stderr.strip() or 'curl failed'}")
        if "\n__HTTP_STATUS__:" not in completed.stdout:
            raise RuntimeError("Unexpected API response: missing HTTP status")
        body, status_str = completed.stdout.rsplit("\n__HTTP_STATUS__:", 1)
        status = int(status_str.strip())
        try:
            result = json.loads(body)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"API returned invalid JSON (HTTP {status}): {body[:250]}") from exc
        if status >= 400:
            detail = result.get("error", {}) if isinstance(result, dict) else {}
            message = detail.get("message", "Request failed") if isinstance(detail, dict) else str(detail)
            raise RuntimeError(f"API error (HTTP {status}): {message}")
    except FileNotFoundError as exc:
        raise RuntimeError("curl is not installed or not found in PATH") from exc
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("API request timed out. Try again.") from exc
    try:
        return result["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError, AttributeError) as exc:
        raise RuntimeError("The API returned an unexpected response format.") from exc


def main() -> int:
    load_env_file(Path(__file__).resolve().parent / ".env")
    parser = argparse.ArgumentParser(description="Summarize a paragraph into bullet points using an LLM API.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--text", help="Paragraph to summarize")
    group.add_argument("--file", type=Path, help="UTF-8 text file containing the paragraph")
    parser.add_argument("--bullets", type=int, default=3, help="Number of bullet points, 1-10 (default: 3)")
    parser.add_argument("--temperature", type=float, default=0.2, help="Sampling temperature, 0-2 (default: 0.2)")
    parser.add_argument("--model", default=os.getenv("GROQ_MODEL", DEFAULT_MODEL), help="Groq model ID")
    args = parser.parse_args()

    if not 1 <= args.bullets <= 10:
        parser.error("--bullets must be between 1 and 10")
    if not 0 <= args.temperature <= 2:
        parser.error("--temperature must be between 0 and 2")

    if args.file:
        try:
            text = args.file.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            print(f"Error reading file: {exc}", file=sys.stderr)
            return 1
    elif args.text is not None:
        text = args.text
    else:
        print("Enter a paragraph (press Enter twice to finish):")
        lines = []
        try:
            while True:
                line = input()
                if not line.strip():
                    break
                lines.append(line)
        except EOFError:
            pass
        text = " ".join(lines)

    if not text.strip():
        print("Error: No paragraph provided.", file=sys.stderr)
        return 1
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        print("Error: GROQ_API_KEY is missing. Create a .env file using .env.example.", file=sys.stderr)
        return 1
    try:
        summary = summarize(text, api_key, args.model, args.bullets, args.temperature)
    except (RuntimeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    print("\n=== BULLET-POINT SUMMARY ===")
    print(summary)
    return 0


if __name__ == "__main__":
    sys.exit(main())
