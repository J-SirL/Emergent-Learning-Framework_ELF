/**
 * InputBar Component - Command input with history support
 */
import React, { useState, KeyboardEvent, useRef, useEffect } from 'react';
import type { WebBridge } from '../types/bridge';

interface InputBarProps {
  bridge: WebBridge | null;
  isProcessRunning: boolean;
}

export const InputBar: React.FC<InputBarProps> = ({ bridge, isProcessRunning }) => {
  const [input, setInput] = useState('');
  const [commandHistory, setCommandHistory] = useState<string[]>([]);
  const [historyIndex, setHistoryIndex] = useState(-1);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-focus input on mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleSubmit = () => {
    console.log('[InputBar] handleSubmit called, input:', JSON.stringify(input));
    console.log('[InputBar] Stack trace:', new Error().stack);

    if (!bridge || !input.trim()) {
      console.log('[InputBar] Aborting - no bridge or empty input');
      return;
    }

    if (isProcessRunning) {
      // Send input to running process stdin
      console.log('[InputBar] Sending to stdin:', input);
      bridge.sendInput(input);
    } else {
      // Run new command
      console.log('[InputBar] Running command:', input);
      bridge.runCommand(input);

      // Add to history (cap at 500 entries for performance)
      setCommandHistory((prev) => {
        const updated = [...prev, input];
        return updated.length > 500 ? updated.slice(-500) : updated;
      });
      setHistoryIndex(-1);
    }

    setInput('');
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleSubmit();
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      if (commandHistory.length === 0) return;

      const newIndex =
        historyIndex === -1
          ? commandHistory.length - 1
          : Math.max(0, historyIndex - 1);

      setHistoryIndex(newIndex);
      setInput(commandHistory[newIndex]);
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      if (historyIndex === -1) return;

      const newIndex = historyIndex + 1;

      if (newIndex >= commandHistory.length) {
        setHistoryIndex(-1);
        setInput('');
      } else {
        setHistoryIndex(newIndex);
        setInput(commandHistory[newIndex]);
      }
    } else if (e.key === 'c' && e.ctrlKey) {
      e.preventDefault();
      // Ctrl+C to stop process
      if (isProcessRunning && bridge) {
        bridge.stopProcess();
      }
    }
  };

  const handleStopClick = () => {
    if (bridge) {
      bridge.stopProcess();
    }
  };

  return (
    <div className="input-bar">
      <span className="input-prompt">$</span>
      <input
        ref={inputRef}
        type="text"
        className="input-field"
        placeholder={
          isProcessRunning
            ? 'Process running... Type input or Ctrl+C to stop'
            : 'Enter command (e.g., ping google.com, python --version)'
        }
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
      />
      {isProcessRunning && (
        <button className="btn btn-danger" onClick={handleStopClick}>
          Stop
        </button>
      )}
    </div>
  );
};
