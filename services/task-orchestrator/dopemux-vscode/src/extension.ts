import * as vscode from 'vscode';
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

let hooksEnabled = true;
let disposables: vscode.Disposable[] = [];

export function activate(context: vscode.ExtensionContext) {
    console.log('Dopemux extension is now active!');

    // Initialize hooks
    initializeHooks(context);

    // Register commands
    context.subscriptions.push(
        vscode.commands.registerCommand('dopemux.enableHooks', () => {
            hooksEnabled = true;
            vscode.window.showInformationMessage('Dopemux hooks enabled');
            initializeHooks(context);
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('dopemux.disableHooks', () => {
            hooksEnabled = false;
            vscode.window.showInformationMessage('Dopemux hooks disabled');
            disposeHooks();
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('dopemux.showStatus', () => {
            const status = hooksEnabled ? 'enabled' : 'disabled';
            vscode.window.showInformationMessage(`Dopemux hooks are ${status}`);
        })
    );
}

export function deactivate() {
    disposeHooks();
}

function initializeHooks(context: vscode.ExtensionContext) {
    disposeHooks(); // Clean up any existing hooks

    if (!hooksEnabled) {
        return;
    }

    const config = vscode.workspace.getConfiguration('dopemux');
    const hooksEnabled = config.get('hooks.enabled', true);
    const saveEnabled = config.get('hooks.save.enabled', true);
    const terminalEnabled = config.get('hooks.terminal.enabled', true);
    const quiet = config.get('hooks.quiet', true);

    if (!hooksEnabled) {
        return;
    }

    // File save hook - LOW RISK, HIGH VALUE
    if (saveEnabled) {
        const saveDisposable = vscode.workspace.onDidSaveTextDocument(async (document) => {
            try {
                // Non-blocking execution - fire and forget
                triggerDopemuxHook('save', {
                    file: document.fileName,
                    language: document.languageId
                }, quiet);
            } catch (error) {
                // Silent failure - never block user workflow
                console.warn('Dopemux save hook failed:', error);
            }
        });
        disposables.push(saveDisposable);
        context.subscriptions.push(saveDisposable);
    }

    // Terminal open hook - MEDIUM RISK, MEDIUM VALUE
    if (terminalEnabled) {
        const terminalDisposable = vscode.window.onDidOpenTerminal(async (terminal) => {
            try {
                // Non-blocking execution
                triggerDopemuxHook('terminal-open', {
                    name: terminal.name,
                    shell: terminal.shellPath
                }, quiet);
            } catch (error) {
                // Silent failure
                console.warn('Dopemux terminal hook failed:', error);
            }
        });
        disposables.push(terminalDisposable);
        context.subscriptions.push(terminalDisposable);
    }
}

function disposeHooks() {
    disposables.forEach(disposable => disposable.dispose());
    disposables = [];
}

async function triggerDopemuxHook(eventType: string, context: any, quiet: boolean = true): Promise<void> {
    try {
        // Find dopemux executable
        const dopemuxPath = await findDopemuxExecutable();

        if (!dopemuxPath) {
            if (!quiet) {
                console.warn('Dopemux executable not found in PATH');
            }
            return;
        }

        // Build command with timeout and background execution
        const args = [
            'trigger',
            eventType,
            '--context', JSON.stringify(context),
            '--async' // Flag for background processing
        ];

        if (quiet) {
            args.push('--quiet');
        }

        const command = `${dopemuxPath} ${args.join(' ')}`;

        // Execute asynchronously with timeout
        const timeoutMs = 100; // Strict timeout to prevent blocking

        try {
            await Promise.race([
                execAsync(command),
                new Promise((_, reject) =>
                    setTimeout(() => reject(new Error('Timeout')), timeoutMs)
                )
            ]);

            if (!quiet) {
                console.log(`Dopemux ${eventType} hook triggered successfully`);
            }
        } catch (error) {
            // Silent failure - hook should never block user workflow
            if (!quiet) {
                console.warn(`Dopemux ${eventType} hook timed out or failed:`, error);
            }
        }

    } catch (error) {
        // Ultimate safety net - never let hook errors affect VS Code
        console.warn(`Dopemux hook system error for ${eventType}:`, error);
    }
}

async function findDopemuxExecutable(): Promise<string | null> {
    try {
        // Check if dopemux is in PATH
        await execAsync('which dopemux');
        return 'dopemux';
    } catch {
        try {
            // Try common locations
            const candidates = [
                '/usr/local/bin/dopemux',
                '/usr/bin/dopemux',
                '/opt/homebrew/bin/dopemux',
                process.env.HOME + '/.local/bin/dopemux'
            ];

            for (const candidate of candidates) {
                try {
                    await execAsync(`test -x ${candidate}`);
                    return candidate;
                } catch {
                    continue;
                }
            }
        } catch {
            // Silent failure
        }
    }
    return null;
}