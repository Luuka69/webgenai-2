import os
from typing import Any, Dict

import requests

OLLAMA_URL = os.getenv('OLLAMA_URL', 'http://127.0.0.1:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'mistral')


def call_ollama(prompt: str, retries: int = 1) -> Dict[str, Any]:
    payload = {
        'model': OLLAMA_MODEL,
        'prompt': prompt,
        'stream': False,
        'format': 'json',
    }
    
    for attempt in range(retries + 1):
        response = requests.post(f"{OLLAMA_URL}/api/generate", json=payload, timeout=600)
        response.raise_for_status()
        data = response.json()
        generated = data.get('response', '')
        if isinstance(generated, str):
            generated = generated.strip()
        # Return raw on first success; validation happens upstream
        return {'generated': generated, 'raw': data}
    return {'error': 'generation failed'}
