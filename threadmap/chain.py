"""HybridChain - directed graph of hybrid operation entities and relationships."""
from __future__ import annotations

from typing import Any

import networkx as nx

from .models import (
    Entity, Relationship, Action, Actor, Capability,
    Infrastructure, Narrative, Target, Effect, EdgeType,
)


class HybridChain:
    """A directed graph representing a hybrid operation chain.

    Nodes are entities (Actor, Action, Capability, etc.).
    Edges are relationships with types and optional resource references.
    """

    def __init__(self, chain_id: str, name: str, description: str = ""):
        self.chain_id = chain_id
        self.name = name
        self.description = description
        self.graph = nx.DiGraph()
        self._entities: dict[str, Entity] = {}

    def add_entity(self, entity: Entity) -> None:
        """Add an entity as a node in the graph."""
        self._entities[entity.id] = entity
        self.graph.add_node(
            entity.id,
            entity_type=type(entity).__name__,
            data=entity,
        )

    def get_entity(self, entity_id: str) -> Entity | None:
        return self._entities.get(entity_id)

    def add_relationship(self, rel: Relationship) -> None:
        """Add a directed edge between two entities."""
        if rel.source_id not in self._entities:
            raise ValueError(f"Source entity '{rel.source_id}' not in chain")
        if rel.target_id not in self._entities:
            raise ValueError(f"Target entity '{rel.target_id}' not in chain")
        self.graph.add_edge(
            rel.source_id,
            rel.target_id,
            edge_type=rel.edge_type,
            resource_id=rel.resource_id,
            description=rel.description,
        )

    @property
    def entities(self) -> dict[str, Entity]:
        return dict(self._entities)

    @property
    def relationships(self) -> list[dict[str, Any]]:
        result = []
        for u, v, data in self.graph.edges(data=True):
            result.append({"source": u, "target": v, **data})
        return result

    def get_chain(self) -> list[str]:
        """Return topologically sorted node IDs (full operation sequence)."""
        if not nx.is_directed_acyclic_graph(self.graph):
            raise ValueError("Chain contains cycles - not a valid DAG")
        return list(nx.topological_sort(self.graph))

    def get_critical_path(self) -> list[str]:
        """Compute the critical path (longest path through the DAG).

        Uses duration_hours for Action nodes as weights; other nodes weight 0.
        Returns ordered list of node IDs on the critical path.
        """
        if not nx.is_directed_acyclic_graph(self.graph):
            raise ValueError("Chain contains cycles - not a valid DAG")

        if len(self.graph.nodes) == 0:
            return []

        # Weight = duration of target node (for Actions)
        def _weight(u: str, v: str) -> float:
            entity = self._entities.get(v)
            if isinstance(entity, Action) and entity.duration_hours:
                return -entity.duration_hours  # negative for longest path
            return 0

        # Add virtual source/sink
        sources = [n for n in self.graph.nodes if self.graph.in_degree(n) == 0]
        sinks = [n for n in self.graph.nodes if self.graph.out_degree(n) == 0]

        if not sources or not sinks:
            return list(nx.topological_sort(self.graph))

        g = self.graph.copy()
        g.add_node("__src__")
        g.add_node("__sink__")
        for s in sources:
            g.add_edge("__src__", s)
        for s in sinks:
            g.add_edge(s, "__sink__")

        # Bellman-Ford with negative weights = longest path
        try:
            path = nx.bellman_ford_path(g, "__src__", "__sink__",
                                         weight=lambda u, v, d: _weight(u, v))
            return [n for n in path if n not in ("__src__", "__sink__")]
        except nx.NetworkXNoPath:
            return []

    def intervention_score(self, node_id: str) -> int:
        """Score a node by how many downstream nodes depend on it.

        Returns the number of nodes reachable from this node (descendants).
        Higher = more impactful intervention point.
        """
        if node_id not in self.graph:
            raise ValueError(f"Node '{node_id}' not in chain")
        return len(nx.descendants(self.graph, node_id))

    def get_entities_by_type(self, entity_type: type) -> list[Entity]:
        """Return all entities of a given type."""
        return [e for e in self._entities.values() if isinstance(e, entity_type)]

    def is_valid_dag(self) -> bool:
        return nx.is_directed_acyclic_graph(self.graph)
