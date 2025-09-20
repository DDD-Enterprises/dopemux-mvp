#!/usr/bin/env node

/**
 * Leantime MCP Server for Dopemux
 *
 * This MCP server provides a bridge to Leantime project management
 * with ADHD-optimized task management and context preservation.
 */

const { spawn } = require('child_process');
const fs = require('fs').promises;
const path = require('path');

class LeantimeMCPServer {
    constructor() {
        this.version = "1.0.0";
        this.capabilities = {
            tools: {
                "leantime-get-tasks": {
                    description: "Get tasks from Leantime with ADHD filtering options",
                    inputSchema: {
                        type: "object",
                        properties: {
                            project_id: { type: "number", description: "Project ID to filter tasks" },
                            status: { type: "string", description: "Task status filter" },
                            priority: { type: "string", description: "Priority level (hyperfocus, focused, scattered, background)" },
                            adhd_mode: { type: "boolean", description: "Enable ADHD-optimized filtering", default: true }
                        }
                    }
                },
                "leantime-create-task": {
                    description: "Create a new task in Leantime with ADHD optimizations",
                    inputSchema: {
                        type: "object",
                        properties: {
                            headline: { type: "string", description: "Task title" },
                            description: { type: "string", description: "Task description" },
                            project_id: { type: "number", description: "Project ID" },
                            priority: { type: "string", description: "Priority level", enum: ["hyperfocus", "focused", "scattered", "background"] },
                            cognitive_load: { type: "number", description: "Cognitive load (1-10)", minimum: 1, maximum: 10 },
                            estimated_hours: { type: "number", description: "Estimated hours" },
                            break_frequency: { type: "number", description: "Minutes between breaks" }
                        },
                        required: ["headline", "project_id"]
                    }
                },
                "leantime-update-task": {
                    description: "Update an existing task with ADHD considerations",
                    inputSchema: {
                        type: "object",
                        properties: {
                            task_id: { type: "number", description: "Task ID to update" },
                            status: { type: "string", description: "New status" },
                            priority: { type: "string", description: "New priority level" },
                            actual_hours: { type: "number", description: "Actual hours worked" },
                            notes: { type: "string", description: "Update notes" }
                        },
                        required: ["task_id"]
                    }
                },
                "leantime-get-projects": {
                    description: "Get projects from Leantime",
                    inputSchema: {
                        type: "object",
                        properties: {
                            state: { type: "string", description: "Project state filter" },
                            adhd_enabled_only: { type: "boolean", description: "Show only ADHD-enabled projects", default: false }
                        }
                    }
                },
                "leantime-track-time": {
                    description: "Track time spent on a task with ADHD break reminders",
                    inputSchema: {
                        type: "object",
                        properties: {
                            task_id: { type: "number", description: "Task ID" },
                            hours: { type: "number", description: "Hours to track" },
                            break_taken: { type: "boolean", description: "Whether breaks were taken", default: false },
                            attention_quality: { type: "string", description: "Quality of attention", enum: ["hyperfocus", "focused", "scattered", "distracted"] }
                        },
                        required: ["task_id", "hours"]
                    }
                }
            },
            resources: {
                "leantime-health": {
                    description: "Leantime server health and connection status",
                    mimeType: "application/json"
                },
                "leantime-adhd-metrics": {
                    description: "ADHD-specific productivity metrics from Leantime",
                    mimeType: "application/json"
                }
            }
        };

        this.pythonBridgePath = path.join(__dirname, 'leantime_bridge.py');
        this.isConnected = false;
    }

    async initialize(request) {
        try {
            // Verify environment variables
            const requiredEnvVars = ['LEANTIME_API_URL', 'LEANTIME_API_TOKEN'];
            const missingVars = requiredEnvVars.filter(varName => !process.env[varName]);

            if (missingVars.length > 0) {
                throw new Error(`Missing required environment variables: ${missingVars.join(', ')}`);
            }

            // Test connection to Leantime
            const healthCheck = await this.callPythonBridge('health_check', {});

            if (healthCheck.success) {
                this.isConnected = true;
                return {
                    protocolVersion: "2024-11-05",
                    capabilities: this.capabilities,
                    serverInfo: {
                        name: "leantime-mcp",
                        version: this.version
                    }
                };
            } else {
                throw new Error(`Leantime connection failed: ${healthCheck.error}`);
            }
        } catch (error) {
            console.error('Failed to initialize Leantime MCP server:', error);
            throw error;
        }
    }

