"""
Safety Layer — Doly barlag testi.
TorqueRateLimiter, DriverOverrideMonitor, EPSFaultMonitor, CommandWatchdog, SafetyManager
"""
import sys
import os
import time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ======================================================================
# 1. TorqueRateLimiter Test
# ======================================================================
print("=== 1. TORQUE RATE LIMITER TEST ===")
from safety_layer import TorqueRateLimiter

rl = TorqueRateLimiter(rate_limit=15)

# Request 1500 instantly — should ramp gradually
torques = []
for i in range(120):
    t = rl.apply(1500)
    torques.append(t)

# After 100 frames at +15/frame -> should reach 1500
assert torques[0] == 15, f"First frame should be 15, got {torques[0]}"
assert torques[99] == 1500, f"100th frame should be 1500, got {torques[99]}"
# Verify no jump > 15 between consecutive frames
for i in range(1, len(torques)):
    delta = abs(torques[i] - torques[i-1])
    assert delta <= 15, f"Jump at frame {i}: {delta}"
print(f"  1500 reached in {torques.index(1500)+1} frames")
print("  [OK] No jumps > 15 Nm/frame")

# Ramp down to 0
for i in range(120):
    t = rl.apply(0)
assert t == 0, f"Should ramp to 0, got {t}"
print("  [OK] Ramps back to 0")

# Negative direction
rl.reset()
t = rl.apply(-500)
assert t == -15, f"First negative frame should be -15, got {t}"
print("  [OK] Negative direction works")

# ======================================================================
# 2. DriverOverrideMonitor Test
# ======================================================================
print("\n=== 2. DRIVER OVERRIDE TEST ===")
from safety_layer import DriverOverrideMonitor

dom = DriverOverrideMonitor(threshold=100, cooldown_s=0.1)

# No override initially
assert not dom.is_overriding
print("  [OK] No override initially")

# STEER_OVERRIDE bit = True -> override
dom.update(steer_override=True, driver_torque=50)
assert dom.is_overriding, "Should be overriding when bit is set"
print("  [OK] STEER_OVERRIDE bit triggers override")

# Clear bit but within cooldown
dom.update(steer_override=False, driver_torque=0)
assert dom.is_overriding, "Should still be overriding during cooldown"
print("  [OK] Cooldown active")

# Wait past cooldown
time.sleep(0.15)
dom.update(steer_override=False, driver_torque=0)
assert not dom.is_overriding, "Override should clear after cooldown"
print("  [OK] Cooldown expired, override cleared")

# High torque -> override
dom.update(steer_override=False, driver_torque=150)
assert dom.is_overriding, "High driver torque should trigger override"
print("  [OK] High driver torque triggers override")

# ======================================================================
# 3. EPSFaultMonitor Test
# ======================================================================
print("\n=== 3. EPS FAULT MONITOR TEST ===")
from safety_layer import EPSFaultMonitor

eps = EPSFaultMonitor()

# Normal state
eps.update(lka_state=1)
assert not eps.has_fault
assert eps.state_name == 'standby'
print("  [OK] LKA_STATE=1 -> standby, no fault")

eps.update(lka_state=5)
assert not eps.has_fault
assert eps.state_name == 'aktiv'
print("  [OK] LKA_STATE=5 -> active, no fault")

# Fault state
eps.update(lka_state=9)
assert eps.has_fault
assert eps.state_name == 'fault'
print("  [OK] LKA_STATE=9 -> fault detected")

eps.reset()
eps.update(lka_state=25)
assert eps.has_fault
assert eps.state_name == 'fault2'
print("  [OK] LKA_STATE=25 -> fault2 detected")

# Timeout test
eps.reset()
eps._last_update = time.monotonic() - 2.0  # simulate 2s ago
assert eps.check_timeout(), "Should detect timeout"
assert eps.has_fault
print("  [OK] EPS message timeout detected as fault")

# ======================================================================
# 4. CommandWatchdog Test
# ======================================================================
print("\n=== 4. COMMAND WATCHDOG TEST ===")
from safety_layer import CommandWatchdog

wd = CommandWatchdog(timeout_ms=100)  # 100ms for fast testing

# Feed steer command
wd.feed_steer()
result = wd.check()
assert not result['steer_timeout'], "Should not timeout immediately"
print("  [OK] No timeout immediately after command")

