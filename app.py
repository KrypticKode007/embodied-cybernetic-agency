import random
from collections import deque
from dataclasses import dataclass
from typing import Optional


# ---------- Core models ----------


class WorldModel:
    def __init__(self):
        self.belief = 0.0

    def predict_observation(self):
        return self.belief

    def update_belief(self, observation, learning_rate=0.30):
        self.belief += learning_rate * (observation - self.belief)

    def prediction_error(self, observation):
        return abs(observation - self.belief)


class TelemetryModel:
    def __init__(self):
        self.battery = 1.0
        self.temperature = 0.0

    def apply_load(self, effort):
        self.battery = max(0.0, self.battery - 0.05 * effort)
        self.temperature = min(1.0, self.temperature + 0.03 * effort)

    def recover(self, battery_charge=0.02, cooling=0.08):
        self.battery = min(1.0, self.battery + battery_charge)
        self.temperature = max(0.0, self.temperature - cooling)

    def resource_integrity(self):
        return 0.5 * self.battery + 0.5 * (1.0 - self.temperature)


class SelfModel:
    def __init__(self):
        self.consistency = 1.0
        self.reliability_estimate = 1.0

    def update(self, prediction_error, resource_integrity, uncertainty):
        error_term = min(1.0, prediction_error)
        uncertainty_term = min(1.0, uncertainty)
        resource_term = 1.0 - resource_integrity

        penalty = (
            0.40 * error_term
            + 0.20 * uncertainty_term
            + 0.40 * resource_term
        )

        self.consistency = max(0.0, min(1.0, 1.0 - penalty))
        self.reliability_estimate = self.consistency


class UncertaintyEstimator:
    """Estimates uncertainty from recent prediction errors.

    The agent does not read Environment.noise_level directly. Instead, it uses
    recent error magnitude and volatility as a practical observable proxy.
    """

    def __init__(self, window_size=5):
        self.errors = deque(maxlen=window_size)

    def update(self, prediction_error):
        self.errors.append(prediction_error)

    def estimate(self):
        if len(self.errors) < 2:
            return min(1.0, self.errors[0] if self.errors else 0.0)

        mean_error = sum(self.errors) / len(self.errors)
        variance = sum((error - mean_error) ** 2 for error in self.errors) / len(self.errors)
        volatility = variance ** 0.5

        return min(1.0, 0.65 * mean_error + 0.35 * volatility)


class Regulator:
    def __init__(self):
        self.mode = "normal"

    def choose_mode(self, smoothed_risk, resource_integrity, consistency):
        if resource_integrity < 0.12:
            self.mode = "shutdown"
            return self.mode

        if smoothed_risk < 0.20:
            self.mode = "normal"
        elif smoothed_risk < 0.45:
            self.mode = "cautious"
        elif smoothed_risk < 0.70:
            self.mode = "safe"
        elif smoothed_risk < 0.85 and consistency >= 0.20:
            self.mode = "recovery"
        else:
            self.mode = "shutdown"

        return self.mode


# ---------- Disturbances ----------


@dataclass
class Disturbance:
    kind: str
    magnitude: float = 0.0

    def __repr__(self):
        return f"Disturbance(kind={self.kind}, magnitude={self.magnitude:.2f})"


# ---------- Environment ----------


class Environment:
    def __init__(self):
        self.true_state = 0.0
        self.noise_level = 0.0
        self.blackout_active = False

    def apply_disturbance(self, disturbance):
        if disturbance.kind == "none":
            self.noise_level = 0.0
            self.blackout_active = False
        elif disturbance.kind == "sensor_noise":
            self.noise_level = max(0.0, disturbance.magnitude)
            self.blackout_active = False
        elif disturbance.kind == "world_shift":
            self.true_state += disturbance.magnitude
        elif disturbance.kind == "sensor_blackout":
            self.blackout_active = True
        else:
            raise ValueError(f"Unknown disturbance kind: {disturbance.kind}")

    def observe(self):
        if self.blackout_active:
            return None

        noise = random.uniform(-self.noise_level, self.noise_level)
        return self.true_state + noise

    def apply_action(self, effort):
        """Higher effort moves the true state closer to the target state of 0."""
        control_gain = 0.22
        self.true_state -= control_gain * effort * self.true_state


# ---------- Logging ----------


@dataclass
class LogEntry:
    t: int
    disturbance: Disturbance
    observation: Optional[float]
    prediction: float
    error: float
    uncertainty: float
    raw_risk: float
    smoothed_risk: float
    mode: str
    reason: str
    effort: float
    battery: float
    temperature: float
    resource_before: float
    resource_after: float
    consistency: float
    true_state_after: float


# ---------- Agent ----------


