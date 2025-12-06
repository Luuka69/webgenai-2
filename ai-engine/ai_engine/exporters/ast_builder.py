from typing import Any, Dict, List


# Simple RenderAST node structure
RenderNode = Dict[str, Any]


def screen_to_ast(screen_schema: Dict[str, Any]) -> List[RenderNode]:
    """Convert a ScreenSchema dict into a RenderAST list of nodes (stub)."""
    components = screen_schema.get('components') or []
    nodes: List[RenderNode] = []
    for comp in components:
        nodes.append(
            {
                'type': comp.get('type', 'div'),
                'props': comp.get('props', {}),
                'style': comp.get('style', {}),
                'layout': comp.get('position', {}),
                'children': comp.get('children', []),
            }
        )
    return nodes
