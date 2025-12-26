"""
Terminal Widget - PySide6 terminal with screen buffer for TUI support
"""
import re
from dataclasses import dataclass, field
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QLineEdit, QFrame
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QFont, QTextCursor, QColor, QTextCharFormat

# Catppuccin Mocha palette
COLORS_16 = [
    '#45475a', '#f38ba8', '#a6e3a1', '#f9e2af', '#89b4fa', '#cba6f7', '#94e2d5', '#bac2de',
    '#585b70', '#f38ba8', '#a6e3a1', '#f9e2af', '#89b4fa', '#cba6f7', '#94e2d5', '#cdd6f4',
]
DEFAULT_FG, DEFAULT_BG = '#cdd6f4', '#1e1e2e'


@dataclass
class Cell:
    char: str = ' '
    fg: str = DEFAULT_FG
    bg: str = None
    bold: bool = False
    dim: bool = False
    italic: bool = False
    underline: bool = False


@dataclass
class ScreenBuffer:
    """Terminal screen buffer with cursor tracking"""
    cols: int = 120
    rows: int = 50
    cursor_x: int = 0
    cursor_y: int = 0
    scroll_top: int = 0
    scroll_bottom: int = 49
    fg: str = DEFAULT_FG
    bg: str = None
    bold: bool = False
    dim: bool = False
    italic: bool = False
    underline: bool = False
    grid: list = field(default_factory=list)

    def __post_init__(self):
        self.scroll_bottom = self.rows - 1
        self.grid = [[Cell() for _ in range(self.cols)] for _ in range(self.rows)]

    def reset_attrs(self):
        self.fg, self.bg = DEFAULT_FG, None
        self.bold = self.dim = self.italic = self.underline = False

    def write_char(self, ch: str):
        if self.cursor_x >= self.cols:
            self.cursor_x = 0
            self.cursor_y += 1
        if self.cursor_y >= self.rows:
            self._scroll_up()
            self.cursor_y = self.rows - 1

        cell = self.grid[self.cursor_y][self.cursor_x]
        cell.char, cell.fg, cell.bg = ch, self.fg, self.bg
        cell.bold, cell.dim, cell.italic, cell.underline = self.bold, self.dim, self.italic, self.underline
        self.cursor_x += 1

    def newline(self):
        self.cursor_x = 0
        self.cursor_y += 1
        if self.cursor_y >= self.rows:
            self._scroll_up()
            self.cursor_y = self.rows - 1

    def _scroll_up(self):
        del self.grid[self.scroll_top]
        self.grid.insert(self.scroll_bottom, [Cell() for _ in range(self.cols)])

    def clear_line(self, mode: int = 0):
        y = self.cursor_y
        if mode == 0:  # cursor to end
            for x in range(self.cursor_x, self.cols):
                self.grid[y][x] = Cell()
        elif mode == 1:  # start to cursor
            for x in range(self.cursor_x + 1):
                self.grid[y][x] = Cell()
        else:  # whole line
            self.grid[y] = [Cell() for _ in range(self.cols)]

    def clear_screen(self, mode: int = 0):
        if mode == 0:  # cursor to end
            self.clear_line(0)
            for y in range(self.cursor_y + 1, self.rows):
                self.grid[y] = [Cell() for _ in range(self.cols)]
        elif mode == 1:  # start to cursor
            for y in range(self.cursor_y):
                self.grid[y] = [Cell() for _ in range(self.cols)]
            self.clear_line(1)
        else:  # whole screen
            self.grid = [[Cell() for _ in range(self.cols)] for _ in range(self.rows)]
            self.cursor_x = self.cursor_y = 0


