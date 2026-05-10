import textwrap

from ursina import Entity, Text, color

from .layout import RectRegion


def normalize_text_color(value):
    if isinstance(value, tuple) and len(value) == 3:
        return color.rgb(value[0], value[1], value[2])
    return value


class TextHandle:
    def __init__(
        self,
        text_entity: Text,
        *,
        region: RectRegion | None = None,
        panel_region: RectRegion | None = None,
        base_scale: float | None = None,
        mode: str = "plain",
    ):
        self._text = text_entity
        self._region = region
        self._panel_region = panel_region
        self._base_scale = self._normalize_scale(base_scale if base_scale is not None else text_entity.scale)
        self._mode = mode

    def set_text(self, text: str):
        if self._region is None or self._panel_region is None or self._mode == "plain":
            self._text.text = text
            return

        wrapped_text = text
        if self._mode in {"wrap", "wrap_shrink", "shrink_wrap"}:
            wrapped_text = self._wrap_text(text, self._base_scale)

        target_scale = self._base_scale
        if self._mode in {"shrink", "wrap_shrink", "shrink_wrap"}:
            target_scale = self._fit_scale(text)
            if self._mode in {"wrap_shrink", "shrink_wrap"}:
                wrapped_text = self._wrap_text(text, target_scale)

        self._text.scale = target_scale
        self._text.text = wrapped_text

    def set_y(self, y: float):
        self._text.y = y

    def set_scale(self, scale: float):
        self._base_scale = self._normalize_scale(scale)
        self._text.scale = self._base_scale

    def clear(self):
        self._text.text = ""
        self._text.scale = self._base_scale

    @property
    def text(self) -> str:
        return self._text.text

    @property
    def entity(self) -> Text:
        return self._text

    def _fit_scale(self, text: str) -> float:
        if self._region is None:
            return self._base_scale
        scale = self._base_scale
        min_scale = max(0.34, self._base_scale * 0.84)
        while scale > min_scale:
            wrapped = self._wrap_text(text, scale)
            if self._fits(wrapped, scale):
                return scale
            scale = round(scale - 0.02, 3)
        return min_scale

    def _fits(self, wrapped_text: str, scale: float) -> bool:
        if self._region is None:
            return True
        lines = max(1, wrapped_text.count("\n") + 1)
        estimated_line_height = scale * 0.10
        return lines * estimated_line_height <= self._region.height

    def _wrap_text(self, text: str, scale: float) -> str:
        if self._region is None:
            return text
        chars_per_line = max(8, int(self._region.width / max(0.001, scale * 0.022)))
        paragraphs = text.split("\n")
        wrapped = [
            textwrap.fill(paragraph, width=chars_per_line, break_long_words=False, break_on_hyphens=False)
            if paragraph.strip()
            else ""
            for paragraph in paragraphs
        ]
        return "\n".join(wrapped)

    @staticmethod
    def _normalize_scale(scale) -> float:
        if isinstance(scale, (int, float)):
            return float(scale)
        if hasattr(scale, "x"):
            return float(scale.x)
        return float(scale)


class PanelBlock:
    def __init__(self, parent, region: RectRegion, inner: bool = False):
        self.parent = parent
        self.region = region
        self.root = Entity(parent=parent)
        self.body = Entity(
            parent=self.root,
            model="quad",
            position=(region.center_x, region.center_y, 0.02),
            scale=(region.width, region.height, 1),
            color=color.rgb(14, 20, 32) if not inner else color.rgb(20, 28, 42),
        )
        self.top_border = Entity(
            parent=self.root,
            model="quad",
            position=(region.center_x, region.top - 0.002, 0.01),
            scale=(region.width, 0.004, 1),
            color=color.rgb(78, 92, 120),
        )
        self.bottom_border = Entity(
            parent=self.root,
            model="quad",
            position=(region.center_x, region.bottom + 0.002, 0.01),
            scale=(region.width, 0.004, 1),
            color=color.rgb(78, 92, 120),
        )
        self.left_border = Entity(
            parent=self.root,
            model="quad",
            position=(region.left + 0.002, region.center_y, 0.01),
            scale=(0.004, region.height, 1),
            color=color.rgb(78, 92, 120),
        )
        self.right_border = Entity(
            parent=self.root,
            model="quad",
            position=(region.right - 0.002, region.center_y, 0.01),
            scale=(0.004, region.height, 1),
            color=color.rgb(78, 92, 120),
        )
        self.content = Entity(parent=parent, position=(region.center_x, region.center_y, -0.08))

    def content_region(self, x_padding: float = 0.0, y_padding: float = 0.0) -> RectRegion:
        return self.region.inset(x_padding, y_padding)

    def local_point(self, x_ratio: float = 0.0, y_ratio: float = 0.0, z: float = -0.12) -> tuple[float, float, float]:
        return self.region.relative_to_center(x_ratio, y_ratio, z)

    def add_text(
        self,
        text: str,
        *,
        x_ratio: float = 0.0,
        y_ratio: float = 0.0,
        z: float = -0.12,
        scale: float = 0.4,
        text_color=color.white,
        origin=(0, 0),
        parent=None,
        mode: str = "plain",
    ) -> TextHandle:
        return TextHandle(Text(
            parent=parent or self.content,
            text=text,
            position=self.local_point(x_ratio, y_ratio, z),
            origin=origin,
            scale=scale,
            color=normalize_text_color(text_color),
        ), base_scale=scale, mode=mode)

    def add_text_in_region(
        self,
        region: RectRegion,
        text: str,
        *,
        scale: float = 0.4,
        text_color=color.white,
        origin=(0, 0),
        parent=None,
        z: float = -0.12,
        mode: str = "wrap_shrink",
    ) -> TextHandle:
        local_x = region.center_x - self.region.center_x
        local_y = region.center_y - self.region.center_y
        return TextHandle(Text(
            parent=parent or self.content,
            text=text,
            position=(local_x, local_y, z),
            origin=origin,
            scale=scale,
            color=normalize_text_color(text_color),
        ), region=region, panel_region=self.region, base_scale=scale, mode=mode)
