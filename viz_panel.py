from ursina import *

class VizPanel(Entity):
    def __init__(self, app_controller):
        super().__init__(parent=camera.ui)
        self.controller = app_controller

        # Меню выбора алгоритма
        self.choice_menu = Entity(parent=self)
        Text("🎛️ Выберите алгоритм для визуализации", origin=(0,0), scale=1.5,
             position=(0, 0.3), parent=self.choice_menu)
        self.btn_shor = Button(text="Алгоритм Шора", scale=(0.3,0.1), position=(0,0.05),
                               parent=self.choice_menu, on_click=lambda: self.show_algorithm('shor'))
        self.btn_grover = Button(text="Алгоритм Гровера", scale=(0.3,0.1), position=(0,-0.1),
                                 parent=self.choice_menu, on_click=lambda: self.show_algorithm('grover'))
        self.btn_home = Button(text="🏠 На главный экран", scale=(0.2,0.08), position=(0,-0.35),
                               parent=self.choice_menu, on_click=self.controller.back_to_main)

        # Панели для каждого алгоритма (пустышки)
        self.shor_panel = Entity(parent=self)
        self.grover_panel = Entity(parent=self)

        # Панель Шора
        Text("Визуализация алгоритма Шора\n(будет реализована на шаге 3)",
             origin=(0,0), scale=1.2, position=(0, 0.2), parent=self.shor_panel)
        btn_back_shor = Button(text="← Назад к выбору", scale=(0.2,0.08), position=(-0.2, -0.3),
                               parent=self.shor_panel, on_click=self.show_choice_menu)
        btn_home_shor = Button(text="🏠 На главный экран", scale=(0.2,0.08), position=(0.2, -0.3),
                               parent=self.shor_panel, on_click=self.controller.back_to_main)

        # Панель Гровера
        Text("Визуализация алгоритма Гровера\n(будет реализована на шаге 3)",
             origin=(0,0), scale=1.2, position=(0, 0.2), parent=self.grover_panel)
        btn_back_grover = Button(text="← Назад к выбору", scale=(0.2,0.08), position=(-0.2, -0.3),
                                 parent=self.grover_panel, on_click=self.show_choice_menu)
        btn_home_grover = Button(text="🏠 На главный экран", scale=(0.2,0.08), position=(0.2, -0.3),
                                 parent=self.grover_panel, on_click=self.controller.back_to_main)

        self.show_choice_menu()
        self.hide()

    def show_choice_menu(self):
        self.choice_menu.enabled = True
        self.shor_panel.enabled = False
        self.grover_panel.enabled = False

    def show_algorithm(self, algo):
        self.choice_menu.enabled = False
        if algo == 'shor':
            self.shor_panel.enabled = True
            self.grover_panel.enabled = False
        else:
            self.shor_panel.enabled = False
            self.grover_panel.enabled = True

    def input(self, key):
        pass

    def show(self):
        self.enabled = True
        self.show_choice_menu()

    def hide(self):
        self.enabled = False