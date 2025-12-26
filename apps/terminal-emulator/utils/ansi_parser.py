"""
ANSI Parser - Convert ANSI escape codes to HTML/CSS styling
Supports basic ANSI color codes for terminal output
"""
import re


class ANSIParser:
    """Parse ANSI escape sequences and convert to HTML spans with CSS classes"""

    # ANSI color codes to CSS class mapping
    COLORS = {
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
    }

    # ANSI escape code regex pattern
    ANSI_ESCAPE = re.compile(r'\x1b\[([0-9;]+)m')

    @classmethod
    def parse(cls, text):
        """
        Parse ANSI codes in text and return structured data for rendering.

        Args:
            text: Text with ANSI escape codes

        Returns:
            List of {text: str, classes: list} segments
        """
        segments = []
        current_classes = []
        last_end = 0

        for match in cls.ANSI_ESCAPE.finditer(text):
            # Add text before this escape code
            if match.start() > last_end:
                plain_text = text[last_end:match.start()]
                if plain_text:
                    segments.append({
                        'text': plain_text,
                        'classes': current_classes.copy()
                    })

            # Parse escape code
            codes = match.group(1).split(';')
            for code in codes:
                if code == '0' or code == '':
                    # Reset all styles
                    current_classes = []
                elif code in cls.COLORS:
                    # Add color class
                    color_class = cls.COLORS[code]
                    # Remove any existing color classes
                    current_classes = [c for c in current_classes if not c.startswith('ansi-')]
                    current_classes.append(color_class)
                elif code == '1':
                    # Bold
                    if 'ansi-bold' not in current_classes:
                        current_classes.append('ansi-bold')
                elif code == '4':
                    # Underline
                    if 'ansi-underline' not in current_classes:
                        current_classes.append('ansi-underline')

            last_end = match.end()

        # Add remaining text
        if last_end < len(text):
            remaining = text[last_end:]
            if remaining:
                segments.append({
                    'text': remaining,
                    'classes': current_classes.copy()
                })

        return segments

    @classmethod
    def strip_ansi(cls, text):
        """
        Remove all ANSI escape codes from text.

        Args:
            text: Text with ANSI escape codes

        Returns:
            Plain text without ANSI codes
        """
        return cls.ANSI_ESCAPE.sub('', text)
