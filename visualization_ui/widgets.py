from ursina import Entity, Text, color, curve, destroy, mouse

from .panels import PanelBlock, TextHandle


def normalize_color(value, fallback):
    if value is None:
        return fallback
    if isinstance(value, tuple) and len(value) == 3:
        return color.rgb(value[0], value[1], value[2])
    if isinstance(value, tuple) and len(value) == 4:
        return color.rgba(value[0], value[1], value[2], value[3])
    return value


class BarChartWidget:
    def __init__(
        self,
        parent,
        *,
        center_x: float,
        baseline_y: float,
        chart_width: float,
        axis_parent,
        axis_label_y: float,
        min_bar_height: float,
        default_bar_color,
    ):
        self.parent = parent
        self.center_x = center_x
        self.baseline_y = baseline_y
        self.chart_width = chart_width
        self.axis_parent = axis_parent
        self.axis_label_y = axis_label_y
        self.min_bar_height = min_bar_height
        self.default_bar_color = default_bar_color
        self.bars = []
        self.axis_labels = []
        self.value_labels = []

    def clear(self):
        for entity in self.bars + self.axis_labels + self.value_labels:
            destroy(entity)
        self.bars = []
        self.axis_labels = []
        self.value_labels = []

    def rebuild(
        self,
        *,
        count: int,
        bar_width: float,
        base_height: float,
        y: float,
        label_indices,
        label_scale_fn,
        show_value_labels: bool = False,
        value_label_y: float | None = None,
        value_label_scale: float = 0.34,
        value_label_color=None,
        bar_color=None,
        hover_key_name: str = "state_index",
    ):
        self.clear()
        slot_width = self.chart_width / count
        start_x = self.center_x - self.chart_width / 2 + slot_width / 2
        for index in range(count):
            x = start_x + index * slot_width
            initial_color = normalize_color(bar_color, self.default_bar_color)
            bar = Entity(
                parent=self.parent,
                model="quad",
                position=(x, y, -0.03),
                scale=(bar_width, base_height, 1),
                color=initial_color,
                collider="box",
            )
            bar.highlight_color = initial_color
            bar.original_color = initial_color
            bar.on_mouse_enter = lambda current=bar: setattr(current, "color", current.original_color)
            bar.on_mouse_exit = lambda current=bar: setattr(current, "color", current.original_color)
            setattr(bar, hover_key_name, index)
            self.bars.append(bar)
            if index in label_indices:
                self.axis_labels.append(
                    Text(
                        parent=self.axis_parent,
                        text=str(index),
                        position=(x, self.axis_label_y, 0),
                        origin=(0, 0),
                        scale=label_scale_fn(index),
                        color=color.rgb(214, 222, 236),
                    )
                )
            if show_value_labels:
                self.value_labels.append(
                    Text(
                        parent=self.parent,
                        text="",
                        position=(x, value_label_y if value_label_y is not None else y + 0.035),
                        origin=(0, 0),
                        scale=value_label_scale,
                        color=normalize_color(value_label_color, color.rgb(196, 205, 218)),
                    )
                )

    def set_bar(self, index: int, *, height: float, center_y: float, bar_color, animated: bool, duration: float):
        bar = self.bars[index]
        if animated:
            bar.animate("scale_y", height, duration=duration, curve=curve.out_cubic)
            bar.animate("y", center_y, duration=duration, curve=curve.out_cubic)
        else:
            bar.scale_y = height
            bar.y = center_y
        new_color = normalize_color(bar_color, self.default_bar_color)
        bar.color = new_color
        bar.highlight_color = new_color
        bar.original_color = new_color

    def set_value_label(self, index: int, text: str, y: float):
        if index < len(self.value_labels):
            self.value_labels[index].text = text
            self.value_labels[index].y = y

    def hovered_index(self, attr_name: str) -> int | None:
        hovered = mouse.hovered_entity
        if hovered is None or hovered not in self.bars or not hasattr(hovered, attr_name):
            return None
        return getattr(hovered, attr_name)


