from ursina import *
from theory_panel import TheoryPanel
from viz_panel import VizPanel

app = Ursina(borderless=False)

window.fullscreen = False
window.size = (1024, 768)
window.title = "Квантовые алгоритмы — обучающий визуализатор"

window.fps_counter.enabled = False
window.entity_counter.enabled = False
window.collider_counter.enabled = False
window.cog_menu.enabled = False

class QuantumVizApp:
    def __init__(self):
        self.theory = TheoryPanel(self)
        self.viz = VizPanel(self)
        self.main_menu = Entity(parent=camera.ui)
        self.create_main_menu()
        self.show_main_menu()

    def create_main_menu(self):
        Text("Интерактивный визуализатор\nквантовых алгоритмов",
             origin=(0,0), scale=2, position=(0, 0.3), parent=self.main_menu)
        Button(text="📚 Теория алгоритмов", scale=(0.35,0.1), position=(0,0),
               parent=self.main_menu, on_click=lambda: self.show_panel('theory'))
        Button(text="🎛️ Визуализация алгоритмов", scale=(0.35,0.1), position=(0,-0.15),
               parent=self.main_menu, on_click=lambda: self.show_panel('viz'))
        Button(text="Выход", scale=(0.2,0.08), position=(0,-0.35),
               parent=self.main_menu, on_click=application.quit)

    def show_panel(self, panel_name):
        self.main_menu.enabled = False
        if panel_name == 'theory':
            self.theory.show()
        elif panel_name == 'viz':
            self.viz.show()

    def show_main_menu(self):
        self.theory.hide()
        self.viz.hide()
        self.main_menu.enabled = True

    def back_to_main(self):
        self.show_main_menu()

    def exit_app(self):
        application.quit()

    def input(self, key):
        if key == 'escape':
            self.exit_app()
            return
        if self.theory.enabled:
            self.theory.input(key)
        elif self.viz.enabled:
            self.viz.input(key)

if __name__ == '__main__':
    app_instance = QuantumVizApp()
    app.run()
