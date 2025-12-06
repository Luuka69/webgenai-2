import html
from typing import Any, Dict, Iterable, List

SELF_CLOSING = {'img', 'input', 'hr', 'br', 'meta', 'link'}


def _attrs_to_string(attrs: Dict[str, Any]) -> str:
    if not attrs:
        return ''
    parts = []
    for key, value in attrs.items():
        if value is None:
            continue
        escaped = html.escape(str(value), quote=True)
        parts.append(f"{key}='{escaped}'")
    return (' ' + ' '.join(parts)) if parts else ''


def render_node(node: Dict[str, Any]) -> str:
    tag = (node.get('type') or 'div').lower()
    attrs = _attrs_to_string(node.get('props', {}))
    children = node.get('children')
    text = html.escape(str(node.get('text', '') or ''))

    children_html = ''
    if isinstance(children, Iterable) and not isinstance(children, (str, bytes, dict)):
        children_html = ''.join(render_node(child) for child in children if isinstance(child, dict))
    elif isinstance(children, dict):
        children_html = render_node(children)

    if tag in SELF_CLOSING and not children_html:
        return f"<{tag}{attrs} />"

    return f"<{tag}{attrs}>{text}{children_html}</{tag}>"


def render_document(nodes: List[Dict[str, Any]]) -> str:
    body = ''.join(render_node(node) for node in nodes)
    return (
        "<!DOCTYPE html>"
        "<html lang='en'>"
        "<head><meta charset='UTF-8'/><meta name='viewport' content='width=device-width, initial-scale=1.0'/>"
        "<title>Generated Interface</title>"
        "<style>body{margin:0;font-family:'Segoe UI',Roboto,sans-serif;}</style>"
        "</head>"
        f"<body>{body}</body>"
        "</html>"
    )
