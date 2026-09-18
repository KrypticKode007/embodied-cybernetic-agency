# src/agent.py

import math
import random


class WorldModel:
    """Predicts external state and updates beliefs."""

    def __init__(self):
        self.belief = 0.0

    def predict_observation(self):
        return self.belief

    def update_belief(self, observation, learning_rate=0.3):
        self.belief += learning_rate * (observation - self.belief)

    def prediction_error(self, observation):
        return abs(observation - self.belief)


class TelemetryModel:
    """Tracks material and computational condition (very simplified)."""

    def __init__(self):
        self.battery = 1.0
        self.temperature = 0.0

    def apply_load(self, effort):
        self.battery = max(0.0, self.battery - 0.05 * effort)
        self.temperature = min(1.0, self.temperature + 0.03 * effort)

    def resource_integrity(self):
        # 1.0 = perfect, 0.0 = fully degraded
        return 0.5 * self.battery + 0.5 * (1.0 - self.temperature)


class SelfModel:
    """Estimates reliability and consistency."""

    def __init__(self):
        self.consistency = 1.0
        self.reliability_estimate = 1.0

    def update(self, prediction_error, resource_integrity):
        error_term = min(1.0, prediction_error)
        resource_term = 1.0 - resource_integrity
        penalty = 0.4 * error_term + 0.6 * resource_term
        self.consistency = max(0.0, 1.0 - penalty)
        self.reliability_estimate = self.consistency


class Regulator:
    """Changes mode under elevated risk."""

    def __init__(self, mode_policy="risk_sensitive"):
        self.mode_policy = mode_policy
        self.mode = "normal"

    def choose_mode(self, risk, resource_integrity=None, error=None):
        if self.mode_policy == "risk_agnostic":
            self.mode = "normal"
        elif self.mode_policy == "risk_light":
            # react only to error component (proxy: risk)
            if risk < 0.3:
                self.mode = "normal"
            elif risk < 0.6:
                self.mode = "cautious"
            else:
                self.mode = "safe"
        elif self.mode_policy == "resource_aware":
            if resource_integrity is not None and resource_integrity < 0.3:
                self.mode = "safe"
            else:
                self.mode = "normal"
        else:  # "risk_sensitive"
            if risk < 0.2:
                self.mode = "normal"
            elif risk < 0.5:
                self.mode = "cautious"
            elif risk < 0.8:
                self.mode = "safe"
            else:
                self.mode = "shutdown"
        return self.mode


class Agent:
    """Embodied cybernetic agent with optional components, driven by condition config."""

    def __init__(self, condition_cfg):
        self.condition_cfg = condition_cfg
        self.name = f"agent_{condition_cfg['id']}"

        # Components may be disabled depending on condition
        self.world = WorldModel() if condition_cfg["world_model_enabled"] else None
        self.telemetry = TelemetryModel() if condition_cfg["telemetry_enabled"] else None
        self.self_model = SelfModel() if condition_cfg["self_model_enabled"] else None
        self.regulator = Regulator(mode_policy=condition_cfg["regulation_mode"])

        # Risk weights (can later be moved to config)
        self.w_e = 0.4  # prediction error
        self.w_u = 0.2  # uncertainty
        self.w_r = 0.2  # resource degradation
        self.w_m = 0.2  # self-model inconsistency

    def predict_observation(self):
        if self.world is None:
            return 0.0
        return self.world.predict_observation()

    def update_world_model(self, observation):
        if self.world is not None:
            self.world.update_belief(observation)

    def compute_error(self, observation):
        if self.world is None:
            return 0.0
        return self.world.prediction_error(observation)

    def update_self_model(self, prediction_error, resource_integrity):
        if self.self_model is not None:
            self.self_model.update(prediction_error, resource_integrity)

    def compute_risk(self, error, uncertainty, resource_integrity):
        r_t = resource_integrity if resource_integrity is not None else 1.0
        m_t = self.self_model.consistency if self.self_model is not None else 1.0

        R_t = (
            self.w_e * error +
            self.w_u * uncertainty +
            self.w_r * (1.0 - r_t) +
            self.w_m * (1.0 - m_t)
        )
        return R_t

    def act(self, mode):
        # Map mode to effort; “shutdown” = zero effort.
        if self.telemetry is None:
            return 0.0

        if mode == "normal":
            effort = 1.0
        elif mode == "cautious":
            effort = 0.6
        elif mode == "safe":
            effort = 0.3
        else:
            effort = 0.0

        self.telemetry.apply_load(effort)
        return effort

    def resource_integrity(self):
        if self.telemetry is None:
            return 1.0
        return self.telemetry.resource_integrity()