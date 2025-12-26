/**
 * TypeScript type definitions for QWebChannel bridge
 * Defines the interface between Python (PySide6) and JavaScript (React)
 */

export interface WebBridge {
  // Methods callable from JavaScript → Python
  runCommand: (command: string) => void;
  sendInput: (data: string) => void;
  stopProcess: () => void;
  submitScore: (username: string, score: number) => void;
  authenticateGitHub: (accessToken: string) => void;
  logout: () => void;
  isAuthenticated: () => boolean;
  getUsername: () => string;
  getVersion: () => string;

  // Signals from Python → JavaScript
  testSignal: {
    connect: (callback: () => void) => void;
    disconnect?: (callback: () => void) => void;
  };
  outputReceived: {
    connect: (callback: (line: string, type: string) => void) => void;
    disconnect?: (callback: (line: string, type: string) => void) => void;
  };
  processFinished: {
    connect: (callback: (exitCode: number) => void) => void;
    disconnect?: (callback: (exitCode: number) => void) => void;
  };
  processError: {
    connect: (callback: (error: string) => void) => void;
    disconnect?: (callback: (error: string) => void) => void;
  };
  leaderboardUpdated: {
    connect: (callback: (leaderboardJson: string) => void) => void;
    disconnect?: (callback: (leaderboardJson: string) => void) => void;
  };
  authStatusChanged: {
    connect: (callback: (isAuthenticated: boolean, username: string) => void) => void;
    disconnect?: (callback: (isAuthenticated: boolean, username: string) => void) => void;
  };
}

export interface QWebChannel {
  objects: {
    bridge: WebBridge;
  };
}

declare global {
  interface Window {
    qt: {
      webChannelTransport: any;
    };
    QWebChannel: new (
      transport: any,
      callback: (channel: QWebChannel) => void
    ) => void;
  }
}

export {};
