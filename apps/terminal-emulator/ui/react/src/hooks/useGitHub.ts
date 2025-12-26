/**
 * useGitHub Hook - Manages GitHub OAuth flow and leaderboard
 */
import { useState, useEffect } from 'react';
import type { WebBridge } from '../types/bridge';

export interface LeaderboardEntry {
  username: string;
  score: number;
  timestamp: string;
  [key: string]: any;
}

export function useGitHub(bridge: WebBridge | null) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [username, setUsername] = useState('');
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);

  useEffect(() => {
    if (!bridge) return;

    // Track mount state to prevent callbacks after unmount
    let isMounted = true;

    // Define handlers with mount guard
    const handleAuthStatusChanged = (authenticated: boolean, user: string) => {
      if (!isMounted) return;
      setIsAuthenticated(authenticated);
      setUsername(user);
    };

    const handleLeaderboardUpdated = (leaderboardJson: string) => {
      if (!isMounted) return;
      try {
        const data = JSON.parse(leaderboardJson);
        setLeaderboard(data);
      } catch (error) {
        console.error('Error parsing leaderboard:', error);
      }
    };

    // Connect to signals
    bridge.authStatusChanged.connect(handleAuthStatusChanged);
    bridge.leaderboardUpdated.connect(handleLeaderboardUpdated);

    // Check initial auth status
    const authenticated = bridge.isAuthenticated();
    const user = bridge.getUsername();
    setIsAuthenticated(authenticated);
    setUsername(user);

    // Cleanup: disconnect signals on unmount
    return () => {
      isMounted = false;
      try {
        if (bridge.authStatusChanged?.disconnect) {
          bridge.authStatusChanged.disconnect(handleAuthStatusChanged);
        }
        if (bridge.leaderboardUpdated?.disconnect) {
          bridge.leaderboardUpdated.disconnect(handleLeaderboardUpdated);
        }
      } catch (e) {
        console.warn('[useGitHub] Error disconnecting signals:', e);
      }
    };
  }, [bridge]);

  const login = () => {
    // Open GitHub OAuth flow in external browser
    // The OAuth callback will be handled by a local server
    const clientId = import.meta.env.VITE_GITHUB_CLIENT_ID || '';
    const redirectUri = 'http://localhost:8765/callback';
    const scope = 'public_repo';

    const authUrl = `https://github.com/login/oauth/authorize?client_id=${clientId}&redirect_uri=${redirectUri}&scope=${scope}`;

    // In Qt WebEngine, we can't easily open external browser
    // Instead, display the URL for user to visit
    console.log('GitHub OAuth URL:', authUrl);
    alert(`Please visit this URL to authenticate:\n\n${authUrl}`);
  };

  const logout = () => {
    if (bridge) {
      bridge.logout();
    }
  };

  const submitScore = (score: number) => {
    if (bridge && isAuthenticated) {
      bridge.submitScore(username, score);
    }
  };

  return {
    isAuthenticated,
    username,
    leaderboard,
    login,
    logout,
    submitScore,
  };
}
