/**
 * XTerminal Component - GPU-accelerated terminal using xterm.js with WebGL
 */
import { useEffect, useRef, useImperativeHandle, forwardRef } from 'react';
import { Terminal } from 'xterm';
import { WebglAddon } from '@xterm/addon-webgl';
import { FitAddon } from '@xterm/addon-fit';
import 'xterm/css/xterm.css';

// Catppuccin Mocha theme matching our CSS
const catppuccinTheme = {
  background: '#1e1e2e',
  foreground: '#cdd6f4',
  cursor: '#f5e0dc',
  cursorAccent: '#1e1e2e',
  selectionBackground: '#585b70',
  selectionForeground: '#cdd6f4',
  black: '#45475a',
  red: '#f38ba8',
  green: '#a6e3a1',
  yellow: '#f9e2af',
  blue: '#89b4fa',
  magenta: '#f5c2e7',
  cyan: '#94e2d5',
  white: '#bac2de',
  brightBlack: '#585b70',
  brightRed: '#f38ba8',
  brightGreen: '#a6e3a1',
  brightYellow: '#f9e2af',
  brightBlue: '#89b4fa',
  brightMagenta: '#f5c2e7',
  brightCyan: '#94e2d5',
  brightWhite: '#cdd6f4',
};

export interface XTerminalHandle {
  write: (data: string) => void;
  writeln: (data: string) => void;
  clear: () => void;
  focus: () => void;
}

interface XTerminalProps {
  onData?: (data: string) => void;
  onResize?: (cols: number, rows: number) => void;
}

export const XTerminal = forwardRef<XTerminalHandle, XTerminalProps>(
  ({ onData, onResize }, ref) => {
    const containerRef = useRef<HTMLDivElement>(null);
    const terminalRef = useRef<Terminal | null>(null);
    const fitAddonRef = useRef<FitAddon | null>(null);
    const webglAddonRef = useRef<WebglAddon | null>(null);

    // Expose methods to parent component
    useImperativeHandle(ref, () => ({
      write: (data: string) => {
        terminalRef.current?.write(data);
      },
      writeln: (data: string) => {
        terminalRef.current?.writeln(data);
      },
      clear: () => {
        terminalRef.current?.clear();
      },
      focus: () => {
        terminalRef.current?.focus();
      },
    }));

    useEffect(() => {
      if (!containerRef.current) return;

      // Create terminal instance
      const terminal = new Terminal({
        theme: catppuccinTheme,
        fontFamily: "'Cascadia Code', 'Fira Code', 'JetBrains Mono', 'Consolas', monospace",
        fontSize: 14,
        lineHeight: 1.5,
        cursorBlink: true,
        cursorStyle: 'block',
        scrollback: 10000,
        allowProposedApi: true,
        convertEol: true,
      });

      // Create addons
      const fitAddon = new FitAddon();
      terminal.loadAddon(fitAddon);

      // Open terminal in container
      terminal.open(containerRef.current);

      // Try to load WebGL addon for GPU acceleration
      try {
        const webglAddon = new WebglAddon();
        webglAddon.onContextLoss(() => {
          console.warn('[XTerminal] WebGL context lost, disposing addon');
          webglAddon.dispose();
        });
        terminal.loadAddon(webglAddon);
        webglAddonRef.current = webglAddon;
        console.log('[XTerminal] WebGL renderer activated');
      } catch (e) {
        console.warn('[XTerminal] WebGL not available, falling back to canvas renderer:', e);
      }

      // Fit terminal to container
      fitAddon.fit();

      // Handle user input
      if (onData) {
        terminal.onData(onData);
      }

      // Handle resize
      if (onResize) {
        terminal.onResize(({ cols, rows }) => {
          onResize(cols, rows);
        });
      }

      // Store refs
      terminalRef.current = terminal;
      fitAddonRef.current = fitAddon;

      // Handle window resize
      const handleResize = () => {
        fitAddon.fit();
      };
      window.addEventListener('resize', handleResize);

      // Observe container size changes
      const resizeObserver = new ResizeObserver(() => {
        fitAddon.fit();
      });
      resizeObserver.observe(containerRef.current);

      // Focus terminal
      terminal.focus();

      // Cleanup
      return () => {
        window.removeEventListener('resize', handleResize);
        resizeObserver.disconnect();
        webglAddonRef.current?.dispose();
        fitAddon.dispose();
        terminal.dispose();
      };
    }, [onData, onResize]);

    return (
      <div
        ref={containerRef}
        style={{
          width: '100%',
          height: '100%',
          padding: '8px',
          boxSizing: 'border-box',
        }}
      />
    );
  }
);

XTerminal.displayName = 'XTerminal';
