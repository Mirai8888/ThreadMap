"""Tests for NetworkEngine -> ThreadMap adapter."""

import sys
from pathlib import Path

import networkx as nx
import pytest

# Ensure HoleSpawn is importable
sys.path.insert(0, str(Path.home() / "HoleSpawn"))

from holespawn.network.engine import NetworkEngine
from threadmap.network_adapter import network_to_chain
from threadmap.models import Actor, Action, Infrastructure, Target, Effect


def _build_graph():
    G = nx.DiGraph()
    edges = [
        ("alice", "bob", 3, "reply"), ("bob", "alice", 5, "retweet"),
        ("alice", "carol", 3, "reply"), ("carol", "alice", 4, "retweet"),
        ("dave", "eve", 3, "reply"), ("eve", "dave", 3, "reply"),
        ("grace", "alice", 2, "reply"), ("grace", "dave", 2, "reply"),
        ("alice", "grace", 1, "reply"), ("dave", "grace", 1, "reply"),
    ]
    for s, t, w, tp in edges:
        G.add_edge(s, t, weight=w, types={tp})
    return G


class TestNetworkToChain:
    def test_basic_conversion(self):
        engine = NetworkEngine(_build_graph())
        intel = engine.analyze()
        chain = network_to_chain(intel)
        assert chain.name == "Network Operation"
        assert len(chain.entities) > 0

    def test_actors_created(self):
        engine = NetworkEngine(_build_graph())
        intel = engine.analyze()
        chain = network_to_chain(intel)
        actors = chain.get_entities_by_type(Actor)
        assert len(actors) > 0
        assert any(a.name == "alice" for a in actors)

    def test_communities_as_infrastructure(self):
        engine = NetworkEngine(_build_graph())
        intel = engine.analyze()
        chain = network_to_chain(intel)
        infra = chain.get_entities_by_type(Infrastructure)
        assert len(infra) >= 1

    def test_with_plan(self):
        engine = NetworkEngine(_build_graph())
        intel = engine.analyze()
        plan = engine.plan_operation(
            objective="reach",
            target_nodes=["dave", "eve"],
            entry_nodes=["alice"],
        )
        chain = network_to_chain(intel, plan, campaign_name="Test Op")
        assert chain.name == "Test Op"

        # Should have actions from entry + amplification
        actions = chain.get_entities_by_type(Action)
        assert len(actions) >= 1

        # Should have an effect
        effects = chain.get_entities_by_type(Effect)
        assert len(effects) >= 1

    def test_chain_is_valid_dag(self):
        engine = NetworkEngine(_build_graph())
        intel = engine.analyze()
        plan = engine.plan_operation(
            objective="reach",
            target_nodes=["dave"],
            entry_nodes=["alice"],
        )
        chain = network_to_chain(intel, plan)
        assert chain.is_valid_dag()

    def test_chain_has_relationships(self):
        engine = NetworkEngine(_build_graph())
        intel = engine.analyze()
        plan = engine.plan_operation(
            objective="reach",
            target_nodes=["dave"],
            entry_nodes=["alice"],
        )
        chain = network_to_chain(intel, plan)
        rels = chain.relationships
        assert len(rels) >= 1
