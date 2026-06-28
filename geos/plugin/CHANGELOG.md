# Changelog

## 0.2.0 (2026-04-21)

- Add `hooks/verify_outputs.py` Stop hook that blocks `end_turn` when
  `/workspace/inputs/` has no `*.xml` files or any XML fails to parse. Gives
  the agent a forced second chance instead of silently terminating on the
  minimax-on-OpenRouter empty-completion failure. See `docs/XN-010`.
- Hook knobs: `GEOS_HOOK_DISABLE`, `GEOS_HOOK_MAX_RETRIES` (default 2),
  `GEOS_HOOK_INPUTS_DIR`, `GEOS_HOOK_SELF_REFLECT` (optional intrinsic-review
  pass, off by default).

## 0.1.0

- Add initial Claude Code plugin scaffold.
- Add `plugin-maintainer` starter skill.
