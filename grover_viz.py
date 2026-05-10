from grover_math import diffusion_step, initial_amplitudes, measure_state, optimal_iterations, oracle_step
from visualization_ui import (
    BarChartWidget,
    ControlGrid,
    PanelBlock,
    ReferenceLine,
    Spacing,
    VisualizationScaffold,
)


class GroverViz:
    def __init__(self, controller, parent_panel):
        self.controller = controller
        self.parent_panel = parent_panel
        self.ui = VisualizationScaffold(parent_panel)

        self.max_bar_extent = 0.22
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
        self.amplitudes = []

        self._build_ui()
        self.reset_algorithm()
        self.hide()

    def _build_ui(self):
        top_left_inner = self.ui.top_left.content_region(Spacing.md, Spacing.md)
        top_right_inner = self.ui.top_right.content_region(Spacing.lg, Spacing.md)
        bottom_left_inner = self.ui.bottom_left.content_region(Spacing.md, Spacing.md)
        bottom_right_inner = self.ui.bottom_right.content_region(Spacing.md, Spacing.md)

        left_rows = bottom_left_inner.split_rows([1, 2, 10], gap=Spacing.sm)
        chart_rows = bottom_right_inner.split_rows([12, 1], gap=Spacing.sm)

        self.chart_panel = PanelBlock(self.ui.root, chart_rows[0], inner=True)
        self.chart_axis_region = chart_rows[1]

        self.title_text = self.ui.top_left.add_text_in_region(top_left_inner, "Grover Search", scale=1.15, mode="shrink")
        self.status_text = self.ui.top_right.add_text_in_region(
            top_right_inner,
            "",
            scale=1.08,
            text_color=(214, 222, 236),
            mode="wrap_shrink",
        )
        self.controls_text = self.ui.bottom_left.add_text_in_region(
            left_rows[0],
            "Controls",
            scale=1.20,
            text_color=(214, 222, 236),
            mode="shrink",
        )
        self.selection_text = self.ui.bottom_left.add_text_in_region(
            left_rows[1],
            "",
            scale=0.64,
            text_color=(185, 194, 208),
            mode="wrap_shrink",
        )

        self.controls_grid = ControlGrid(
            self.ui.bottom_left,
            rows=6,
            columns=2,
            region=left_rows[2],
            x_padding=0.0,
            y_padding=0.0,
            h_gap=Spacing.sm,
            v_gap=Spacing.sm,
        )

        self.buttons = {
            "start": self.controls_grid.add_button("Start", 0, 0, self.toggle_run),
            "step": self.controls_grid.add_button("Step", 0, 1, self.step),
            "measure": self.controls_grid.add_button("Measure", 1, 0, self.measure_current_state),
            "reset": self.controls_grid.add_button("Reset", 1, 1, self.reset_algorithm),
            "qubits_minus": self.controls_grid.add_button("Qubits -", 2, 0, self.decrease_qubits),
            "qubits_plus": self.controls_grid.add_button("Qubits +", 2, 1, self.increase_qubits),
            "target_minus": self.controls_grid.add_button("Target -", 3, 0, self.decrease_marked),
            "target_plus": self.controls_grid.add_button("Target +", 3, 1, self.increase_marked),
            "slower": self.controls_grid.add_button("Slower", 4, 0, self.slower),
            "faster": self.controls_grid.add_button("Faster", 4, 1, self.faster, accent=True),
            "back": self.controls_grid.add_button("Back", 5, 0, self.parent_panel.show_choice_menu),
            "home": self.controls_grid.add_button("Home", 5, 1, self.controller.back_to_main, accent=True),
        }

        baseline_y = self.chart_panel.region.bottom + self.chart_panel.region.height * 0.18
        line_width = self.chart_panel.region.width - 2 * Spacing.sm
        self.baseline = ReferenceLine(
            self.ui.root,
            x=self.chart_panel.region.center_x,
            y=baseline_y,
            width=line_width,
            thickness=0.004,
            line_color=(190, 198, 214, 220),
        )
        self.mean_line = ReferenceLine(
            self.ui.root,
            x=self.chart_panel.region.center_x,
            y=baseline_y,
            width=line_width,
            thickness=0.006,
            line_color=(100, 220, 170, 235),
        )
        self.chart = BarChartWidget(
            self.ui.root,
            center_x=self.chart_panel.region.center_x,
            baseline_y=baseline_y,
            chart_width=self.chart_panel.region.width - 2 * Spacing.lg,
            axis_parent=self.ui.root,
            axis_label_y=self.chart_axis_region.center_y,
            min_bar_height=0.02,
            default_bar_color=(85, 170, 255),
        )

    @property
    def enabled(self):
        return self.ui.enabled

    @property
    def n_states(self):
        return 2 ** self.qubits

    def bit_label(self, index):
        return str(index)

    def goal_iterations(self):
        return optimal_iterations(self.n_states)

    def show(self):
        self.ui.show()

    def hide(self):
        self.running = False
        self.auto_timer = 0.0
        self.ui.hide()

    def reset_algorithm(self):
        self.running = False
        self.auto_timer = 0.0
        self.phase = "oracle"
        self.iteration = 0
        self.measured_index = None
        self.marked_index %= self.n_states
        self.amplitudes = initial_amplitudes(self.n_states)
        self.last_mean = self.amplitudes[0]
        self.buttons["start"].set_text("Start")
        self.rebuild_chart()
        self.update_visuals(animated=False)
        self.update_ui()

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
        self.update_ui()

    def slower(self):
        self.auto_interval = min(2.0, self.auto_interval + 0.1)
        self.update_ui()

    def rebuild_chart(self):
        count = self.n_states
        slot_width = self.chart.chart_width / count
        bar_width = min(0.07, slot_width * 0.56)
        max_labels = 8 if count > 8 else count
        if count <= max_labels:
            label_indices = set(range(count))
        else:
            label_indices = {round(slot * (count - 1) / (max_labels - 1)) for slot in range(max_labels)}
        self.chart.rebuild(
            count=count,
            bar_width=bar_width,
            base_height=0.05,
            y=self.chart.baseline_y + 0.10,
            label_indices=label_indices,
            label_scale_fn=lambda _: 0.72 if count <= 8 else 0.56 if count <= 16 else 0.46,
            show_value_labels=False,
            bar_color=(85, 170, 255),
            hover_key_name="state_index",
        )

    def bar_color(self, index, amplitude):
        if self.measured_index == index:
            return (80, 210, 120)
        if self.measured_index is not None:
            return (50, 66, 94)
        if index == self.marked_index:
            return (255, 190, 80) if amplitude >= 0 else (255, 132, 94)
        return (85, 170, 255) if amplitude >= 0 else (230, 96, 108)

    def update_visuals(self, animated=True):
        duration = 0.28 if animated else 0.0
        max_amplitude = max(max(abs(amplitude) for amplitude in self.amplitudes), abs(self.last_mean), 0.001)
        visual_scale = self.max_bar_extent / max_amplitude
        mean_y = self.chart.baseline_y + self.last_mean * visual_scale
        self.mean_line.set_y(mean_y, animated=animated, duration=duration)

        for index, amplitude in enumerate(self.amplitudes):
            visual_height = amplitude * visual_scale
            height = max(abs(visual_height), 0.02)
            center_y = self.chart.baseline_y + visual_height / 2
            self.chart.set_bar(
                index,
                height=height,
                center_y=center_y,
                bar_color=self.bar_color(index, amplitude),
                animated=animated,
                duration=duration,
            )

    def do_oracle(self):
        self.amplitudes, self.last_mean = oracle_step(self.amplitudes, self.marked_index)
        self.phase = "diffusion"
        self.update_visuals(animated=True)
        self.update_ui()

    def do_diffusion(self):
        self.amplitudes, self.last_mean = diffusion_step(self.amplitudes)
        self.iteration += 1
        self.phase = "oracle"
        self.update_visuals(animated=True)
        self.update_ui()

    def step(self):
        self.measured_index = None
        if self.phase == "oracle":
            self.do_oracle()
        else:
            self.do_diffusion()

    def toggle_run(self):
        self.running = not self.running
        self.buttons["start"].set_text("Pause" if self.running else "Start")
        self.update_ui()

    def measure_current_state(self):
        self.running = False
        self.buttons["start"].set_text("Start")
        result = measure_state(self.amplitudes)
        self.measured_index = result
        self.amplitudes = [0.0 for _ in range(self.n_states)]
        self.amplitudes[result] = 1.0
        self.last_mean = 1.0 / self.n_states
        self.update_visuals(animated=False)
        self.update_ui()

    def describe_state(self):
        target_probability = self.amplitudes[self.marked_index] * self.amplitudes[self.marked_index]
        if self.measured_index is not None:
            if self.measured_index == self.marked_index:
                return f"Measured target {self.bit_label(self.marked_index)}."
            return f"Measured {self.bit_label(self.measured_index)}. Target {self.bit_label(self.marked_index)}."
        if self.phase == "oracle":
            if self.iteration == 0:
                return f"Ready. Target {self.bit_label(self.marked_index)} starts at {target_probability:.0%}."
            if self.iteration >= self.goal_iterations():
                return f"Peak reached. Target {self.bit_label(self.marked_index)} at {target_probability:.0%}."
            return f"Iteration {self.iteration}: target {self.bit_label(self.marked_index)} at {target_probability:.0%}."
        return f"Oracle flips target {self.bit_label(self.marked_index)}."

    def update_ui(self):
        target_amplitude = self.amplitudes[self.marked_index]
        target_probability = target_amplitude * target_amplitude
        self.selection_text.set_text(
            f"{self.qubits} qubits   {self.n_states} states\n"
            f"Target {self.bit_label(self.marked_index)}   Goal {self.goal_iterations()} iterations\n"
            f"Speed {self.auto_interval:.1f}s   Current chance {target_probability:.0%}"
        )
        self.status_text.set_text(self.describe_state())

    def tick(self, dt: float):
        if not self.enabled:
            return
        if self.running:
            self.auto_timer += dt
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
            self.measure_current_state()
        elif key == "escape":
            self.controller.exit_app()
