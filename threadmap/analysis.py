"""Chain analysis functions for ThreadMap."""
from __future__ import annotations

from typing import Any

import networkx as nx

from .chain import HybridChain
from .models import Action, Capability, Narrative


def find_chokepoints(chain: HybridChain, top_n: int = 10) -> list[dict[str, Any]]:
    """Find nodes whose removal breaks the most chains.

    Returns list of {node_id, entity_type, impact, downstream_count}
    sorted by impact descending.
    """
    results = []
    for node_id in chain.graph.nodes:
        descendants = len(nx.descendants(chain.graph, node_id))
        ancestors = len(nx.ancestors(chain.graph, node_id))
        # Impact = downstream nodes disabled if this node is removed
        # Also consider how many upstream paths converge here (betweenness-like)
        impact = descendants
        results.append({
            "node_id": node_id,
            "entity_type": type(chain.get_entity(node_id)).__name__,
            "downstream_count": descendants,
            "upstream_count": ancestors,
            "impact": impact,
        })
    results.sort(key=lambda x: x["impact"], reverse=True)
    return results[:top_n]


def narrative_threads(chain: HybridChain) -> list[list[str]]:
    """Extract all paths through the chain that include Narrative nodes.

    Returns list of paths (each path is a list of node IDs).
    """
    narrative_ids = {e.id for e in chain.get_entities_by_type(Narrative)}
    if not narrative_ids:
        return []

    sources = [n for n in chain.graph.nodes if chain.graph.in_degree(n) == 0]
    sinks = [n for n in chain.graph.nodes if chain.graph.out_degree(n) == 0]

    threads = []
    for source in sources:
        for sink in sinks:
            for path in nx.all_simple_paths(chain.graph, source, sink):
                if any(n in narrative_ids for n in path):
                    threads.append(path)
    return threads


def capability_requirements(chain: HybridChain) -> list[dict[str, Any]]:
    """What capabilities does a chain require?

    Returns all Capability entities plus capabilities listed on Action/Actor nodes.
    """
    caps = []

    # Explicit Capability entities
    for entity in chain.get_entities_by_type(Capability):
        caps.append({
            "id": entity.id,
            "name": entity.name,
            "type": entity.capability_type.value,
            "source": "entity",
        })

    # Capabilities listed on Actions
    for entity in chain.get_entities_by_type(Action):
        for tool in entity.tools:
            caps.append({
                "id": f"{entity.id}:{tool}",
                "name": tool,
                "type": "tooling",
                "source": f"action:{entity.id}",
            })

    return caps


def intervention_ranking(chain: HybridChain) -> list[dict[str, Any]]:
    """Rank possible intervention points by impact.

    For each node, compute:
    - downstream_impact: nodes disabled if removed
    - in_degree: how many paths converge here (harder to bypass)
    - score: composite ranking

    Returns sorted list, highest priority first.
    """
    rankings = []
    for node_id in chain.graph.nodes:
        entity = chain.get_entity(node_id)
        downstream = len(nx.descendants(chain.graph, node_id))
        in_deg = chain.graph.in_degree(node_id)
        out_deg = chain.graph.out_degree(node_id)

        # Nodes with high downstream impact AND that are convergence points
        # (high in-degree) are the best intervention targets
        score = downstream * (1 + in_deg)

        # Actions with low success probability are natural weak points
        if isinstance(entity, Action):
            score *= (2.0 - entity.success_probability)

        rankings.append({
            "node_id": node_id,
            "entity_type": type(entity).__name__,
            "name": getattr(entity, "name", node_id),
            "downstream_impact": downstream,
            "in_degree": in_deg,
            "out_degree": out_deg,
            "score": round(score, 2),
        })

    rankings.sort(key=lambda x: x["score"], reverse=True)
    return rankings