# Wait past timeout
time.sleep(0.15)
result = wd.check()
assert result['steer_timeout'], "Should timeout after 150ms"
print("  [OK] Steer watchdog timeout detected after 150ms")

# Feed accel
wd.feed_accel()
result = wd.check()
assert not result['accel_timeout']
time.sleep(0.15)
result = wd.check()
assert result['accel_timeout']
print("  [OK] Accel watchdog timeout detected")

# ======================================================================
# 5. SafetyManager Integration Test
# ======================================================================
print("\n=== 5. SAFETY MANAGER TEST ===")
from safety_layer import SafetyManager

sm = SafetyManager()

# Normal operation with rate limiting
sm.notify_steer_cmd()
torque, req = sm.apply_steer(1500, True)
assert torque == 15, f"First frame should be rate-limited to 15, got {torque}"
assert req is True
print(f"  [OK] Rate limited: 1500 -> {torque}")

# Several frames
for i in range(99):
    sm.notify_steer_cmd()
    torque, req = sm.apply_steer(1500, True)
assert torque == 1500
print(f"  [OK] Reached 1500 after 100 frames")

# Status check
status = sm.get_status()
assert status['engaged'] is True
assert status['rate_limited_torque'] == 1500
print(f"  [OK] Status: engaged={status['engaged']}, torque={status['rate_limited_torque']}")

# Driver override -> disengage
disengage_reasons = []
sm.on_disengage = lambda r: disengage_reasons.append(r)

import can
override_msg = can.Message(
    arbitration_id=0x260,
    data=bytes([0x01, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]),
    is_extended_id=False
)
sm.feed_can_msg(override_msg)

sm.notify_steer_cmd()
torque, req = sm.apply_steer(1500, True)
# Should be ramping to 0 (not instantly 0 — rate limiter still applies)
assert torque < 1500, f"Should disengage, got torque={torque}"
assert req is False
print(f"  [OK] Driver override -> disengage, torque ramping to 0: {torque}")

assert len(disengage_reasons) > 0
assert "OVERRIDE" in disengage_reasons[0]
print(f"  [OK] Disengage callback: '{disengage_reasons[0]}'")

# ======================================================================
# 6. Commander with Safety Layer Test
# ======================================================================
print("\n=== 6. COMMANDER + SAFETY TEST ===")

import config
config.DEMO_MODE = True
from can_interface import CANInterface
from toyota_commands import ToyotaCommander

ci = CANInterface()
ci.connect()

cmdr = ToyotaCommander(ci)
cmdr.start()
cmdr.set_steer(1500)
time.sleep(0.15)  # ~15 frames

# Check safety status
status = cmdr.get_safety_status()
actual_torque = status['rate_limited_torque']
print(f"  After 150ms: rate-limited torque = {actual_torque}")
# Should not be 1500 yet — rate limiter should have ramped ~15*15=225
assert actual_torque < 1500, f"Should be rate-limited, got {actual_torque}"
assert actual_torque > 0, f"Should be positive, got {actual_torque}"
print(f"  [OK] Torque properly rate-limited: {actual_torque}")

cmdr.stop()
ci.disconnect()
print("  [OK] Commander with safety layer works")

# ======================================================================
# 7. Accel Safety Test
# ======================================================================
print("\n=== 7. ACCEL SAFETY TEST ===")

sm2 = SafetyManager()
sm2.notify_accel_cmd()
accel, permit, cancel = sm2.apply_accel(2.0, True)
assert abs(accel - 2.0) < 0.01
assert permit is True
assert cancel is False
print(f"  [OK] Normal accel: {accel} m/s2, permit={permit}")

# Disengage -> cancel
override_msg2 = can.Message(
    arbitration_id=0x260,
    data=bytes([0x01, 0x00, 0xC8, 0x00, 0x00, 0x00, 0x00, 0x00]),
    is_extended_id=False
)
sm2.feed_can_msg(override_msg2)
sm2.notify_accel_cmd()
accel, permit, cancel = sm2.apply_accel(2.0, True)
assert accel == 0.0
assert cancel is True
print(f"  [OK] Override -> accel=0, cancel=True")


print("\n============================")
print("ALL 7 SAFETY TESTS PASSED!")
print("============================")
