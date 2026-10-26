"""Start local Ollama, using the project runtime if present."""

import os
import shutil
import subprocess
from pathlib import Path

from dotenv import load_dotenv


def main():
    root = Path(__file__).resolve().parent
    load_dotenv(root / ".env", override=False)
    portable = root / ".cache" / "ollama-runtime" / "ollama"
    binary = str(portable) if portable.is_file() else shutil.which("ollama")
    if binary is None:
        raise SystemExit("Install Ollama from https://ollama.com/download, then run ollama pull qwen2.5:1.5b.")
    environment = os.environ.copy()
    environment.setdefault("OLLAMA_NO_CLOUD", "1")
    if portable.is_file():
        environment.setdefault("OLLAMA_MODELS", str(root / ".cache" / "ollama-models"))
    print("Starting Ollama locally. Leave this terminal open; run python app.py in another terminal.", flush=True)
    try:
        subprocess.run([binary, "serve"], env=environment, check=True)
    except KeyboardInterrupt:
        print("\nSummary server stopped.")
    except subprocess.CalledProcessError:
        raise SystemExit("Ollama could not start. If port 11434 is already in use, the server may already be running.")


if __name__ == "__main__":
    main()
