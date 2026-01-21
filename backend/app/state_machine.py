"""
LOCKED Adaptive Quality State Machine
DO NOT MODIFY without approval - production specification

NOALBS-Inspired Enhancement:
- Retry logic wrapper (opt-in via FEATURE_RETRY_LOGIC)
- Instant recovery option (opt-in via INSTANT_RECOVERY_ENABLED)
- Core state machine logic unchanged
"""

import time
import logging
from typing import Optional, Tuple, Dict
from dataclasses import dataclass
from .models import QualityState, QualityPreset, QUALITY_PRESETS
from .config import settings

logger = logging.getLogger(__name__)


class StateMachineTimers:
    """Timer constants - LOCKED"""
    DOWNGRADE_OBSERVATION_WINDOW = 5
    UPGRADE_OBSERVATION_WINDOW = 60
    RECOVERY_DWELL_TIME = 60
    MIN_STATE_DWELL_TIME = 45
    EVALUATION_INTERVAL = 1
    POST_RESTART_GRACE_PERIOD = 4
    ERROR_STATE_COOLDOWN = 10


@dataclass
class StateContext:
    """Current state machine context"""
    current_state: QualityState
    previous_state: Optional[QualityState]
    entered_at: float
    condition_name: Optional[str] = None
    condition_met_at: Optional[float] = None
    
    def time_in_state(self) -> float:
        return time.time() - self.entered_at
    
    def condition_duration(self) -> float:
        if self.condition_met_at is None:
            return 0.0
        return time.time() - self.condition_met_at
    
    def set_condition(self, name: str):
        if self.condition_name != name:
            self.condition_met_at = time.time()
            self.condition_name = name
    
    def clear_condition(self):
        self.condition_met_at = None
        self.condition_name = None
    
    def transition_to(self, new_state: QualityState):
        if new_state == QualityState.RECOVERY:
            self.previous_state = self.current_state
        elif self.current_state == QualityState.RECOVERY:
            self.previous_state = None
        
        self.current_state = new_state
        self.entered_at = time.time()
        self.clear_condition()


