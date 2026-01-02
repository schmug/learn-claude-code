# Learn Claude Code

> **Disclaimer**: This is an independent educational project by [shareAI Lab](https://github.com/shareAI-lab). It is not affiliated with, endorsed by, or sponsored by Anthropic. "Claude Code" is a trademark of Anthropic.

**Learn how modern AI agents work by building one from scratch.**

[中文文档](./README_zh.md)

---

**A note to readers:**

We created this repository out of admiration for Claude Code - **what we believe to be the most capable AI coding agent in the world**. Initially, we attempted to reverse-engineer its design through behavioral observation and speculation. The analysis we published was riddled with inaccuracies, unfounded guesses, and technical errors. We deeply apologize to the Claude Code team and anyone who was misled by that content.

Over the past six months, through building and iterating on real agent systems, our understanding of **"what makes a true AI agent"** has been fundamentally reshaped. We'd like to share these insights with you. All previous speculative content has been removed and replaced with original educational material.

---

> Works with **[Kode CLI](https://github.com/shareAI-lab/Kode)**, **Claude Code**, **Cursor**, and any agent supporting the [Agent Skills Spec](https://github.com/anthropics/agent-skills).

<img height="400" alt="demo" src="https://github.com/user-attachments/assets/0e1e31f8-064f-4908-92ce-121e2eb8d453" />

## What is this?

A progressive tutorial that demystifies AI coding agents like Kode, Claude Code, and Cursor Agent.

**5 versions, ~1100 lines total, each adding one concept:**

| Version | Lines | What it adds | Core insight |
|---------|-------|--------------|--------------|
| [v0](./v0_bash_agent.py) | ~50 | 1 bash tool | Bash is all you need |
| [v1](./v1_basic_agent.py) | ~200 | 4 core tools | Model as Agent |
| [v2](./v2_todo_agent.py) | ~300 | Todo tracking | Explicit planning |
| [v3](./v3_subagent.py) | ~450 | Subagents | Divide and conquer |
| [v4](./v4_skills_agent.py) | ~550 | Skills | Domain expertise on-demand |

## Quick Start

```bash
pip install anthropic python-dotenv

# Configure your API
cp .env.example .env
# Edit .env with your API key

# Run any version
python v0_bash_agent.py  # Minimal
python v1_basic_agent.py # Core agent loop
python v2_todo_agent.py  # + Todo planning
python v3_subagent.py    # + Subagents
python v4_skills_agent.py # + Skills
```

## 🌐 Web UI for Multi-Agent Orchestration

**NEW**: Visual interface for managing and monitoring multiple agents in real-time!

```bash
# Quick start
./start_web_ui.sh        # Linux/Mac
# or
start_web_ui.bat         # Windows

# Then open http://localhost:8000
```

**Features:**
- 🎯 Visual agent management with hierarchy tree
- 📊 Real-time monitoring via WebSocket
- 💬 Live conversation history
- 🛠️ Tool execution logs
- 🌳 Parent-child agent relationships
- 🎨 Modern, responsive UI

See [web_ui/README.md](./web_ui/README.md) for full documentation.

## The Core Pattern

Every coding agent is just this loop:

```python
while True:
    response = model(messages, tools)
    if response.stop_reason != "tool_use":
        return response.text
    results = execute(response.tool_calls)
    messages.append(results)
```

That's it. The model calls tools until done. Everything else is refinement.

## File Structure

```
learn-claude-code/
├── v0_bash_agent.py       # ~50 lines: 1 tool, recursive subagents
├── v0_bash_agent_mini.py  # ~16 lines: extreme compression
├── v1_basic_agent.py      # ~200 lines: 4 tools, core loop
├── v2_todo_agent.py       # ~300 lines: + TodoManager
├── v3_subagent.py         # ~450 lines: + Task tool, agent registry
├── v4_skills_agent.py     # ~550 lines: + Skill tool, SkillLoader
├── web_ui/                # Web interface for multi-agent orchestration
│   ├── server.py          # FastAPI backend with WebSocket support
│   ├── static/            # Frontend (HTML/CSS/JS)
│   └── README.md          # Web UI documentation
├── skills/                # Example skills (for learning)
├── docs/                  # Detailed explanations (EN + ZH)
├── start_web_ui.sh        # Quick start script (Linux/Mac)
└── start_web_ui.bat       # Quick start script (Windows)
```

## Using the Agent Builder Skill

This repository includes a meta-skill that teaches agents how to build agents:

```bash
# Scaffold a new agent project
python skills/agent-builder/scripts/init_agent.py my-agent

# Or with specific complexity level
python skills/agent-builder/scripts/init_agent.py my-agent --level 0  # Minimal
python skills/agent-builder/scripts/init_agent.py my-agent --level 1  # 4 tools (default)
```

### Install Skills for Production Use

```bash
# Kode CLI (recommended)
kode plugins install https://github.com/shareAI-lab/shareAI-skills

# Claude Code
claude plugins install https://github.com/shareAI-lab/shareAI-skills
```

See [shareAI-skills](https://github.com/shareAI-lab/shareAI-skills) for the full collection of production-ready skills.

## Key Concepts

### v0: Bash is All You Need
One tool. Recursive self-calls for subagents. Proves the core is tiny.

### v1: Model as Agent
4 tools (bash, read, write, edit). The complete agent in one function.

### v2: Structured Planning
Todo tool makes plans explicit. Constraints enable complex tasks.

### v3: Subagent Mechanism
Task tool spawns isolated child agents. Context stays clean.

### v4: Skills Mechanism
SKILL.md files provide domain expertise on-demand. Knowledge as a first-class citizen.

## Deep Dives

**Technical tutorials (docs/):**

| English | 中文 |
|---------|------|
| [v0: Bash is All You Need](./docs/v0-bash-is-all-you-need.md) | [v0: Bash 就是一切](./docs/v0-Bash就是一切.md) |
| [v1: Model as Agent](./docs/v1-model-as-agent.md) | [v1: 模型即代理](./docs/v1-模型即代理.md) |
| [v2: Structured Planning](./docs/v2-structured-planning.md) | [v2: 结构化规划](./docs/v2-结构化规划.md) |
| [v3: Subagent Mechanism](./docs/v3-subagent-mechanism.md) | [v3: 子代理机制](./docs/v3-子代理机制.md) |
| [v4: Skills Mechanism](./docs/v4-skills-mechanism.md) | [v4: Skills 机制](./docs/v4-Skills机制.md) |

**Original articles (articles/) - Chinese only, social media style:**
- [v0文章](./articles/v0文章.md) | [v1文章](./articles/v1文章.md) | [v2文章](./articles/v2文章.md) | [v3文章](./articles/v3文章.md) | [v4文章](./articles/v4文章.md)
- [上下文缓存经济学](./articles/上下文缓存经济学.md) - Context Caching Economics for Agent Developers

## Related Projects

| Repository | Purpose |
|------------|---------|
| [Kode](https://github.com/shareAI-lab/Kode) | Full-featured open source agent CLI (production) |
| [shareAI-skills](https://github.com/shareAI-lab/shareAI-skills) | Production-ready skills for AI agents |
| [Agent Skills Spec](https://github.com/anthropics/agent-skills) | Official specification |

### Use as Template

Fork and customize for your own agent projects:

```bash
git clone https://github.com/shareAI-lab/learn-claude-code
cd learn-claude-code
# Start from any version level
cp v1_basic_agent.py my_agent.py
```

## Philosophy

> The model is 80%. Code is 20%.

Modern agents like Kode and Claude Code work not because of clever engineering, but because the model is trained to be an agent. Our job is to give it tools and stay out of the way.

## License

MIT

---

**Model as Agent. That's the whole secret.**

[@baicai003](https://x.com/baicai003)
