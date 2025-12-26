/**
 * Terminal Component - Main terminal UI with WebGL-accelerated output
 */
import React, { useState, useEffect, useRef, useCallback } from 'react';
import type { WebBridge } from '../types/bridge';
import { XTerminal, XTerminalHandle } from './XTerminal';
import { Leaderboard } from './Leaderboard';
import { useGitHub } from '../hooks/useGitHub';

interface TerminalProps {
  bridge: WebBridge;
}

// ANSI color codes for different output types
const ANSI = {
  reset: '\x1b[0m',
  bold: '\x1b[1m',
  purple: '\x1b[35m',
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  dim: '\x1b[2m',
  italic: '\x1b[3m',
};

export const Terminal: React.FC<TerminalProps> = ({ bridge }) => {
  const [isProcessRunning, setIsProcessRunning] = useState(false);
  const [showLeaderboard, setShowLeaderboard] = useState(false);
  const [inputBuffer, setInputBuffer] = useState('');
  const [commandHistory, setCommandHistory] = useState<string[]>([]);
  const [historyIndex, setHistoryIndex] = useState(-1);
  const terminalRef = useRef<XTerminalHandle>(null);

  const github = useGitHub(bridge);

  // Write styled output to terminal
  const writeOutput = useCallback((text: string, type: 'command' | 'stdout' | 'stderr' | 'error' | 'system' | 'stdin') => {
    if (!terminalRef.current) return;

    let styledText = text;
    switch (type) {
      case 'command':
        styledText = `${ANSI.bold}${ANSI.purple}$ ${text}${ANSI.reset}`;
        break;
      case 'stderr':
      case 'error':
        styledText = `${ANSI.red}${text}${ANSI.reset}`;
        break;
      case 'system':
        styledText = `${ANSI.dim}${ANSI.italic}${text}${ANSI.reset}`;
        break;
      case 'stdin':
        styledText = `${ANSI.green}${text}${ANSI.reset}`;
        break;
      default:
        // stdout - no styling, let ANSI codes pass through
        styledText = text;
    }

    terminalRef.current.writeln(styledText);
  }, []);

  // Handle user input from xterm
  const handleTerminalData = useCallback((data: string) => {
    if (!bridge) return;

    // Handle special keys
    if (data === '\r') {
      // Enter key - submit command
      terminalRef.current?.write('\r\n');

      if (inputBuffer.trim()) {
        if (isProcessRunning) {
          // Send to running process stdin
          bridge.sendInput(inputBuffer);
        } else {
          // Run new command
          writeOutput(inputBuffer, 'command');
          bridge.runCommand(inputBuffer);

          // Add to history
          setCommandHistory(prev => {
            const updated = [...prev, inputBuffer];
            return updated.length > 500 ? updated.slice(-500) : updated;
          });
        }
      }

      setInputBuffer('');
      setHistoryIndex(-1);
    } else if (data === '\x7f' || data === '\b') {
      // Backspace
      if (inputBuffer.length > 0) {
        setInputBuffer(prev => prev.slice(0, -1));
        terminalRef.current?.write('\b \b');
      }
    } else if (data === '\x03') {
      // Ctrl+C
      if (isProcessRunning) {
        bridge.stopProcess();
        terminalRef.current?.write('^C\r\n');
      }
    } else if (data === '\x1b[A') {
      // Arrow Up - history
      if (commandHistory.length > 0 && !isProcessRunning) {
        const newIndex = historyIndex === -1
          ? commandHistory.length - 1
          : Math.max(0, historyIndex - 1);

        // Clear current line
        terminalRef.current?.write('\r\x1b[K$ ');
        const cmd = commandHistory[newIndex];
        terminalRef.current?.write(cmd);
        setInputBuffer(cmd);
        setHistoryIndex(newIndex);
      }
    } else if (data === '\x1b[B') {
      // Arrow Down - history
      if (historyIndex !== -1 && !isProcessRunning) {
        const newIndex = historyIndex + 1;

        // Clear current line
        terminalRef.current?.write('\r\x1b[K$ ');

        if (newIndex >= commandHistory.length) {
          setInputBuffer('');
          setHistoryIndex(-1);
        } else {
          const cmd = commandHistory[newIndex];
          terminalRef.current?.write(cmd);
          setInputBuffer(cmd);
          setHistoryIndex(newIndex);
        }
      }
    } else if (data >= ' ' && data <= '~') {
      // Printable characters
      setInputBuffer(prev => prev + data);
      terminalRef.current?.write(data);
    }
  }, [bridge, inputBuffer, isProcessRunning, commandHistory, historyIndex, writeOutput]);

  useEffect(() => {
    if (!bridge) {
      console.log('[Terminal] Bridge not ready yet, skipping signal setup');
      return;
    }

    let isMounted = true;

    console.log('[Terminal] Setting up bridge signal listeners...');

    if (!bridge.outputReceived || !bridge.processFinished || !bridge.processError) {
      console.error('[Terminal] Bridge signals not available!');
      return;
    }

    const handleOutputReceived = (line: string, type: string) => {
      if (!isMounted) return;
      // Write directly to xterm - it handles ANSI natively
      if (type === 'stderr' || type === 'error') {
        terminalRef.current?.write(`${ANSI.red}${line}${ANSI.reset}\r\n`);
      } else {
        terminalRef.current?.write(`${line}\r\n`);
      }
      setIsProcessRunning(true);
    };

    const handleProcessFinished = (exitCode: number) => {
      if (!isMounted) return;
      console.log('[Terminal] processFinished:', { exitCode });
      setIsProcessRunning(false);
      // Show prompt after process ends
      terminalRef.current?.write('$ ');
    };

    const handleProcessError = (error: string) => {
      if (!isMounted) return;
      terminalRef.current?.write(`${ANSI.red}${ANSI.bold}Error: ${error}${ANSI.reset}\r\n`);
      setIsProcessRunning(false);
      terminalRef.current?.write('$ ');
    };

    bridge.outputReceived.connect(handleOutputReceived);
    bridge.processFinished.connect(handleProcessFinished);
    bridge.processError.connect(handleProcessError);

    console.log('[Terminal] Signal listeners connected successfully!');

    // Initial welcome message
    setTimeout(() => {
      if (!isMounted || !terminalRef.current) return;

      terminalRef.current.writeln(`${ANSI.blue}${ANSI.bold}Terminal Emulator v1.0.0${ANSI.reset}`);
      terminalRef.current.writeln(`${ANSI.dim}GPU-accelerated with WebGL${ANSI.reset}`);
      terminalRef.current.writeln('');
      terminalRef.current.writeln(`${ANSI.dim}Type a command to get started${ANSI.reset}`);
      terminalRef.current.writeln('');
      terminalRef.current.write('$ ');
    }, 100);

    return () => {
      isMounted = false;
      console.log('[Terminal] Cleaning up signal listeners...');
      try {
        bridge.outputReceived?.disconnect?.(handleOutputReceived);
        bridge.processFinished?.disconnect?.(handleProcessFinished);
        bridge.processError?.disconnect?.(handleProcessError);
      } catch (e) {
        console.warn('[Terminal] Error disconnecting signals:', e);
      }
    };
  }, [bridge]);

  return (
    <div className="terminal-container">
      {/* Header */}
      <div className="terminal-header">
        <div className="terminal-title">
          <span>⚡</span>
          <span>Terminal Emulator</span>
        </div>
        <div className="terminal-status">
          <div className="status-indicator" />
          <span>Connected</span>
          <span style={{ color: '#a6e3a1', marginLeft: '8px' }}>WebGL</span>
          <span>|</span>
          <button
            className="btn"
            onClick={() => setShowLeaderboard(!showLeaderboard)}
            style={{ padding: '4px 12px', fontSize: '12px' }}
          >
            {showLeaderboard ? 'Hide' : 'Show'} Leaderboard
          </button>
        </div>
      </div>

      {/* XTerm Output Area */}
      <div style={{ flex: 1, overflow: 'hidden' }}>
        <XTerminal
          ref={terminalRef}
          onData={handleTerminalData}
        />
      </div>

      {/* Leaderboard */}
      {showLeaderboard && (
        <Leaderboard
          entries={github.leaderboard}
          currentUsername={github.username}
          isAuthenticated={github.isAuthenticated}
          onLogin={github.login}
          onLogout={github.logout}
        />
      )}
    </div>
  );
};
