from typing import Any, Dict, List

RenderNode = Dict[str, Any]


def build_ast(screen_schema: Dict[str, Any]) -> List[RenderNode]:
    nodes: List[RenderNode] = []
    components = screen_schema.get('components') or []
    for comp in components:
        nodes.append(
            {
                'id': comp.get('id'),
                'type': comp.get('type', 'div'),
                'props': comp.get('props', {}),
                'style': comp.get('style', {}),
                'layout': comp.get('position', {}),
                'children': comp.get('children', []),
            }
        )
    return nodes
