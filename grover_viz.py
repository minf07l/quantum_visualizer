from math import pi, sqrt
from random import random

from ursina import Button, Entity, Text, color, curve, destroy, time


class GroverViz(Entity):
    def __init__(self, controller, parent_panel):
        super().__init__(parent=parent_panel)
        self.controller = controller
        self.parent_panel = parent_panel
        self.enabled = False

        self.left_x = -0.55
        self.left_width = 0.34
        self.right_x = 0.20
        self.right_width = 0.88
        self.top_y = 0.29
        self.top_height = 0.16
        self.bottom_y = -0.10
        self.bottom_height = 0.58
        self.chart_inner_width = 0.78
        self.chart_inner_height = 0.46
        self.chart_inner_y = self.bottom_y - 0.015
        self.baseline_y = -0.13
        self.max_bar_extent = 0.22
        self.chart_label_y = self.chart_inner_y - self.chart_inner_height / 2 - 0.028

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
        self.axis_panel = None
        self._setup_scene()
        self._setup_ui()
        self.reset_algorithm()
        self.hide()

    @property
    def n_states(self):
        return 2 ** self.qubits

    def bit_label(self, index):
        return str(index)

    def optimal_iterations(self):
        return max(1, int((pi / 4) * sqrt(self.n_states)))

    def _panel(self, x, y, width, height, inner=False):
        Entity(
            parent=self,
            model="quad",
            position=(x, y, 0.02),
            scale=(width, height, 1),
            color=color.rgb(14, 20, 32) if not inner else color.rgb(20, 28, 42),
        )
        Entity(
            parent=self,
            model="quad",
            position=(x, y + height / 2 - 0.002, 0.01),
            scale=(width, 0.004, 1),
            color=color.rgb(78, 92, 120),
        )
        Entity(
            parent=self,
            model="quad",
            position=(x, y - height / 2 + 0.002, 0.01),
            scale=(width, 0.004, 1),
            color=color.rgb(78, 92, 120),
        )
        Entity(
            parent=self,
            model="quad",
            position=(x - width / 2 + 0.002, y, 0.01),
            scale=(0.004, height, 1),
            color=color.rgb(78, 92, 120),
        )
        Entity(
            parent=self,
            model="quad",
            position=(x + width / 2 - 0.002, y, 0.01),
            scale=(0.004, height, 1),
            color=color.rgb(78, 92, 120),
        )

    def _setup_scene(self):
        self._panel(self.left_x, self.top_y, self.left_width, self.top_height)
        self._panel(self.right_x, self.top_y, self.right_width, self.top_height)
        self._panel(self.left_x, self.bottom_y, self.left_width, self.bottom_height)
        self._panel(self.right_x, self.bottom_y, self.right_width, self.bottom_height)
        self._panel(self.right_x, self.chart_inner_y, self.chart_inner_width, self.chart_inner_height, inner=True)
        self.axis_panel = Entity(parent=self, position=(self.right_x, self.chart_label_y + 0.01, -0.08))
        self.baseline = Entity(
            parent=self,
            model="quad",
            position=(self.right_x, self.baseline_y, -0.03),
            scale=(0.76, 0.004, 1),
            color=color.rgba(190, 198, 214, 220),
        )
        self.mean_line = Entity(
            parent=self,
            model="quad",
            position=(self.right_x, 0.0, -0.03),
            scale=(0.76, 0.006, 1),
            color=color.rgba(100, 220, 170, 235),
        )

    def _setup_ui(self):
        self.controls_panel = Entity(parent=self, position=(self.left_x, self.bottom_y, -0.03))
        self.title_text = Text(
            parent=self,
            text="Grover Search",
            position=(self.left_x, self.top_y - 0.01, -0.12),
            origin=(0, 0),
            scale=1.15,
            color=color.white,
        )
        self.controls_text = Text(
            parent=self.controls_panel,
            text="Controls",
            position=(0, 0.255, -0.12),
            origin=(0, 0),
            scale=0.98,
            color=color.rgb(214, 222, 236),
        )
        self.selection_text = Text(
            parent=self.controls_panel,
            text="",
            position=(0, 0.185, -0.12),
            origin=(0, 0),
            scale=0.42,
            color=color.rgb(185, 194, 208),
        )
        self.status_banner = Text(
            parent=self,
            text="",
            position=(self.right_x - 0.37, self.top_y - 0.015, -0.12),
            origin=(-0.5, 0),
            scale=0.88,
            color=color.rgb(244, 92, 92),
        )

        self.start_button = self._button("Start", (-0.072, 0.125), self.toggle_run)
        self.step_button = self._button("Step", (0.072, 0.125), self.step)
        self.measure_button = self._button("Measure", (-0.072, 0.055), self.measure_state)
        self.reset_button = self._button("Reset", (0.072, 0.055), self.reset_algorithm)
        self.q_minus_button = self._button("Qubits -", (-0.072, -0.015), self.decrease_qubits)
        self.q_plus_button = self._button("Qubits +", (0.072, -0.015), self.increase_qubits)
        self.m_minus_button = self._button("Target -", (-0.072, -0.085), self.decrease_marked)
        self.m_plus_button = self._button("Target +", (0.072, -0.085), self.increase_marked)
        self.slower_button = self._button("Slower", (-0.072, -0.155), self.slower)
        self.faster_button = self._button("Faster", (0.072, -0.155), self.faster, accent=True)
        self.back_button = self._button("Back", (-0.072, -0.225), self.parent_panel.show_choice_menu)
        self.home_button = self._button("Home", (0.072, -0.225), self.controller.back_to_main, accent=True)

    def _button(self, text, local_position, on_click, accent=False):
        base_color = color.rgb(56, 72, 102) if not accent else color.rgb(86, 122, 214)
        hover_color = color.rgb(76, 92, 124) if not accent else color.rgb(106, 142, 232)
        press_color = color.rgb(40, 54, 78) if not accent else color.rgb(70, 106, 194)
        button = Button(
            parent=self.controls_panel,
            text="",
            position=(local_position[0], local_position[1], -0.06),
            scale=(0.112, 0.050),
            color=base_color,
            highlight_color=hover_color,
            pressed_color=press_color,
        )
        button.on_click = on_click
        button.label = Text(
            parent=self.controls_panel,
            text=text,
            position=(local_position[0], local_position[1] - 0.010, -0.12),
            origin=(0, 0),
            scale=0.34,
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

        chart_width = 0.72
        slot_width = chart_width / count
        bar_width = min(0.07, slot_width * 0.56)
        start_x = self.right_x - chart_width / 2 + slot_width / 2
        max_labels = 8 if count > 8 else count
        label_indices = set()
        if count <= max_labels:
            label_indices = set(range(count))
        else:
            for slot in range(max_labels):
                idx = round(slot * (count - 1) / (max_labels - 1))
                label_indices.add(idx)

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
            if index in label_indices:
                self.labels.append(
                    Text(
                        parent=self.axis_panel,
                        text=str(index),
                        position=(x - self.right_x, 0, 0),
                        origin=(0, 0),
                        scale=0.52 if count <= 8 else 0.38 if count <= 16 else 0.30,
                        color=color.rgb(214, 222, 236),
                    )
                )

    def bar_color(self, index, amplitude):
        if self.measured_index == index:
            return color.rgb(80, 210, 120)
        if self.measured_index is not None:
            return color.rgb(50, 66, 94)
        if index == self.marked_index:
            return color.rgb(255, 190, 80) if amplitude >= 0 else color.rgb(255, 132, 94)
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
        self.amplitudes = [0.0 for _ in range(self.n_states)]
        self.amplitudes[result] = 1.0
        self.last_mean = 1.0 / self.n_states
        self.update_visuals(animated=False)

        if result == self.marked_index:
            self.update_ui(f"Measured target {self.bit_label(result)}.")
        else:
            self.update_ui(f"Measured {self.bit_label(result)}. Target was {self.bit_label(self.marked_index)}.")

    def describe_state(self):
        target_probability = self.amplitudes[self.marked_index] * self.amplitudes[self.marked_index]
        if self.measured_index is not None:
            if self.measured_index == self.marked_index:
                return f"Measured target {self.bit_label(self.marked_index)}."
            return f"Measured {self.bit_label(self.measured_index)}. Target {self.bit_label(self.marked_index)}."
        if self.phase == "oracle":
            if self.iteration == 0:
                return f"Ready. Target {self.bit_label(self.marked_index)} starts at {target_probability:.0%}."
            if self.iteration >= self.optimal_iterations():
                return f"Peak reached. Target {self.bit_label(self.marked_index)} at {target_probability:.0%}."
            return f"Iteration {self.iteration}: target {self.bit_label(self.marked_index)} at {target_probability:.0%}."
        return f"Oracle flips target {self.bit_label(self.marked_index)}."

    def update_ui(self, status):
        target_amplitude = self.amplitudes[self.marked_index]
        target_probability = target_amplitude * target_amplitude
        self.selection_text.text = (
            f"{self.qubits} qubits   {self.n_states} states\n"
            f"Target {self.bit_label(self.marked_index)}   Goal {self.optimal_iterations()} iterations\n"
            f"Speed {self.auto_interval:.1f}s   Current chance {target_probability:.0%}"
        )
        self.status_banner.text = self.describe_state()

    def update(self):
        if not self.enabled:
            return

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
