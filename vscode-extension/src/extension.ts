import * as vscode from "vscode";
import { ChildProcess, spawn } from "child_process";
import * as path from "path";
import * as os from "os";
import WebSocket from "ws";

type State = "disconnected" | "ready" | "recording" | "transcribing";

let ws: WebSocket | null = null;
let state: State = "disconnected";
let statusBar: vscode.StatusBarItem;
let currentFileType = "";
let backendProcess: ChildProcess | null = null;
let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
let reconnectDelay = 1000;
const MAX_RECONNECT_DELAY = 30000;

function getPort(): number {
  return vscode.workspace
    .getConfiguration("voice-to-cursor")
    .get<number>("port", 9876);
}

function getAutoStart(): boolean {
  return vscode.workspace
    .getConfiguration("voice-to-cursor")
    .get<boolean>("autoStart", true);
}

function updateStatusBar(): void {
  switch (state) {
    case "disconnected":
      statusBar.text = "$(debug-disconnect) Voice";
      statusBar.backgroundColor = undefined;
      break;
    case "ready":
      statusBar.text = "$(mic) Voice";
      statusBar.backgroundColor = undefined;
      break;
    case "recording":
      statusBar.text = "$(record) Recording...";
      statusBar.backgroundColor = new vscode.ThemeColor(
        "statusBarItem.warningBackground"
      );
      break;
    case "transcribing":
      statusBar.text = "$(loading~spin) Transcribing...";
      statusBar.backgroundColor = undefined;
      break;
  }
  statusBar.show();
}

function getBackendPath(): string {
  return vscode.workspace
    .getConfiguration("voice-to-cursor")
    .get<string>("backendPath", "");
}

function startBackend(): void {
  if (backendProcess) {
    return;
  }

  const backendPath = getBackendPath();
  if (!backendPath) {
    vscode.window
      .showErrorMessage(
        "Voice to Cursor: Set \"voice-to-cursor.backendPath\" to your vosk-project directory to enable auto-start.",
        "Open Settings"
      )
      .then((action) => {
        if (action === "Open Settings") {
          vscode.commands.executeCommand(
            "workbench.action.openSettings",
            "voice-to-cursor.backendPath"
          );
        }
      });
    return;
  }

  // Use explicit pythonPath if configured, otherwise auto-detect venv
  const configuredPython = vscode.workspace
    .getConfiguration("voice-to-cursor")
    .get<string>("pythonPath", "");

  let pythonBin: string;
  if (configuredPython) {
    pythonBin = configuredPython;
  } else {
    const isWindows = os.platform() === "win32";
    const venvBinDir = isWindows ? "Scripts" : "bin";
    const pythonExe = isWindows ? "python.exe" : "python";
    pythonBin = path.join(backendPath, "backend", ".venv", venvBinDir, pythonExe);
  }

  backendProcess = spawn(pythonBin, ["-m", "backend.server"], {
    cwd: backendPath,
    stdio: "ignore",
    detached: false,
  });

  backendProcess.on("exit", (code) => {
    console.log(`[voice-to-cursor] Backend exited with code ${code}`);
    backendProcess = null;
    if (code !== 0 && code !== null) {
      vscode.window
        .showErrorMessage(
          "Voice to Cursor: Backend crashed.",
          "Restart Backend"
        )
        .then((action) => {
          if (action === "Restart Backend") {
            startBackend();
            setTimeout(connect, 2000);
          }
        });
    }
  });

  backendProcess.on("error", (err) => {
    console.error(`[voice-to-cursor] Failed to start backend: ${err.message}`);
    backendProcess = null;
    vscode.window.showErrorMessage(
      `Voice to Cursor: Failed to start backend: ${err.message}`
    );
  });
}

function stopBackend(): void {
  if (backendProcess) {
    backendProcess.kill("SIGTERM");
    backendProcess = null;
  }
}