class AdaptiveStateMachine:
    """LOCKED state machine - quality control"""
    
    def __init__(self, initial_state: QualityState = QualityState.MEDIUM):
        self.context = StateContext(
            current_state=initial_state,
            previous_state=None,
            entered_at=time.time()
        )
        logger.info(f"State machine initialized: {initial_state.value}")
    
    def get_current_state(self) -> QualityState:
        return self.context.current_state
    
    def get_current_preset(self) -> QualityPreset:
        return QUALITY_PRESETS[self.context.current_state]
    
    def evaluate_downgrade(
        self,
        total_bandwidth_bps: float,
        packet_loss_percent: float,
        max_rtt_ms: float,
        active_subflows: int
    ) -> Optional[Tuple[QualityState, str]]:
        """Evaluate downgrade conditions - LOCKED logic"""
        
        if self.context.time_in_state() < StateMachineTimers.MIN_STATE_DWELL_TIME:
            return None
        
        current = self.context.current_state
        
        # ERROR conditions
        if active_subflows == 0:
            return (QualityState.ERROR, "Both uplinks failed")
        
        # HIGH downgrade
        if current == QualityState.HIGH:
            if packet_loss_percent > 2.0:
                if self.context.condition_duration() >= 5:
                    return (QualityState.MEDIUM, f"Packet loss {packet_loss_percent:.1f}% >2% for 5s")
                self.context.set_condition("high_packet_loss")
            elif total_bandwidth_bps < 5_000_000:
                if self.context.condition_duration() >= 10:
                    return (QualityState.MEDIUM, f"Bandwidth {total_bandwidth_bps/1e6:.2f} Mbps <5 Mbps for 10s")
                self.context.set_condition("high_low_bandwidth")
            else:
                self.context.clear_condition()
        
        # MEDIUM downgrade
        elif current == QualityState.MEDIUM:
            if packet_loss_percent > 3.0:
                if self.context.condition_duration() >= 5:
                    return (QualityState.LOW, f"Packet loss {packet_loss_percent:.1f}% >3% for 5s")
                self.context.set_condition("medium_packet_loss")
            elif total_bandwidth_bps < 3_000_000:
                if self.context.condition_duration() >= 10:
                    return (QualityState.LOW, f"Bandwidth {total_bandwidth_bps/1e6:.2f} Mbps <3 Mbps for 10s")
                self.context.set_condition("medium_low_bandwidth")
            else:
                self.context.clear_condition()
        
        # LOW downgrade
        elif current == QualityState.LOW:
            if packet_loss_percent > 5.0:
                if self.context.condition_duration() >= 5:
                    return (QualityState.VERY_LOW, f"Packet loss {packet_loss_percent:.1f}% >5% for 5s")
                self.context.set_condition("low_packet_loss")
            elif total_bandwidth_bps < 1_500_000:
                if self.context.condition_duration() >= 10:
                    return (QualityState.VERY_LOW, f"Bandwidth {total_bandwidth_bps/1e6:.2f} Mbps <1.5 Mbps for 10s")
                self.context.set_condition("low_low_bandwidth")
            else:
                self.context.clear_condition()
        
        # VERY_LOW downgrade
        elif current == QualityState.VERY_LOW:
            if total_bandwidth_bps < 500_000:
                if self.context.condition_duration() >= 20:
                    return (QualityState.ERROR, f"Bandwidth {total_bandwidth_bps/1e6:.2f} Mbps <0.5 Mbps for 20s")
                self.context.set_condition("very_low_critical")
            else:
                self.context.clear_condition()
        
        return None
    
    def evaluate_upgrade(
        self,
        total_bandwidth_bps: float,
        packet_loss_percent: float,
        min_rtt_ms: float,
        active_subflows: int
    ) -> Optional[Tuple[QualityState, str]]:
        """Evaluate upgrade conditions - LOCKED logic"""
        
        current = self.context.current_state
        
        if current == QualityState.ERROR:
            return None
        
        if self.context.time_in_state() < StateMachineTimers.MIN_STATE_DWELL_TIME:
            return None
        
        # RECOVERY state upgrade
        if current == QualityState.RECOVERY:
            if self.context.time_in_state() >= StateMachineTimers.RECOVERY_DWELL_TIME:
                prev = self.context.previous_state
                if prev == QualityState.VERY_LOW:
                    target = QualityState.LOW
                elif prev == QualityState.LOW:
                    target = QualityState.MEDIUM
                elif prev == QualityState.MEDIUM:
                    target = QualityState.HIGH
                else:
                    return None
                
                return (target, f"Recovery complete, upgrading from {prev.value}")
            return None
        
        # VERY_LOW upgrade
        if current == QualityState.VERY_LOW:
            if (total_bandwidth_bps > 2_500_000 and
                packet_loss_percent < 1.0 and
                min_rtt_ms < 100):
                
                if self.context.condition_duration() >= 60:
                    return (QualityState.RECOVERY, "Network stable for 60s")
                self.context.set_condition("very_low_upgrade")
            else:
                self.context.clear_condition()
        
        # LOW upgrade
        elif current == QualityState.LOW:
            if (total_bandwidth_bps > 4_500_000 and
                packet_loss_percent < 0.5 and
                min_rtt_ms < 80):
                
                if self.context.condition_duration() >= 60:
                    return (QualityState.RECOVERY, "Network stable for 60s")
                self.context.set_condition("low_upgrade")
            else:
                self.context.clear_condition()
        
        # MEDIUM upgrade
        elif current == QualityState.MEDIUM:
            if (total_bandwidth_bps > 7_000_000 and
                packet_loss_percent < 0.5 and
                min_rtt_ms < 100):
                
                if self.context.condition_duration() >= 60:
                    return (QualityState.RECOVERY, "Network stable for 60s")
                self.context.set_condition("medium_upgrade")
            else:
                self.context.clear_condition()
        
        return None
    
    def apply_transition(self, target_state: QualityState, reason: str):
        """Apply state transition"""
        old_state = self.context.current_state
        logger.info(f"TRANSITION: {old_state.value} → {target_state.value} | {reason}")
        self.context.transition_to(target_state)


