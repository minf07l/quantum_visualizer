from ursina import *
import os

class TheoryContent(Entity):
    def __init__(self, controller, parent_panel):
        super().__init__(parent=camera.ui)
        self.controller = controller
        self.parent_panel = parent_panel

        self.bg = Panel(color=color.rgba(0,0,0,0.85), scale=(1.3, 0.8), position=(0, -0.1), parent=self)
        self.text_entity = None
        self.scroll_y = 0
        self.text_height = 0

        self.btn_back = Button(text="← Назад к выбору", scale=(0.25,0.08), position=(-0.25, -0.42),
                               color=color.lime, text_color=color.black,
                               parent=self, on_click=self.parent_panel.back_to_choice)
        self.btn_home = Button(text="🏠 На главный экран", scale=(0.25,0.08), position=(0.25, -0.42),
                               color=color.orange, text_color=color.white,
                               parent=self, on_click=self.controller.back_to_main)

        self.enabled = False

    def show_topic(self, topic):
        if topic == 'shor':
            file_path = os.path.join('theory_data', 'shor_theory.txt')
        else:
            file_path = os.path.join('theory_data', 'grover_theory.txt')
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            content = f"Ошибка загрузки: {e}"

        if self.text_entity:
            destroy(self.text_entity)

        self.text_entity = Text(content, origin=(0,0), scale=0.75, position=(0, 0.0),
                                parent=self, line_height=1.4, width=1.1, alignment='center')
        lines = content.count('\n') + 1
        self.text_height = lines * 0.75 * 1.4
        self.scroll_y = 0
        self.update_text_position()
        self.enabled = True

    def update_text_position(self):
        if self.text_entity:
            visible_height = 0.65
            max_scroll = max(0, self.text_height - visible_height)
            self.scroll_y = max(0, min(self.scroll_y, max_scroll))
            self.text_entity.y = 0.0 - self.scroll_y

    def input(self, key):
        if not self.enabled:
            return
        if key == 'scroll up':
            self.scroll_y -= 0.2
            self.update_text_position()
        elif key == 'scroll down':
            self.scroll_y += 0.2
            self.update_text_position()

    def hide(self):
        self.enabled = False