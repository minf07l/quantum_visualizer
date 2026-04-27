from ursina import *


class TheoryPanel:
    def __init__(self, app_controller):
        self.controller = app_controller
        self.entity = Entity(parent=camera.ui)
        self.text = Text("Здесь будет подробная теория по алгоритмам\nШора и Гровера (шаг 2)",
                         origin=(0, 0), scale=1.5, position=(0, 0.1), parent=self.entity)
        self.back_btn = Button(text="← Назад", scale=(0.2, 0.08), position=(0, -0.4),
                               parent=self.entity, on_click=self.controller.back_to_main)
        self.hide()

    def show(self):
        self.entity.enabled = True

    def hide(self):
        self.entity.enabled = False