function scheduleReconnect(): void {
  if (reconnectTimer) {
    return;
  }
  reconnectTimer = setTimeout(() => {
    reconnectTimer = null;
    connect();
  }, reconnectDelay);
  reconnectDelay = Math.min(reconnectDelay * 2, MAX_RECONNECT_DELAY);
}

function connect(): void {
  if (ws && ws.readyState === WebSocket.OPEN) {
    return;
  }

  // Clean up stale connection
  if (ws) {
    ws.removeAllListeners();
    ws = null;
  }

  const port = getPort();
  ws = new WebSocket(`ws://localhost:${port}`);

  ws.on("open", () => {
    state = "ready";
    reconnectDelay = 1000; // Reset backoff on success
    updateStatusBar();
  });

  ws.on("message", (data: WebSocket.Data) => {
    let msg: Record<string, unknown>;
    try {
      msg = JSON.parse(data.toString());
    } catch {
      console.error("[voice-to-cursor] Received non-JSON message from backend");
      return;
    }

    if (msg.type === "status") {
      state = msg.state as State;
      updateStatusBar();
    } else if (msg.type === "result") {
      insertText(msg.text as string);
      state = "ready";
      updateStatusBar();
    } else if (msg.type === "error") {
      vscode.window.showErrorMessage(`Voice to Cursor: ${msg.message}`);
    }
  });

  ws.on("close", () => {
    state = "disconnected";
    ws = null;
    updateStatusBar();
    scheduleReconnect();
  });

  ws.on("error", () => {
    state = "disconnected";
    ws = null;
    updateStatusBar();

    // Try auto-starting the backend if enabled
    if (getAutoStart() && !backendProcess) {
      startBackend();
      setTimeout(connect, 2000);
    } else {
      scheduleReconnect();
    }
  });
}

function send(obj: Record<string, unknown>): void {
  if (!ws || ws.readyState !== WebSocket.OPEN) {
    vscode.window.showErrorMessage(
      "Voice to Cursor: Not connected to backend."
    );
    connect();
    return;
  }
  ws.send(JSON.stringify(obj));
}

function insertText(text: string): void {
  const editor = vscode.window.activeTextEditor;
  if (!editor) {
    vscode.window.showWarningMessage(
      "Voice to Cursor: No active editor to insert text."
    );
    return;
  }
  editor.edit((eb) => {
    eb.insert(editor.selection.active, text);
  });
}

function toggle(): void {
  if (state === "disconnected") {
    connect();
    vscode.window.showInformationMessage(
      "Voice to Cursor: Connecting to backend..."
    );
    return;
  }

  if (state === "ready") {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
      vscode.window.showWarningMessage(
        "Voice to Cursor: No active editor for dictation."
      );
      return;
    }
    currentFileType = editor.document.fileName
      ? "." + (editor.document.fileName.split(".").pop() ?? "")
      : "";
    send({ command: "start", file_type: currentFileType });
  } else if (state === "recording") {
    send({ command: "stop", file_type: currentFileType });
  }
}

function cancel(): void {
  if (state === "recording") {
    send({ command: "cancel" });
  }
}

export function activate(context: vscode.ExtensionContext): void {
  statusBar = vscode.window.createStatusBarItem(
    vscode.StatusBarAlignment.Right,
    100
  );
  statusBar.command = "voice-to-cursor.toggle";
  updateStatusBar();

  context.subscriptions.push(statusBar);

  context.subscriptions.push(
    vscode.commands.registerCommand("voice-to-cursor.toggle", toggle)
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("voice-to-cursor.cancel", cancel)
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("voice-to-cursor.reconnect", () => {
      reconnectDelay = 1000;
      connect();
      vscode.window.showInformationMessage(
        "Voice to Cursor: Reconnecting..."
      );
    })
  );

  connect();
}

export function deactivate(): void {
  if (reconnectTimer) {
    clearTimeout(reconnectTimer);
    reconnectTimer = null;
  }
  if (ws) {
    ws.close();
    ws = null;
  }
  stopBackend();
}
