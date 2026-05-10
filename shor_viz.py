from math import gcd
from random import Random

from shor_math import (
    build_recovery_candidates,
    candidate_witnesses,
    extract_factors,
    multiplicative_order,
    simulate_quantum_measurement,
)
from visualization_ui import (
    BarChartWidget,
    ControlGrid,
    MeasurementLaneWidget,
    PanelBlock,
    ReferenceLine,
    Spacing,
    StageTrackerWidget,
    VisualizationScaffold,
)


class ShorViz:
    def __init__(self, controller, parent_panel):
        self.controller = controller
        self.parent_panel = parent_panel
        self.ui = VisualizationScaffold(parent_panel)

        self.samples = [15, 21, 33, 35, 39, 51, 55, 57, 65, 77, 85, 91]
        self.number_index = 0
        self.rng = Random()
        self.auto_interval = 0.8
        self.auto_timer = 0.0
        self.running = False

        self.number = self.samples[self.number_index]
        self.witness_choices = []
        self.witness_index = 0
        self.witness = 2
        self.register_size = 0
        self.true_order = None
        self.stage = "gcd"
        self.sequence_values = [1]
        self.scan_index = 0
        self.measurement = None
        self.recovered_order = None
        self.result_factors = None
        self.phase_fraction = 0.0
        self.recovery_candidates = []
        self.recovery_choice = None

        self._build_ui()
        self._set_number(self.number_index)
        self.hide()

    def _build_ui(self):
        top_left_inner = self.ui.top_left.content_region(Spacing.md, Spacing.md)
        top_right_inner = self.ui.top_right.content_region(Spacing.md, Spacing.md)
        bottom_left_inner = self.ui.bottom_left.content_region(Spacing.md, Spacing.md)
        bottom_right_inner = self.ui.bottom_right.content_region(Spacing.md, Spacing.md)

        left_rows = bottom_left_inner.split_rows([1, 2, 7, 1], gap=Spacing.sm)
        right_columns = bottom_right_inner.split_columns([7, 3], gap=Spacing.md)
        chart_rows = right_columns[0].split_rows([12, 1], gap=Spacing.sm)
        side_rows = right_columns[1].split_rows([3, 7], gap=Spacing.sm)
        measure_rows = top_right_inner.split_rows([1, 2], gap=Spacing.sm)
        text_rows = side_rows[0].inset(Spacing.sm, Spacing.sm).split_rows([2, 2, 3.5, 3.5], gap=Spacing.xs)

        self.chart_panel = PanelBlock(self.ui.root, chart_rows[0], inner=True)
        self.text_panel = PanelBlock(self.ui.root, side_rows[0], inner=True)
        self.stage_panel = PanelBlock(self.ui.root, side_rows[1], inner=True)

        self.title_text = self.ui.top_left.add_text_in_region(top_left_inner, "Shor Algorithm", scale=1.15, mode="shrink")
        self.controls_text = self.ui.bottom_left.add_text_in_region(
            left_rows[0],
            "Controls",
            scale=1.20,
            text_color=(214, 222, 236),
            mode="shrink",
        )
        self.info_text = self.ui.bottom_left.add_text_in_region(left_rows[1], "", scale=0.64, mode="wrap_shrink")
        self.measure_title = self.ui.top_right.add_text_in_region(
            measure_rows[0],
            "Measurement lane c / Q",
            scale=0.92,
            text_color=(185, 194, 208),
            mode="shrink",
        )
        self.status_text = self.text_panel.add_text_in_region(
            text_rows[0],
            "",
            scale=0.66,
            text_color=(214, 222, 236),
            mode="wrap_shrink",
        )
        self.result_text = self.text_panel.add_text_in_region(
            text_rows[1],
            "",
            scale=0.60,
            text_color=(214, 222, 236),
            mode="wrap_shrink",
        )
        self.recovery_text = self.text_panel.add_text_in_region(
            text_rows[2],
            "",
            scale=0.54,
            text_color=(196, 205, 218),
            mode="wrap_shrink",
        )
        self.hover_text = self.text_panel.add_text_in_region(
            text_rows[3],
            "",
            scale=0.48,
            text_color=(185, 194, 208),
            mode="wrap_shrink",
        )

        self.controls_grid = ControlGrid(
            self.ui.bottom_left,
            rows=4,
            columns=2,
            region=left_rows[2],
            x_padding=0.0,
            y_padding=0.0,
            h_gap=Spacing.sm,
            v_gap=Spacing.sm,
        )
        self.navigation_grid = ControlGrid(
            self.ui.bottom_left,
            rows=1,
            columns=2,
            region=left_rows[3],
            x_padding=0.0,
            y_padding=0.0,
            h_gap=Spacing.sm,
            v_gap=0.0,
        )

        self.buttons = {
            "start": self.controls_grid.add_button("Start", 0, 0, self.toggle_run, accent=True),
            "step": self.controls_grid.add_button("Step", 0, 1, self.step),
            "reset": self.controls_grid.add_button("Reset", 1, 0, self.reset_algorithm),
            "factor": self.controls_grid.add_button("Factor", 1, 1, self.run_to_completion),
            "number_minus": self.controls_grid.add_button("Number -", 2, 0, self.decrease_number),
            "number_plus": self.controls_grid.add_button("Number +", 2, 1, self.increase_number),
            "base_minus": self.controls_grid.add_button("Base -", 3, 0, self.decrease_witness),
            "base_plus": self.controls_grid.add_button("Base +", 3, 1, self.increase_witness),
            "back": self.navigation_grid.add_button("Back", 0, 0, self.parent_panel.show_choice_menu),
            "home": self.navigation_grid.add_button("Home", 0, 1, self.controller.back_to_main, accent=True),
        }

        baseline_y = self.chart_panel.region.bottom + self.chart_panel.region.height * 0.10
        self.baseline = ReferenceLine(
            self.ui.root,
            x=self.chart_panel.region.center_x,
            y=baseline_y,
            width=self.chart_panel.region.width - 2 * Spacing.xs,
            thickness=0.004,
            line_color=(186, 194, 206, 220),
        )
        self.chart = BarChartWidget(
            self.ui.root,
            center_x=self.chart_panel.region.center_x,
            baseline_y=baseline_y,
            chart_width=self.chart_panel.region.width - 2 * Spacing.sm,
            axis_parent=self.ui.root,
            axis_label_y=chart_rows[1].center_y,
            min_bar_height=0.026,
            default_bar_color=(58, 89, 146),
        )
        self.measurement_lane = MeasurementLaneWidget(
            self.ui.root,
            center_x=measure_rows[1].center_x,
            center_y=measure_rows[1].center_y,
            width=measure_rows[1].width - 2 * Spacing.lg,
            left=measure_rows[1].left + Spacing.lg,
        )
        self.stage_tracker = StageTrackerWidget(
            self.stage_panel,
            [("gcd", "GCD"), ("order", "Order"), ("measure", "Measure"), ("recover", "Recover"), ("factor", "Factor")],
        )
        self.stage_palette = {
            "gcd": (78, 110, 186),
            "order": (255, 196, 88),
            "measure": (255, 146, 88),
            "recover": (112, 208, 168),
            "factor": (96, 214, 150),
        }
        self.stage_inactive = (39, 50, 74)

    @property
    def enabled(self):
        return self.ui.enabled

    def show(self):
        self.ui.show()

    def hide(self):
        self.running = False
        self.auto_timer = 0.0
        self.ui.hide()

    def _set_number(self, index: int):
        self.number_index = index % len(self.samples)
        self.number = self.samples[self.number_index]
        self.witness_choices = candidate_witnesses(self.number)
        self.witness_index = 0
        self.witness = self.witness_choices[0]
        self.reset_algorithm()

    def increase_number(self):
        self._set_number(self.number_index + 1)

    def decrease_number(self):
        self._set_number(self.number_index - 1)

    def increase_witness(self):
        self.witness_index = (self.witness_index + 1) % len(self.witness_choices)
        self.witness = self.witness_choices[self.witness_index]
        self.reset_algorithm()

    def decrease_witness(self):
        self.witness_index = (self.witness_index - 1) % len(self.witness_choices)
        self.witness = self.witness_choices[self.witness_index]
        self.reset_algorithm()

    def visible_slots(self) -> int:
        if self.true_order is None:
            return 8
        return max(8, min(18, self.true_order + 2))

    def reset_algorithm(self):
        self.running = False
        self.auto_timer = 0.0
        self.stage = "gcd"
        self.scan_index = 0
        self.measurement = None
        self.recovered_order = None
        self.result_factors = None
        self.phase_fraction = 0.0
        self.recovery_candidates = []
        self.recovery_choice = None
        self.register_size = 1 << (2 * self.number.bit_length())
        self.true_order = multiplicative_order(self.witness, self.number)
        self.sequence_values = [1]
        self.buttons["start"].set_text("Start")
        self.rebuild_chart()
        self.measurement_lane.rebuild_markers(self.true_order)
        self.update_visuals(animated=False)
        self.update_ui("Ready to inspect the sequence.")

    def rebuild_chart(self):
        slots = self.visible_slots()
        slot_width = self.chart.chart_width / slots
        bar_width = min(0.055, slot_width * 0.55)
        self.chart.rebuild(
            count=slots,
            bar_width=bar_width,
            base_height=0.04,
            y=self.chart.baseline_y + 0.02,
            label_indices=set(range(slots)),
            label_scale_fn=lambda _: 0.54,
            show_value_labels=True,
            value_label_y=self.chart.baseline_y + 0.055,
            value_label_scale=0.48,
            value_label_color=(196, 205, 218),
            bar_color=(58, 89, 146),
            hover_key_name="step_index",
        )

    def bar_color(self, index: int, value: int):
        if index > self.scan_index and self.stage == "order":
            return (52, 68, 98)
        if index == self.scan_index and self.stage == "order":
            return (255, 196, 88)
        if value == 1 and index != 0:
            return (96, 214, 150)
        if index < len(self.sequence_values):
            return (84, 166, 255)
        return (52, 68, 98)

    def update_visuals(self, animated=True):
        duration = 0.24 if animated else 0.0
        divisor = max(1, self.number - 1)
        for index in range(len(self.chart.bars)):
            has_value = index < len(self.sequence_values)
            value = self.sequence_values[index] if has_value else 0
            height = max(0.026, (value / divisor if has_value else 0.0) * 0.31)
            center_y = self.chart.baseline_y + height / 2
            self.chart.set_bar(
                index,
                height=height,
                center_y=center_y,
                bar_color=self.bar_color(index, value),
                animated=animated,
                duration=duration,
            )
            self.chart.set_value_label(index, str(value) if has_value else "", center_y + height / 2 + 0.02)

        self.measurement_lane.set_fraction(self.phase_fraction, animated=animated, duration=duration)
        if self.stage in self.stage_palette:
            self.stage_tracker.set_active(self.stage, self.stage_palette, self.stage_inactive)

    def step(self):
        if self.stage == "done":
            self.running = False
            self.buttons["start"].set_text("Start")
            return

        if self.stage == "gcd":
            divisor = gcd(self.witness, self.number)
            if 1 < divisor < self.number:
                self.result_factors = tuple(sorted((divisor, self.number // divisor)))
                self.stage = "done"
                self.update_visuals(animated=False)
                self.update_ui("Base shares a divisor with N.")
                return
            self.stage = "order"
            self.update_visuals(animated=False)
            self.update_ui("gcd(a, N)=1. Search for period r.")
            return

        if self.stage == "order":
            self.scan_index += 1
            value = pow(self.witness, self.scan_index, self.number)
            if len(self.sequence_values) <= self.scan_index:
                self.sequence_values.append(value)
            else:
                self.sequence_values[self.scan_index] = value
            if value == 1:
                self.true_order = self.scan_index
                self.stage = "measure"
                self.measurement_lane.rebuild_markers(self.true_order)
                self.update_visuals(animated=True)
                self.update_ui(f"Found period r={self.true_order}. Next: phase estimate.")
            else:
                self.update_visuals(animated=True)
                self.update_ui(f"x={self.scan_index}: a^x mod N = {value}")
            return

        if self.stage == "measure":
            if self.true_order is None or self.true_order <= 1:
                self.stage = "done"
                self.update_ui("This base does not give a useful period.")
                return
            self.measurement = simulate_quantum_measurement(self.true_order, self.register_size, self.rng)
            self.phase_fraction = self.measurement / float(self.register_size)
            self.stage = "recover"
            self.recovery_candidates = build_recovery_candidates(self.measurement, self.register_size, self.witness, self.number)
            self.recovery_choice = None
            self.update_visuals(animated=True)
            self.update_ui(f"Measured c={self.measurement}, c/Q={self.phase_fraction:.3f}")
            return

        if self.stage == "recover":
            self.recovered_order = None
            self.recovery_choice = None
            for candidate in self.recovery_candidates:
                if candidate["matches"]:
                    self.recovered_order = candidate["matches"][0]
                    self.recovery_choice = candidate
                    break
            self.stage = "factor"
            self.update_visuals(animated=False)
            if self.recovered_order is None:
                self.update_ui("Continued fractions did not recover a period.")
            else:
                self.update_ui(f"Continued fractions recovered r={self.recovered_order}.")
            return

        if self.stage == "factor":
            if self.recovered_order is not None:
                self.result_factors = extract_factors(self.number, self.witness, self.recovered_order)
            self.stage = "done"
            self.update_visuals(animated=False)
            if self.result_factors is None:
                self.update_ui("Recovered period was not enough to extract factors.")
            else:
                left, right = self.result_factors
                self.update_ui(f"Factors found: {self.number} = {left} x {right}")

    def run_to_completion(self):
        self.running = False
        self.buttons["start"].set_text("Start")
        guard = 0
        while self.stage != "done" and guard < 64:
            self.step()
            guard += 1

    def toggle_run(self):
        self.running = not self.running
        self.buttons["start"].set_text("Pause" if self.running else "Start")
        self.update_ui("Auto-play running." if self.running else "Paused.")

    def update_ui(self, status: str):
        divisor = gcd(self.witness, self.number)
        order_text = str(self.true_order) if self.true_order is not None else "?"
        self.info_text.set_text(
            f"N={self.number}   a={self.witness}   gcd={divisor}\n"
            f"Q={self.register_size}   base {self.witness_index + 1}/{len(self.witness_choices)}"
        )

        if self.result_factors is not None:
            left, right = self.result_factors
            status_text = "FACTOR"
            result_text = f"{self.number} = {left} x {right}"
        elif self.stage == "gcd":
            status_text = f"GCD   r={order_text}"
            result_text = status
        elif self.stage == "order":
            status_text = f"ORDER   r={order_text}"
            result_text = status
        elif self.stage == "measure":
            status_text = "MEASURE"
            result_text = status
        elif self.stage == "recover":
            status_text = "RECOVER"
            result_text = status
        elif self.stage == "factor":
            status_text = "FACTOR"
            result_text = status
        else:
            status_text = "DONE"
            result_text = status

        if not self.recovery_candidates:
            recovery_text = "Continued fractions\nwaiting for measurement"
        else:
            lines = ["Continued fractions"]
            for candidate in self.recovery_candidates[:3]:
                suffix = " -> no period"
                if candidate["matches"]:
                    suffix = f" -> {candidate['matches'][0]}"
                prefix = "> " if self.recovery_choice is candidate else "  "
                lines.append(f"{prefix}{candidate['fraction']}{suffix}")
            recovery_text = "\n".join(lines)

        if self.result_factors is None and self.measurement is not None and self.recovered_order is not None:
            result_text = f"c={self.measurement}   r={self.recovered_order}"

        self.status_text.set_text(status_text)
        self.result_text.set_text(result_text)
        self.recovery_text.set_text(recovery_text)

    def update_hover_text(self):
        index = self.chart.hovered_index("step_index")
        if index is None:
            self.hover_text.set_text("")
            return
        if index < len(self.sequence_values):
            value = self.sequence_values[index]
            marker = " *" if index == self.scan_index and self.stage == "order" else ""
            self.hover_text.set_text(f"x = {index}{marker}\n{self.witness}^{index} mod {self.number} = {value}")
        else:
            self.hover_text.set_text(f"x = {index}\nSequence not expanded yet.")

    def tick(self, dt: float):
        if not self.enabled:
            return
        self.update_hover_text()
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
        elif key == "n":
            self.increase_number()
        elif key == "a":
            self.increase_witness()
        elif key == "enter":
            self.run_to_completion()
        elif key == "escape":
            self.controller.exit_app()
