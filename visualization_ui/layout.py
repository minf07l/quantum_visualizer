from dataclasses import dataclass


@dataclass(frozen=True)
class RectRegion:
    center_x: float
    center_y: float
    width: float
    height: float

    @property
    def left(self) -> float:
        return self.center_x - self.width / 2

    @property
    def right(self) -> float:
        return self.center_x + self.width / 2

    @property
    def top(self) -> float:
        return self.center_y + self.height / 2

    @property
    def bottom(self) -> float:
        return self.center_y - self.height / 2

    def point(self, x_ratio: float = 0.0, y_ratio: float = 0.0, z: float = 0.0) -> tuple[float, float, float]:
        return (
            self.center_x + x_ratio * self.width / 2,
            self.center_y + y_ratio * self.height / 2,
            z,
        )

    def relative_to_center(self, x_ratio: float = 0.0, y_ratio: float = 0.0, z: float = 0.0) -> tuple[float, float, float]:
        return (x_ratio * self.width / 2, y_ratio * self.height / 2, z)

    def subregion(
        self,
        *,
        x_ratio: float = 0.0,
        y_ratio: float = 0.0,
        width_ratio: float = 1.0,
        height_ratio: float = 1.0,
    ) -> "RectRegion":
        return RectRegion(
            self.center_x + x_ratio * self.width / 2,
            self.center_y + y_ratio * self.height / 2,
            self.width * width_ratio,
            self.height * height_ratio,
        )

    def inset(self, x_padding: float = 0.0, y_padding: float = 0.0) -> "RectRegion":
        return RectRegion(
            self.center_x,
            self.center_y,
            max(0.0, self.width - 2 * x_padding),
            max(0.0, self.height - 2 * y_padding),
        )

    def split_columns(self, weights: list[float], gap: float = 0.0) -> list["RectRegion"]:
        total_weight = sum(weights)
        total_gap = gap * max(0, len(weights) - 1)
        usable_width = self.width - total_gap
        left = self.left
        regions = []
        for index, weight in enumerate(weights):
            width = usable_width * (weight / total_weight)
            center_x = left + width / 2
            regions.append(RectRegion(center_x, self.center_y, width, self.height))
            left += width
            if index < len(weights) - 1:
                left += gap
        return regions

    def split_rows(self, weights: list[float], gap: float = 0.0) -> list["RectRegion"]:
        total_weight = sum(weights)
        total_gap = gap * max(0, len(weights) - 1)
        usable_height = self.height - total_gap
        top = self.top
        regions = []
        for index, weight in enumerate(weights):
            height = usable_height * (weight / total_weight)
            center_y = top - height / 2
            regions.append(RectRegion(self.center_x, center_y, self.width, height))
            top -= height
            if index < len(weights) - 1:
                top -= gap
        return regions


class VisualizationLayout:
    def __init__(self):
        self.left_top = RectRegion(-0.55, 0.29, 0.34, 0.16)
        self.right_top = RectRegion(0.20, 0.29, 0.88, 0.16)
        self.left_bottom = RectRegion(-0.55, -0.10, 0.34, 0.58)
        self.right_bottom = RectRegion(0.20, -0.10, 0.88, 0.58)
