"""
Toyota CAN Safety Layer — OpenPilot-dan ylham alnan howpsuzlyk ulgamy.

5 komponent:
  1. TorqueRateLimiter  — Torque üýtgeşme tizligini çäklendirmek
  2. DriverOverrideMonitor — Sürüji override anyklamak
  3. EPSFaultMonitor    — EPS ýalňyşlyk anyklamak
  4. CommandWatchdog    — Buýruk timeout anyklamak
  5. SafetyManager      — Ähli komponentleri dolandyrmak
"""
import time
import threading
from config import (
    MAX_STEER_TORQUE, MIN_STEER_TORQUE,
    MAX_ACCEL_MPS2, MIN_ACCEL_MPS2,
    STEER_TORQUE_RATE_LIMIT, DRIVER_OVERRIDE_THRESHOLD,
    WATCHDOG_TIMEOUT_MS, OVERRIDE_COOLDOWN_S,
    ID_STEER_TORQ, ID_EPS_STATUS,
)


# ======================================================================
# 1. Torque Rate Limiter
# ======================================================================
class TorqueRateLimiter:
    """
    Torque-yň birden üýtgemeginiň öňüni alýar.
    Her 10ms frame-de maksimum RATE_LIMIT Nm üýtgäp bilýär.

    OpenPilot: toyota/safety_toyota.c → max_rate_up / max_rate_down
    """

    def __init__(self, rate_limit: int = 15):
        self._rate_limit = rate_limit   # Nm per frame (10ms)
        self._last_torque = 0           # Soňky iberilen torque

    def apply(self, desired_torque: int) -> int:
        """
        desired_torque → rate-limited torque.
        Birden 0-dan 1500-e gitmez, ýuwaş-ýuwaş artýar.
        """
        desired_torque = int(max(MIN_STEER_TORQUE, min(MAX_STEER_TORQUE, desired_torque)))

        delta = desired_torque - self._last_torque

        if delta > self._rate_limit:
            safe_torque = self._last_torque + self._rate_limit
        elif delta < -self._rate_limit:
            safe_torque = self._last_torque - self._rate_limit
        else:
            safe_torque = desired_torque

        # Çäklerden çykmasyn
        safe_torque = int(max(MIN_STEER_TORQUE, min(MAX_STEER_TORQUE, safe_torque)))
        self._last_torque = safe_torque
        return safe_torque

    def reset(self):
        """Hemme zady nol et (disengage bolanda)"""
        self._last_torque = 0

    @property
    def current_torque(self) -> int:
        return self._last_torque


# ======================================================================
# 2. Driver Override Monitor
# ======================================================================
class DriverOverrideMonitor:
    """
    Sürüjiniň ruly öwürýändigini anyklaýar.
    STEER_TORQUE_SENSOR (0x260):
      - STEER_OVERRIDE (bit 0)  → sürüji torque çäginden geçdi
      - STEER_TORQUE_DRIVER     → sürüji torque gymmaty

    Override anyklananda → disengage.
    Gaýtadan engage üçin cooldown garaşmaly.

    OpenPilot: controls/controlsd.py → driver_override check
    """

    def __init__(self, threshold: int = 100, cooldown_s: float = 0.5):
        self._threshold = threshold
        self._cooldown_s = cooldown_s
        self._override_active = False
        self._override_timestamp = 0.0
        self._driver_torque = 0
        self._steer_override_bit = False

    def update(self, steer_override: bool, driver_torque: int):
        """CAN habaryndan STEER_TORQUE_SENSOR maglumatlaryny täzele"""
        self._steer_override_bit = steer_override
        self._driver_torque = driver_torque

        if steer_override or abs(driver_torque) > self._threshold:
            self._override_active = True
            self._override_timestamp = time.monotonic()
        elif self._override_active:
            # Override aýryldy — cooldown garaş
            elapsed = time.monotonic() - self._override_timestamp
            if elapsed >= self._cooldown_s:
                self._override_active = False

    @property
    def is_overriding(self) -> bool:
        return self._override_active

    @property
    def driver_torque(self) -> int:
        return self._driver_torque

    def reset(self):
        self._override_active = False
        self._override_timestamp = 0.0


