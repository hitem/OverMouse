# hitem / OverMouse
import sys
import json
import ctypes
import re
import shutil
from pathlib import Path
from PyQt6.QtCore import Qt, QTimer, QPoint, QRect
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QPolygon, QCursor, QImage, QPixmap
from PyQt6.QtWidgets import QApplication, QWidget


APP_NAME = "OverMouse"
STATE_FILE = Path(__file__).with_name("OverMouse.state.json")

SCALE = 0.5
TERMINAL_PREVIEW_SCALE = 0.26
POLL_MS = 12

CURSOR_PIXMAP_SOURCE_W = 180
CURSOR_PIXMAP_SOURCE_H = 190
CURSOR_DIRTY_PADDING = 8

VK_F6 = 0x75
VK_F7 = 0x76
VK_RBUTTON = 0x02

GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x00080000
WS_EX_TRANSPARENT = 0x00000020
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_NOACTIVATE = 0x08000000

HWND_TOPMOST = -1
SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001
SWP_NOACTIVATE = 0x0010
SWP_SHOWWINDOW = 0x0040

ANSI_RESET = "\033[0m"
ANSI_BOLD = "\033[1m"
ANSI_DIM = "\033[2m"

BUTTON_FG = (20, 20, 24)
BUTTON_BG = (255, 210, 80)
BUTTON_BG_ALT = (90, 210, 255)
TEXT_DIM = (150, 150, 160)
FOOTER_COLOR = (255, 210, 80)
FOOTER_DIM = (105, 105, 115)


THEMES = [
    {
        "name": "Pink/Purple",
        "outline_rgb": (55, 47, 90),
        "main_rgb": (226, 72, 178),
        "highlight_rgb": (255, 145, 225),
        "shadow_rgb": (125, 87, 210),
        "line_rgb": (80, 45, 120),
    },
    {
        "name": "Cyan/Blue",
        "outline_rgb": (28, 55, 85),
        "main_rgb": (50, 185, 255),
        "highlight_rgb": (145, 235, 255),
        "shadow_rgb": (45, 95, 210),
        "line_rgb": (20, 70, 140),
    },
    {
        "name": "Lime/Green",
        "outline_rgb": (35, 65, 45),
        "main_rgb": (105, 245, 85),
        "highlight_rgb": (200, 255, 155),
        "shadow_rgb": (40, 155, 95),
        "line_rgb": (25, 105, 65),
    },
    {
        "name": "Amber/Orange",
        "outline_rgb": (85, 52, 25),
        "main_rgb": (255, 155, 45),
        "highlight_rgb": (255, 225, 120),
        "shadow_rgb": (210, 85, 35),
        "line_rgb": (140, 65, 25),
    },
]


def rgb_to_qcolor(rgb: tuple[int, int, int], alpha: int = 255) -> QColor:
    return QColor(rgb[0], rgb[1], rgb[2], alpha)


for theme in THEMES:
    theme["outline"] = rgb_to_qcolor(theme["outline_rgb"])
    theme["main"] = rgb_to_qcolor(theme["main_rgb"])
    theme["highlight"] = rgb_to_qcolor(theme["highlight_rgb"])
    theme["shadow"] = rgb_to_qcolor(theme["shadow_rgb"])
    theme["line"] = rgb_to_qcolor(theme["line_rgb"], 160)


def ansi_fg(rgb: tuple[int, int, int]) -> str:
    return f"\033[38;2;{rgb[0]};{rgb[1]};{rgb[2]}m"


def ansi_bg(rgb: tuple[int, int, int]) -> str:
    return f"\033[48;2;{rgb[0]};{rgb[1]};{rgb[2]}m"


def ansi_button(text: str, bg: tuple[int, int, int] = BUTTON_BG) -> str:
    return f"{ansi_bg(bg)}{ansi_fg(BUTTON_FG)}{ANSI_BOLD} {text} {ANSI_RESET}"


def visible_len(text: str) -> int:
    return len(re.sub(r"\033\[[0-9;]*m", "", text))


def pad_ansi(text: str, width: int) -> str:
    return text + (" " * max(0, width - visible_len(text)))


def scaled(value: int, scale: float) -> int:
    return int(value * scale)


def s(value: int) -> int:
    return int(value * SCALE)


def terminal_width() -> int:
    return shutil.get_terminal_size((100, 24)).columns