class Agent:
    def __init__(self, name):
        self.name = name
        self.world = WorldModel()
        self.telemetry = TelemetryModel()
        self.self_model = SelfModel()
        self.uncertainty_estimator = UncertaintyEstimator(window_size=5)
        self.regulator = Regulator()

        self.w_e = 0.35
        self.w_u = 0.25
        self.w_r = 0.20
        self.w_m = 0.20

        self.smoothed_risk = 0.0
        self.risk_smoothing = 0.45

    def compute_risk(self, error, uncertainty, resource_integrity):
        normalized_error = min(1.0, error)
        normalized_uncertainty = min(1.0, uncertainty)
        inconsistency = 1.0 - self.self_model.consistency
        resource_degradation = 1.0 - resource_integrity

        return min(
            1.0,
            self.w_e * normalized_error
            + self.w_u * normalized_uncertainty
            + self.w_r * resource_degradation
            + self.w_m * inconsistency,
        )

    def smooth_risk(self, raw_risk):
        alpha = self.risk_smoothing
        self.smoothed_risk = alpha * raw_risk + (1.0 - alpha) * self.smoothed_risk
        return self.smoothed_risk

    def act(self, mode):
        effort_by_mode = {
            "normal": 1.00,
            "cautious": 0.60,
            "safe": 0.30,
            "recovery": 0.00,
            "shutdown": 0.00,
        }

        effort = effort_by_mode[mode]

        if mode in {"recovery", "shutdown"}:
            charging = 0.04 if mode == "recovery" else 0.06
            cooling = 0.10 if mode == "recovery" else 0.14
            self.telemetry.recover(battery_charge=charging, cooling=cooling)
        else:
            self.telemetry.apply_load(effort)

        return effort

    def explain_decision(self, error, uncertainty, resource_integrity, raw_risk, smoothed_risk, mode):
        if resource_integrity < 0.12:
            return "Critical resource integrity: forced shutdown."
        if mode == "shutdown":
            return "Sustained high risk or severe self-model inconsistency: shutdown."
        if mode == "recovery":
            return "Elevated risk: pausing action to cool and recharge."
        if uncertainty >= 0.65:
            return "High uncertainty from unstable recent observations."
        if error >= 0.65:
            return "Large prediction error: world model does not match observations."
        if resource_integrity <= 0.55:
            return "Reduced resource integrity: conserving energy and limiting heat."
        if smoothed_risk >= 0.20:
            return "Moderate accumulated risk: acting cautiously."
        return "Low prediction error, stable observations, and healthy resources."


# ---------- Simulation ----------


def run_simulation(steps=30, seed=42):
    random.seed(seed)

    env = Environment()
    agent = Agent(name="cybernetic_agent")

    disturbances = [
        Disturbance("none", 0.0),
        Disturbance("sensor_noise", 0.20),
        Disturbance("sensor_noise", 0.50),
        Disturbance("world_shift", 1.00),
        Disturbance("sensor_blackout", 0.0),
        Disturbance("sensor_noise", 0.10),
        Disturbance("none", 0.0),
    ]

    logs = []

    for t in range(steps):
        disturbance = disturbances[t % len(disturbances)]
        env.apply_disturbance(disturbance)

        prediction = agent.world.predict_observation()
        observation = env.observe()
        resource_before = agent.telemetry.resource_integrity()

        if observation is None:
            error = 1.0
            uncertainty = 1.0
        else:
            error = agent.world.prediction_error(observation)
            agent.world.update_belief(observation)
            agent.uncertainty_estimator.update(error)
            uncertainty = agent.uncertainty_estimator.estimate()

        agent.self_model.update(
            prediction_error=error,
            resource_integrity=resource_before,
            uncertainty=uncertainty,
        )

        raw_risk = agent.compute_risk(
            error=error,
            uncertainty=uncertainty,
            resource_integrity=resource_before,
        )
        smoothed_risk = agent.smooth_risk(raw_risk)

        mode = agent.regulator.choose_mode(
            smoothed_risk=smoothed_risk,
            resource_integrity=resource_before,
            consistency=agent.self_model.consistency,
        )

        reason = agent.explain_decision(
            error=error,
            uncertainty=uncertainty,
            resource_integrity=resource_before,
            raw_risk=raw_risk,
            smoothed_risk=smoothed_risk,
            mode=mode,
        )

        effort = agent.act(mode)
        env.apply_action(effort)
        resource_after = agent.telemetry.resource_integrity()

        logs.append(
            LogEntry(
                t=t,
                disturbance=disturbance,
                observation=observation,
                prediction=prediction,
                error=error,
                uncertainty=uncertainty,
                raw_risk=raw_risk,
                smoothed_risk=smoothed_risk,
                mode=mode,
                reason=reason,
                effort=effort,
                battery=agent.telemetry.battery,
                temperature=agent.telemetry.temperature,
                resource_before=resource_before,
                resource_after=resource_after,
                consistency=agent.self_model.consistency,
                true_state_after=env.true_state,
            )
        )

    print_results(logs)
    return logs


def print_results(logs):
    print(
        f"{'t':>2} | {'disturbance':>25} | {'obs':>7} | {'pred':>7} | "
        f"{'err':>5} | {'unc':>5} | {'raw':>5} | {'risk':>5} | "
        f"{'mode':>8} | {'eff':>4} | {'bat':>5} | {'tmp':>5} | {'con':>5}"
    )
    print("-" * 145)

    for entry in logs:
        observation = "BLACKOUT" if entry.observation is None else f"{entry.observation:7.2f}"

        print(
            f"{entry.t:2d} | "
            f"{str(entry.disturbance):>25} | "
            f"{observation:>7} | "
            f"{entry.prediction:7.2f} | "
            f"{entry.error:5.2f} | "
            f"{entry.uncertainty:5.2f} | "
            f"{entry.raw_risk:5.2f} | "
            f"{entry.smoothed_risk:5.2f} | "
            f"{entry.mode:>8} | "
            f"{entry.effort:4.1f} | "
            f"{entry.battery:5.2f} | "
            f"{entry.temperature:5.2f} | "
            f"{entry.consistency:5.2f}"
        )

    print("\nDecision explanations:")
    for entry in logs:
        print(f"t={entry.t:02d} | {entry.mode:>8} | {entry.reason}")


if __name__ == "__main__":
    run_simulation(steps=30, seed=42)