    async callTool(request) {
        const { name, arguments: args } = request.params;

        try {
            switch (name) {
                case 'leantime-get-tasks':
                    return await this.getTasks(args);
                case 'leantime-create-task':
                    return await this.createTask(args);
                case 'leantime-update-task':
                    return await this.updateTask(args);
                case 'leantime-get-projects':
                    return await this.getProjects(args);
                case 'leantime-track-time':
                    return await this.trackTime(args);
                default:
                    throw new Error(`Unknown tool: ${name}`);
            }
        } catch (error) {
            return {
                content: [{
                    type: "text",
                    text: `Error calling ${name}: ${error.message}`
                }],
                isError: true
            };
        }
    }

    async getResource(request) {
        const { uri } = request.params;

        try {
            switch (uri) {
                case 'leantime-health':
                    const health = await this.callPythonBridge('health_check', {});
                    return {
                        contents: [{
                            uri: uri,
                            mimeType: "application/json",
                            text: JSON.stringify(health, null, 2)
                        }]
                    };
                case 'leantime-adhd-metrics':
                    const metrics = await this.callPythonBridge('get_adhd_metrics', {});
                    return {
                        contents: [{
                            uri: uri,
                            mimeType: "application/json",
                            text: JSON.stringify(metrics, null, 2)
                        }]
                    };
                default:
                    throw new Error(`Unknown resource: ${uri}`);
            }
        } catch (error) {
            throw new Error(`Error getting resource ${uri}: ${error.message}`);
        }
    }

    async getTasks(args) {
        const result = await this.callPythonBridge('get_tasks', args);
        return {
            content: [{
                type: "text",
                text: `Found ${result.tasks.length} tasks:\n\n${this.formatTasks(result.tasks)}`
            }]
        };
    }

    async createTask(args) {
        const result = await this.callPythonBridge('create_task', args);
        return {
            content: [{
                type: "text",
                text: `✅ Created task "${args.headline}" with ID ${result.task_id}\n\nADHD Optimizations Applied:\n- Cognitive load: ${args.cognitive_load || 'Auto-detected'}\n- Break frequency: ${args.break_frequency || 25} minutes\n- Priority: ${args.priority || 'focused'}`
            }]
        };
    }

    async updateTask(args) {
        const result = await this.callPythonBridge('update_task', args);
        return {
            content: [{
                type: "text",
                text: `🔄 Updated task ${args.task_id}\n\nChanges:\n${this.formatTaskUpdate(args)}`
            }]
        };
    }

    async getProjects(args) {
        const result = await this.callPythonBridge('get_projects', args);
        return {
            content: [{
                type: "text",
                text: `Found ${result.projects.length} projects:\n\n${this.formatProjects(result.projects)}`
            }]
        };
    }

    async trackTime(args) {
        const result = await this.callPythonBridge('track_time', args);
        return {
            content: [{
                type: "text",
                text: `⏰ Tracked ${args.hours} hours on task ${args.task_id}\n\nAttention Quality: ${args.attention_quality}\nBreaks Taken: ${args.break_taken ? 'Yes ✅' : 'No ⚠️'}\n\n${result.recommendations || ''}`
            }]
        };
    }

    async callPythonBridge(method, params) {
        return new Promise((resolve, reject) => {
            const python = spawn('python3', ['-c', `
import sys
import json
import asyncio
sys.path.append('${path.dirname(this.pythonBridgePath)}')

from leantime_bridge import LeantimeMCPClient
from dopemux.core.config import Config

async def main():
    config = Config()
    async with LeantimeMCPClient(config) as client:
        result = await client.${method}(${JSON.stringify(params)})
        print(json.dumps(result))

asyncio.run(main())
            `]);

            let output = '';
            let errorOutput = '';

            python.stdout.on('data', (data) => {
                output += data.toString();
            });

            python.stderr.on('data', (data) => {
                errorOutput += data.toString();
            });

            python.on('close', (code) => {
                if (code === 0) {
                    try {
                        const result = JSON.parse(output);
                        resolve(result);
                    } catch (e) {
                        reject(new Error(`Failed to parse Python output: ${e.message}`));
                    }
                } else {
                    reject(new Error(`Python bridge failed: ${errorOutput}`));
                }
            });
        });
    }