def load_state() -> dict:
    if not STATE_FILE.exists():
        return {"theme_index": 0}

    try:
        with STATE_FILE.open("r", encoding="utf-8") as f:
            state = json.load(f)

        theme_index = int(state.get("theme_index", 0))

        if theme_index < 0 or theme_index >= len(THEMES):
            theme_index = 0

        return {"theme_index": theme_index}
    except Exception:
        return {"theme_index": 0}


def save_state(theme_index: int):
    try:
        with STATE_FILE.open("w", encoding="utf-8") as f:
            json.dump({"theme_index": theme_index}, f, indent=2)
    except Exception as e:
        print(f"Could not save state: {e}", flush=True)


def print_separator():
    width = min(terminal_width(), 120)
    print(f"{ansi_fg(FOOTER_DIM)}{'─' * width}{ANSI_RESET}")


def print_footer():
    left = "→ by hitem"
    right = "🖰"

    print(
        f"{ansi_fg(FOOTER_COLOR)}{left}  {right}{ANSI_RESET}"
    )


def draw_cursor_shape(painter: QPainter, theme: dict, scale: float):
    def p(x: int, y: int) -> QPoint:
        return QPoint(scaled(x, scale), scaled(y, scale))

    # Shape tuned so the real gray/iron game cursor sits inside the front tip.
    # The front tip is pulled down/right slightly and the rear wing is made a bit flatter.
    outer = QPolygon(
        [
            p(21, 21),    # front tip, slightly lower/right than before
            p(146, 82),   # right wing
            p(88, 99),    # inner notch
            p(55, 165),   # back tail
        ]
    )

    inner_main = QPolygon(
        [
            p(34, 37),    # fill starts farther inside the iron tip
            p(121, 78),
            p(78, 92),
            p(58, 139),
        ]
    )

    highlight = QPolygon(
        [
            p(35, 38),
            p(77, 58),
            p(65, 105),
        ]
    )

    shadow = QPolygon(
        [
            p(77, 58),
            p(121, 78),
            p(78, 92),
            p(58, 139),
            p(65, 105),
        ]
    )

    outline_pen = QPen(theme["outline"], max(1, scaled(7, scale)))
    outline_pen.setJoinStyle(Qt.PenJoinStyle.MiterJoin)
    outline_pen.setCapStyle(Qt.PenCapStyle.FlatCap)

    painter.setPen(outline_pen)
    painter.setBrush(QBrush(theme["outline"]))
    painter.drawPolygon(outer)

    painter.setPen(Qt.PenStyle.NoPen)

    painter.setBrush(QBrush(theme["main"]))
    painter.drawPolygon(inner_main)

    painter.setBrush(QBrush(theme["highlight"]))
    painter.drawPolygon(highlight)

    painter.setBrush(QBrush(theme["shadow"]))
    painter.drawPolygon(shadow)

    line_pen = QPen(theme["line"], max(1, scaled(2, scale)))
    line_pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)

    painter.setPen(line_pen)
    painter.drawLine(p(77, 58), p(65, 105))
    painter.drawLine(p(65, 105), p(58, 139))

def render_cursor_pixmap(theme: dict) -> QPixmap:
    pixmap = QPixmap(s(CURSOR_PIXMAP_SOURCE_W), s(CURSOR_PIXMAP_SOURCE_H))
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    draw_cursor_shape(painter, theme, SCALE)
    painter.end()

    return pixmap

def average_color_from_region(image: QImage, x0: int, y0: int, x1: int, y1: int):
    r_total = 0
    g_total = 0
    b_total = 0
    count = 0

    for y in range(max(0, y0), min(image.height(), y1)):
        for x in range(max(0, x0), min(image.width(), x1)):
            color = image.pixelColor(x, y)

            if color.alpha() < 20:
                continue

            r_total += color.red()
            g_total += color.green()
            b_total += color.blue()
            count += 1

    if count == 0:
        return None

    return (
        int(r_total / count),
        int(g_total / count),
        int(b_total / count),
    )


