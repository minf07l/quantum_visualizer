from ursina import *
from shor_viz import ShorViz
from grover_viz import GroverViz

class VizPanel(Entity):
    def __init__(self, app_controller):
        super().__init__(parent=camera.ui)
        self.controller = app_controller

        self.choice_menu = Entity(parent=self)
        Text("🎛️ Выберите алгоритм для визуализации", origin=(0,0), scale=1.5,
             position=(0, 0.35), parent=self.choice_menu)
        self.btn_shor = Button(text="Алгоритм Шора", scale=(0.45,0.1), position=(0,0.1),
                               color=color.azure, text_color=color.white,
                               parent=self.choice_menu, on_click=lambda: self.start_algorithm('shor'))
        self.btn_grover = Button(text="Алгоритм Гровера", scale=(0.45,0.1), position=(0,-0.05),
                                 color=color.azure, text_color=color.white,
                                 parent=self.choice_menu, on_click=lambda: self.start_algorithm('grover'))
        self.btn_home = Button(text="🏠 На главный экран", scale=(0.25,0.08), position=(0,-0.35),
                               color=color.orange, text_color=color.white,
                               parent=self.choice_menu, on_click=self.controller.back_to_main)

        self.shor_stub = ShorViz(self.controller, self)
        self.grover_stub = GroverViz(self.controller, self)

        self.show_choice_menu()
        self.hide()

    def start_algorithm(self, algo):
        self.choice_menu.enabled = False
        if algo == 'shor':
            self.shor_stub.show()
        else:
            self.grover_stub.show()

    def show_choice_menu(self):
        self.choice_menu.enabled = True
        self.shor_stub.hide()
        self.grover_stub.hide()

    def input(self, key):
        if self.shor_stub.enabled:
            self.shor_stub.input(key)
        elif self.grover_stub.enabled:
            self.grover_stub.input(key)

    def show(self):
        self.enabled = True
        self.show_choice_menu()

    def hide(self):
        self.enabled = False
        self.shor_stub.hide()
        self.grover_stub.hide()
