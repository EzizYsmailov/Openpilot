"""
Toyota Corolla 2017 - Gözegçilik buýruklary
STEERING_LKA  (0x2E4) → Ruly torque buýrugy
ACC_CONTROL   (0x343) → Tizlendirmek / haýallatmak

Safety Layer integrasiýasy bilen — OpenPilot ýaly howpsuzlyk.
"""
import threading
import time
from config import (
    ID_STEERING_LKA as DEFAULT_STEER_ID,
    ID_ACC_CONTROL as DEFAULT_ACCEL_ID,
    MAX_STEER_TORQUE, MIN_STEER_TORQUE,
    MAX_ACCEL_MPS2, MIN_ACCEL_MPS2,
    STEER_RATE_HZ, ACCEL_RATE_HZ
)
from safety_layer import SafetyManager


# ======================================================================
# Toyota CAN Checksum
# ======================================================================
def toyota_checksum(msg_id: int, data: bytearray) -> int:
    """
    Toyota checksummy hasaplamak
    Formulasy: 0xFF - (len + id_high + id_low + sum(data[:-1])) & 0xFF
    """
    s = len(data)
    s += (msg_id >> 8) & 0xFF
    s += (msg_id) & 0xFF
    for b in data[:-1]:
        s += b
    return (0xFF - (s & 0xFF)) & 0xFF


# ======================================================================
# STEERING_LKA Encoder
# ======================================================================
def encode_steering_lka(torque: int, counter: int, steer_request: bool = True, msg_id: int = DEFAULT_STEER_ID) -> bytes:
    """
    STEERING_LKA (CAN ID: 0x2E4, 5 baýt)

    DBC signallary:
      SET_ME_1        : 7|1   → byte0 bit7
      COUNTER         : 6|6   → byte0 bits6-1
      STEER_REQUEST   : 0|1   → byte0 bit0
      STEER_TORQUE_CMD: 15|16 → bytes 1-2 (signed, big-endian)
      LKA_STATE       : 31|8  → byte 3
      CHECKSUM        : 39|8  → byte 4
    """
    torque  = int(max(MIN_STEER_TORQUE, min(MAX_STEER_TORQUE, torque)))
    t_bytes = torque & 0xFFFF          # 2-lik doldurma (signed → unsigned)

    data    = bytearray(5)
    data[0] = 0x80 | ((counter & 0x3F) << 1) | int(steer_request)  # SET_ME_1=1, COUNTER, REQUEST
    data[1] = (t_bytes >> 8) & 0xFF                     # TORQUE high byte
    data[2] = t_bytes & 0xFF                            # TORQUE low byte
    data[3] = 0x00                                      # LKA_STATE
    data[4] = toyota_checksum(msg_id, data)

    return bytes(data)


# ======================================================================
# ACC_CONTROL Encoder
# ======================================================================
def encode_acc_control(accel_mps2: float,
                       permit_braking: bool = True,
                       release_standstill: bool = False,
                       cancel: bool = False,
                       msg_id: int = DEFAULT_ACCEL_ID) -> bytes:
    """
    ACC_CONTROL (CAN ID: 0x343, 8 baýt)

    DBC signallary:
      ACCEL_CMD          : 7|16  → bytes 0-1 (signed, big-endian, factor=0.001)
      PERMIT_BRAKING     : 16|1  → byte2 bit0
      ALLOW_LONG_PRESS   : 17|2  → byte2 bits2-1  (=2 adatça)
      CANCEL_REQ         : 24|1  → byte3 bit0
      RELEASE_STANDSTILL : 26|1  → byte3 bit2
      ACCEL_CMD_ALT      : 47|8  → byte5 (0 goýulýar)
      CHECKSUM           : 63|8  → byte7
    """
    accel_mps2 = max(MIN_ACCEL_MPS2, min(MAX_ACCEL_MPS2, accel_mps2))
    accel_int  = int(accel_mps2 / 0.001)
    a_bytes    = accel_int & 0xFFFF

    data    = bytearray(8)
    data[0] = (a_bytes >> 8) & 0xFF          # ACCEL_CMD high byte
    data[1] = a_bytes & 0xFF                 # ACCEL_CMD low byte
    data[2] = 2 & 0x3                        # ALLOW_LONG_PRESS=2 (bits 1-0)
    data[3] = (int(release_standstill) << 7) | (int(permit_braking) << 6) | int(cancel)
    data[4] = 0x00                           # ITS_CONNECT_LEAD=0
    data[5] = 0x00                           # ACCEL_CMD_ALT=0
    data[6] = 0x00
    data[7] = toyota_checksum(msg_id, data)

    return bytes(data)