def render_terminal_cursor(theme: dict, active: bool) -> list[str]:
    width = 52
    height = 54

    image = QImage(width, height, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)

    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.translate(1, 0)
    draw_cursor_shape(painter, theme, TERMINAL_PREVIEW_SCALE)
    painter.end()

    char_w = 3
    char_h = 6

    rows = []

    title = f"> {theme['name']}" if active else f"  {theme['name']}"
    rows.append(title)

    for y in range(0, height, char_h):
        line = ""

        for x in range(0, width, char_w):
            top = average_color_from_region(
                image,
                x,
                y,
                x + char_w,
                y + char_h // 2,
            )
            bottom = average_color_from_region(
                image,
                x,
                y + char_h // 2,
                x + char_w,
                y + char_h,
            )

            if top is None and bottom is None:
                line += " "
            elif top is not None and bottom is None:
                line += f"{ansi_fg(top)}▀{ANSI_RESET}"
            elif top is None and bottom is not None:
                line += f"{ansi_fg(bottom)}▄{ANSI_RESET}"
            else:
                line += f"{ansi_fg(top)}{ansi_bg(bottom)}▀{ANSI_RESET}"

        rows.append(line.rstrip())

    while rows and visible_len(rows[-1]) == 0:
        rows.pop()

    return rows


def print_terminal_preview(active_index: int):
    print()
    print(f"{ANSI_BOLD}{APP_NAME} running{ANSI_RESET}")
    print()

    previews = [
        render_terminal_cursor(theme, i == active_index)
        for i, theme in enumerate(THEMES)
    ]

    column_width = 22
    max_lines = max(len(p) for p in previews)

    print("Cursor themes:")
    print()

    for line_index in range(max_lines):
        row_parts = []

        for preview in previews:
            text = preview[line_index] if line_index < len(preview) else ""
            row_parts.append(pad_ansi(text, column_width))

        print("".join(row_parts).rstrip())

    print()
    print("Hotkeys:")
    print(f"  {ansi_button('F6')} start/stop overlay")
    print(f"  {ansi_button('F7')} toggle cursor theme")
    print(f"  {ansi_button('Right mouse held', BUTTON_BG_ALT)} temporarily hide overlay")
    print(f"  {ansi_button('Ctrl+C', BUTTON_BG_ALT)} abort from this terminal")
    print()
    print(f"Active theme: {THEMES[active_index]['name']}")
    print(f"{ansi_fg(TEXT_DIM)}State file: {STATE_FILE}{ANSI_RESET}")
    print()
    print_separator()
    print_footer()
    print_separator()
    print()


class ScreenOverlay(QWidget):
    def __init__(self, controller, screen):
        super().__init__()

        self.controller = controller
        self.screen = screen
        self.user32 = ctypes.windll.user32

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowTransparentForInput
        )

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)

        self.setGeometry(screen.geometry())

        QTimer.singleShot(0, self.make_clickthrough)

    def make_clickthrough(self):
        hwnd = int(self.winId())

        style = self.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        style |= WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE
        self.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)

        self.user32.SetWindowPos(
            hwnd,
            HWND_TOPMOST,
            0,
            0,
            0,
            0,
            0,
            SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_SHOWWINDOW,
        )

    def paintEvent(self, event):
        painter = QPainter(self)

        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
        painter.fillRect(event.rect(), Qt.GlobalColor.transparent)

        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)

        if not self.controller.overlay_enabled:
            return

        global_pos = self.controller.last_pos
        if global_pos is None:
            return

        active_screen = self.controller.active_screen
        if active_screen is None:
            return

        if active_screen.name() != self.screen.name():
            return

        local_pos = self.mapFromGlobal(global_pos)
        draw_pos = local_pos - self.controller.hotspot + self.controller.draw_offset

        painter.drawPixmap(draw_pos, self.controller.cursor_pixmaps[self.controller.theme_index])


