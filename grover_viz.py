from math import pi, sqrt
from random import random

from ursina import Button, Entity, Text, color, curve, destroy, mouse, time


class GroverViz(Entity):
    def __init__(self, controller, parent_panel):
        super().__init__(parent=parent_panel)
        self.controller = controller
        self.parent_panel = parent_panel
        self.enabled = False

        self.panel_x = -0.54
        self.panel_width = 0.38
        self.button_left_x = -0.62
        self.button_right_x = -0.46
        self.chart_x = 0.16
        self.chart_width = 0.94
        self.chart_height = 0.70
        self.chart_inner_width = 0.86
        self.chart_inner_height = 0.62
        self.baseline_y = -0.08
        self.max_bar_extent = 0.24

        self.min_qubits = 2
        self.max_qubits = 5
        self.qubits = 3
        self.marked_index = 5

        self.auto_interval = 0.85
        self.auto_timer = 0.0
        self.running = False
        self.phase = "oracle"
        self.iteration = 0
        self.last_mean = 0.0
        self.measured_index = None

        self.bars = []
        self.labels = []

        self._setup_scene()
        self._setup_ui()
        self.reset_algorithm()
        self.hide()

    @property
    def n_states(self):
        return 2 ** self.qubits

    def bit_label(self, index):
        return format(index, f"0{self.qubits}b")

    def optimal_iterations(self):
        return max(1, int((pi / 4) * sqrt(self.n_states)))

    def _setup_scene(self):
        Entity(
            parent=self,
            model="quad",
            position=(self.chart_x, 0.0, 0),
            scale=(self.chart_width, self.chart_height, 1),
            color=color.rgb(16, 22, 34),
        )
        Entity(
            parent=self,
            model="quad",
            position=(self.chart_x, 0.0, -0.01),
            scale=(self.chart_inner_width, self.chart_inner_height, 1),
            color=color.rgb(20, 28, 42),
        )
        self.baseline = Entity(
            parent=self,
            model="quad",
            position=(self.chart_x, self.baseline_y, -0.02),
            scale=(0.76, 0.004, 1),
            color=color.rgba(190, 198, 214, 220),
        )
        self.mean_line = Entity(
            parent=self,
            model="quad",
            position=(self.chart_x, 0.0, -0.02),
            scale=(0.76, 0.006, 1),
            color=color.rgba(100, 220, 170, 235),
        )

    def _setup_ui(self):
        Entity(
            parent=self,
            model="quad",
            position=(self.panel_x, 0.0, 0.01),
            scale=(self.panel_width, 0.80, 1),
            color=color.rgb(18, 24, 36),
        )
        Text(
            parent=self,
            text="Grover Search",
            position=(-0.70, 0.31),
            origin=(-0.5, 0),
            scale=1.3,
            color=color.white,
        )
        Text(
            parent=self,
            text="Search amplification made visual.",
            position=(-0.70, 0.255),
            origin=(-0.5, 0),
            scale=0.62,
            color=color.rgb(185, 194, 208),
        )
        self.info_text = Text(
            parent=self,
            text="",
            position=(-0.70, 0.16),
            origin=(-0.5, 0),
            scale=0.76,
            color=color.white,
        )
        self.phase_text = Text(
            parent=self,
            text="",
            position=(-0.70, 0.05),
            origin=(-0.5, 0),
            scale=0.66,
            color=color.rgb(255, 205, 110),
        )
        self.status_text = Text(
            parent=self,
            text="",
            position=(-0.70, -0.03),
            origin=(-0.5, 0),
            scale=0.52,
            color=color.rgb(196, 205, 218),
        )
        self.hover_text = Text(
            parent=self,
            text="",
            position=(0.47, 0.31),
            origin=(-0.5, 0),
            scale=0.50,
            color=color.rgb(185, 194, 208),
        )
        Text(
            parent=self,
            text="Space auto   Right step   Enter measure   R reset   M change target",
            position=(0.0, -0.44),
            origin=(0, 0),
            scale=0.42,
            color=color.rgb(146, 156, 172),
        )

        self.back_button = self._button(
            "Back",
            (self.button_left_x, -0.47),
            self.parent_panel.show_choice_menu,
        )
        self.home_button = self._button(
            "Home",
            (self.button_right_x, -0.47),
            self.controller.back_to_main,
            accent=True,
        )
        self.start_button = self._button("Start", (self.button_left_x, -0.12), self.toggle_run)
        self.step_button = self._button("Step", (self.button_right_x, -0.12), self.step)
        self.measure_button = self._button("Measure", (self.button_left_x, -0.19), self.measure_state)
        self.reset_button = self._button("Reset", (self.button_right_x, -0.19), self.reset_algorithm)
        self.q_minus_button = self._button("Qubits -", (self.button_left_x, -0.26), self.decrease_qubits)
        self.q_plus_button = self._button("Qubits +", (self.button_right_x, -0.26), self.increase_qubits)
        self.m_minus_button = self._button("Target -", (self.button_left_x, -0.33), self.decrease_marked)
        self.m_plus_button = self._button("Target +", (self.button_right_x, -0.33), self.increase_marked)
        self.slower_button = self._button("Slower", (self.button_left_x, -0.40), self.slower)
        self.faster_button = self._button("Faster", (self.button_right_x, -0.40), self.faster, accent=True)

    def _button(self, text, position, on_click, accent=False):
        base_color = color.rgb(56, 72, 102) if not accent else color.rgb(86, 122, 214)
        hover_color = color.rgb(76, 92, 124) if not accent else color.rgb(106, 142, 232)
        press_color = color.rgb(40, 54, 78) if not accent else color.rgb(70, 106, 194)
        button = Button(
            parent=self,
            text="",
            position=position,
            scale=(0.125, 0.054),
            color=base_color,
            highlight_color=hover_color,
            pressed_color=press_color,
        )
        button.on_click = on_click
        button.label = Text(
            parent=self,
            text=text,
            position=(position[0], position[1] - 0.006),
            origin=(0, 0),
            scale=0.44,
            color=color.white,
        )
        return button

    def _set_button_label(self, button, text):
        button.label.text = text

    def reset_algorithm(self):
        self.running = False
        self.auto_timer = 0.0
        self.phase = "oracle"
        self.iteration = 0
        self.measured_index = None
        self.marked_index %= self.n_states

        initial = 1 / sqrt(self.n_states)
        self.amplitudes = [initial for _ in range(self.n_states)]
        self.last_mean = initial

        self._set_button_label(self.start_button, "Start")
        self.rebuild_bars()
        self.update_visuals(animated=False)
        self.update_ui("Uniform superposition ready.")

    def increase_qubits(self):
        if self.qubits < self.max_qubits:
            self.qubits += 1
            self.reset_algorithm()

    def decrease_qubits(self):
        if self.qubits > self.min_qubits:
            self.qubits -= 1
            self.reset_algorithm()

    def increase_marked(self):
        self.marked_index = (self.marked_index + 1) % self.n_states
        self.reset_algorithm()

    def decrease_marked(self):
        self.marked_index = (self.marked_index - 1) % self.n_states
        self.reset_algorithm()

    def faster(self):
        self.auto_interval = max(0.2, self.auto_interval - 0.1)
        self.update_ui("Speed increased.")

    def slower(self):
        self.auto_interval = min(2.0, self.auto_interval + 0.1)
        self.update_ui("Speed decreased.")

    def rebuild_bars(self):
        for entity in self.bars + self.labels:
            destroy(entity)

        self.bars = []
        self.labels = []
        count = self.n_states

        chart_width = 0.78
        slot_width = chart_width / count
        bar_width = min(0.07, slot_width * 0.56)
        start_x = self.chart_x - chart_width / 2 + slot_width / 2
        label_scale = 0.54 if count <= 8 else 0.40 if count <= 16 else 0.28

        for index in range(count):
            x = start_x + index * slot_width
            bar = Entity(
                parent=self,
                model="quad",
                position=(x, -0.03, -0.03),
                scale=(bar_width, 0.05, 1),
                color=color.azure,
                collider="box",
            )
            bar.state_index = index
            self.bars.append(bar)

            label = Text(
                parent=self,
                text=self.bit_label(index),
                position=(x, -0.315),
                origin=(0, 0),
                scale=label_scale,
                color=color.rgb(224, 230, 240),
            )
            self.labels.append(label)

    def bar_color(self, index, amplitude):
        if index == self.marked_index:
            return color.rgb(255, 190, 80) if amplitude >= 0 else color.rgb(255, 132, 94)
        if self.measured_index == index:
            return color.rgb(80, 210, 120)
        return color.rgb(85, 170, 255) if amplitude >= 0 else color.rgb(230, 96, 108)

    def update_visuals(self, animated=True):
        duration = 0.28 if animated else 0.0
        max_amplitude = max(
            max(abs(amplitude) for amplitude in self.amplitudes),
            abs(self.last_mean),
            0.001,
        )
        visual_scale = self.max_bar_extent / max_amplitude
        mean_y = self.baseline_y + self.last_mean * visual_scale

        if animated:
            self.mean_line.animate("y", mean_y, duration=duration, curve=curve.out_cubic)
        else:
            self.mean_line.y = mean_y

        for index, bar in enumerate(self.bars):
            amplitude = self.amplitudes[index]
            visual_height = amplitude * visual_scale
            height = max(abs(visual_height), 0.02)
            center_y = self.baseline_y + visual_height / 2

            if animated:
                bar.animate("scale_y", height, duration=duration, curve=curve.out_cubic)
                bar.animate("y", center_y, duration=duration, curve=curve.out_cubic)
            else:
                bar.scale_y = height
                bar.y = center_y

            bar.color = self.bar_color(index, amplitude)

    def do_oracle(self):
        self.amplitudes[self.marked_index] *= -1
        self.last_mean = sum(self.amplitudes) / self.n_states
        self.phase = "diffusion"
        self.update_visuals(animated=True)
        self.update_ui("Oracle flipped the target phase.")

    def do_diffusion(self):
        self.last_mean = sum(self.amplitudes) / self.n_states
        self.amplitudes = [(2 * self.last_mean - amplitude) for amplitude in self.amplitudes]
        self.last_mean = sum(self.amplitudes) / self.n_states
        self.iteration += 1
        self.phase = "oracle"
        self.update_visuals(animated=True)

        if self.iteration >= self.optimal_iterations():
            self.update_ui("Diffusion done. You can measure now.")
        else:
            self.update_ui("Diffusion reflected amplitudes around the mean.")

    def step(self):
        self.measured_index = None
        if self.phase == "oracle":
            self.do_oracle()
        else:
            self.do_diffusion()

    def toggle_run(self):
        self.running = not self.running
        self._set_button_label(self.start_button, "Pause" if self.running else "Start")
        self.update_ui("Auto-play running." if self.running else "Paused.")

    def measure_state(self):
        self.running = False
        self._set_button_label(self.start_button, "Start")

        threshold = random()
        cumulative = 0.0
        result = self.n_states - 1
        for index, amplitude in enumerate(self.amplitudes):
            cumulative += amplitude * amplitude
            if threshold <= cumulative:
                result = index
                break

        self.measured_index = result
        self.update_visuals(animated=False)

        if result == self.marked_index:
            self.update_ui(f"Measured target {self.bit_label(result)}.")
        else:
            self.update_ui(f"Measured {self.bit_label(result)}. Target was {self.bit_label(self.marked_index)}.")

    def update_ui(self, status):
        target_amplitude = self.amplitudes[self.marked_index]
        target_probability = target_amplitude * target_amplitude
        recommended = self.optimal_iterations()

        self.info_text.text = (
            f"{self.qubits} qubits   {self.n_states} states\n"
            f"Target {self.bit_label(self.marked_index)}\n"
            f"Iteration {self.iteration} of {recommended}"
        )
        self.phase_text.text = (
            f"{self.phase.upper()} phase\n"
            f"Target chance {target_probability:.0%}   Speed {self.auto_interval:.1f}s"
        )
        self.status_text.text = status

    def update_hover_text(self):
        hovered = mouse.hovered_entity
        if hovered is not None and hasattr(hovered, "state_index") and hovered in self.bars:
            index = hovered.state_index
            amplitude = self.amplitudes[index]
            probability = amplitude * amplitude
            marker = "  [marked]" if index == self.marked_index else ""
            measured = "  [measured]" if index == self.measured_index else ""
            self.hover_text.text = f"State {self.bit_label(index)}{marker}{measured}\nChance {probability:.0%}\nAmplitude {amplitude:+.3f}"
        else:
            self.hover_text.text = ""

    def update(self):
        if not self.enabled:
            return

        self.update_hover_text()
        if self.running:
            self.auto_timer += time.dt
            if self.auto_timer >= self.auto_interval:
                self.auto_timer = 0.0
                self.step()

    def input(self, key):
        if key == "space":
            self.toggle_run()
        elif key == "right arrow":
            self.step()
        elif key == "r":
            self.reset_algorithm()
        elif key == "m":
            self.increase_marked()
        elif key == "enter":
            self.measure_state()

    def show(self):
        self.enabled = True

    def hide(self):
        self.running = False
        self.auto_timer = 0.0
        self.enabled = False
