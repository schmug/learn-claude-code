# Multi-Agent Orchestration Web UI

A visual interface for managing and monitoring AI agents and subagents in real-time.

## Features

- 🎯 **Visual Agent Management**: Create, monitor, and control multiple agents through an intuitive web interface
- 🌳 **Hierarchy Visualization**: See parent-child relationships between agents in a clear tree structure
- 📊 **Real-time Monitoring**: Live updates via WebSocket for agent status, messages, and tool execution
- 🔧 **Multi-Agent Types**: Support for different agent types (explore, code, plan, custom)
- 💬 **Conversation History**: View complete message history for each agent
- 🛠️ **Tool Execution Log**: Monitor all tool calls and results in real-time
- 🎨 **Modern UI**: Beautiful, responsive interface with gradient backgrounds and smooth animations

## Architecture

### Backend (FastAPI)

The backend server (`server.py`) provides:

- **REST API** for agent CRUD operations
- **WebSocket** for real-time bidirectional communication
- **Agent Orchestration** engine that integrates with existing v3/v4 agent implementations
- **Tool Execution** framework (bash, read_file, write_file, edit_file)
- **State Management** for all active agents and their hierarchies

### Frontend (Vanilla JavaScript)

The frontend (`static/`) includes:

- **AgentOrchestrator** class managing WebSocket connections and UI updates
- **Real-time event handling** for agent lifecycle events
- **Responsive design** that works on desktop and mobile
- **Interactive visualizations** of agent status and relationships

## Installation

### 1. Install Dependencies

```bash
pip install -r ../requirements.txt
```

This will install:
- `fastapi` - Modern web framework
- `uvicorn` - ASGI server
- `websockets` - WebSocket support
- `anthropic` - Claude API client
- `python-dotenv` - Environment configuration
- `pydantic` - Data validation

### 2. Configure Environment

Create a `.env` file in the project root:

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-xxxxx

# Optional - for API switching
ANTHROPIC_BASE_URL=https://api.moonshot.cn/anthropic
MODEL_NAME=kimi-k2-turbo-preview
```

Or use the provided template:

```bash
cp .env.example .env
# Then edit .env with your API key
```

## Usage

### Start the Server

From the `web_ui` directory:

```bash
python server.py
```

Or from the project root:

```bash
python web_ui/server.py
```

The server will start on `http://localhost:8000`

### Access the Web UI

Open your browser and navigate to:

```
http://localhost:8000
```

### Create Your First Agent

1. **Fill in the form** on the left panel:
   - **Agent Name**: Give your agent a descriptive name (e.g., "File Explorer")
   - **Agent Type**: Choose from:
     - `explore` - Read-only exploration (bash, read_file)
     - `code` - Full implementation access (all tools + subagent)
     - `plan` - Design without modifying (bash, read_file)
     - `custom` - Configurable tools
   - **Task**: Describe what you want the agent to do
   - **Parent Agent**: (Optional) Select a parent to create a subagent

2. **Click "Create & Start Agent"**

3. **Monitor Progress** in real-time:
   - Watch status changes in the agent tree
   - View conversation messages
   - See tool execution logs

### Managing Agents

#### View Agent Details

Click on any agent in the tree to see:
- Agent ID and metadata
- Current status
- Assigned tools
- Creation and update timestamps
- Full task description

#### Control Agent Execution

Use the control buttons:
- **▶️ Start**: Begin or resume agent execution
- **⏸️ Stop**: Pause the agent
- **🗑️ Delete**: Remove the agent (with confirmation)

#### Create Subagents

To create a subagent:
1. Select the parent agent in the tree
2. Fill in the form with the subagent details
3. Choose the parent from the dropdown (auto-selected)
4. Create the agent

The subagent will appear indented under its parent in the tree.

## Agent Types Reference

Based on the v3_subagent.py implementation:

| Type | Tools | Description | Use Case |
|------|-------|-------------|----------|
| **explore** | bash, read_file | Read-only exploration | Investigating codebases, gathering information |
| **code** | bash, read_file, write_file, edit_file, subagent | Full implementation | Building features, fixing bugs, making changes |
| **plan** | bash, read_file | Design without modifying | Architecting solutions, reviewing code |
| **custom** | User-defined | Flexible configuration | Special-purpose agents |

## WebSocket Events

The UI receives real-time updates via WebSocket:

### Event Types

- `initial_state` - Full state snapshot on connection
- `agent_created` - New agent was created
- `agent_status` - Agent status changed (created → running → completed)
- `agent_message` - New message in conversation
- `agent_deleted` - Agent was removed
- `tool_use` - Agent is executing a tool
- `tool_result` - Tool execution completed

### Status Lifecycle

```
created → running → waiting → running → ... → completed
          ↓
        stopped
          ↓
        error
```

## API Reference

