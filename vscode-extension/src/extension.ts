import * as vscode from "vscode";
import WebSocket from "ws";

type State = "disconnected" | "ready" | "recording" | "transcribing";

let ws: WebSocket | null = null;
let state: State = "disconnected";
let statusBar: vscode.StatusBarItem;
let currentFileType = "";

function getPort(): number {
  return vscode.workspace
    .getConfiguration("voice-to-cursor")
    .get<number>("port", 9876);
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

function connect(): void {
  if (ws && ws.readyState === WebSocket.OPEN) {
    return;
  }

  const port = getPort();
  ws = new WebSocket(`ws://localhost:${port}`);

  ws.on("open", () => {
    state = "ready";
    updateStatusBar();
  });

  ws.on("message", (data: WebSocket.Data) => {
    const msg = JSON.parse(data.toString());

    if (msg.type === "status") {
      state = msg.state as State;
      updateStatusBar();
    } else if (msg.type === "result") {
      insertText(msg.text);
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
  });

  ws.on("error", () => {
    state = "disconnected";
    ws = null;
    updateStatusBar();
    vscode.window.showErrorMessage(
      "Voice to Cursor: Cannot connect to backend. Is the server running?"
    );
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
    currentFileType = editor?.document.fileName
      ? "." +
        (editor.document.fileName.split(".").pop() ?? "")
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

  connect();
}

export function deactivate(): void {
  if (ws) {
    ws.close();
    ws = null;
  }
}
