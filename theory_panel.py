from ursina import *
import os

class TheoryPanel(Entity):
    def __init__(self, app_controller):
        super().__init__(parent=camera.ui)
        self.controller = app_controller

        self.title = Text("📘 Теория квантовых алгоритмов", origin=(0,0), scale=2,
                          position=(0, 0.45), parent=self)

        # Меню выбора алгоритма
        self.choice_menu = Entity(parent=self)
        Text("Выберите алгоритм:", origin=(0,0), scale=1.2, position=(0, 0.25), parent=self.choice_menu)
        self.btn_shor = Button(text="Алгоритм Шора", scale=(0.3,0.1), position=(0,0.05),
                               parent=self.choice_menu, on_click=lambda: self.show_topic('shor'))
        self.btn_grover = Button(text="Алгоритм Гровера", scale=(0.3,0.1), position=(0,-0.1),
                                 parent=self.choice_menu, on_click=lambda: self.show_topic('grover'))
        self.btn_home = Button(text="🏠 На главный экран", scale=(0.2,0.08), position=(0,-0.35),
                               parent=self.choice_menu, on_click=self.controller.back_to_main)

        # Панель отображения темы
        self.topic_panel = Entity(parent=self)
        self.text_bg = Panel(color=color.rgba(0,0,0,0.7), scale=(1.2, 0.8), position=(0, -0.05), parent=self.topic_panel)
        self.text_entity = None
        self.scroll_y = 0
        self.text_height = 0

        self.btn_back = Button(text="← Назад к выбору", scale=(0.2,0.08), position=(-0.25, -0.4),
                               parent=self.topic_panel, on_click=self.show_choice_menu)
        self.btn_home_topic = Button(text="🏠 На главный экран", scale=(0.2,0.08), position=(0.25, -0.4),
                                     parent=self.topic_panel, on_click=self.controller.back_to_main)

        self.show_choice_menu()
        self.hide()

    def show_choice_menu(self):
        self.choice_menu.enabled = True
        self.topic_panel.enabled = False

    def load_text_from_file(self, topic):
        if topic == 'shor':
            file_path = os.path.join('theory_data', 'shor_theory.txt')
        else:
            file_path = os.path.join('theory_data', 'grover_theory.txt')
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            return f"Ошибка загрузки файла: {e}\nУбедитесь, что папка 'theory_data' и файлы существуют."

    def show_topic(self, topic):
        self.choice_menu.enabled = False
        self.topic_panel.enabled = True

        content = self.load_text_from_file(topic)

        if self.text_entity:
            destroy(self.text_entity)

        self.text_entity = Text(content, origin=(0,0), scale=0.8, position=(-0.55, 0.3),
                                parent=self.topic_panel, line_height=1.4, width=1.1, alignment='left')
        # Расчёт высоты текста для прокрутки
        lines = content.count('\n') + 1
        self.text_height = lines * 0.8 * 1.4
        self.scroll_y = 0
        self.update_text_position()

    def update_text_position(self):
        if self.text_entity:
            visible_height = 0.7
            max_scroll = max(0, self.text_height - visible_height)
            self.scroll_y = max(0, min(self.scroll_y, max_scroll))
            self.text_entity.y = 0.3 - self.scroll_y

    def input(self, key):
        if self.topic_panel.enabled and self.text_entity:
            if key == 'scroll up':
                self.scroll_y -= 0.2
                self.update_text_position()
            elif key == 'scroll down':
                self.scroll_y += 0.2
                self.update_text_position()

    def show(self):
        self.enabled = True

    def hide(self):
        self.enabled = False