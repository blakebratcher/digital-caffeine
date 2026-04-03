"""PC-98 Textual application - main display driver."""

from __future__ import annotations

import time

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.widgets import Static

from digital_caffeine.animations import MODE_DISPLAY, format_time
from digital_caffeine.constants import Mode
from digital_caffeine.engine import CaffeineEngine
from digital_caffeine.pc98.dialogue import format_dialogue_box
from digital_caffeine.pc98.palette import (
    DEEP_NAVY,
    GOLD,
    MAGENTA,
    OFF_WHITE,
    PALETTE,
    STEEL_BLUE,
)
from digital_caffeine.pc98.scene import CoffeeScene
from digital_caffeine.pc98.status import format_status_text

_FPS = 24

# Box drawing for title bar
_H = "\u2550"
_DIAMOND = "\u25c6"


class SceneWidget(Static):
    """Displays the Pillow-rendered pixel art scene as half-block characters."""

    DEFAULT_CSS = """
    SceneWidget {
        width: auto;
        height: auto;
        padding: 0 1;
    }
    """


class StatusWidget(Static):
    """Displays the right-side status panel."""

    DEFAULT_CSS = """
    StatusWidget {
        width: 30;
        height: 100%;
        padding: 0 0;
    }
    """


class DialogueWidget(Static):
    """Displays the bottom VN dialogue box."""

    DEFAULT_CSS = """
    DialogueWidget {
        width: 100%;
        height: 4;
        padding: 0 1;
    }
    """


class TitleWidget(Static):
    """Startup title card shown briefly on launch."""

    DEFAULT_CSS = f"""
    TitleWidget {{
        width: 100%;
        height: 100%;
        background: {PALETTE[DEEP_NAVY]};
        color: {PALETTE[GOLD]};
        content-align: center middle;
        text-align: center;
    }}
    """


class PC98App(App):
    """PC-98 visual novel style keep-awake display."""

    TITLE = "Digital Caffeine"
    CSS = f"""
    Screen {{
        background: {PALETTE[DEEP_NAVY]};
    }}
    #title-bar {{
        width: 100%;
        height: 1;
        background: {PALETTE[STEEL_BLUE]};
        color: {PALETTE[GOLD]};
        padding: 0 1;
    }}
    #main-area {{
        width: 100%;
        height: 1fr;
    }}
    #scene-area {{
        width: 1fr;
        height: 100%;
    }}
    #status-area {{
        width: 30;
        height: 100%;
        border-left: solid {PALETTE[STEEL_BLUE]};
    }}
    #dialogue-area {{
        width: 100%;
        height: 4;
        border-top: solid {PALETTE[STEEL_BLUE]};
        padding: 0 1;
    }}
    #title-screen {{
        width: 100%;
        height: 100%;
        background: {PALETTE[DEEP_NAVY]};
        color: {PALETTE[GOLD]};
        content-align: center middle;
        text-align: center;
    }}
    """

    BINDINGS = [
        Binding("q", "quit", "Quit", show=False),
        Binding("space", "toggle_pause", "Pause/Resume", show=False),
        Binding("ctrl+c", "quit", "Exit"),
    ]

    def __init__(
        self,
        engine: CaffeineEngine,
        mode: Mode,
        duration_seconds: int | None,
        interval: int,
        simulate: bool,
    ) -> None:
        super().__init__()
        self._engine = engine
        self._mode = mode
        self._duration_seconds = duration_seconds
        self._interval = interval
        self._simulate = simulate
        self._scene = CoffeeScene()
        self._frame = 0
        self._start_time = time.monotonic()
        self._title_done = False

    def compose(self) -> ComposeResult:
        gold = PALETTE[GOLD]
        blue = PALETTE[STEEL_BLUE]
        mag = PALETTE[MAGENTA]
        white = PALETTE[OFF_WHITE]

        # Title card with PC-98 drama
        title_text = (
            f"\n\n\n"
            f"[{blue}]{_H * 20}[/]\n"
            f"\n"
            f"[bold {gold}]{_DIAMOND}  DIGITAL CAFFEINE  {_DIAMOND}[/]\n"
            f"\n"
            f"[{blue}]{_H * 20}[/]\n"
            f"\n"
            f"[{mag}]PC-98 ver.[/]  [{white} dim]press Q to quit, SPACE to pause[/]"
        )
        yield TitleWidget(title_text, id="title-screen")

        # Title bar
        bar_text = (
            f"  [{gold}]{_DIAMOND} Digital Caffeine[/]"
            f"{'':>30}"
            f"[dim]Q=quit  SPACE=pause[/]"
        )
        yield Static(bar_text, id="title-bar")

        with Horizontal(id="main-area"):
            yield SceneWidget("", id="scene-area")
            yield StatusWidget("", id="status-area")
        yield DialogueWidget("", id="dialogue-area")

    def on_mount(self) -> None:
        self.query_one("#title-bar").display = False
        self.query_one("#main-area").display = False
        self.query_one("#dialogue-area").display = False
        self.set_timer(2.0, self.dismiss_title)

    def dismiss_title(self) -> None:
        """Hide title card and show main UI."""
        self.query_one("#title-screen").display = False
        self.query_one("#title-bar").display = True
        self.query_one("#main-area").display = True
        self.query_one("#dialogue-area").display = True
        self._title_done = True
        self.set_interval(1.0 / _FPS, self.animate_frame)

    def animate_frame(self) -> None:
        self._frame += 1
        elapsed = int(time.monotonic() - self._start_time)
        paused = self._engine.is_paused

        if self._duration_seconds is not None and elapsed >= self._duration_seconds:
            self._engine.stop()
            self.exit()
            return

        if not paused:
            self._scene.update()

        scene_text = self._scene.render()
        self.query_one("#scene-area", Static).update(scene_text)

        if self._duration_seconds is not None:
            remaining = max(0, self._duration_seconds - elapsed)
            remaining_str = format_time(remaining)
            progress_pct = min(100, int(elapsed / self._duration_seconds * 100))
        else:
            remaining_str = "Indefinite"
            progress_pct = None

        status_text = format_status_text(
            active=self._engine.is_active,
            paused=paused,
            mode_label=MODE_DISPLAY.get(self._mode, str(self._mode)),
            uptime_seconds=elapsed,
            remaining_str=remaining_str,
            interval=self._interval,
            simulate=self._simulate,
            frame=self._frame,
            progress_pct=progress_pct,
        )
        self.query_one("#status-area", Static).update(status_text)

        dialogue_text = format_dialogue_box(self._frame, paused=paused)
        self.query_one("#dialogue-area", Static).update(dialogue_text)

    def action_toggle_pause(self) -> None:
        self._engine.toggle_pause()

    def action_quit(self) -> None:
        self._engine.stop()
        self.exit()
