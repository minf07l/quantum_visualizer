from math import gcd
from random import Random
from typing import List, Optional, Tuple

from ursina import Button, Entity, Text, color, curve, destroy, mouse, time


def multiplicative_order(a: int, modulus: int) -> Optional[int]:
    if gcd(a, modulus) != 1:
        return None
    value = 1
    for order in range(1, modulus + 1):
        value = (value * a) % modulus
        if value == 1:
            return order
    return None


def continued_fraction_convergents(numerator: int, denominator: int) -> List[Tuple[int, int]]:
    a = numerator
    b = denominator
    quotients = []
    while b:
        q = a // b
        quotients.append(q)
        a, b = b, a - q * b

    prev_num, num = 0, 1
    prev_den, den = 1, 0
    convergents = []
    for q in quotients:
        prev_num, num = num, q * num + prev_num
        prev_den, den = den, q * den + prev_den
        convergents.append((num, den))
    return convergents


def recover_period_from_measurement(measurement: int, register_size: int, a: int, modulus: int) -> Optional[int]:
    if measurement == 0:
        return None
    for _, denominator in continued_fraction_convergents(measurement, register_size):
        if denominator == 0:
            continue
        for multiplier in range(1, modulus + 1):
            candidate = denominator * multiplier
            if pow(a, candidate, modulus) == 1:
                return candidate
    return None


def simulate_quantum_measurement(order: int, register_size: int, rng: Random) -> int:
    numerator = rng.randrange(1, order)
    return int(round(numerator * register_size / order)) % register_size


