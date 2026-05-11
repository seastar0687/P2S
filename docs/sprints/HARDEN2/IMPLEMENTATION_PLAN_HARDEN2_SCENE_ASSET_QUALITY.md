# IMPLEMENTATION PLAN — P2S HARDEN-2：Scene / Asset Quality

> Stub created by HARDEN-1. HARDEN-2 is not superseded.

## Position

HARDEN-2 covers scene wording quality, presentation consistency, asset plan semantic quality, asset selection quality, and scene/media mismatch. HARDEN-1 touches only the upstream extraction pieces that affect these concerns.

## Initial Scope

- Review scene wording for clarity, claim grounding, and presenter suitability.
- Check presentation plan consistency across scene type, presenter mode, visual focus, asset policy, and asset type hints.
- Validate asset plan semantic fit beyond figure caption token overlap.
- Evaluate required vs optional asset downgrades.
- Reassess after MVP2C-thin produces concrete media artifacts.

## Non-goals

- Do not implement full media generation here.
- Do not replace HARDEN-3 media quality checks.
- Do not redesign Architecture Spec v8.2.

## Recommended Timing

Follow the v8.2 route:

```text
HARDEN-1 → MVP2C-thin → HARDEN-3 → HARDEN-2 reassessment
```

HARDEN-2 should become a full sprint plan once MVP2C-thin and HARDEN-3 provide enough concrete output to judge scene/media mismatch.