class RetryLogicWrapper:
    """
    NOALBS-Inspired Retry Logic Wrapper (Opt-In)

    Wraps the core state machine to add retry counting before transitions.
    Only active when FEATURE_RETRY_LOGIC is enabled. When disabled, passes
    through directly to state machine without modification.

    This prevents quality flapping from momentary network spikes.
    """

    def __init__(self, state_machine: AdaptiveStateMachine):
        self.state_machine = state_machine
        self.enabled = settings.feature_retry_logic
        self.retry_attempts = settings.state_change_retry_attempts
        self.instant_recovery = settings.instant_recovery_enabled

        # Retry counters per potential transition
        self.downgrade_counters: Dict[QualityState, int] = {}
        self.upgrade_counters: Dict[QualityState, int] = {}
        self.last_recommendation: Optional[Tuple[QualityState, str]] = None

        logger.info(
            f"Retry Logic Wrapper initialized "
            f"(enabled={self.enabled}, attempts={self.retry_attempts}, "
            f"instant_recovery={self.instant_recovery})"
        )

    def evaluate_with_retry(
        self,
        total_bandwidth_bps: float,
        packet_loss_percent: float,
        min_rtt_ms: float,
        max_rtt_ms: float,
        active_subflows: int
    ) -> Optional[Tuple[QualityState, str]]:
        """
        Evaluate state transitions with retry logic

        If retry logic is disabled, passes through directly to state machine.
        If enabled, requires N consecutive recommendations before transitioning.
        """
        # Get recommendations from core state machine
        downgrade_recommendation = self.state_machine.evaluate_downgrade(
            total_bandwidth_bps, packet_loss_percent, max_rtt_ms, active_subflows
        )

        upgrade_recommendation = self.state_machine.evaluate_upgrade(
            total_bandwidth_bps, packet_loss_percent, min_rtt_ms, active_subflows
        )

        # If retry logic disabled, apply immediately (original behavior)
        if not self.enabled:
            if downgrade_recommendation:
                self.state_machine.apply_transition(*downgrade_recommendation)
                return downgrade_recommendation
            elif upgrade_recommendation:
                self.state_machine.apply_transition(*upgrade_recommendation)
                return upgrade_recommendation
            return None

        # Retry logic enabled - count recommendations
        current_state = self.state_machine.get_current_state()

        # Handle downgrade recommendations
        if downgrade_recommendation:
            target_state, reason = downgrade_recommendation

            # Increment counter
            if target_state not in self.downgrade_counters:
                self.downgrade_counters[target_state] = 0
            self.downgrade_counters[target_state] += 1

            # Reset upgrade counters (condition changed)
            self.upgrade_counters.clear()

            retry_count = self.downgrade_counters[target_state]
            logger.debug(
                f"Downgrade to {target_state.value} recommended "
                f"({retry_count}/{self.retry_attempts}): {reason}"
            )

            # Check if retry threshold met
            if retry_count >= self.retry_attempts:
                logger.info(
                    f"Downgrade retry threshold met ({retry_count}/{self.retry_attempts}), "
                    f"applying transition"
                )
                self.state_machine.apply_transition(target_state, reason)
                self.downgrade_counters.clear()
                return (target_state, reason)

            return None

        # Handle upgrade recommendations
        elif upgrade_recommendation:
            target_state, reason = upgrade_recommendation

            # Clear downgrade counters (conditions improved)
            self.downgrade_counters.clear()

            # Instant recovery bypass (NOALBS pattern)
            if self.instant_recovery:
                logger.info(
                    f"Instant recovery enabled, applying upgrade immediately: "
                    f"{current_state.value} → {target_state.value}"
                )
                self.state_machine.apply_transition(target_state, reason)
                self.upgrade_counters.clear()
                return (target_state, reason)

            # Normal upgrade with retry counting
            if target_state not in self.upgrade_counters:
                self.upgrade_counters[target_state] = 0
            self.upgrade_counters[target_state] += 1

            retry_count = self.upgrade_counters[target_state]
            logger.debug(
                f"Upgrade to {target_state.value} recommended "
                f"({retry_count}/{self.retry_attempts}): {reason}"
            )

            # Check if retry threshold met
            if retry_count >= self.retry_attempts:
                logger.info(
                    f"Upgrade retry threshold met ({retry_count}/{self.retry_attempts}), "
                    f"applying transition"
                )
                self.state_machine.apply_transition(target_state, reason)
                self.upgrade_counters.clear()
                return (target_state, reason)

            return None

        # No recommendations - reset counters
        else:
            if self.downgrade_counters or self.upgrade_counters:
                logger.debug("Conditions cleared, resetting retry counters")
            self.downgrade_counters.clear()
            self.upgrade_counters.clear()
            return None

    def get_retry_status(self) -> Dict[str, any]:
        """Get current retry counter status (for diagnostics)"""
        return {
            "enabled": self.enabled,
            "retry_attempts": self.retry_attempts,
            "instant_recovery": self.instant_recovery,
            "downgrade_counters": {
                state.value: count
                for state, count in self.downgrade_counters.items()
            },
            "upgrade_counters": {
                state.value: count
                for state, count in self.upgrade_counters.items()
            }
        }

    def reset_counters(self):
        """Reset all retry counters (for testing/manual override)"""
        self.downgrade_counters.clear()
        self.upgrade_counters.clear()
        logger.info("Retry counters reset")

    def get_current_state(self) -> QualityState:
        """Pass-through to state machine"""
        return self.state_machine.get_current_state()

    def get_current_preset(self) -> QualityPreset:
        """Pass-through to state machine"""
        return self.state_machine.get_current_preset()