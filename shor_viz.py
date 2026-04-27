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

        self.safe_right = 0.78
        self.safe_top = 0.39
        self.panel_x = -0.54
        self.panel_width = 0.38
        self.button_left_x = -0.62
        self.button_right_x = -0.46
        self.chart_x = 0.18
        self.chart_bottom_y = -0.18
        self.chart_width = 0.78
        self.bar_max_height = 0.31

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

        self.bars = []
        self.x_labels = []
        self.value_labels = []
        self.stage_cards = {}
        self.fraction_markers = []

        self._setup_scene()
        self._setup_ui()
        self._set_number(self.number_index)
        self.hide()

    def _setup_scene(self):
        Entity(
            parent=self,
            model="quad",
            position=(self.chart_x, 0.02, 0),
            scale=(0.96, 0.54, 1),
            color=color.rgb(16, 22, 34),
        )
        Entity(
            parent=self,
            model="quad",
            position=(self.chart_x, 0.02, -0.01),
            scale=(0.86, 0.46, 1),
            color=color.rgb(21, 29, 45),
        )
        self.baseline = Entity(
            parent=self,
            model="quad",
            position=(self.chart_x, self.chart_bottom_y, -0.02),
            scale=(self.chart_width, 0.004, 1),
            color=color.rgba(186, 194, 206, 220),
        )
        self.measure_line = Entity(
            parent=self,
            model="quad",
            position=(self.chart_x, 0.24, -0.02),
            scale=(0.76, 0.004, 1),
            color=color.rgba(120, 170, 240, 160),
        )
        self.measure_dot = Entity(
            parent=self,
            model="quad",
            position=(self.chart_x - 0.38, 0.24, -0.03),
            scale=(0.016, 0.016, 1),
            color=color.rgb(255, 202, 96),
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
            text="Shor Algorithm",
            position=(-0.70, 0.31),
            origin=(-0.5, 0),
            scale=1.3,
            color=color.white,
        )
        Text(
            parent=self,
            text="Period finding through modular powers.",
            position=(-0.70, 0.255),
            origin=(-0.5, 0),
            scale=0.58,
            color=color.rgb(185, 194, 208),
        )
        self.info_text = Text(
            parent=self,
            text="",
            position=(-0.70, 0.16),
            origin=(-0.5, 0),
            scale=0.72,
            color=color.white,
        )
        self.phase_text = Text(
            parent=self,
            text="",
            position=(-0.70, 0.06),
            origin=(-0.5, 0),
            scale=0.62,
            color=color.rgb(255, 209, 116),
        )
        self.status_text = Text(
            parent=self,
            text="",
            position=(-0.70, -0.02),
            origin=(-0.5, 0),
            scale=0.50,
            color=color.rgb(196, 205, 218),
        )
        self.result_text = Text(
            parent=self,
            text="",
            position=(-0.70, -0.13),
            origin=(-0.5, 0),
            scale=0.50,
            color=color.rgb(120, 220, 154),
        )
        self.hover_text = Text(
            parent=self,
            text="",
            position=(0.41, 0.31),
            origin=(-0.5, 0),
            scale=0.50,
            color=color.rgb(185, 194, 208),
        )
        Text(
            parent=self,
            text="Measurement lane c / Q",
            position=(-0.20, 0.285),
            origin=(-0.5, 0),
            scale=0.48,
            color=color.rgb(185, 194, 208),
        )
        Text(
            parent=self,
            text="Space auto   Right step   R reset   N/A change number or base   Enter factor",
            position=(0.0, -0.44),
            origin=(0, 0),
            scale=0.42,
            color=color.rgb(146, 156, 172),
        )

        self.back_button = self._button(
            "Back",
            (self.button_left_x, -0.48),
            self.parent_panel.show_choice_menu,
        )
        self.home_button = self._button(
            "Home",
            (self.button_right_x, -0.48),
            self.controller.back_to_main,
            accent=True,
        )
        self.start_button = self._button(
            "Start",
            (self.button_left_x, -0.20),
            self.toggle_run,
            accent=True,
        )
        self.step_button = self._button("Step", (self.button_right_x, -0.20), self.step)
        self.reset_button = self._button("Reset", (self.button_left_x, -0.27), self.reset_algorithm)
        self.factor_button = self._button("Factor", (self.button_right_x, -0.27), self.run_to_completion)
        self.n_minus_button = self._button("Number -", (self.button_left_x, -0.34), self.decrease_number)
        self.n_plus_button = self._button("Number +", (self.button_right_x, -0.34), self.increase_number)
        self.a_minus_button = self._button("Base -", (self.button_left_x, -0.41), self.decrease_witness)
        self.a_plus_button = self._button("Base +", (self.button_right_x, -0.41), self.increase_witness)

        stage_names = [
            ("gcd", "GCD"),
            ("order", "Order"),
            ("measure", "Measure"),
            ("recover", "Recover"),
            ("factor", "Factor"),
        ]
        start_x = -0.20
        for offset, (stage_key, title) in enumerate(stage_names):
            x = start_x + offset * 0.18
            card = Entity(
                parent=self,
                model="quad",
                position=(x, -0.31, 0.02),
                scale=(0.14, 0.05, 1),
                color=color.rgb(39, 50, 74),
            )
            Text(
                parent=self,
                text=title,
                position=(x, -0.316),
                origin=(0, 0),
                scale=0.44,
                color=color.white,
            )
            self.stage_cards[stage_key] = card

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
        return self.chart_x - 0.38 + 0.76 * fraction

    def reset_algorithm(self):
        self.running = False
        self.auto_timer = 0.0
        self.stage = "gcd"
        self.scan_index = 0
        self.measurement = None
        self.recovered_order = None
        self.result_factors = None
        self.phase_fraction = 0.0
        self.register_size = 1 << (2 * self.number.bit_length())
        self.true_order = multiplicative_order(self.witness, self.number)
        self.sequence_values = [1]
        self._set_button_label(self.start_button, "Start")
        self.rebuild_bars()
        self.rebuild_fraction_markers()
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
                    parent=self,
                    text=str(index),
                    position=(x, -0.315),
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
            self.update_visuals(animated=True)
            self.update_ui(f"Measured c = {self.measurement}, so c / Q = {self.phase_fraction:.3f}.")
            return

        if self.stage == "recover":
            self.recovered_order = recover_period_from_measurement(
                self.measurement,
                self.register_size,
                self.witness,
                self.number,
            )
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
        self.phase_text.text = (
            f"Stage: {self.stage.upper()}\n"
            f"Period r = {order_text}   Speed {self.auto_interval:.1f}s"
        )
        self.status_text.text = status

        if self.result_factors is None:
            measurement_text = "Measurement pending" if self.measurement is None else f"c = {self.measurement}"
            recovered_text = "Recovered r pending" if self.recovered_order is None else f"Recovered r = {self.recovered_order}"
            self.result_text.text = f"{measurement_text}\n{recovered_text}"
        else:
            left, right = self.result_factors
            self.result_text.text = f"Factors: {left} x {right}\nCheck: {left * right} = {self.number}"

    def update_hover_text(self):
        hovered = mouse.hovered_entity
        if hovered is not None and hasattr(hovered, "step_index") and hovered in self.bars:
            index = hovered.step_index
            if index < len(self.sequence_values):
                value = self.sequence_values[index]
                marker = "  [active]" if index == self.scan_index and self.stage == "order" else ""
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
