"""
Graphs module - Auto-select extraction version based on config
"""

from config import ExtractionVersion

if ExtractionVersion.is_v2():
    print("🚀 Loading Extraction Pipeline V2 (FACTS + LOGIC separation)")
    from graphs.extraction_graph_v2 import graph_v2 as graph, invoke_clean_v2 as invoke_clean
else:
    print("📊 Loading Extraction Pipeline V1 (original)")
    from graphs.extraction_graph import graph, invoke_clean

# Export unified interface
extraction_graph = graph
__all__ = ['extraction_graph', 'graph', 'invoke_clean']