# ======================================================================
# 3. EPS Fault Monitor
# ======================================================================
class EPSFaultMonitor:
    """
    EPS_STATUS (0x262 = 610) habaryndan LKA_STATE-i okaýar.
    LKA_STATE gymmatlary:
      1 = standby (taýýar)
      5 = active  (işleýär)
      9 = temporary_fault
     25 = temporary_fault2

    Fault ýagdaýynda → disengage.

    OpenPilot: car/toyota/carstate.py → steer_fault check
    """
    FAULT_STATES = {9, 25}
    ACTIVE_STATES = {1, 5}

    def __init__(self):
        self._lka_state = 0
        self._ipas_state = 0
        self._has_fault = False
        self._last_update = 0.0
        self._msg_timeout = 1.0  # 1 sekuntdan köp habar gelmese fault

    def update(self, lka_state: int, ipas_state: int = 0):
        """EPS_STATUS habaryndan maglumatlary täzele"""
        self._lka_state = lka_state
        self._ipas_state = ipas_state
        self._last_update = time.monotonic()

        if lka_state in self.FAULT_STATES:
            self._has_fault = True
        elif lka_state in self.ACTIVE_STATES:
            self._has_fault = False

    def check_timeout(self) -> bool:
        """EPS habary gelmese — fault diý"""
        if self._last_update > 0:
            elapsed = time.monotonic() - self._last_update
            if elapsed > self._msg_timeout:
                self._has_fault = True
                return True
        return False

    @property
    def has_fault(self) -> bool:
        return self._has_fault

    @property
    def lka_state(self) -> int:
        return self._lka_state

    @property
    def state_name(self) -> str:
        names = {0: 'ýok', 1: 'standby', 5: 'aktiv', 9: 'fault', 25: 'fault2'}
        return names.get(self._lka_state, str(self._lka_state))

    def reset(self):
        self._has_fault = False
        self._last_update = 0.0


# ======================================================================
# 4. Command Watchdog
# ======================================================================
class CommandWatchdog:
    """
    Buýruk timeout sagatjygy.
    Eger set_steer() ýa-da set_accel() belli wagt içinde çagyrylmasa →
    awtomatik disengage.

    Bu GUI crash ýa-da doňma ýagdaýynda goraýar.

    OpenPilot: car/toyota/carcontroller.py → steer_step timeout
    """

    def __init__(self, timeout_ms: int = 200):
        self._timeout_s = timeout_ms / 1000.0
        self._last_steer_cmd = 0.0
        self._last_accel_cmd = 0.0
        self._steer_active = False
        self._accel_active = False

    def feed_steer(self):
        """Steer buýrugynyň gelendigini belle"""
        self._last_steer_cmd = time.monotonic()
        self._steer_active = True

    def feed_accel(self):
        """Accel buýrugynyň gelendigini belle"""
        self._last_accel_cmd = time.monotonic()
        self._accel_active = True

    def check(self) -> dict:
        """Timeout barla"""
        now = time.monotonic()
        result = {'steer_timeout': False, 'accel_timeout': False}

        if self._steer_active:
            if (now - self._last_steer_cmd) > self._timeout_s:
                result['steer_timeout'] = True
                self._steer_active = False

        if self._accel_active:
            if (now - self._last_accel_cmd) > self._timeout_s:
                result['accel_timeout'] = True
                self._accel_active = False

        return result

    def reset(self):
        self._steer_active = False
        self._accel_active = False
        self._last_steer_cmd = 0.0
        self._last_accel_cmd = 0.0


