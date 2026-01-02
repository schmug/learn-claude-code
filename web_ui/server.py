"""
Multi-Agent Orchestration Web UI Server

FastAPI-based server providing REST API and WebSocket support
for managing and monitoring AI agents and subagents.
"""

import asyncio
import json
import os
import sys
import uuid
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import anthropic
from dotenv import load_dotenv

# Add parent directory to path to import agent modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

app = FastAPI(title="Multi-Agent Orchestration UI")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Models
class AgentType(str, Enum):
    EXPLORE = "explore"
    CODE = "code"
    PLAN = "plan"
    CUSTOM = "custom"


class AgentStatus(str, Enum):
    CREATED = "created"
    RUNNING = "running"
    WAITING = "waiting"
    COMPLETED = "completed"
    ERROR = "error"
    STOPPED = "stopped"


class CreateAgentRequest(BaseModel):
    name: str
    agent_type: AgentType
    task: str
    parent_id: Optional[str] = None
    tools: Optional[List[str]] = None


class AgentMessage(BaseModel):
    role: str
    content: str
    timestamp: str


class Agent(BaseModel):
    id: str
    name: str
    agent_type: AgentType
    task: str
    status: AgentStatus
    parent_id: Optional[str]
    children: List[str]
    messages: List[AgentMessage]
    created_at: str
    updated_at: str
    tools: List[str]


# Agent Registry based on v3_subagent.py
AGENT_TYPES_CONFIG = {
    "explore": {
        "tools": ["bash", "read_file"],
        "description": "Read-only exploration agent"
    },
    "code": {
        "tools": ["bash", "read_file", "write_file", "edit_file", "subagent"],
        "description": "Full implementation access agent"
    },
    "plan": {
        "tools": ["bash", "read_file"],
        "description": "Design agent without modifying capabilities"
    },
    "custom": {
        "tools": ["bash", "read_file", "write_file", "edit_file"],
        "description": "Custom agent with configurable tools"
    }
}


# In-memory storage (in production, use a database)
agents: Dict[str, Agent] = {}
active_tasks: Dict[str, asyncio.Task] = {}


# WebSocket Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass


manager = ConnectionManager()


# Tool implementations (simplified for web UI)
async def execute_bash(command: str, agent_id: str) -> str:
    """Execute bash command"""
    await broadcast_event("tool_use", {
        "agent_id": agent_id,
        "tool": "bash",
        "input": command
    })

    try:
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        result = stdout.decode() if stdout else stderr.decode()

        await broadcast_event("tool_result", {
            "agent_id": agent_id,
            "tool": "bash",
            "output": result[:1000]  # Limit output
        })

        return result
    except Exception as e:
        error = f"Error executing command: {str(e)}"
        await broadcast_event("tool_result", {
            "agent_id": agent_id,
            "tool": "bash",
            "output": error,
            "error": True
        })
        return error


async def read_file(file_path: str, agent_id: str) -> str:
    """Read file contents"""
    await broadcast_event("tool_use", {
        "agent_id": agent_id,
        "tool": "read_file",
        "input": file_path
    })

    try:
        with open(file_path, 'r') as f:
            content = f.read()

        await broadcast_event("tool_result", {
            "agent_id": agent_id,
            "tool": "read_file",
            "output": f"Read {len(content)} characters from {file_path}"
        })

        return content
    except Exception as e:
        error = f"Error reading file: {str(e)}"
        await broadcast_event("tool_result", {
            "agent_id": agent_id,
            "tool": "read_file",
            "output": error,
            "error": True
        })
        return error


async def write_file(file_path: str, content: str, agent_id: str) -> str:
    """Write file contents"""
    await broadcast_event("tool_use", {
        "agent_id": agent_id,
        "tool": "write_file",
        "input": {"path": file_path, "content": content[:100] + "..."}
    })

    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w') as f:
            f.write(content)

        result = f"Successfully wrote {len(content)} characters to {file_path}"
        await broadcast_event("tool_result", {
            "agent_id": agent_id,
            "tool": "write_file",
            "output": result
        })

        return result
    except Exception as e:
        error = f"Error writing file: {str(e)}"
        await broadcast_event("tool_result", {
            "agent_id": agent_id,
            "tool": "write_file",
            "output": error,
            "error": True
        })
        return error