def extract_factors(number: int, witness: int, order: int) -> Optional[Tuple[int, int]]:
    if order % 2 == 1:
        return None
    midpoint = pow(witness, order // 2, number)
    if midpoint in (1, number - 1):
        return None
    factor_a = gcd(midpoint - 1, number)
    factor_b = gcd(midpoint + 1, number)
    if 1 < factor_a < number and 1 < factor_b < number:
        return tuple(sorted((factor_a, factor_b)))
    return None


def candidate_witnesses(number: int, max_order: int = 18) -> List[int]:
    useful = []
    shortcuts = []
    for witness in range(2, number):
        divisor = gcd(witness, number)
        if 1 < divisor < number:
            shortcuts.append(witness)
            continue
        order = multiplicative_order(witness, number)
        if order is None or order % 2 == 1 or order > max_order:
            continue
        if extract_factors(number, witness, order) is not None:
            useful.append(witness)
    return useful + shortcuts or [2]


class ShorViz(Entity):
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
        self.chart_x = 0.08
        self.chart_inner_width = 0.54
        self.chart_inner_height = 0.46
        self.chart_inner_y = self.bottom_y - 0.015
        self.info_panel_x = 0.50
        self.info_panel_width = 0.26
        self.info_panel_height = 0.46
        self.chart_bottom_y = -0.18
        self.chart_width = 0.54
        self.bar_max_height = 0.31
        self.chart_label_y = self.chart_inner_y - self.chart_inner_height / 2 - 0.028
        self.measure_lane_left = self.right_x - 0.37
        self.measure_lane_width = 0.74
        self.info_panel_top = self.chart_inner_y + self.info_panel_height / 2
        self.info_panel_left = self.info_panel_x - self.info_panel_width / 2 + 0.05
        self.side_gap = 0.015
        self.text_panel_height = 0.14
        self.states_panel_height = self.chart_inner_height - self.text_panel_height - self.side_gap
        self.text_panel_y = self.chart_inner_y + self.chart_inner_height / 2 - self.text_panel_height / 2
        self.states_panel_y = self.chart_inner_y - self.chart_inner_height / 2 + self.states_panel_height / 2
        self.side_panel_width = 0.25

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

        self.bars = []
        self.x_labels = []
        self.value_labels = []
        self.stage_cards = {}
        self.fraction_markers = []
        self.peak_markers = []
        self.axis_panel = None
        self.measure_panel = None
        self.info_content_panel = None
        self.text_content_panel = None
        self.states_content_panel = None

        self._setup_scene()
        self._setup_ui()
        self._set_number(self.number_index)
        self.hide()

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
        self._panel(self.chart_x, self.chart_inner_y, self.chart_inner_width, self.chart_inner_height, inner=True)
        self._panel(self.info_panel_x, self.text_panel_y, self.side_panel_width, self.text_panel_height, inner=True)
        self._panel(self.info_panel_x, self.states_panel_y, self.side_panel_width, self.states_panel_height, inner=True)
        self.axis_panel = Entity(parent=self, position=(self.chart_x, self.chart_label_y + 0.01, -0.08))
        self.measure_panel = Entity(parent=self, position=(self.right_x, self.top_y, -0.08))
        self.info_content_panel = Entity(parent=self, position=(self.info_panel_x, self.chart_inner_y, -0.08))
        self.text_content_panel = Entity(parent=self, position=(self.info_panel_x, self.text_panel_y, -0.08))
        self.states_content_panel = Entity(parent=self, position=(self.info_panel_x, self.states_panel_y, -0.08))
        self.baseline = Entity(
            parent=self,
            model="quad",
            position=(self.chart_x, self.chart_bottom_y, -0.03),
            scale=(self.chart_width, 0.004, 1),
            color=color.rgba(186, 194, 206, 220),
        )
        self.measure_line = Entity(
            parent=self,
            model="quad",
            position=(self.right_x, 0.242, -0.03),
            scale=(self.measure_lane_width, 0.004, 1),
            color=color.rgba(120, 170, 240, 160),
        )
        self.measure_dot = Entity(
            parent=self,
            model="quad",
            position=(self.measure_lane_left, 0.242, -0.04),
            scale=(0.016, 0.016, 1),
            color=color.rgb(255, 202, 96),
        )

    def _setup_ui(self):
        self.controls_panel = Entity(parent=self, position=(self.left_x, self.bottom_y, -0.03))
        Text(
            parent=self,
            text="Shor Algorithm",
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
        self.info_text = Text(
            parent=self.controls_panel,
            text="",
            position=(0, 0.19, -0.12),
            origin=(0, 0),
            scale=0.40,
            color=color.white,
        )
        self.status_text = Text(
            parent=self.text_content_panel,
            text="",
            position=(0, 0.035, -0.12),
            origin=(0, 0),
            scale=0.42,
            color=color.rgb(214, 222, 236),
        )
        self.result_text = Text(
            parent=self.text_content_panel,
            text="",
            position=(0, -0.005, -0.12),
            origin=(0, 0),
            scale=0.38,
            color=color.rgb(214, 222, 236),
        )
        self.recovery_text = Text(
            parent=self.text_content_panel,
            text="",
            position=(0, -0.045, -0.12),
            origin=(0, 0),
            scale=0.34,
            color=color.rgb(196, 205, 218),
        )
        self.hover_text = Text(
            parent=self.text_content_panel,
            text="",
            position=(0, -0.080, -0.12),
            origin=(-0.5, 0),
            scale=0.0,
            color=color.rgb(185, 194, 208),
        )
        self.measure_title = Text(
            parent=self.measure_panel,
            text="Measurement lane c / Q",
            position=(0, 0.055, -0.12),
            origin=(0, 0),
            scale=0.70,
            color=color.rgb(185, 194, 208),
        )

        self.back_button = self._button(
            "Back",
            (-0.072, -0.225),
            self.parent_panel.show_choice_menu,
        )
        self.home_button = self._button(
            "Home",
            (0.072, -0.225),
            self.controller.back_to_main,
            accent=True,
        )
        self.start_button = self._button(
            "Start",
            (-0.072, 0.125),
            self.toggle_run,
            accent=True,
        )
        self.step_button = self._button("Step", (0.072, 0.125), self.step)
        self.reset_button = self._button("Reset", (-0.072, 0.055), self.reset_algorithm)
        self.factor_button = self._button("Factor", (0.072, 0.055), self.run_to_completion)
        self.n_minus_button = self._button("Number -", (-0.072, -0.015), self.decrease_number)
        self.n_plus_button = self._button("Number +", (0.072, -0.015), self.increase_number)
        self.a_minus_button = self._button("Base -", (-0.072, -0.085), self.decrease_witness)
        self.a_plus_button = self._button("Base +", (0.072, -0.085), self.increase_witness)

        stage_names = [
            ("gcd", "GCD"),
            ("order", "Order"),
            ("measure", "Measure"),
            ("recover", "Recover"),
            ("factor", "Factor"),
        ]
        start_x = 0.0
        for offset, (stage_key, title) in enumerate(stage_names):
            y = 0.085 - offset * 0.045
            card = Entity(
                parent=self.states_content_panel,
                model="quad",
                position=(start_x, y, -0.06),
                scale=(0.18, 0.036, 1),
                color=color.rgb(39, 50, 74),
            )
            Text(
                parent=self.states_content_panel,
                text=title,
                position=(start_x, y - 0.006, -0.12),
                origin=(0, 0),
                scale=0.42,
                color=color.white,
            )
            self.stage_cards[stage_key] = card

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
            scale=0.36,
            color=color.white,
        )
        return button

    def _set_button_label(self, button, text):
        button.label.text = text

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

    def fraction_x(self, fraction: float) -> float:
        return self.measure_lane_left + self.measure_lane_width * fraction

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
        self._set_button_label(self.start_button, "Start")
        self.rebuild_bars()
        self.rebuild_fraction_markers()
        self.rebuild_peak_markers()
        self.update_visuals(animated=False)
        self.update_ui("Ready to inspect the modular sequence.")

    def rebuild_bars(self):
        for entity in self.bars + self.x_labels + self.value_labels:
            destroy(entity)
        self.bars = []
        self.x_labels = []
        self.value_labels = []
        slots = self.visible_slots()
        slot_width = self.chart_width / slots
        bar_width = min(0.055, slot_width * 0.55)
        start_x = self.chart_x - self.chart_width / 2 + slot_width / 2

        for index in range(slots):
            x = start_x + index * slot_width
            bar = Entity(
                parent=self,
                model="quad",
                position=(x, self.chart_bottom_y + 0.02, -0.03),
                scale=(bar_width, 0.04, 1),
                color=color.rgb(58, 89, 146),
                collider="box",
            )
            bar.step_index = index
            self.bars.append(bar)
            self.x_labels.append(
                Text(
                    parent=self.axis_panel,
                    text=str(index),
                    position=(x - self.chart_x, 0, 0),
                    origin=(0, 0),
                    scale=0.38,
                    color=color.rgb(222, 229, 240),
                )
            )
            self.value_labels.append(
                Text(
                    parent=self,
                    text="",
                    position=(x, self.chart_bottom_y + 0.055),
                    origin=(0, 0),
                    scale=0.34,
                    color=color.rgb(196, 205, 218),
                )
            )

    def rebuild_fraction_markers(self):
        for marker in self.fraction_markers:
            destroy(marker)
        self.fraction_markers = []
        if not self.true_order or self.true_order <= 1:
            return

        for numerator in range(self.true_order + 1):
            fraction = numerator / self.true_order
            size_y = 0.032 if numerator in (0, self.true_order) else 0.022
            marker = Entity(
                parent=self,
                model="quad",
                position=(self.fraction_x(fraction), 0.24, -0.025),
                scale=(0.004, size_y, 1),
                color=color.rgba(138, 168, 218, 150),
            )
            self.fraction_markers.append(marker)

    def rebuild_peak_markers(self):
        for marker in self.peak_markers:
            destroy(marker)
        self.peak_markers = []
        if not self.true_order or self.true_order <= 1:
            return

        for numerator in range(self.true_order):
            fraction = numerator / self.true_order
            marker = Entity(
                parent=self,
                model="quad",
                position=(self.fraction_x(fraction), 0.262, -0.024),
                scale=(0.010, 0.010, 1),
                color=color.rgba(255, 196, 88, 190),
            )
            self.peak_markers.append(marker)

    def build_recovery_candidates(self):
        if self.measurement is None:
            return []

        candidates = []
        seen = set()
        for numerator, denominator in continued_fraction_convergents(self.measurement, self.register_size):
            if denominator == 0 or denominator in seen:
                continue
            seen.add(denominator)
            matches = []
            for multiplier in range(1, self.number + 1):
                candidate = denominator * multiplier
                if pow(self.witness, candidate, self.number) == 1:
                    matches.append(candidate)
                    if len(matches) >= 3:
                        break
            candidates.append(
                {
                    "fraction": f"{numerator}/{denominator}",
                    "denominator": denominator,
                    "matches": matches,
                }
            )
        return candidates

    def bar_color(self, index: int, value: int):
        if index > self.scan_index and self.stage == "order":
            return color.rgb(52, 68, 98)
        if index == self.scan_index and self.stage == "order":
            return color.rgb(255, 196, 88)
        if value == 1 and index != 0:
            return color.rgb(96, 214, 150)
        if index < len(self.sequence_values):
            return color.rgb(84, 166, 255)
        return color.rgb(52, 68, 98)

    def update_visuals(self, animated=True):
        duration = 0.24 if animated else 0.0
        divisor = max(1, self.number - 1)

        for index, bar in enumerate(self.bars):
            has_value = index < len(self.sequence_values)
            value = self.sequence_values[index] if has_value else 0
            height = max(0.026, (value / divisor if has_value else 0.0) * self.bar_max_height)
            center_y = self.chart_bottom_y + height / 2
            if animated:
                bar.animate("scale_y", height, duration=duration, curve=curve.out_cubic)
                bar.animate("y", center_y, duration=duration, curve=curve.out_cubic)
            else:
                bar.scale_y = height
                bar.y = center_y

            bar.color = self.bar_color(index, value)
            self.value_labels[index].text = str(value) if has_value else ""
            self.value_labels[index].y = center_y + height / 2 + 0.02

        target_x = self.fraction_x(self.phase_fraction)
        if animated:
            self.measure_dot.animate("x", target_x, duration=duration, curve=curve.out_cubic)
        else:
            self.measure_dot.x = target_x

        active = {
            "gcd": color.rgb(78, 110, 186),
            "order": color.rgb(255, 196, 88),
            "measure": color.rgb(255, 146, 88),
            "recover": color.rgb(112, 208, 168),
            "factor": color.rgb(96, 214, 150),
        }
        for stage_name, card in self.stage_cards.items():
            card.color = active[stage_name] if stage_name == self.stage else color.rgb(39, 50, 74)

    def step(self):
        if self.stage == "done":
            self.running = False
            self._set_button_label(self.start_button, "Start")
            return

        if self.stage == "gcd":
            divisor = gcd(self.witness, self.number)
            if 1 < divisor < self.number:
                self.result_factors = tuple(sorted((divisor, self.number // divisor)))
                self.stage = "done"
                self.update_visuals(animated=False)
                self.update_ui("The chosen base already shares a divisor with N.")
                return
            self.stage = "order"
            self.update_visuals(animated=False)
            self.update_ui("gcd(a, N) = 1, so the algorithm searches for the period r.")
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
                self.rebuild_fraction_markers()
                self.rebuild_peak_markers()
                self.update_visuals(animated=True)
                self.update_ui(f"Found period r = {self.true_order}. Next step simulates phase estimation.")
            else:
                self.update_visuals(animated=True)
                self.update_ui(f"x = {self.scan_index}: a^x mod N = {value}. The cycle has not closed yet.")
            return

        if self.stage == "measure":
            if self.true_order is None or self.true_order <= 1:
                self.stage = "done"
                self.update_ui("This base does not produce a useful period.")
                return
            self.measurement = simulate_quantum_measurement(self.true_order, self.register_size, self.rng)
            self.phase_fraction = self.measurement / float(self.register_size)
            self.stage = "recover"
            self.recovery_candidates = self.build_recovery_candidates()
            self.recovery_choice = None
            self.update_visuals(animated=True)
            self.update_ui(f"Measured c = {self.measurement}, so c / Q = {self.phase_fraction:.3f}.")
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
                self.update_ui("Continued fractions could not recover a period from this sample.")
            else:
                self.update_ui(f"Continued fractions recovered r = {self.recovered_order}.")
            return

        if self.stage == "factor":
            if self.recovered_order is not None:
                self.result_factors = extract_factors(self.number, self.witness, self.recovered_order)
            self.stage = "done"
            self.update_visuals(animated=False)
            if self.result_factors is None:
                self.update_ui("The recovered period was not enough to extract non-trivial factors.")
            else:
                left, right = self.result_factors
                self.update_ui(f"Factor extraction succeeded: {self.number} = {left} x {right}.")

    def run_to_completion(self):
        self.running = False
        self._set_button_label(self.start_button, "Start")
        guard = 0
        while self.stage != "done" and guard < 64:
            self.step()
            guard += 1

    def toggle_run(self):
        self.running = not self.running
        self._set_button_label(self.start_button, "Pause" if self.running else "Start")
        self.update_ui("Auto-play running." if self.running else "Paused.")

    def update_ui(self, status: str):
        divisor = gcd(self.witness, self.number)
        order_text = str(self.true_order) if self.true_order is not None else "?"
        self.info_text.text = (
            f"N = {self.number}   a = {self.witness}\n"
            f"gcd(a, N) = {divisor}   Q = {self.register_size}\n"
            f"Useful bases {self.witness_index + 1}/{len(self.witness_choices)}"
        )
        if self.result_factors is not None:
            left, right = self.result_factors
            self.status_text.text = "Stage: FACTOR"
            self.result_text.text = f"Result: {self.number} = {left} x {right}"
        elif self.stage == "gcd":
            self.status_text.text = f"Stage: GCD   r = {order_text}"
            self.result_text.text = status
        elif self.stage == "order":
            self.status_text.text = f"Stage: ORDER   r = {order_text}"
            self.result_text.text = status
        elif self.stage == "measure":
            self.status_text.text = "Stage: MEASURE"
            self.result_text.text = status
        elif self.stage == "recover":
            self.status_text.text = "Stage: RECOVER"
            self.result_text.text = status
        elif self.stage == "factor":
            self.status_text.text = "Stage: FACTOR"
            self.result_text.text = status
        else:
            self.status_text.text = "Stage: DONE"
            self.result_text.text = status

        if not self.recovery_candidates:
            self.recovery_text.text = "Continued fractions\nwaiting for measurement"
        else:
            lines = ["Continued fractions"]
            for candidate in self.recovery_candidates[:4]:
                suffix = " -> no period"
                if candidate["matches"]:
                    suffix = f" -> {candidate['matches'][0]}"
                prefix = "> " if self.recovery_choice is candidate else "  "
                lines.append(f"{prefix}{candidate['fraction']}{suffix}")
            self.recovery_text.text = "\n".join(lines)

        if self.result_factors is None and self.measurement is not None and self.recovered_order is not None:
            self.result_text.text = f"c = {self.measurement}   recovered r = {self.recovered_order}"

    def update_hover_text(self):
        hovered = mouse.hovered_entity
        if hovered is not None and hasattr(hovered, "step_index") and hovered in self.bars:
            index = hovered.step_index
            if index < len(self.sequence_values):
                value = self.sequence_values[index]
                marker = " *" if index == self.scan_index and self.stage == "order" else ""
                self.hover_text.text = f"x = {index}{marker}\n{self.witness}^{index} mod {self.number} = {value}"
            else:
                self.hover_text.text = f"x = {index}\nSequence not expanded yet."
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
        elif key == "n":
            self.increase_number()
        elif key == "a":
            self.increase_witness()
        elif key == "enter":
            self.run_to_completion()

    def show(self):
        self.enabled = True

    def hide(self):
        self.running = False
        self.auto_timer = 0.0
        self.enabled = False