### REST Endpoints

#### List All Agents
```http
GET /api/agents
```

Response:
```json
{
  "agents": [
    {
      "id": "uuid",
      "name": "Agent Name",
      "agent_type": "explore",
      "status": "running",
      "task": "Task description",
      "parent_id": null,
      "children": [],
      "messages": [],
      "tools": ["bash", "read_file"],
      "created_at": "2025-01-02T10:00:00",
      "updated_at": "2025-01-02T10:00:00"
    }
  ]
}
```

#### Get Agent Details
```http
GET /api/agents/{agent_id}
```

#### Create Agent
```http
POST /api/agents
Content-Type: application/json

{
  "name": "Explorer Agent",
  "agent_type": "explore",
  "task": "Find all Python files in the project",
  "parent_id": null,  // optional
  "tools": null  // optional, defaults to agent type tools
}
```

#### Start Agent
```http
POST /api/agents/{agent_id}/start
```

#### Stop Agent
```http
POST /api/agents/{agent_id}/stop
```

#### Delete Agent
```http
DELETE /api/agents/{agent_id}
```

#### Get Agent Types
```http
GET /api/agent-types
```

### WebSocket Connection

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('Event:', message.type, message.data);
};
```

## Project Structure

```
web_ui/
├── server.py              # FastAPI backend server
├── static/
│   ├── index.html         # Main UI page
│   ├── styles.css         # UI styling
│   └── app.js             # Frontend application logic
└── README.md              # This file
```

## Integration with Existing Agents

The web UI integrates seamlessly with the existing agent implementations:

### v3_subagent.py Integration

The web UI uses the same agent type registry and tool definitions:

```python
AGENT_TYPES_CONFIG = {
    "explore": {"tools": ["bash", "read_file"]},
    "code": {"tools": ["bash", "read_file", "write_file", "edit_file", "subagent"]},
    "plan": {"tools": ["bash", "read_file"]},
}
```

### v4_skills_agent.py Integration

While the current version uses the core v3 architecture, the design supports extension for skills:

- Skills could be added as additional agent types
- The tool registry can be extended to include skill loading
- Future versions could add a "Skills" tab to the UI

## Development

### Running in Development Mode

With auto-reload:

```bash
uvicorn web_ui.server:app --reload --host 0.0.0.0 --port 8000
```

### Testing the API

Using curl:

```bash
# List agents
curl http://localhost:8000/api/agents

# Create agent
curl -X POST http://localhost:8000/api/agents \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Agent",
    "agent_type": "explore",
    "task": "List files in current directory"
  }'

# Start agent
curl -X POST http://localhost:8000/api/agents/{agent_id}/start
```

## Troubleshooting

### WebSocket Connection Failed

- Ensure the server is running
- Check browser console for errors
- Verify no firewall is blocking port 8000

### Agent Not Starting

- Check that your `.env` file has a valid `ANTHROPIC_API_KEY`
- Verify the API key has sufficient credits
- Check server logs for errors

### Tool Execution Errors

- Ensure the working directory has proper permissions
- For bash commands, verify they're valid for your OS
- Check file paths are absolute or relative to the server's working directory

## Security Considerations

⚠️ **Important**: This is a development/educational tool

- No authentication or authorization is implemented
- All WebSocket clients receive all events
- Tool execution has minimal sandboxing
- Not recommended for production use without security enhancements

For production deployment, consider:
- Adding user authentication (JWT, OAuth)
- Implementing per-user agent isolation
- Sandboxing tool execution
- Rate limiting API endpoints
- HTTPS/WSS encryption

## Future Enhancements

Potential improvements:

- [ ] **Persistent Storage**: Database backend for agent history
- [ ] **Agent Templates**: Pre-configured agent patterns
- [ ] **Skills Integration**: v4 skills system in the UI
- [ ] **Metrics Dashboard**: Performance and usage analytics
- [ ] **Multi-user Support**: User accounts and permissions
- [ ] **Agent Cloning**: Duplicate existing agents
- [ ] **Export/Import**: Save and load agent configurations
- [ ] **Graph Visualization**: D3.js tree/graph view
- [ ] **Code Editor**: In-browser editing with syntax highlighting
- [ ] **Chat Interface**: Direct interaction with agents

## License

MIT License - Same as the parent project

## Contributing

This is part of the **learn-claude-code** educational repository. Contributions are welcome!

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Related Projects

- [kode](https://github.com/anthropics/kode) - Full-featured AI coding agent CLI
- [shareAI-skills](https://github.com/shareAI/skills) - Production skills collection
- [Agent Skills Spec](https://github.com/anthropics/agent-skills-spec) - Skills specification

## Support

For issues or questions:
- Open an issue on GitHub
- Check the main project README
- Review the documentation in `/docs`

---

**Built with ❤️ for the Claude Code community**