class CursorOverlay:
    def __init__(self):
        self.user32 = ctypes.windll.user32

        state = load_state()
        self.theme_index = state["theme_index"]

        self.overlay_enabled = True
        self.temporarily_hidden = False

        self.last_f6_down = False
        self.last_f7_down = False

        self.last_pos = None
        self.active_screen = None
        self.last_screen_name = None
        self.last_draw_rect_by_screen = {}

        self.hotspot = QPoint(s(24), s(24))
        self.draw_offset = QPoint(s(5), s(5))

        self.cursor_pixmaps = [
            render_cursor_pixmap(theme)
            for theme in THEMES
        ]

        self.cursor_pixmap_size = self.cursor_pixmaps[0].size()

        self.overlays = []
        self.screen_signature = None

        self.rebuild_overlays()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_overlay)
        self.timer.start(POLL_MS)

    def screen_signature_now(self):
        return [
            (
                screen.name(),
                screen.geometry().x(),
                screen.geometry().y(),
                screen.geometry().width(),
                screen.geometry().height(),
            )
            for screen in QApplication.screens()
        ]

    def rebuild_overlays(self):
        for overlay in self.overlays:
            overlay.hide()
            overlay.deleteLater()

        self.overlays = []

        for screen in QApplication.screens():
            overlay = ScreenOverlay(self, screen)
            overlay.show()
            self.overlays.append(overlay)

        self.screen_signature = self.screen_signature_now()

    def screens_changed(self) -> bool:
        return self.screen_signature_now() != self.screen_signature

    def current_theme(self) -> dict:
        return THEMES[self.theme_index]

    def show(self):
        for overlay in self.overlays:
            if not overlay.isVisible():
                overlay.show()

    def hide(self):
        for overlay in self.overlays:
            if overlay.isVisible():
                overlay.hide()

    def update_active_overlay_only(self):
        if self.active_screen is None or self.last_pos is None:
            return

        active_name = self.active_screen.name()

        for overlay in self.overlays:
            screen_name = overlay.screen.name()

            old_rect = self.last_draw_rect_by_screen.get(screen_name)

            if screen_name == active_name:
                local_pos = overlay.mapFromGlobal(self.last_pos)
                draw_pos = local_pos - self.hotspot + self.draw_offset

                new_rect = QRect(draw_pos, self.cursor_pixmap_size).adjusted(
                    -CURSOR_DIRTY_PADDING,
                    -CURSOR_DIRTY_PADDING,
                    CURSOR_DIRTY_PADDING,
                    CURSOR_DIRTY_PADDING,
                )

                if old_rect is not None:
                    overlay.update(old_rect)

                overlay.update(new_rect)
                self.last_draw_rect_by_screen[screen_name] = new_rect
            else:
                if old_rect is not None:
                    overlay.update(old_rect)
                    self.last_draw_rect_by_screen.pop(screen_name, None)

    def key_down(self, vk_code: int) -> bool:
        return bool(self.user32.GetAsyncKeyState(vk_code) & 0x8000)

    def handle_hotkeys(self) -> bool:
        changed = False

        f6_down = self.key_down(VK_F6)
        f7_down = self.key_down(VK_F7)

        if f6_down and not self.last_f6_down:
            self.overlay_enabled = not self.overlay_enabled
            changed = True

            if self.overlay_enabled:
                self.show()
                print(f"{ANSI_BOLD}Overlay started{ANSI_RESET}", flush=True)
            else:
                self.hide()
                print(f"{ANSI_BOLD}Overlay stopped{ANSI_RESET}", flush=True)

        if f7_down and not self.last_f7_down:
            self.theme_index = (self.theme_index + 1) % len(THEMES)
            save_state(self.theme_index)
            changed = True

            theme = self.current_theme()
            print(f"Theme changed to: {theme['name']}", flush=True)

        self.last_f6_down = f6_down
        self.last_f7_down = f7_down

        return changed

    def update_overlay(self):
        changed = self.handle_hotkeys()

        if not self.overlay_enabled:
            return

        right_down = self.key_down(VK_RBUTTON)

        if right_down:
            if not self.temporarily_hidden:
                self.temporarily_hidden = True
                self.hide()
            return

        if self.temporarily_hidden:
            self.temporarily_hidden = False
            self.show()
            changed = True

        current_pos = QCursor.pos()
        current_screen = QApplication.screenAt(current_pos)

        if current_screen is None:
            current_screen = QApplication.primaryScreen()

        current_screen_name = current_screen.name() if current_screen else None

        pos_changed = self.last_pos != current_pos
        screen_changed = self.last_screen_name != current_screen_name

        if not changed and not pos_changed and not screen_changed:
            return

        self.last_pos = current_pos
        self.active_screen = current_screen
        self.last_screen_name = current_screen_name

        self.update_active_overlay_only()


def main():
    app = QApplication(sys.argv)

    overlay = CursorOverlay()

    print_terminal_preview(overlay.theme_index)

    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        overlay.hide()
        print(f"{ANSI_BOLD}OverMouse aborted.{ANSI_RESET}", flush=True)
        sys.exit(0)


if __name__ == "__main__":
    main()