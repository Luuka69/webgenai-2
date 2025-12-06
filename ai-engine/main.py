"""Entry point that forwards to the ai_engine package app factory."""

import os

from dotenv import load_dotenv

from ai_engine.app import create_app

# Load environment variables once on startup
load_dotenv()


def run() -> None:
    app = create_app()
    host = os.getenv("AI_ENGINE_HOST", "0.0.0.0")
    port = int(os.getenv("AI_ENGINE_PORT", "5005"))
    print(f"AI Engine running on {host}:{port}")
    app.run(host=host, port=port)


if __name__ == "__main__":
    run()