# ======================================================================
# Commander - Arka planda habar ibermek (Safety Layer bilen)
# ======================================================================
class ToyotaCommander:
    """
    Ruly we gaz buýruklaryny 100Hz-de arka planda iber.
    Safety Layer ähli buýruklary barlaýar we çäklendirýär.

    Ulanyş:
        cmdr = ToyotaCommander(can_iface, steer_id=0x2E4, accel_id=0x343)
        cmdr.start()
        cmdr.set_steer(+400)      # Saga — rate-limited bolar
        ...
        cmdr.stop()               # Hemme zady howpsuz dur
    """

    def __init__(self, can_interface, steer_id=DEFAULT_STEER_ID, accel_id=DEFAULT_ACCEL_ID):
        self.can     = can_interface
        self._lock   = threading.Lock()
        self._stop   = threading.Event()
        
        # CAN IDs
        self.steer_id = steer_id
        self.accel_id = accel_id

        # Häzirki gymmatlar
        self._steer_torque  = 0
        self._accel_mps2    = 0.0
        self._steer_active  = False
        self._accel_active  = False
        self._counter       = 0

        self._thread = None

        # Safety Layer
        self.safety = SafetyManager()

    # ------------------------------------------------------------------
    def start(self):
        """Gözegçilik thread-ini başlat"""
        self._stop.clear()
        self.safety.reset()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Hemme gözegçiligi dur"""
        self._stop.set()
        with self._lock:
            self._steer_active = False
            self._accel_active = False
            self._steer_torque = 0
            self._accel_mps2 = 0.0
        self.safety.reset()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        self._thread = None

    # ------------------------------------------------------------------
    def feed_can_msg(self, msg):
        """CAN habaryny safety ulgamyna iber (CAN thread-den çagyrylýar)"""
        self.safety.feed_can_msg(msg)

    # ------------------------------------------------------------------
    def set_steer(self, torque: int):
        """Ruly torque set et (saga +, çepe -)"""
        with self._lock:
            self._steer_torque = int(torque)
            self._steer_active = True
        self.safety.notify_steer_cmd()

    def stop_steer(self):
        """Ruly buýrugyny bes et"""
        with self._lock:
            self._steer_torque = 0
            self._steer_active = False

    # ------------------------------------------------------------------
    def set_accel(self, accel_mps2: float):
        """Tizlendirme set et m/s² (+ = tizlenmek, - = haýallamak)"""
        with self._lock:
            self._accel_mps2   = float(accel_mps2)
            self._accel_active = True
        self.safety.notify_accel_cmd()

    def stop_accel(self):
        """Gaz buýrugyny bes et"""
        with self._lock:
            self._accel_mps2   = 0.0
            self._accel_active = False

    # ------------------------------------------------------------------
    def get_safety_status(self) -> dict:
        """Safety ýagdaý maglumatlaryny al (GUI üçin)"""
        return self.safety.get_status()

    # ------------------------------------------------------------------
    def _loop(self):
        """100Hz gözegçilik loop-y (Safety Layer bilen)"""
        interval = 1.0 / 100  # 10ms

        while not self._stop.is_set():
            t_start = time.perf_counter()

            with self._lock:
                steer_active = self._steer_active
                accel_active = self._accel_active
                torque       = self._steer_torque
                accel        = self._accel_mps2

            # --- Safety: Ruly torque barla we çäklendir ---
            if self.steer_id is not None:
                safe_torque, steer_request = self.safety.apply_steer(
                    torque if steer_active else 0,
                    steer_active
                )

                msg = encode_steering_lka(
                    safe_torque,
                    self._counter,
                    steer_request=steer_request,
                    msg_id=self.steer_id
                )
                self.can.send(self.steer_id, msg)

            # --- Safety: Accel barla we çäklendir ---
            if self.accel_id is not None:
                safe_accel, permit_braking, cancel = self.safety.apply_accel(
                    accel if accel_active else 0.0,
                    accel_active
                )

                msg = encode_acc_control(
                    safe_accel,
                    permit_braking=permit_braking,
                    release_standstill=False,
                    cancel=cancel,
                    msg_id=self.accel_id
                )
                self.can.send(self.accel_id, msg)

            # Counter 0-63 aralygynda
            self._counter = (self._counter + 1) % 64

            # 100Hz saklamak
            elapsed = time.perf_counter() - t_start
            sleep_t = interval - elapsed
            if sleep_t > 0:
                time.sleep(sleep_t)