class ReferenceLine:
    def __init__(self, parent, *, x: float, y: float, width: float, thickness: float, line_color):
        self.entity = Entity(
            parent=parent,
            model="quad",
            position=(x, y, -0.03),
            scale=(width, thickness, 1),
            color=line_color,
        )

    def set_y(self, y: float, animated: bool, duration: float):
        if animated:
            self.entity.animate("y", y, duration=duration, curve=curve.out_cubic)
        else:
            self.entity.y = y


class MeasurementLaneWidget:
    def __init__(self, parent, *, center_x: float, center_y: float, width: float, left: float):
        self.parent = parent
        self.center_x = center_x
        self.center_y = center_y
        self.width = width
        self.left = left
        self.line = Entity(
            parent=parent,
            model="quad",
            position=(center_x, center_y, -0.03),
            scale=(width, 0.004, 1),
            color=color.rgba(84, 108, 146, 90),
        )
        self.dot = Entity(
            parent=parent,
            model="quad",
            position=(left, center_y, -0.04),
            scale=(0.016, 0.016, 1),
            color=color.rgb(214, 182, 112),
        )
        self.fraction_markers = []
        self.peak_markers = []

    def fraction_x(self, fraction: float) -> float:
        return self.left + self.width * fraction

    def set_fraction(self, fraction: float, animated: bool, duration: float):
        target_x = self.fraction_x(fraction)
        if animated:
            self.dot.animate("x", target_x, duration=duration, curve=curve.out_cubic)
        else:
            self.dot.x = target_x

    def clear_markers(self):
        for marker in self.fraction_markers + self.peak_markers:
            destroy(marker)
        self.fraction_markers = []
        self.peak_markers = []

    def rebuild_markers(self, order: int | None):
        self.clear_markers()
        if not order or order <= 1:
            return
        for numerator in range(order + 1):
            fraction = numerator / order
            size_y = 0.032 if numerator in (0, order) else 0.022
            self.fraction_markers.append(
                Entity(
                    parent=self.parent,
                    model="quad",
                    position=(self.fraction_x(fraction), self.center_y - 0.002, -0.025),
                    scale=(0.004, size_y, 1),
                    color=color.rgba(92, 114, 148, 70),
                )
            )
        for numerator in range(order):
            fraction = numerator / order
            self.peak_markers.append(
                Entity(
                    parent=self.parent,
                    model="quad",
                    position=(self.fraction_x(fraction), self.center_y + 0.020, -0.024),
                    scale=(0.010, 0.010, 1),
                    color=color.rgba(170, 138, 88, 85),
                )
            )


class StageTrackerWidget:
    def __init__(self, panel: PanelBlock, stage_names: list[tuple[str, str]]):
        self.panel = panel
        self.stage_labels = {}
        start_x = 0.0
        for offset, (stage_key, title) in enumerate(stage_names):
            y = 0.085 - offset * 0.045
            label = Text(
                parent=self.panel.content,
                text=title,
                position=(start_x, y - 0.006, -0.12),
                origin=(0, 0),
                scale=0.58,
                color=color.rgb(208, 216, 230),
            )
            self.stage_labels[stage_key] = label

    def set_active(self, stage_name: str, active_palette: dict[str, object], inactive_color):
        for key in self.stage_labels:
            self.stage_labels[key].color = color.rgb(208, 216, 230)


class TextStackWidget:
    def __init__(self, panel: PanelBlock, specs: list[dict]):
        self.handles = {}
        for spec in specs:
            self.handles[spec["name"]] = panel.add_text(
                spec.get("text", ""),
                x_ratio=spec.get("x_ratio", 0.0),
                y_ratio=spec.get("y_ratio", 0.0),
                scale=spec.get("scale", 0.4),
                text_color=spec.get("text_color", color.white),
                origin=spec.get("origin", (0, 0)),
                parent=spec.get("parent"),
            )

    def set_text(self, name: str, text: str):
        self.handles[name].set_text(text)

    def clear(self, name: str):
        self.handles[name].clear()

    def get(self, name: str) -> TextHandle:
        return self.handles[name]