# ======================================================================
# 5. SafetyManager — Ähli komponentleri dolandyrmak
# ======================================================================
class SafetyManager:
    """
    Ähli safety komponentlerini birleşdirýär.

    Ulanyş:
        safety = SafetyManager()
        # Her CAN habary gelende:
        safety.feed_can_msg(msg)
        # Her control frame-de:
        safe_torque = safety.apply_steer(desired_torque, steer_active)
        safe_accel  = safety.apply_accel(desired_accel, accel_active)
    """

    def __init__(self):
        self._lock = threading.Lock()

        self.rate_limiter = TorqueRateLimiter(STEER_TORQUE_RATE_LIMIT)
        self.driver_override = DriverOverrideMonitor(
            DRIVER_OVERRIDE_THRESHOLD, OVERRIDE_COOLDOWN_S
        )
        self.eps_monitor = EPSFaultMonitor()
        self.watchdog = CommandWatchdog(WATCHDOG_TIMEOUT_MS)

        # Ýagdaý
        self._engaged = False
        self._disengage_reason = ""
        self._fault_count = 0

        # Callback: disengage bolanda çagyrylýar
        self.on_disengage = None   # callback(reason: str)

    # ------------------------------------------------------------------
    def feed_can_msg(self, msg):
        """
        Her gelen CAN habaryny safety ulgamyna iber.
        CAN thread-den çagyrylýar.
        """
        mid = msg.arbitration_id
        data = msg.data

        with self._lock:
            # STEER_TORQUE_SENSOR (0x260 = 608)
            if mid == ID_STEER_TORQ and len(data) >= 3:
                steer_override = bool(data[0] & 0x01)
                # STEER_TORQUE_DRIVER: 15|16@0- (signed, big-endian)
                dt_raw = (data[1] << 8) | data[2]
                if dt_raw > 32767:
                    dt_raw -= 65536
                self.driver_override.update(steer_override, dt_raw)

            # EPS_STATUS (0x262 = 610)
            elif mid == ID_EPS_STATUS and len(data) >= 5:
                # LKA_STATE: 31|7@0+ → byte3 bits 6-0
                lka_state = data[3] & 0x7F
                # IPAS_STATE: 3|4@0+ → byte0 bits 3-0
                ipas_state = data[0] & 0x0F
                self.eps_monitor.update(lka_state, ipas_state)

    # ------------------------------------------------------------------
    def apply_steer(self, desired_torque: int, steer_active: bool) -> tuple:
        """
        Desired torque → safe torque.
        Returns: (safe_torque: int, steer_request: bool)
        """
        with self._lock:
            # 1. Safety barlaglar
            disengage_reason = self._check_safety()
            if disengage_reason:
                self._do_disengage(disengage_reason)
                self.rate_limiter.apply(0)  # 0-a ramp et
                return (self.rate_limiter.current_torque, False)

            if not steer_active:
                safe_torque = self.rate_limiter.apply(0)
                return (safe_torque, abs(safe_torque) > 0)

            # 2. Rate limit ulan
            safe_torque = self.rate_limiter.apply(desired_torque)

            # 3. Engaged belle
            if abs(safe_torque) > 0:
                self._engaged = True

            return (safe_torque, steer_active)

    # ------------------------------------------------------------------
    def apply_accel(self, desired_accel: float, accel_active: bool) -> tuple:
        """
        Desired accel → safe accel.
        Returns: (safe_accel: float, permit_braking: bool, cancel: bool)
        """
        with self._lock:
            # Safety barlaglar
            disengage_reason = self._check_safety()
            if disengage_reason:
                self._do_disengage(disengage_reason)
                return (0.0, False, True)

            if not accel_active:
                return (0.0, False, True)

            # Çäkle
            safe_accel = max(MIN_ACCEL_MPS2, min(MAX_ACCEL_MPS2, desired_accel))
            return (safe_accel, True, False)

    # ------------------------------------------------------------------
    def notify_steer_cmd(self):
        """Steer buýrugy iberilendigini watchdog-a habar ber"""
        self.watchdog.feed_steer()

    def notify_accel_cmd(self):
        """Accel buýrugy iberilendigini watchdog-a habar ber"""
        self.watchdog.feed_accel()

    # ------------------------------------------------------------------
    def _check_safety(self) -> str:
        """Ähli safety barlaglaryny amala aşyr. Disengage sebäbini return et ýa-da ''"""
        # 1. Driver override
        if self.driver_override.is_overriding:
            return "DRIVER OVERRIDE"

        # 2. EPS fault
        if self.eps_monitor.has_fault:
            return f"EPS FAULT (LKA={self.eps_monitor.state_name})"

        # 3. EPS timeout (demo mode-da barlanmaýar)
        if self.eps_monitor.check_timeout():
            return "EPS TIMEOUT"

        # 4. Watchdog
        wd = self.watchdog.check()
        if wd['steer_timeout']:
            return "STEER WATCHDOG TIMEOUT"
        if wd['accel_timeout']:
            return "ACCEL WATCHDOG TIMEOUT"

        return ""

    # ------------------------------------------------------------------
    def _do_disengage(self, reason: str):
        """Disengage prosesi"""
        was_engaged = self._engaged
        self._engaged = False
        self._disengage_reason = reason
        self._fault_count += 1

        if was_engaged and self.on_disengage:
            self.on_disengage(reason)

    # ------------------------------------------------------------------
    def get_status(self) -> dict:
        """GUI üçin häzirki howpsuzlyk ýagdaýy"""
        with self._lock:
            return {
                'engaged': self._engaged,
                'disengage_reason': self._disengage_reason,
                'fault_count': self._fault_count,
                'driver_override': self.driver_override.is_overriding,
                'driver_torque': self.driver_override.driver_torque,
                'eps_fault': self.eps_monitor.has_fault,
                'lka_state': self.eps_monitor.state_name,
                'rate_limited_torque': self.rate_limiter.current_torque,
            }

    def reset(self):
        """Ähli ýagdaýy sypyr"""
        with self._lock:
            self.rate_limiter.reset()
            self.driver_override.reset()
            self.eps_monitor.reset()
            self.watchdog.reset()
            self._engaged = False
            self._disengage_reason = ""
