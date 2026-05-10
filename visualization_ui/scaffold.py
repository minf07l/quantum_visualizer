from ursina import Entity

from .layout import VisualizationLayout
from .panels import PanelBlock


class VisualizationScaffold:
    def __init__(self, parent):
        self.root = Entity(parent=parent)
        self.layout = VisualizationLayout()
        self.top_left = PanelBlock(self.root, self.layout.left_top)
        self.top_right = PanelBlock(self.root, self.layout.right_top)
        self.bottom_left = PanelBlock(self.root, self.layout.left_bottom)
        self.bottom_right = PanelBlock(self.root, self.layout.right_bottom)

    @property
    def enabled(self) -> bool:
        return self.root.enabled

    @enabled.setter
    def enabled(self, value: bool):
        self.root.enabled = value

    def show(self):
        self.enabled = True

    def hide(self):
        self.enabled = False
