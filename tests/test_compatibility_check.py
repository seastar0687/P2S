from p2s_core.models import PersonaProfile
from p2s_core.services import check_persona_style_compatibility, load_persona, load_style


def test_seina_rigorous_style_compatible():
    persona = load_persona("seina")
    style = load_style("rigorous_science_short")

    warnings = check_persona_style_compatibility(persona, style)

    assert warnings == []


def test_dramatic_persona_warns_with_high_rigor_style():
    style = load_style("rigorous_science_short")
    persona = PersonaProfile(
        persona_id="dramatic_test",
        name="Dramatic Test",
        role="paper explainer",
        positioning="A deliberately incompatible test persona.",
        personality_traits=["dramatic", "overexcited"],
        speaking_style_summary="Uses 誇張 hooks and clickbait energy.",
        relationship_to_audience="Performer",
        allowed_emotional_range=["excited"],
        version="0.1.0",
        created_at="2026-05-06T00:00:00Z",
        updated_at="2026-05-06T00:00:00Z",
    )

    warnings = check_persona_style_compatibility(persona, style)

    assert warnings == ["high-rigor style may conflict with dramatic persona tone"]
