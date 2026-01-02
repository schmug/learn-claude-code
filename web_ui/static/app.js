/**
 * Multi-Agent Orchestration UI - Frontend Application
 */

class AgentOrchestrator {
    constructor() {
        this.agents = new Map();
        this.selectedAgentId = null;
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;

        this.initializeWebSocket();
        this.initializeEventListeners();
        this.loadAgents();
    }

    /**
     * Initialize WebSocket connection
     */
    initializeWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;

        try {
            this.ws = new WebSocket(wsUrl);

            this.ws.onopen = () => {
                console.log('WebSocket connected');
                this.updateConnectionStatus(true);
                this.reconnectAttempts = 0;
            };

            this.ws.onmessage = (event) => {
                const message = JSON.parse(event.data);
                this.handleWebSocketMessage(message);
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
            };

            this.ws.onclose = () => {
                console.log('WebSocket disconnected');
                this.updateConnectionStatus(false);
                this.attemptReconnect();
            };
        } catch (error) {
            console.error('Failed to create WebSocket:', error);
            this.updateConnectionStatus(false);
        }
    }

    /**
     * Attempt to reconnect WebSocket
     */
    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`Reconnecting... Attempt ${this.reconnectAttempts}`);
            setTimeout(() => this.initializeWebSocket(), 2000 * this.reconnectAttempts);
        } else {
            console.error('Max reconnection attempts reached');
        }
    }

    /**
     * Handle WebSocket messages
     */
    handleWebSocketMessage(message) {
        const { type, data } = message;

        switch (type) {
            case 'initial_state':
                data.agents.forEach(agent => {
                    this.agents.set(agent.id, agent);
                });
                this.renderAgentTree();
                this.updateAgentCount();
                break;

            case 'agent_created':
                this.agents.set(data.agent.id, data.agent);
                this.renderAgentTree();
                this.updateAgentCount();
                this.updateParentSelect();
                break;

            case 'agent_status':
                if (this.agents.has(data.agent_id)) {
                    const agent = this.agents.get(data.agent_id);
                    agent.status = data.status;
                    this.renderAgentTree();
                    if (this.selectedAgentId === data.agent_id) {
                        this.displayAgentDetails(agent);
                    }
                }
                break;

            case 'agent_message':
                if (this.agents.has(data.agent_id)) {
                    const agent = this.agents.get(data.agent_id);
                    agent.messages.push(data.message);
                    if (this.selectedAgentId === data.agent_id) {
                        this.addMessageToHistory(data.message);
                    }
                }
                break;

            case 'agent_deleted':
                this.agents.delete(data.agent_id);
                if (this.selectedAgentId === data.agent_id) {
                    this.selectedAgentId = null;
                    this.clearAgentDetails();
                }
                this.renderAgentTree();
                this.updateAgentCount();
                this.updateParentSelect();
                break;

            case 'tool_use':
                this.addToolLog('use', data);
                break;

            case 'tool_result':
                this.addToolLog('result', data);
                break;

            default:
                console.log('Unknown message type:', type);
        }
    }

    /**
     * Initialize event listeners
     */
    initializeEventListeners() {
        // Create agent form
        document.getElementById('createAgentForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.createAgent();
        });

        // Refresh button
        document.getElementById('refreshBtn').addEventListener('click', () => {
            this.loadAgents();
        });

        // Agent controls
        document.getElementById('startAgentBtn').addEventListener('click', () => {
            if (this.selectedAgentId) {
                this.startAgent(this.selectedAgentId);
            }
        });

        document.getElementById('stopAgentBtn').addEventListener('click', () => {
            if (this.selectedAgentId) {
                this.stopAgent(this.selectedAgentId);
            }
        });

        document.getElementById('deleteAgentBtn').addEventListener('click', () => {
            if (this.selectedAgentId) {
                if (confirm('Are you sure you want to delete this agent?')) {
                    this.deleteAgent(this.selectedAgentId);
                }
            }
        });
    }

    /**
     * Load agents from API
     */
    async loadAgents() {
        try {
            const response = await fetch('/api/agents');
            const data = await response.json();

            this.agents.clear();
            data.agents.forEach(agent => {
                this.agents.set(agent.id, agent);
            });

            this.renderAgentTree();
            this.updateAgentCount();
            this.updateParentSelect();
        } catch (error) {
            console.error('Failed to load agents:', error);
        }
    }

    /**
     * Create a new agent
     */
    async createAgent() {
        const name = document.getElementById('agentName').value;
        const agentType = document.getElementById('agentType').value;
        const task = document.getElementById('agentTask').value;
        const parentId = document.getElementById('parentAgent').value || null;

        try {
            const response = await fetch('/api/agents', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    name,
                    agent_type: agentType,
                    task,
                    parent_id: parentId,
                }),
            });

            const data = await response.json();

            // Start the agent automatically
            await this.startAgent(data.agent_id);

            // Clear form
            document.getElementById('createAgentForm').reset();

            // Select the new agent
            this.selectAgent(data.agent_id);
        } catch (error) {
            console.error('Failed to create agent:', error);
            alert('Failed to create agent: ' + error.message);
        }
    }

    /**
     * Start an agent
     */
    async startAgent(agentId) {
        try {
            await fetch(`/api/agents/${agentId}/start`, {
                method: 'POST',
            });
        } catch (error) {
            console.error('Failed to start agent:', error);
            alert('Failed to start agent: ' + error.message);
        }
    }

    /**
     * Stop an agent
     */
    async stopAgent(agentId) {
        try {
            await fetch(`/api/agents/${agentId}/stop`, {
                method: 'POST',
            });
        } catch (error) {
            console.error('Failed to stop agent:', error);
            alert('Failed to stop agent: ' + error.message);
        }
    }

    /**
     * Delete an agent
     */
    async deleteAgent(agentId) {
        try {
            await fetch(`/api/agents/${agentId}`, {
                method: 'DELETE',
            });
        } catch (error) {
            console.error('Failed to delete agent:', error);
            alert('Failed to delete agent: ' + error.message);
        }
    }

    /**
     * Render agent tree
     */
    renderAgentTree() {
        const treeContainer = document.getElementById('agentTree');
        treeContainer.innerHTML = '';

        // Get root agents (no parent)
        const rootAgents = Array.from(this.agents.values()).filter(a => !a.parent_id);

        if (rootAgents.length === 0) {
            treeContainer.innerHTML = '<div class="empty-state"><p>No agents yet. Create one to get started!</p></div>';
            return;
        }

        // Render each root agent and its children
        rootAgents.forEach(agent => {
            this.renderAgentNode(agent, treeContainer, false);
        });
    }

    /**
     * Render a single agent node
     */
    renderAgentNode(agent, container, isChild) {
        const node = document.createElement('div');
        node.className = `agent-node ${isChild ? 'child' : ''}`;
        if (this.selectedAgentId === agent.id) {
            node.classList.add('selected');
        }

        node.innerHTML = `
            <div class="agent-node-header">
                <span class="agent-name">${this.escapeHtml(agent.name)}</span>
                <span class="agent-type ${agent.agent_type}">${agent.agent_type}</span>
            </div>
            <div class="agent-status status-${agent.status}">${agent.status}</div>
        `;

        node.addEventListener('click', (e) => {
            e.stopPropagation();
            this.selectAgent(agent.id);
        });

        container.appendChild(node);

        // Render children
        if (agent.children && agent.children.length > 0) {
            agent.children.forEach(childId => {
                const childAgent = this.agents.get(childId);
                if (childAgent) {
                    this.renderAgentNode(childAgent, container, true);
                }
            });
        }
    }

    /**
     * Select an agent
     */
    selectAgent(agentId) {
        this.selectedAgentId = agentId;
        const agent = this.agents.get(agentId);

        if (agent) {
            this.displayAgentDetails(agent);
            this.renderAgentTree(); // Re-render to update selection
        }
    }

    /**
     * Display agent details
     */
    displayAgentDetails(agent) {
        const detailsContainer = document.getElementById('agentDetails');

        detailsContainer.innerHTML = `
            <div class="detail-row">
                <div class="detail-label">Agent ID</div>
                <div class="detail-value">${agent.id}</div>
            </div>
            <div class="detail-row">
                <div class="detail-label">Name</div>
                <div class="detail-value">${this.escapeHtml(agent.name)}</div>
            </div>
            <div class="detail-row">
                <div class="detail-label">Type</div>
                <div class="detail-value">${agent.agent_type}</div>
            </div>
            <div class="detail-row">
                <div class="detail-label">Status</div>
                <div class="detail-value">
                    <span class="agent-status status-${agent.status}">${agent.status}</span>
                </div>
            </div>
            <div class="detail-row">
                <div class="detail-label">Task</div>
                <div class="detail-value">${this.escapeHtml(agent.task)}</div>
            </div>
            <div class="detail-row">
                <div class="detail-label">Tools</div>
                <div class="detail-value">${agent.tools.join(', ')}</div>
            </div>
            <div class="detail-row">
                <div class="detail-label">Created At</div>
                <div class="detail-value">${new Date(agent.created_at).toLocaleString()}</div>
            </div>
            <div class="detail-row">
                <div class="detail-label">Updated At</div>
                <div class="detail-value">${new Date(agent.updated_at).toLocaleString()}</div>
            </div>
        `;

        // Show controls
        document.getElementById('agentControls').style.display = 'flex';

        // Update conversation history
        this.displayConversationHistory(agent);
    }

    /**
     * Display conversation history
     */
    displayConversationHistory(agent) {
        const historyContainer = document.getElementById('conversationHistory');
        historyContainer.innerHTML = '';

        if (agent.messages.length === 0) {
            historyContainer.innerHTML = '<div class="empty-state"><p>No messages yet</p></div>';
            return;
        }

        agent.messages.forEach(message => {
            this.addMessageToHistory(message);
        });

        // Scroll to bottom
        historyContainer.scrollTop = historyContainer.scrollHeight;
    }

    /**
     * Add message to conversation history
     */
    addMessageToHistory(message) {
        const historyContainer = document.getElementById('conversationHistory');

        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${message.role}`;

        messageDiv.innerHTML = `
            <div class="message-role">${message.role}</div>
            <div class="message-content">${this.escapeHtml(message.content)}</div>
            <div class="message-time">${new Date(message.timestamp).toLocaleString()}</div>
        `;

        historyContainer.appendChild(messageDiv);

        // Scroll to bottom
        historyContainer.scrollTop = historyContainer.scrollHeight;
    }

    /**
     * Clear agent details
     */
    clearAgentDetails() {
        document.getElementById('agentDetails').innerHTML = '<div class="empty-state"><p>Select an agent from the tree to view details</p></div>';
        document.getElementById('conversationHistory').innerHTML = '';
        document.getElementById('agentControls').style.display = 'none';
    }

    /**
     * Add tool log entry
     */
    addToolLog(type, data) {
        const logContainer = document.getElementById('toolLog');

        const entry = document.createElement('div');
        entry.className = `tool-entry ${data.error ? 'error' : ''}`;

        const agent = this.agents.get(data.agent_id);
        const agentName = agent ? agent.name : data.agent_id;

        if (type === 'use') {
            entry.innerHTML = `
                <div class="tool-header">[${agentName}] Executing: ${data.tool}</div>
                <div class="tool-input">Input: ${this.escapeHtml(JSON.stringify(data.input, null, 2))}</div>
                <div class="tool-time">${new Date().toLocaleTimeString()}</div>
            `;
        } else {
            entry.innerHTML = `
                <div class="tool-header">[${agentName}] Result: ${data.tool}</div>
                <div class="tool-output">Output: ${this.escapeHtml(data.output)}</div>
                <div class="tool-time">${new Date().toLocaleTimeString()}</div>
            `;
        }

        logContainer.appendChild(entry);

        // Limit log size
        while (logContainer.children.length > 50) {
            logContainer.removeChild(logContainer.firstChild);
        }

        // Scroll to bottom
        logContainer.scrollTop = logContainer.scrollHeight;
    }

    /**
     * Update connection status indicator
     */
    updateConnectionStatus(connected) {
        const statusElement = document.getElementById('connectionStatus');
        if (connected) {
            statusElement.textContent = '🟢 Connected';
        } else {
            statusElement.textContent = '🔴 Disconnected';
        }
    }

    /**
     * Update agent count display
     */
    updateAgentCount() {
        const total = this.agents.size;
        const active = Array.from(this.agents.values()).filter(
            a => a.status === 'running' || a.status === 'waiting'
        ).length;

        document.getElementById('agentCount').textContent = `${total} agent${total !== 1 ? 's' : ''}`;
        document.getElementById('activeAgentCount').textContent = `${active} active`;
    }

    /**
     * Update parent agent select dropdown
     */
    updateParentSelect() {
        const select = document.getElementById('parentAgent');
        const currentValue = select.value;

        // Clear and add default option
        select.innerHTML = '<option value="">None (Root Agent)</option>';

        // Add all agents as options
        Array.from(this.agents.values()).forEach(agent => {
            const option = document.createElement('option');
            option.value = agent.id;
            option.textContent = `${agent.name} (${agent.agent_type})`;
            select.appendChild(option);
        });

        // Restore previous selection if still valid
        if (currentValue && this.agents.has(currentValue)) {
            select.value = currentValue;
        }
    }

    /**
     * Escape HTML to prevent XSS
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize the application when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.orchestrator = new AgentOrchestrator();
});