class TerminalEmulator:
    """ANSI terminal emulator with screen buffer"""

    CSI = re.compile(r'\x1b\[([?>=]?)([0-9;]*)([A-Za-z~])')
    OSC = re.compile(r'\x1b\].*?(?:\x07|\x1b\\)')
    OTHER = re.compile(r'\x1b[PX^_].*?(?:\x1b\\|\x07)|\x1b[NODEHMZc78]|\x1b[\s()*+][^\x1b]?')

    def __init__(self, cols=120, rows=50):
        self.buf = ScreenBuffer(cols=cols, rows=rows)

    def feed(self, data: str):
        """Process input data"""
        data = self.OSC.sub('', data)
        data = self.OTHER.sub('', data)
        data = data.replace('\r\n', '\n').replace('\r', '\n')

        pos = 0
        for m in self.CSI.finditer(data):
            self._write_text(data[pos:m.start()])
            self._handle_csi(m.group(1), m.group(2), m.group(3))
            pos = m.end()
        self._write_text(data[pos:])

    def _write_text(self, text: str):
        for ch in text:
            if ch == '\n':
                self.buf.newline()
            elif ch == '\t':
                spaces = 8 - (self.buf.cursor_x % 8)
                for _ in range(spaces):
                    self.buf.write_char(' ')
            elif ch >= ' ':
                self.buf.write_char(ch)

    def _handle_csi(self, prefix: str, params: str, cmd: str):
        p = [int(x) if x else 0 for x in params.split(';')] if params else [0]
        b = self.buf

        if prefix:  # Private sequences (?25l, etc.) - ignore
            return

        if cmd == 'm':  # SGR
            self._handle_sgr(p)
        elif cmd == 'A':  # Cursor up
            b.cursor_y = max(0, b.cursor_y - (p[0] or 1))
        elif cmd == 'B':  # Cursor down
            b.cursor_y = min(b.rows - 1, b.cursor_y + (p[0] or 1))
        elif cmd == 'C':  # Cursor forward
            b.cursor_x = min(b.cols - 1, b.cursor_x + (p[0] or 1))
        elif cmd == 'D':  # Cursor back
            b.cursor_x = max(0, b.cursor_x - (p[0] or 1))
        elif cmd == 'H' or cmd == 'f':  # Cursor position
            b.cursor_y = max(0, min(b.rows - 1, (p[0] or 1) - 1))
            b.cursor_x = max(0, min(b.cols - 1, (p[1] if len(p) > 1 else 1) - 1))
        elif cmd == 'J':  # Erase display
            b.clear_screen(p[0])
        elif cmd == 'K':  # Erase line
            b.clear_line(p[0])
        elif cmd == 'G':  # Cursor horizontal absolute
            b.cursor_x = max(0, min(b.cols - 1, (p[0] or 1) - 1))

    def _handle_sgr(self, codes: list):
        b = self.buf
        i = 0
        while i < len(codes):
            c = codes[i]
            if c == 0:
                b.reset_attrs()
            elif c == 1:
                b.bold = True
            elif c == 2:
                b.dim = True
            elif c == 3:
                b.italic = True
            elif c == 4:
                b.underline = True
            elif c in (22, 23, 24):
                if c == 22: b.bold = b.dim = False
                elif c == 23: b.italic = False
                else: b.underline = False
            elif 30 <= c <= 37:
                b.fg = COLORS_16[c - 30]
            elif c == 38 and i + 2 < len(codes):
                if codes[i+1] == 5:
                    b.fg = self._color256(codes[i+2])
                    i += 2
                elif codes[i+1] == 2 and i + 4 < len(codes):
                    b.fg = f'#{codes[i+2]:02x}{codes[i+3]:02x}{codes[i+4]:02x}'
                    i += 4
            elif c == 39:
                b.fg = DEFAULT_FG
            elif 40 <= c <= 47:
                b.bg = COLORS_16[c - 40]
            elif c == 48 and i + 2 < len(codes):
                if codes[i+1] == 5:
                    b.bg = self._color256(codes[i+2])
                    i += 2
                elif codes[i+1] == 2 and i + 4 < len(codes):
                    b.bg = f'#{codes[i+2]:02x}{codes[i+3]:02x}{codes[i+4]:02x}'
                    i += 4
            elif c == 49:
                b.bg = None
            elif 90 <= c <= 97:
                b.fg = COLORS_16[c - 90 + 8]
            elif 100 <= c <= 107:
                b.bg = COLORS_16[c - 100 + 8]
            i += 1

    def _color256(self, n: int) -> str:
        if n < 16:
            return COLORS_16[n]
        elif n < 232:
            n -= 16
            r, g, b = (n // 36) * 51, ((n // 6) % 6) * 51, (n % 6) * 51
            return f'#{r:02x}{g:02x}{b:02x}'
        else:
            v = (n - 232) * 10 + 8
            return f'#{v:02x}{v:02x}{v:02x}'

    def render(self) -> list:
        """Return list of (text, format) tuples for display"""
        result = []
        for row in self.buf.grid:
            line_parts = []
            current_fmt = None
            current_text = ""

            for cell in row:
                fmt = (cell.fg, cell.bg, cell.bold, cell.italic, cell.underline, cell.dim)
                if fmt != current_fmt:
                    if current_text:
                        line_parts.append((current_text, current_fmt))
                    current_text = cell.char
                    current_fmt = fmt
                else:
                    current_text += cell.char

            if current_text:
                line_parts.append((current_text, current_fmt))
            line_parts.append(('\n', current_fmt))
            result.extend(line_parts)

        return result


class TerminalOutput(QTextEdit):
    """Terminal display widget"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setFont(QFont("Cascadia Code", 11))
        self.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.emu = TerminalEmulator()
        self._simple_mode = True  # Start in simple append mode

        self.type_colors = {
            'command': '#89b4fa', 'stdout': '#cdd6f4', 'stderr': '#f38ba8',
            'error': '#f38ba8', 'system': '#a6e3a1', 'stdin': '#f9e2af',
        }

    def append_line(self, text: str, line_type: str = 'stdout'):
        """Simple line append (non-TUI mode)"""
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(self.type_colors.get(line_type, self.type_colors['stdout'])))

        prefix = '$ ' if line_type == 'command' else '[ERROR] ' if line_type == 'error' else ''
        cursor.insertText(prefix + text + '\n', fmt)
        self.ensureCursorVisible()

    def append_raw(self, text: str):
        """Process raw PTY output"""
        if self._simple_mode:
            self._append_simple(text)
        else:
            self._append_buffered(text)

    def _append_simple(self, text: str):
        """Simple append mode - strip escapes, append text"""
        # Strip OSC sequences (title, etc): ESC ] ... BEL or ESC \
        text = re.sub(r'\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)?', '', text)
        # Strip CSI sequences: ESC [ ... letter
        text = re.sub(r'\x1b\[[^a-zA-Z]*[a-zA-Z]', '', text)
        # Strip other escapes
        text = re.sub(r'\x1b.', '', text)
        # Strip OSC fragments without ESC (like "0;title")
        text = re.sub(r'^\d+;[^\n]*\n?', '', text, flags=re.MULTILINE)
        # Strip control chars
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)
        text = text.replace('\r\n', '\n').replace('\r', '\n')

        if not text.strip():
            return

        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(DEFAULT_FG))
        cursor.insertText(text, fmt)
        self.ensureCursorVisible()

    def _append_buffered(self, text: str):
        """Full TUI mode with screen buffer"""
        self.emu.feed(text)
        self._render_buffer()

    def _render_buffer(self):
        """Render screen buffer to widget"""
        self.clear()
        cursor = self.textCursor()

        for text, fmt_tuple in self.emu.render():
            if fmt_tuple:
                fg, bg, bold, italic, underline, dim = fmt_tuple
                fmt = QTextCharFormat()
                color = QColor(fg) if fg else QColor(DEFAULT_FG)
                if dim:
                    color = color.darker(150)
                fmt.setForeground(color)
                if bg:
                    fmt.setBackground(QColor(bg))
                if bold:
                    fmt.setFontWeight(QFont.Weight.Bold)
                if italic:
                    fmt.setFontItalic(True)
                if underline:
                    fmt.setFontUnderline(True)
                cursor.insertText(text, fmt)
            else:
                cursor.insertText(text)

        self.ensureCursorVisible()

    def set_tui_mode(self, enabled: bool):
        """Switch between simple and TUI mode"""
        self._simple_mode = not enabled
        if enabled:
            self.emu = TerminalEmulator()

    def clear_output(self):
        self.clear()
        self.emu = TerminalEmulator()


class TerminalInput(QLineEdit):
    """Terminal input with history"""

    command_submitted = Signal(str)
    input_submitted = Signal(str)
    stop_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFont(QFont("Cascadia Code", 11))
        self.setPlaceholderText("Enter command...")
        self.history, self.hist_idx = [], -1
        self.is_running = False
        self.returnPressed.connect(self._submit)

    def _submit(self):
        text = self.text()
        if self.is_running:
            self.input_submitted.emit(text)
        elif text:
            self.command_submitted.emit(text)
            self.history.append(text)
            self.hist_idx = -1
        self.clear()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Up and self.history:
            self.hist_idx = len(self.history) - 1 if self.hist_idx == -1 else max(0, self.hist_idx - 1)
            self.setText(self.history[self.hist_idx])
        elif event.key() == Qt.Key.Key_Down and self.hist_idx != -1:
            self.hist_idx += 1
            self.setText(self.history[self.hist_idx] if self.hist_idx < len(self.history) else "")
            if self.hist_idx >= len(self.history):
                self.hist_idx = -1
        elif event.key() == Qt.Key.Key_C and event.modifiers() & Qt.KeyboardModifier.ControlModifier and self.is_running:
            self.stop_requested.emit()
        else:
            super().keyPressEvent(event)

    def set_process_running(self, running: bool):
        self.is_running = running
        self.setPlaceholderText("Type input... (Ctrl+C to stop)" if running else "Enter command...")


class TerminalWidget(QWidget):
    """Combined terminal widget"""

    command_submitted = Signal(str)
    input_submitted = Signal(str)
    stop_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.output = TerminalOutput()
        layout.addWidget(self.output, stretch=1)

        input_frame = QFrame()
        input_frame.setObjectName("inputFrame")
        input_layout = QVBoxLayout(input_frame)
        input_layout.setContentsMargins(8, 8, 8, 8)
        self.input = TerminalInput()
        input_layout.addWidget(self.input)
        layout.addWidget(input_frame)

        self.input.command_submitted.connect(self.command_submitted)
        self.input.input_submitted.connect(self.input_submitted)
        self.input.stop_requested.connect(self.stop_requested)

    @Slot(str, str)
    def append_output(self, text: str, line_type: str = 'stdout'):
        self.output.append_line(text, line_type)

    @Slot(bool)
    def set_process_running(self, running: bool):
        self.input.set_process_running(running)

    def clear(self):
        self.output.clear_output()

    def focus_input(self):
        self.input.setFocus()
