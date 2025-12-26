/**
 * useBridge Hook - Manages QWebChannel connection to Python backend
 * Provides access to the bridge object and connection status
 */
import { useState, useEffect } from 'react';
import type { WebBridge } from '../types/bridge';

export function useBridge() {
  const [bridge, setBridge] = useState<WebBridge | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    console.log('[Bridge] Starting connection attempt...');
    console.log('[Bridge] window.QWebChannel:', typeof window.QWebChannel);
    console.log('[Bridge] window.qt:', window.qt);

    // Track mount state and timeout for cleanup
    let isMounted = true;
    let timeoutId: ReturnType<typeof setTimeout> | null = null;

    // Wait for QWebChannel to be available
    const initBridge = () => {
      if (!isMounted) return;

      // Check if QWebChannel is available (running in Qt WebEngine)
      if (typeof window.QWebChannel === 'undefined') {
        console.warn('[Bridge] QWebChannel not available yet, retrying...');
        timeoutId = setTimeout(initBridge, 100);
        return;
      }

      // Check if Qt WebChannel transport is available
      if (!window.qt || !window.qt.webChannelTransport) {
        console.warn('[Bridge] Qt WebChannel transport not available yet, retrying...');
        timeoutId = setTimeout(initBridge, 100);
        return;
      }

      console.log('[Bridge] Initializing QWebChannel...');
      // Initialize QWebChannel
      new window.QWebChannel(window.qt.webChannelTransport, (channel) => {
        if (!isMounted) return;
        console.log('[Bridge] Channel callback received');
        console.log('[Bridge] Channel objects:', Object.keys(channel.objects));
        if (channel.objects.bridge) {
          console.log('[Bridge] Connected successfully!');
          setBridge(channel.objects.bridge);
          setIsConnected(true);
          setError(null);
        } else {
          console.error('[Bridge] Bridge object not found in channel');
          setError('Bridge object not found');
        }
      });
    };

    initBridge();

    // Cleanup: clear timeout on unmount
    return () => {
      isMounted = false;
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
    };
  }, []);

  return {
    bridge,
    isConnected,
    error,
  };
}
