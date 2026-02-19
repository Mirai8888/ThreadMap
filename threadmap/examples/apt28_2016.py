"""APT28 2016 US Election Interference - modeled as a 7-node hybrid chain.

Based on public reporting of GRU Units 26165/74455 operations combining
cyber intrusion with information operations (hack-and-leak).
"""
from threadmap.chain import HybridChain
from threadmap.models import (
    Actor, Action, Capability, Infrastructure, Narrative, Target, Effect,
    Relationship, ActorType, ActionDomain, CapabilityType,
    InfrastructureType, NarrativeType, EffectType, EdgeType,
)


def build_apt28_chain() -> HybridChain:
    """Construct the APT28 2016 election interference hybrid chain."""
    chain = HybridChain(
        chain_id="chain-apt28-election-2016",
        name="APT28 DNC Hack and Leak Operation",
        description=(
            "Hybrid operation combining cyber intrusion (GRU Unit 26165) with "
            "information operations (GRU Unit 74455) to interfere in the 2016 "
            "US presidential election. Publicly attributed by US IC, Mueller "
            "investigation, and multiple cybersecurity firms."
        ),
    )

    # --- 7 Core Entity Types ---

    # 1. ACTOR: GRU operators
    actor_26165 = Actor(
        id="actor-unit-26165",
        name="GRU Unit 26165",
        actor_type=ActorType.STATE,
        capabilities=["spearphishing", "credential-harvesting", "lateral-movement", "exfiltration"],
        known_aliases=["Fancy Bear", "APT28", "Sofacy", "Pawn Storm"],
        attribution_confidence=0.95,
    )
    actor_74455 = Actor(
        id="actor-unit-74455",
        name="GRU Unit 74455",
        actor_type=ActorType.STATE,
        capabilities=["persona-creation", "media-placement", "narrative-ops", "platform-manipulation"],
        known_aliases=["Sandworm adjacency"],
        attribution_confidence=0.90,
    )

    # 2. ACTION: Operation steps
    action_spearphish = Action(
        id="action-spearphish",
        name="Spearphishing credential harvester",
        description="Targeted phishing campaign against DNC/DCCC staff to harvest email credentials.",
        domain=ActionDomain.CYBER,
        attack_ids=["T1566.002"],
        actor_id="actor-unit-26165",
        platform_id="infra-email",
        duration_hours=168,  # 7 days
        success_probability=0.3,
        detection_surface=["email-gateway-logs", "url-click-tracking"],
    )
    action_exfiltrate = Action(
        id="action-exfiltrate",
        name="Email compromise and exfiltration",
        description="Access compromised accounts, exfiltrate emails and documents.",
        domain=ActionDomain.CYBER,
        attack_ids=["T1114.002", "T1048"],
        actor_id="actor-unit-26165",
        platform_id="infra-email",
        duration_hours=720,  # 30 days
        success_probability=0.8,
        detection_surface=["unusual-login-location", "bulk-download-patterns"],
    )
    action_release = Action(
        id="action-selective-release",
        name="Staged document release",
        description="Timed release of selected documents via personas to maximize narrative impact.",
        domain=ActionDomain.HYBRID,
        attack_ids=["T1567"],
        disarm_ids=["T0085", "TA06"],
        sct_codes=["SCT-006", "SCT-001", "SCT-002"],
        actor_id="actor-unit-74455",
        duration_hours=2160,  # 90 days
        success_probability=0.7,
    )

    # 3. CAPABILITY: Tools and exploits
    cap_xagent = Capability(
        id="cap-xagent",
        name="X-Agent implant",
        capability_type=CapabilityType.TOOLING,
        description="Custom GRU backdoor for persistent access and exfiltration.",
    )

    # 4. INFRASTRUCTURE: Platforms and servers
    infra_email = Infrastructure(
        id="infra-email",
        name="Campaign email systems",
        infra_type=InfrastructureType.EMAIL,
        detection_difficulty=0.3,
    )
    infra_dcleaks = Infrastructure(
        id="infra-dcleaks",
        name="DCLeaks.com",
        infra_type=InfrastructureType.MEDIA,
        description="GRU-operated leak website using synthetic persona.",
        detection_difficulty=0.6,
    )

    # 5. NARRATIVE: Information operation threads
    narrative_corruption = Narrative(
        id="narrative-corruption",
        name="DNC corruption narrative",
        narrative_type=NarrativeType.LEAK,
        description="Selective release of emails to paint DNC leadership as corrupt and biased.",
        target_audience="US voting public, media",
        sct_codes=["SCT-002", "SCT-006"],
        platforms=["infra-dcleaks", "infra-twitter"],
    )

    # 6. TARGET: Who is being targeted
    target_dnc = Target(
        id="target-dnc",
        name="Democratic National Committee",
        target_type="organization",
        description="Primary target of cyber intrusion and subsequent information operations.",
        vulnerabilities=["email-security", "insider-communications-sensitivity"],
    )

    # 7. EFFECT: Outcomes
    effect_narrative_adoption = Effect(
        id="effect-narrative-adoption",
        name="Narrative adoption by media and public",
        effect_type=EffectType.NARRATIVE_ADOPTION,
        description="Leaked documents become major news stories, shaping election discourse.",
        severity=0.8,
        reversibility=0.1,
    )

    # Add all entities
    for entity in [
        actor_26165, actor_74455,
        action_spearphish, action_exfiltrate, action_release,
        cap_xagent,
        infra_email, infra_dcleaks,
        narrative_corruption,
        target_dnc,
        effect_narrative_adoption,
    ]:
        chain.add_entity(entity)

    # Add relationships (the operation chain)
    relationships = [
        # Cyber kill chain
        Relationship(source_id="actor-unit-26165", target_id="action-spearphish",
                     edge_type=EdgeType.TRIGGERS, description="Unit 26165 executes phishing"),
        Relationship(source_id="action-spearphish", target_id="action-exfiltrate",
                     edge_type=EdgeType.DEPENDENCY, description="Credentials enable access"),
        Relationship(source_id="cap-xagent", target_id="action-exfiltrate",
                     edge_type=EdgeType.ENABLES, description="X-Agent used for persistent access"),
        Relationship(source_id="action-exfiltrate", target_id="action-selective-release",
                     edge_type=EdgeType.DEPENDENCY, description="Exfiltrated docs fed to release"),
        # Target
        Relationship(source_id="action-spearphish", target_id="target-dnc",
                     edge_type=EdgeType.DEPENDENCY, description="DNC targeted by phishing"),
        # Info ops
        Relationship(source_id="actor-unit-74455", target_id="action-selective-release",
                     edge_type=EdgeType.TRIGGERS, description="Unit 74455 runs leak ops"),
        Relationship(source_id="action-selective-release", target_id="narrative-corruption",
                     edge_type=EdgeType.TRIGGERS, description="Releases drive narrative"),
        Relationship(source_id="infra-dcleaks", target_id="action-selective-release",
                     edge_type=EdgeType.ENABLES, description="DCLeaks hosts released docs"),
        # Effects
        Relationship(source_id="narrative-corruption", target_id="effect-narrative-adoption",
                     edge_type=EdgeType.AMPLIFIES, description="Narrative adopted by media"),
    ]

    for rel in relationships:
        chain.add_relationship(rel)

    return chain


if __name__ == "__main__":
    from threadmap.analysis import find_chokepoints, intervention_ranking, narrative_threads
    from threadmap.io import to_markdown

    chain = build_apt28_chain()
    print(to_markdown(chain))