    formatTasks(tasks) {
        return tasks.map(task => {
            const cognitiveInfo = task.cognitive_load ? ` (Cognitive Load: ${task.cognitive_load}/10)` : '';
            const adhdInfo = task.attention_requirement ? ` [${task.attention_requirement.toUpperCase()}]` : '';
            return `• ${task.headline}${adhdInfo}${cognitiveInfo}\n  Status: ${task.status} | Priority: ${task.priority}\n  Estimated: ${task.estimated_hours || 'TBD'} hours`;
        }).join('\n\n');
    }

    formatProjects(projects) {
        return projects.map(project => {
            const adhdMode = project.adhd_mode_enabled ? ' 🧠 ADHD-Optimized' : '';
            return `• ${project.name}${adhdMode}\n  ${project.description}\n  State: ${project.state}`;
        }).join('\n\n');
    }

    formatTaskUpdate(args) {
        const changes = [];
        if (args.status) changes.push(`Status: ${args.status}`);
        if (args.priority) changes.push(`Priority: ${args.priority}`);
        if (args.actual_hours) changes.push(`Actual hours: ${args.actual_hours}`);
        if (args.notes) changes.push(`Notes: ${args.notes}`);
        return changes.join('\n');
    }
}

// MCP Server Protocol Handler
class MCPHandler {
    constructor() {
        this.server = new LeantimeMCPServer();
    }

    async handleRequest(request) {
        try {
            switch (request.method) {
                case 'initialize':
                    return await this.server.initialize(request);
                case 'tools/call':
                    return await this.server.callTool(request);
                case 'resources/read':
                    return await this.server.getResource(request);
                case 'tools/list':
                    return { tools: Object.keys(this.server.capabilities.tools).map(name => ({
                        name,
                        description: this.server.capabilities.tools[name].description,
                        inputSchema: this.server.capabilities.tools[name].inputSchema
                    }))};
                case 'resources/list':
                    return { resources: Object.keys(this.server.capabilities.resources).map(name => ({
                        uri: name,
                        description: this.server.capabilities.resources[name].description,
                        mimeType: this.server.capabilities.resources[name].mimeType
                    }))};
                default:
                    throw new Error(`Unknown method: ${request.method}`);
            }
        } catch (error) {
            return {
                error: {
                    code: -32603,
                    message: error.message
                }
            };
        }
    }
}

// Main execution
if (require.main === module) {
    const handler = new MCPHandler();

    process.stdin.setEncoding('utf8');
    process.stdin.on('readable', async () => {
        const chunk = process.stdin.read();
        if (chunk !== null) {
            try {
                const request = JSON.parse(chunk.trim());
                const response = await handler.handleRequest(request);

                const jsonResponse = {
                    jsonrpc: "2.0",
                    id: request.id,
                    ...response
                };

                console.log(JSON.stringify(jsonResponse));
            } catch (error) {
                console.error('Error processing request:', error);
                const errorResponse = {
                    jsonrpc: "2.0",
                    id: request?.id || null,
                    error: {
                        code: -32700,
                        message: 'Parse error'
                    }
                };
                console.log(JSON.stringify(errorResponse));
            }
        }
    });

    process.stdin.on('end', () => {
        process.exit(0);
    });

    // Handle graceful shutdown
    process.on('SIGINT', () => {
        console.error('Received SIGINT, shutting down gracefully...');
        process.exit(0);
    });

    process.on('SIGTERM', () => {
        console.error('Received SIGTERM, shutting down gracefully...');
        process.exit(0);
    });
}

module.exports = { LeantimeMCPServer, MCPHandler };