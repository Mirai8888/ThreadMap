"""Tests for ThreadMap MVP."""
import json
import pytest

from threadmap.models import (
    Actor, Action, Capability, Infrastructure, Narrative, Target, Effect,
    Relationship, ActorType, ActionDomain, CapabilityType,
    InfrastructureType, NarrativeType, EffectType, EdgeType,
)
from threadmap.chain import HybridChain
from threadmap.analysis import (
    find_chokepoints, narrative_threads, capability_requirements, intervention_ranking,
)
from threadmap.io import to_json, from_json, to_stix_bundle, to_markdown
from threadmap.examples.apt28_2016 import build_apt28_chain


# --- Fixtures ---

@pytest.fixture
def simple_chain():
    """A minimal 3-action chain for unit testing."""
    chain = HybridChain("test-chain", "Test Chain", "A simple test chain")

    chain.add_entity(Actor(id="a1", name="Attacker", actor_type=ActorType.STATE))
    chain.add_entity(Action(id="act1", name="Recon", domain=ActionDomain.CYBER, duration_hours=24))
    chain.add_entity(Action(id="act2", name="Exploit", domain=ActionDomain.CYBER,
                            duration_hours=48, success_probability=0.3, tools=["metasploit"]))
    chain.add_entity(Action(id="act3", name="Exfil", domain=ActionDomain.CYBER, duration_hours=12))
    chain.add_entity(Capability(id="cap1", name="Zero-day", capability_type=CapabilityType.EXPLOIT))
    chain.add_entity(Target(id="t1", name="Victim Org", target_type="organization"))
    chain.add_entity(Effect(id="eff1", name="Data breach", effect_type=EffectType.DATA_LOSS, severity=0.9))
    chain.add_entity(Narrative(id="nar1", name="Leak narrative", narrative_type=NarrativeType.LEAK))

    chain.add_relationship(Relationship(source_id="a1", target_id="act1", edge_type=EdgeType.TRIGGERS))
    chain.add_relationship(Relationship(source_id="act1", target_id="act2", edge_type=EdgeType.DEPENDENCY))
    chain.add_relationship(Relationship(source_id="act2", target_id="act3", edge_type=EdgeType.DEPENDENCY))
    chain.add_relationship(Relationship(source_id="cap1", target_id="act2", edge_type=EdgeType.ENABLES))
    chain.add_relationship(Relationship(source_id="act3", target_id="eff1", edge_type=EdgeType.TRIGGERS))
    chain.add_relationship(Relationship(source_id="act3", target_id="nar1", edge_type=EdgeType.ENABLES))
    chain.add_relationship(Relationship(source_id="nar1", target_id="t1", edge_type=EdgeType.AMPLIFIES))

    return chain


# --- Model Tests ---

class TestModels:
    def test_actor_creation(self):
        a = Actor(id="a1", name="Test", actor_type=ActorType.STATE)
        assert a.id == "a1"
        assert a.actor_type == ActorType.STATE

    def test_action_defaults(self):
        a = Action(id="x", name="X", domain=ActionDomain.CYBER)
        assert a.success_probability == 0.5
        assert a.attack_ids == []

    def test_all_entity_types(self):
        """All 7 entity types can be instantiated."""
        entities = [
            Actor(id="a", name="A", actor_type=ActorType.STATE),
            Action(id="b", name="B", domain=ActionDomain.CYBER),
            Capability(id="c", name="C", capability_type=CapabilityType.EXPLOIT),
            Infrastructure(id="d", name="D", infra_type=InfrastructureType.SERVER),
            Narrative(id="e", name="E", narrative_type=NarrativeType.LEAK),
            Target(id="f", name="F"),
            Effect(id="g", name="G", effect_type=EffectType.DATA_LOSS),
        ]
        assert len(entities) == 7


# --- Chain Tests ---

