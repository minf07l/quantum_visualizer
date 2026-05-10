from ursina import Button, Text, color

from .layout import RectRegion
from .panels import PanelBlock, TextHandle
from .theme import Sizes, Spacing


class ButtonHandle:
    def __init__(self, button: Button, label: TextHandle):
        self.button = button
        self.label = label

    def set_text(self, text: str):
        self.label.set_text(text)

    @property
    def on_click(self):
        return self.button.on_click

    @on_click.setter
    def on_click(self, value):
        self.button.on_click = value


def create_button(
    parent,
    position,
    text: str,
    on_click,
    accent: bool = False,
    scale=(Sizes.button_width, Sizes.button_height),
    label_region: RectRegion | None = None,
) -> ButtonHandle:
    base_color = color.rgb(56, 72, 102) if not accent else color.rgb(86, 122, 214)
    hover_color = color.rgb(76, 92, 124) if not accent else color.rgb(106, 142, 232)
    press_color = color.rgb(40, 54, 78) if not accent else color.rgb(70, 106, 194)
    button = Button(
        parent=parent,
        text="",
        position=(position[0], position[1], -0.06),
        scale=(scale[0], scale[1], 1),
        color=base_color,
        highlight_color=hover_color,
        pressed_color=press_color,
    )
    button.on_click = on_click
    label_entity = Text(
        parent=parent,
        text=text,
        position=(position[0], position[1] - 0.010, -0.12),
        origin=(0, 0),
        scale=0.50 if scale[0] <= Sizes.button_width else 0.54,
        color=color.white,
    )
    label = TextHandle(
        label_entity,
        region=label_region,
        panel_region=label_region,
        base_scale=label_entity.scale,
        mode="wrap_shrink" if label_region is not None else "plain",
    )
    label.set_text(text)
    return ButtonHandle(button, label)


class ControlGrid:
    def __init__(
        self,
        panel: PanelBlock,
        *,
        rows: int,
        columns: int = 2,
        region: RectRegion | None = None,
        x_padding: float = Spacing.md,
        y_padding: float = Spacing.md,
        h_gap: float = Spacing.sm,
        v_gap: float = Spacing.sm,
    ):
        self.panel = panel
        self.rows = rows
        self.columns = columns
        self.region = region
        self.x_padding = x_padding
        self.y_padding = y_padding
        self.h_gap = h_gap
        self.v_gap = v_gap

    def _grid_region(self) -> RectRegion:
        base = self.region or self.panel.region
        return base.inset(self.x_padding, self.y_padding)

    def _cell_region(self, row: int, col: int) -> RectRegion:
        rows = self._grid_region().split_rows([1] * self.rows, gap=self.v_gap)
        cols = rows[row].split_columns([1] * self.columns, gap=self.h_gap)
        return cols[col]

    def button_position(self, row: int, col: int) -> tuple[float, float]:
        cell = self._cell_region(row, col)
        local_x = cell.center_x - self.panel.region.center_x
        local_y = cell.center_y - self.panel.region.center_y
        return local_x, local_y

    def add_button(self, text: str, row: int, col: int, on_click, accent: bool = False) -> ButtonHandle:
        cell = self._cell_region(row, col)
        return create_button(
            self.panel.content,
            self.button_position(row, col),
            text,
            on_click,
            accent=accent,
            label_region=cell.inset(Spacing.xs, Spacing.xs),
        )
