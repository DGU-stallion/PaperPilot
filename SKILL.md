# PaperPilot — Skill Manifest

> **受众**：本文件供配置和安装 PaperPilot 的开发者/用户阅读，提供技能包的版本元数据、安装方式和技术协议。  
> **运行时 agent 行为规范**：见根目录 `AGENTS.md`。

**Version:** 6.0.0a1 (source of truth: `scripts/__init__.__version__`)  
**Type:** Skills package (multi-skill)  
**Protocol:** CLI (`pp`) + JSON over stdout  
**Runtime:** Python ≥ 3.11 (no mandatory external services)

## Skills Included

| Skill | Path | Optional |
|-------|------|----------|
| paperpilot | `AGENTS.md` (root) | No (meta-skill) |
| web-access | `skills/web-access/SKILL.md` | No (base capability) |
| topic-explorer | `skills/topic-explorer/SKILL.md` | No |
| literature-survey | `skills/literature-survey/SKILL.md` | No |
| data-collector | `skills/data-collector/SKILL.md` | No |
| empirical-analysis | `skills/empirical-analysis/SKILL.md` | Yes (requires `pip install paperpilot[standard]`) |
| paper-writer | `skills/paper-writer/SKILL.md` | No |
| integrity-auditor | `skills/integrity-auditor/SKILL.md` | No |

## How to Load

Any coding agent that reads markdown skill files can load PaperPilot:

1. Clone this repository
2. Read `AGENTS.md` (meta-skill + agent behavior rules) — Claude Code users: `CLAUDE.md` imports it automatically
3. The agent becomes a PaperPilot-powered research assistant

## CLI Protocol

```bash
pp doctor --json           # Environment capabilities
pp inspect <dir> --json    # Project state (7 dimensions)
pp workflow plan <skill>   # Plan execution
pp workflow commit <skill> # Commit results
pp workflow verify <skill> # Mark as verified
pp workflow recover        # Restore from last revision
```

## Evidence Status Contract

| Status | Meaning |
|--------|---------|
| planned | Scheduled but not executed |
| user_supplied | Researcher provided (not machine-verified) |
| executed | Code produced this result |
| verified | Passed validation checks |

## Agent Guide Interface

Every skill returns after completion:

```json
{
  "completed": "<skill-name>",
  "artifacts": ["<relative-paths>"],
  "context_written": ["<context-keys>"],
  "next_steps": [{"skill": "...", "reason": "...", "ready": true/false}],
  "warnings": ["..."]
}
```

The meta-skill (paperpilot) uses this to recommend the next action.
