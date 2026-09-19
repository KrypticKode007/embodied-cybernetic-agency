"""
main.py -- Embodied Cybernetic Agency prototype

Kivy app scaffold implementing the structural risk index (R_t):

    R_t = w_e * e_t + w_u * u_t + w_r * (1 - r_t) + w_m * (1 - m_t)

where:
    e_t = prediction error
    u_t = uncertainty
    r_t = resource integrity (1 = full resources)
    m_t = self-model consistency (1 = fully consistent)
    w_* = task-specific weights

Wire your own engine logic into compute_structural_risk() and
on_compute() below as the project grows.
"""

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button


def compute_structural_risk(e_t, u_t, r_t, m_t, w_e=0.25, w_u=0.25, w_r=0.25, w_m=0.25):
    """
    Compute the structural risk index R_t from the four state
    variables and their weights. Weights default to an even split;
    override them once you've tuned them for your task.
    """
    return w_e * e_t + w_u * u_t + w_r * (1 - r_t) + w_m * (1 - m_t)


def risk_state(risk_value):
    """Map a numeric risk score to a human-readable state."""
    if risk_value < 0.3:
        return "Stable"
    elif risk_value < 0.6:
        return "Caution"
    else:
        return "Critical -- recovery/escalation recommended"


class ECSApp(App):
    """Root Kivy application for the Embodied Cybernetic Agency prototype."""

    def build(self):
        root = BoxLayout(orientation="vertical", padding=20, spacing=10)

        root.add_widget(Label(
            text="Structural Risk Index (R_t)",
            font_size=22,
            size_hint=(1, 0.1),
        ))

        grid = GridLayout(cols=2, spacing=10, size_hint=(1, 0.5))

        self.e_input = TextInput(text="0.0", multiline=False)
        self.u_input = TextInput(text="0.0", multiline=False)
        self.r_input = TextInput(text="1.0", multiline=False)
        self.m_input = TextInput(text="1.0", multiline=False)

        grid.add_widget(Label(text="Prediction error (e_t)"))
        grid.add_widget(self.e_input)
        grid.add_widget(Label(text="Uncertainty (u_t)"))
        grid.add_widget(self.u_input)
        grid.add_widget(Label(text="Resource integrity (r_t)"))
        grid.add_widget(self.r_input)
        grid.add_widget(Label(text="Self-model consistency (m_t)"))
        grid.add_widget(self.m_input)

        root.add_widget(grid)

        compute_btn = Button(text="Compute Risk", size_hint=(1, 0.15))
        compute_btn.bind(on_press=self.on_compute)
        root.add_widget(compute_btn)

        self.result_label = Label(
            text="Risk: --",
            font_size=20,
            size_hint=(1, 0.25),
        )
        root.add_widget(self.result_label)

        return root

    def on_compute(self, instance):
        """Read the input fields, compute R_t, and update the result label."""
        try:
            e_t = float(self.e_input.text)
            u_t = float(self.u_input.text)
            r_t = float(self.r_input.text)
            m_t = float(self.m_input.text)
        except ValueError:
            self.result_label.text = "Enter valid numbers in all fields."
            return

        risk = compute_structural_risk(e_t, u_t, r_t, m_t)
        state = risk_state(risk)
        self.result_label.text = f"R_t = {risk:.3f}  ({state})"


if __name__ == "__main__":
    ECSApp().run()
