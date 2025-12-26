/**
 * App Component - Root component with bridge connection handling
 */
import React from 'react';
import { useBridge } from './hooks/useBridge';
import { Terminal } from './components/Terminal';
import './styles/terminal.css';

export const App: React.FC = () => {
  const { bridge, isConnected, error } = useBridge();

  if (error) {
    return (
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          height: '100vh',
          background: '#1e1e2e',
          color: '#f38ba8',
          fontFamily: 'monospace',
          flexDirection: 'column',
          gap: '16px',
        }}
      >
        <h1>⚠️ Connection Error</h1>
        <p>{error}</p>
        <p style={{ color: '#a6adc8', fontSize: '14px' }}>
          This app must be run inside the PySide6 application.
        </p>
        <p style={{ color: '#585b70', fontSize: '12px' }}>
          For development: Run <code>python main.py</code> with DEV_MODE=true
        </p>
      </div>
    );
  }

  if (!isConnected || !bridge) {
    return (
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          height: '100vh',
          background: '#1e1e2e',
          color: '#89b4fa',
          fontFamily: 'monospace',
        }}
      >
        <div style={{ textAlign: 'center' }}>
          <div
            style={{
              fontSize: '48px',
              animation: 'pulse 2s infinite',
            }}
          >
            ⚡
          </div>
          <p>Connecting to Python backend...</p>
        </div>
      </div>
    );
  }

  return <Terminal bridge={bridge} />;
};
