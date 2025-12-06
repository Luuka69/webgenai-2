import re

def strip_code_fences(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith('```'):
        stripped = re.sub(r"^```[\w-]*\s*", '', stripped)
    if stripped.endswith('```'):
        stripped = re.sub(r"\s*```$", '', stripped)
    return stripped.strip()
