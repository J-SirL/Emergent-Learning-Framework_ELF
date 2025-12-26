/**
 * Leaderboard Component - Display GitHub-based leaderboard
 */
import React from 'react';
import type { LeaderboardEntry } from '../hooks/useGitHub';

interface LeaderboardProps {
  entries: LeaderboardEntry[];
  currentUsername: string;
  isAuthenticated: boolean;
  onLogin: () => void;
  onLogout: () => void;
}

export const Leaderboard: React.FC<LeaderboardProps> = ({
  entries,
  currentUsername,
  isAuthenticated,
  onLogin,
  onLogout,
}) => {
  return (
    <div className="leaderboard">
      <div className="leaderboard-title">🏆 Leaderboard</div>

      {!isAuthenticated && (
        <div style={{ marginBottom: '12px' }}>
          <button className="btn" onClick={onLogin} style={{ width: '100%' }}>
            Login with GitHub
          </button>
        </div>
      )}

      {isAuthenticated && (
        <div style={{ marginBottom: '12px', fontSize: '12px' }}>
          <span style={{ color: 'var(--accent-green)' }}>
            ✓ {currentUsername}
          </span>
          <button
            className="btn"
            onClick={onLogout}
            style={{ marginLeft: '8px', padding: '4px 8px', fontSize: '11px' }}
          >
            Logout
          </button>
        </div>
      )}

      {entries.length === 0 && (
        <div style={{ color: 'var(--text-muted)', fontSize: '12px' }}>
          No scores yet. Be the first!
        </div>
      )}

      {entries.slice(0, 10).map((entry, index) => (
        <div
          key={index}
          className="leaderboard-entry"
          style={{
            borderLeft:
              entry.username === currentUsername
                ? '3px solid var(--accent-green)'
                : 'none',
          }}
        >
          <span className="leaderboard-rank">#{index + 1}</span>
          <span className="leaderboard-username">{entry.username}</span>
          <span className="leaderboard-score">{entry.score}</span>
        </div>
      ))}
    </div>
  );
};