class TestHybridChain:
    def test_add_entity(self, simple_chain):
        assert len(simple_chain.entities) == 8

    def test_get_entity(self, simple_chain):
        e = simple_chain.get_entity("act1")
        assert e is not None
        assert e.name == "Recon"

    def test_get_chain_topological(self, simple_chain):
        order = simple_chain.get_chain()
        assert order.index("act1") < order.index("act2")
        assert order.index("act2") < order.index("act3")

    def test_is_valid_dag(self, simple_chain):
        assert simple_chain.is_valid_dag()

    def test_critical_path(self, simple_chain):
        cp = simple_chain.get_critical_path()
        assert "act2" in cp  # longest duration node

    def test_intervention_score(self, simple_chain):
        score = simple_chain.intervention_score("act1")
        assert score >= 1  # at least act2 downstream

    def test_invalid_relationship(self):
        chain = HybridChain("x", "X")
        chain.add_entity(Actor(id="a", name="A", actor_type=ActorType.STATE))
        with pytest.raises(ValueError):
            chain.add_relationship(Relationship(source_id="a", target_id="nonexistent"))

    def test_get_entities_by_type(self, simple_chain):
        actions = simple_chain.get_entities_by_type(Action)
        assert len(actions) == 3


# --- Analysis Tests ---

class TestAnalysis:
    def test_find_chokepoints(self, simple_chain):
        cps = find_chokepoints(simple_chain)
        assert len(cps) > 0
        assert cps[0]["impact"] >= cps[-1]["impact"]

    def test_narrative_threads(self, simple_chain):
        threads = narrative_threads(simple_chain)
        assert len(threads) > 0
        # All threads should contain the narrative node
        for thread in threads:
            assert "nar1" in thread

    def test_capability_requirements(self, simple_chain):
        caps = capability_requirements(simple_chain)
        cap_names = [c["name"] for c in caps]
        assert "Zero-day" in cap_names
        assert "metasploit" in cap_names

    def test_intervention_ranking(self, simple_chain):
        rankings = intervention_ranking(simple_chain)
        assert len(rankings) > 0
        # Should be sorted by score descending
        scores = [r["score"] for r in rankings]
        assert scores == sorted(scores, reverse=True)


# --- IO Tests ---

class TestIO:
    def test_json_roundtrip(self, simple_chain):
        json_str = to_json(simple_chain)
        restored = from_json(json_str)
        assert restored.chain_id == simple_chain.chain_id
        assert len(restored.entities) == len(simple_chain.entities)
        assert len(restored.relationships) == len(simple_chain.relationships)

    def test_stix_bundle(self, simple_chain):
        bundle = to_stix_bundle(simple_chain)
        assert bundle["type"] == "bundle"
        assert len(bundle["objects"]) > 0
        # Should have relationship objects
        rel_objs = [o for o in bundle["objects"] if o["type"] == "relationship"]
        assert len(rel_objs) > 0

    def test_markdown_report(self, simple_chain):
        md = to_markdown(simple_chain)
        assert "# ThreadMap Report" in md
        assert "Test Chain" in md
        assert "Intervention" in md


# --- APT28 Example Tests ---

class TestAPT28Example:
    def test_build_chain(self):
        chain = build_apt28_chain()
        assert chain.chain_id == "chain-apt28-election-2016"
        assert chain.is_valid_dag()

    def test_has_all_entity_types(self):
        chain = build_apt28_chain()
        types_present = {type(e).__name__ for e in chain.entities.values()}
        assert types_present == {"Actor", "Action", "Capability", "Infrastructure",
                                  "Narrative", "Target", "Effect"}

    def test_critical_path(self):
        chain = build_apt28_chain()
        cp = chain.get_critical_path()
        assert len(cp) > 0

    def test_intervention_ranking(self):
        chain = build_apt28_chain()
        rankings = intervention_ranking(chain)
        assert len(rankings) > 0

    def test_json_export(self):
        chain = build_apt28_chain()
        j = to_json(chain)
        data = json.loads(j)
        assert data["id"] == "chain-apt28-election-2016"

    def test_markdown_report(self):
        chain = build_apt28_chain()
        md = to_markdown(chain)
        assert "APT28" in md
