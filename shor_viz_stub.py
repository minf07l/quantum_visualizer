from ursina import *

class ShorVizStub(Entity):
    def __init__(self, controller, parent_panel):
        super().__init__(parent=camera.ui)
        self.controller = controller
        self.parent_panel = parent_panel

        self.bg = Panel(color=color.rgba(30,30,80,180), scale=(1.4, 0.9), position=(0, -0.05), parent=self)
        self.text = Text("Визуализация алгоритма Шора\n(будет реализована в следующих шагах)",
                         origin=(0,0), scale=1.2, position=(0, 0.2), parent=self, alignment='center')
        self.btn_back = Button(text="← Назад к выбору", scale=(0.25,0.08), position=(-0.25, -0.42),
                               color=color.lime, text_color=color.black,
                               parent=self, on_click=self.parent_panel.show_choice_menu)
        self.btn_home = Button(text="🏠 На главный экран", scale=(0.25,0.08), position=(0.25, -0.42),
                               color=color.orange, text_color=color.white,
                               parent=self, on_click=self.controller.back_to_main)

        self.enabled = False

    def show(self):
        self.enabled = True

    def hide(self):
        self.enabled = False