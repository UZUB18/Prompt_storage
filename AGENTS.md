<!--
AGENTS.md (repo-level instructions for Codex)

Goal: Make Codex consistently follow the user's preferred "strong reasoner & planner" workflow.
-->

# Codex Operating Instructions (Repo Default)

## Always follow the reasoning protocol

Before taking **any** action (tool call, code change, or user-facing response), follow the protocol in:

- `references/reasoning_protocol.md`

**Do not** paste or “think out loud” the entire protocol in responses. Apply it internally, and only surface:
- a brief plan (when helpful),
- concrete assumptions **only** when ambiguity is high-impact (per the protocol),
- precise, grounded outputs (paths, commands, exact error text).

## Skills

A skill is a set of local instructions stored in a `SKILL.md` file.

### Available skills (in this repo)
- deepmind: Enforces the strict planning/reasoning protocol and the “assumptions only when high-impact” communication style. (file: skills/public/deepmind/SKILL.md)

### How to use skills (trigger rules)
- If the user names a skill (with `$SkillName` or plain text) OR the task clearly matches a skill's description, use that skill for that turn.
- Multiple mentions mean use them all. Do not carry skills across turns unless re-mentioned.