# Tool registry
TOOLS = {
    "bash": {
        "name": "bash",
        "description": "Execute bash commands",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Bash command to execute"}
            },
            "required": ["command"]
        }
    },
    "read_file": {
        "name": "read_file",
        "description": "Read file contents",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Path to file"}
            },
            "required": ["file_path"]
        }
    },
    "write_file": {
        "name": "write_file",
        "description": "Write content to a file",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Path to file"},
                "content": {"type": "string", "description": "Content to write"}
            },
            "required": ["file_path", "content"]
        }
    },
    "edit_file": {
        "name": "edit_file",
        "description": "Edit file by replacing old string with new string",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string"},
                "old_string": {"type": "string"},
                "new_string": {"type": "string"}
            },
            "required": ["file_path", "old_string", "new_string"]
        }
    }
}


async def broadcast_event(event_type: str, data: dict):
    """Broadcast event to all WebSocket clients"""
    await manager.broadcast({
        "type": event_type,
        "data": data,
        "timestamp": datetime.utcnow().isoformat()
    })


async def run_agent(agent_id: str):
    """Run an agent with its task"""
    agent = agents[agent_id]

    try:
        # Update status
        agent.status = AgentStatus.RUNNING
        await broadcast_event("agent_status", {
            "agent_id": agent_id,
            "status": agent.status
        })

        # Initialize Claude client
        client = anthropic.Anthropic(
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            base_url=os.getenv("ANTHROPIC_BASE_URL")
        )

        model_name = os.getenv("MODEL_NAME", "claude-sonnet-4-20250514")

        # Build tools list
        available_tools = [TOOLS[tool] for tool in agent.tools if tool in TOOLS]

        # Initialize conversation
        messages = [
            {
                "role": "user",
                "content": agent.task
            }
        ]

        agent.messages.append(AgentMessage(
            role="user",
            content=agent.task,
            timestamp=datetime.utcnow().isoformat()
        ))

        await broadcast_event("agent_message", {
            "agent_id": agent_id,
            "message": {
                "role": "user",
                "content": agent.task
            }
        })

        # Agent loop
        max_iterations = 25
        for iteration in range(max_iterations):
            if agent.status == AgentStatus.STOPPED:
                break

            agent.status = AgentStatus.RUNNING

            # Call Claude API
            response = client.messages.create(
                model=model_name,
                max_tokens=4096,
                messages=messages,
                tools=available_tools if available_tools else anthropic.NOT_GIVEN
            )

            # Add assistant message
            assistant_content = []
            for block in response.content:
                if block.type == "text":
                    assistant_content.append(block.text)
                    agent.messages.append(AgentMessage(
                        role="assistant",
                        content=block.text,
                        timestamp=datetime.utcnow().isoformat()
                    ))
                    await broadcast_event("agent_message", {
                        "agent_id": agent_id,
                        "message": {
                            "role": "assistant",
                            "content": block.text
                        }
                    })

            # Check if done
            if response.stop_reason == "end_turn":
                agent.status = AgentStatus.COMPLETED
                await broadcast_event("agent_status", {
                    "agent_id": agent_id,
                    "status": agent.status
                })
                break

            # Execute tools
            if response.stop_reason == "tool_use":
                agent.status = AgentStatus.WAITING

                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        tool_name = block.name
                        tool_input = block.input

                        # Execute tool
                        result = ""
                        if tool_name == "bash" and "command" in tool_input:
                            result = await execute_bash(tool_input["command"], agent_id)
                        elif tool_name == "read_file" and "file_path" in tool_input:
                            result = await read_file(tool_input["file_path"], agent_id)
                        elif tool_name == "write_file":
                            result = await write_file(
                                tool_input["file_path"],
                                tool_input["content"],
                                agent_id
                            )
                        else:
                            result = f"Tool {tool_name} not implemented in web UI"

                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result
                        })

                # Add to messages
                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": tool_results})

        if iteration >= max_iterations - 1:
            agent.status = AgentStatus.ERROR
            await broadcast_event("agent_status", {
                "agent_id": agent_id,
                "status": agent.status,
                "error": "Max iterations reached"
            })

    except Exception as e:
        agent.status = AgentStatus.ERROR
        await broadcast_event("agent_status", {
            "agent_id": agent_id,
            "status": agent.status,
            "error": str(e)
        })

    finally:
        agent.updated_at = datetime.utcnow().isoformat()
        if agent_id in active_tasks:
            del active_tasks[agent_id]


