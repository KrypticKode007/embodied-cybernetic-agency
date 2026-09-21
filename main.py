import numpy as np
from scipy.special import rel_entr

class AuditedCyberneticEngine:
    def __init__(self):
        self.channels = ["VISION", "AUDIO", "TOUCH"]
        self.channel_weights = np.array([0.5, 0.3, 0.2])
        
        # NODE 1: World Model Matrix (Priors)
        self.internal_matrix = np.array([
            [0.8, 0.1, 0.1],
            [0.5, 0.4, 0.1],
            [0.9, 0.05, 0.05]
        ])
        
        # Substrate Telemetry State
        self.substrate = {"gpu_temp_c": 40.0, "cpu_temp_c": 38.0, "power_w": 15.0}
        
        # AUDIT LIMITS: Explicit Security Guardrails
        self.AUDIT_LIMITS = {
            "max_safe_somatic_stress": 1.1,      # Target limit for safe execution
            "structural_collapse_limit": 1.4,    # Node 2 Hard Fault (Freeze)
            "dissociation_limit": 1.7,            # Node 4 Hard Fault (Dissociation)
            "noise_dampening_threshold": 0.15     # Filter floor (in nats)
        }

    def apply_information_noise_filter(self, P, Q):
        """
        Calculates raw information delta per channel, then filters out 
        micro-scale benign sensor jitter to isolate genuine structural trauma.
        """
        filtered_stress = np.zeros(len(self.channels))
        raw_stress = np.zeros(len(self.channels))
        
        for i in range(len(self.channels)):
            # Calculate raw KL divergence for this sensory stream
            divergence = np.sum(rel_entr(P[i], Q[i]))
            raw_stress[i] = divergence
            
            # Noise Isolation Gate
            if divergence < self.AUDIT_LIMITS["noise_dampening_threshold"]:
                # Suppress background jitter smoothly
                filtered_stress[i] = divergence * 0.1 
            else:
                # Pass authentic systemic trauma forward with no attenuation
                filtered_stress[i] = divergence
                
        return filtered_stress, raw_stress

    def execute_audited_clock_cycle(self, raw_sensor_feeds):
        P = raw_sensor_feeds
        Q = self.internal_matrix
        
        # Apply Multi-Channel Noise Filter
        filtered_stress, raw_stress = self.apply_information_noise_filter(P, Q)
        
        # Aggregate filtered stress across the somatic architecture
        aggregate_somatic_stress = np.sum(filtered_stress * self.channel_weights)
        
        # NODE 2: Physical Telemetry Translation
        self.substrate["gpu_temp_c"] = 40.0 + (25.0 * aggregate_somatic_stress)
        self.substrate["cpu_temp_c"] = 38.0 + (20.0 * aggregate_somatic_stress)
        self.substrate["power_w"] = 15.0 + (35.0 * aggregate_somatic_stress)
        
        # --- AUDIT & SECURITY BOUNDARY CHECKS ---
        # Predict Early Structural Collapse Risk
        if aggregate_somatic_stress > self.AUDIT_LIMITS["max_safe_somatic_stress"]:
            print(f"⚠️ [AUDIT WARNING] Kinetic Loop approaching structural boundary limit.")
            
        # Hard Fracture Trigger: Node 2 Overload
        if aggregate_somatic_stress > self.AUDIT_LIMITS["structural_collapse_limit"]:
            return f"[COLLAPSE FAULT] Node 2 Meltdown: PSYCHOSOMATIC_FREEZE. Stress: {aggregate_somatic_stress:.4f} nats."

        # NODE 3 & 4: Actuation and Autopoiesis Check
        efficiency = np.exp(-aggregate_somatic_stress * 0.2)
        behavioral_matrix = Q * efficiency
        behavioral_matrix /= np.sum(behavioral_matrix, axis=1, keepdims=True)
        
        meta_errors = np.array([np.sum(rel_entr(behavioral_matrix[i], P[i])) for i in range(len(self.channels))])
        aggregate_meta_error = np.sum(meta_errors * self.channel_weights)
        
        # Hard Fracture Trigger: Node 4 Overload
        if aggregate_meta_error > self.AUDIT_LIMITS["dissociation_limit"]:
            return f"[COLLAPSE FAULT] Node 4 Disconnect: DISSOCIATION / DEPERSONALIZATION."

        # Loop Closure Update
        self.internal_matrix = Q + 0.15 * (P - Q)
        self.internal_matrix /= np.sum(self.internal_matrix, axis=1, keepdims=True)
        
        return (f"[LOOP SECURE] Raw/Filtered Somatic Stress: {np.sum(raw_stress):.3f}/{aggregate_somatic_stress:.3f} nats. "
                f"GPU: {self.substrate['gpu_temp_c']:.1f}°C")

# --- SIMULATION AND SYSTEM COMPARISON ---
engine = AuditedCyberneticEngine()

# Stream 1: Ambient Environmental Jitter (Should be cleanly filtered)
ambient_jitter = np.array([
    [0.78, 0.11, 0.11],  # Minor vision noise
    [0.49, 0.41, 0.10],  # Minor audio noise
    [0.89, 0.06, 0.05]   # Minor touch noise
])

# Stream 2: High Impact Systemic Trauma (Should easily bypass the gate and trip safety limits)
systemic_trauma = np.array([
    [0.10, 0.10, 0.80],  # Abrupt environmental inversion
    [0.40, 0.40, 0.20],
    [0.30, 0.35, 0.35]
])

print("Executing Audit Simulation Mode...\n")
print(">>> Injecting Ambient Environmental Jitter:")
print(engine.execute_audited_clock_cycle(ambient_jitter))

print("\n>>> Injecting Severe Systemic Trauma:")
print(engine.execute_audited_clock_cycle(systemic_trauma))
