from ursina import *
from theory_content import TheoryContent

class TheoryPanel(Entity):
    def __init__(self, app_controller):
        super().__init__(parent=camera.ui)
        self.controller = app_controller

        self.title = Text("📘 Теория квантовых алгоритмов", origin=(0,0), scale=2,
                          position=(0, 0.45), parent=self)

        self.choice_menu = Entity(parent=self)
        Text("Выберите алгоритм:", origin=(0,0), scale=1.2, position=(0, 0.25), parent=self.choice_menu)
        self.btn_shor = Button(text="Алгоритм Шора", scale=(0.45,0.1), position=(0,0.05),
                               color=color.azure, text_color=color.white,
                               parent=self.choice_menu, on_click=lambda: self.show_topic('shor'))
        self.btn_grover = Button(text="Алгоритм Гровера", scale=(0.45,0.1), position=(0,-0.1),
                                 color=color.azure, text_color=color.white,
                                 parent=self.choice_menu, on_click=lambda: self.show_topic('grover'))
        self.btn_home = Button(text="🏠 На главный экран", scale=(0.25,0.08), position=(0,-0.35),
                               color=color.orange, text_color=color.white,
                               parent=self.choice_menu, on_click=self.controller.back_to_main)

        self.theory_content = None

        self.show_choice_menu()
        self.hide()

    def show_choice_menu(self):
        self.choice_menu.enabled = True
        if self.theory_content:
            self.theory_content.hide()

    def show_topic(self, topic):
        self.choice_menu.enabled = False
        if not self.theory_content:
            self.theory_content = TheoryContent(self.controller, self)
        self.theory_content.show_topic(topic)

    def back_to_choice(self):
        self.show_choice_menu()

    def input(self, key):
        if self.theory_content and self.theory_content.enabled:
            self.theory_content.input(key)

    def show(self):
        self.enabled = True

    def hide(self):
        self.enabled = False
        if self.theory_content:
            self.theory_content.hide()