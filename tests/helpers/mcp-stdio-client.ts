/**
 * Minimal JSON-RPC 2.0 client that drives the built server over stdio.
 *
 * The server is an MCP stdio server, so stdout carries the JSON-RPC stream and
 * nothing else. Anything non-JSON on stdout is a protocol violation, which is
 * why this client records unparseable lines instead of ignoring them - the
 * contract test asserts the list stays empty. Diagnostics belong on stderr.
 */

import { spawn, type ChildProcessWithoutNullStreams } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import { existsSync } from 'node:fs';

const HERE = path.dirname(fileURLToPath(import.meta.url));
export const REPO_ROOT = path.resolve(HERE, '..', '..');
const SERVER_ENTRY = path.join(REPO_ROOT, 'build', 'index.js');

/** Protocol version this suite negotiates with the server. */
export const PROTOCOL_VERSION = '2025-06-18';

const DEFAULT_TIMEOUT_MS = 20_000;

export interface JsonRpcResponse {
  jsonrpc: '2.0';
  id: number;
  result?: unknown;
  error?: { code: number; message: string };
}

interface Pending {
  resolve: (value: JsonRpcResponse) => void;
  reject: (reason: Error) => void;
  timer: NodeJS.Timeout;
}

export class McpStdioClient {
  private child: ChildProcessWithoutNullStreams;
  private nextId = 1;
  private pending = new Map<number, Pending>();
  private stdoutBuffer = '';

  /** Lines seen on stdout that did not parse as JSON. Must stay empty. */
  public readonly nonJsonStdoutLines: string[] = [];
  /** Everything the server wrote to stderr, for diagnostics on failure. */
  public stderr = '';

  private constructor() {
    if (!existsSync(SERVER_ENTRY)) {
      throw new Error(
        `Built server not found at ${SERVER_ENTRY}. Run "npm run build" before the tests.`
      );
    }

    this.child = spawn(process.execPath, [SERVER_ENTRY], {
      cwd: REPO_ROOT,
      stdio: ['pipe', 'pipe', 'pipe'],
      // Keep the run hermetic: no API key, no ambient log level.
      env: { ...process.env, FDA_API_KEY: '', LOG_LEVEL: 'error' }
    });

    this.child.stdout.setEncoding('utf8');
    this.child.stderr.setEncoding('utf8');
    this.child.stdout.on('data', (chunk: string) => this.consumeStdout(chunk));
    this.child.stderr.on('data', (chunk: string) => {
      this.stderr += chunk;
    });
    this.child.on('exit', (code, signal) => {
      const err = new Error(
        `Server exited early (code=${code}, signal=${signal}). stderr:\n${this.stderr}`
      );
      for (const [, p] of this.pending) {
        clearTimeout(p.timer);
        p.reject(err);
      }
      this.pending.clear();
    });
  }

  private consumeStdout(chunk: string): void {
    this.stdoutBuffer += chunk;

    let newlineAt = this.stdoutBuffer.indexOf('\n');
    while (newlineAt !== -1) {
      const line = this.stdoutBuffer.slice(0, newlineAt).trim();
      this.stdoutBuffer = this.stdoutBuffer.slice(newlineAt + 1);
      newlineAt = this.stdoutBuffer.indexOf('\n');

      if (line.length === 0) {
        continue;
      }

      let parsed: JsonRpcResponse;
      try {
        parsed = JSON.parse(line) as JsonRpcResponse;
      } catch {
        this.nonJsonStdoutLines.push(line);
        continue;
      }

      const waiter = typeof parsed.id === 'number' ? this.pending.get(parsed.id) : undefined;
      if (waiter) {
        clearTimeout(waiter.timer);
        this.pending.delete(parsed.id);
        waiter.resolve(parsed);
      }
    }
  }

  /** Send a request and wait for the matching response. */
  public request(
    method: string,
    params: Record<string, unknown> = {},
    timeoutMs = DEFAULT_TIMEOUT_MS
  ): Promise<JsonRpcResponse> {
    const id = this.nextId++;

    return new Promise<JsonRpcResponse>((resolve, reject) => {
      const timer = setTimeout(() => {
        this.pending.delete(id);
        reject(
          new Error(`Timed out after ${timeoutMs}ms waiting for "${method}". stderr:\n${this.stderr}`)
        );
      }, timeoutMs);

      this.pending.set(id, { resolve, reject, timer });
      this.child.stdin.write(`${JSON.stringify({ jsonrpc: '2.0', id, method, params })}\n`);
    });
  }

  /** Send a notification (no response expected). */
  public notify(method: string, params: Record<string, unknown> = {}): void {
    this.child.stdin.write(`${JSON.stringify({ jsonrpc: '2.0', method, params })}\n`);
  }

  /** Spawn a server and complete the MCP initialize handshake. */
  public static async start(): Promise<{ client: McpStdioClient; initializeResult: InitializeResult }> {
    const client = new McpStdioClient();

    const response = await client.request('initialize', {
      protocolVersion: PROTOCOL_VERSION,
      capabilities: {},
      clientInfo: { name: 'fda-mcp-contract-tests', version: '1.0.0' }
    });

    if (response.error) {
      throw new Error(`initialize failed: ${response.error.message}`);
    }

    client.notify('notifications/initialized');

    return { client, initializeResult: response.result as InitializeResult };
  }

  /** Terminate the server and wait for the process to go away. */
  public async stop(): Promise<void> {
    if (this.child.exitCode !== null || this.child.signalCode !== null) {
      return;
    }

    await new Promise<void>((resolve) => {
      this.child.once('exit', () => resolve());
      this.child.kill('SIGTERM');
      // Hard stop if the server ignores SIGTERM.
      setTimeout(() => {
        this.child.kill('SIGKILL');
        resolve();
      }, 3000).unref();
    });
  }
}

export interface InitializeResult {
  protocolVersion: string;
  capabilities: Record<string, unknown>;
  serverInfo: { name: string; version: string; description?: string };
}

export interface ToolDefinition {
  name: string;
  description: string;
  inputSchema: {
    type: string;
    properties: Record<string, { type?: string; enum?: string[] }>;
    required?: string[];
  };
}

export interface ResourceDefinition {
  uri: string;
  name: string;
  description?: string;
  mimeType?: string;
}

export interface PromptDefinition {
  name: string;
  description: string;
  arguments?: { name: string; description?: string; required?: boolean }[];
}