# REST API Endpoints

@app.get("/")
async def root():
    """Serve the main UI"""
    return FileResponse("web_ui/static/index.html")


@app.get("/api/agents")
async def list_agents():
    """List all agents"""
    return {"agents": list(agents.values())}


@app.get("/api/agents/{agent_id}")
async def get_agent(agent_id: str):
    """Get agent details"""
    if agent_id not in agents:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agents[agent_id]


@app.post("/api/agents")
async def create_agent(request: CreateAgentRequest):
    """Create a new agent"""
    agent_id = str(uuid.uuid4())

    # Determine tools
    if request.tools:
        tools = request.tools
    else:
        tools = AGENT_TYPES_CONFIG[request.agent_type]["tools"]

    agent = Agent(
        id=agent_id,
        name=request.name,
        agent_type=request.agent_type,
        task=request.task,
        status=AgentStatus.CREATED,
        parent_id=request.parent_id,
        children=[],
        messages=[],
        created_at=datetime.utcnow().isoformat(),
        updated_at=datetime.utcnow().isoformat(),
        tools=tools
    )

    agents[agent_id] = agent

    # Update parent if exists
    if request.parent_id and request.parent_id in agents:
        agents[request.parent_id].children.append(agent_id)

    await broadcast_event("agent_created", {
        "agent": agent.dict()
    })

    return {"agent_id": agent_id, "agent": agent}


@app.post("/api/agents/{agent_id}/start")
async def start_agent(agent_id: str):
    """Start an agent"""
    if agent_id not in agents:
        raise HTTPException(status_code=404, detail="Agent not found")

    if agent_id in active_tasks:
        raise HTTPException(status_code=400, detail="Agent already running")

    # Create and store task
    task = asyncio.create_task(run_agent(agent_id))
    active_tasks[agent_id] = task

    return {"status": "started", "agent_id": agent_id}


@app.post("/api/agents/{agent_id}/stop")
async def stop_agent(agent_id: str):
    """Stop an agent"""
    if agent_id not in agents:
        raise HTTPException(status_code=404, detail="Agent not found")

    agent = agents[agent_id]
    agent.status = AgentStatus.STOPPED

    if agent_id in active_tasks:
        active_tasks[agent_id].cancel()
        del active_tasks[agent_id]

    await broadcast_event("agent_status", {
        "agent_id": agent_id,
        "status": agent.status
    })

    return {"status": "stopped", "agent_id": agent_id}


@app.delete("/api/agents/{agent_id}")
async def delete_agent(agent_id: str):
    """Delete an agent"""
    if agent_id not in agents:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Stop if running
    if agent_id in active_tasks:
        await stop_agent(agent_id)

    # Remove from parent
    agent = agents[agent_id]
    if agent.parent_id and agent.parent_id in agents:
        agents[agent.parent_id].children.remove(agent_id)

    # Delete agent
    del agents[agent_id]

    await broadcast_event("agent_deleted", {
        "agent_id": agent_id
    })

    return {"status": "deleted", "agent_id": agent_id}


@app.get("/api/agent-types")
async def get_agent_types():
    """Get available agent types"""
    return AGENT_TYPES_CONFIG


# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket connection for real-time updates"""
    await manager.connect(websocket)

    try:
        # Send current state
        await websocket.send_json({
            "type": "initial_state",
            "data": {
                "agents": [agent.dict() for agent in agents.values()]
            }
        })

        # Keep connection alive
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# Mount static files
app.mount("/static", StaticFiles(directory="web_ui/static"), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
