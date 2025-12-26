/**
 * OutputLine Component - Renders a single line of terminal output with ANSI support
 */
import React from 'react';

interface Segment {
  text: string;
  classes: string[];
}

interface OutputLineProps {
  line: string;
  type: 'command' | 'stdout' | 'stderr' | 'error' | 'system' | 'stdin';
}

// Simple ANSI parser for basic color support
function parseANSI(text: string): Segment[] {
  const segments: Segment[] = [];
  const ansiRegex = /\x1b\[([0-9;]+)m/g;
  let lastIndex = 0;
  let currentClasses: string[] = [];

  const colorMap: Record<string, string> = {
    '30': 'ansi-black',
    '31': 'ansi-red',
    '32': 'ansi-green',
    '33': 'ansi-yellow',
    '34': 'ansi-blue',
    '35': 'ansi-magenta',
    '36': 'ansi-cyan',
    '37': 'ansi-white',
    '90': 'ansi-bright-black',
    '91': 'ansi-bright-red',
    '92': 'ansi-bright-green',
    '93': 'ansi-bright-yellow',
    '94': 'ansi-bright-blue',
    '95': 'ansi-bright-magenta',
    '96': 'ansi-bright-cyan',
    '97': 'ansi-bright-white',
  };

  let match;
  while ((match = ansiRegex.exec(text)) !== null) {
    // Add text before this escape code
    if (match.index > lastIndex) {
      const plainText = text.substring(lastIndex, match.index);
      if (plainText) {
        segments.push({ text: plainText, classes: [...currentClasses] });
      }
    }

    // Parse escape code
    const codes = match[1].split(';');
    for (const code of codes) {
      if (code === '0' || code === '') {
        currentClasses = [];
      } else if (colorMap[code]) {
        currentClasses = currentClasses.filter((c) => !c.startsWith('ansi-'));
        currentClasses.push(colorMap[code]);
      } else if (code === '1') {
        if (!currentClasses.includes('ansi-bold')) {
          currentClasses.push('ansi-bold');
        }
      } else if (code === '4') {
        if (!currentClasses.includes('ansi-underline')) {
          currentClasses.push('ansi-underline');
        }
      }
    }

    lastIndex = match.index + match[0].length;
  }

  // Add remaining text
  if (lastIndex < text.length) {
    const remaining = text.substring(lastIndex);
    if (remaining) {
      segments.push({ text: remaining, classes: [...currentClasses] });
    }
  }

  return segments.length > 0 ? segments : [{ text, classes: [] }];
}

export const OutputLine: React.FC<OutputLineProps> = ({ line, type }) => {
  const segments = parseANSI(line);

  return (
    <div className={`output-line ${type}`}>
      {segments.map((segment, index) => (
        <span key={index} className={segment.classes.join(' ')}>
          {segment.text}
        </span>
      ))}
    </div>
  );
};
