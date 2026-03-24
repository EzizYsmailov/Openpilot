"""
IXXAT USB-to-CAN - Windows baglanysy
Thread-safe CAN okamak we ibermek
"""
import can
import threading
import time
import math
import random
import config


class CANInterface:
    def __init__(self, on_message=None):
        """
        on_message: callback(msg) - her CAN habary gelanda çagyrylýar
        """
        self.bus         = None
        self.on_message  = on_message
        self.connected   = False
        self._rx_thread  = None
        self._demo_thread = None
        self._stop_event = threading.Event()

    # ------------------------------------------------------------------
    def connect(self):
        """IXXAT adapterine birikdir"""
        if config.DEMO_MODE:
            self._start_demo()
            return True

        try:
            self.bus = can.Bus(
                interface=config.CAN_INTERFACE,
                channel=config.CAN_CHANNEL,
                bitrate=config.CAN_BITRATE
            )
            self.connected   = True
            self._stop_event.clear()
            self._rx_thread  = threading.Thread(target=self._receive_loop, daemon=True)
            self._rx_thread.start()
            return True
        except Exception as e:
            raise ConnectionError(f"IXXAT birikmedi: {e}")

    # ------------------------------------------------------------------
    def disconnect(self):
        """Baglanysy kes"""
        self._stop_event.set()
        self.connected = False
        if self._rx_thread and self._rx_thread.is_alive():
            self._rx_thread.join(timeout=1.0)
        self._rx_thread = None
        if self._demo_thread and self._demo_thread.is_alive():
            self._demo_thread.join(timeout=1.0)
        self._demo_thread = None
        if self.bus:
            try:
                self.bus.shutdown()
            except Exception:
                pass
            self.bus = None

    # ------------------------------------------------------------------
    def send(self, can_id, data: bytes):
        """CAN habary iber"""
        if config.DEMO_MODE:
            return True
        if not self.connected or not self.bus:
            return False
        try:
            msg = can.Message(
                arbitration_id=can_id,
                data=data,
                is_extended_id=False
            )
            self.bus.send(msg)
            return True
        except Exception as e:
            print(f"Ibermek ýalňyşlygy: {e}")
            return False

    # ------------------------------------------------------------------
    def _receive_loop(self):
        """Arka planda CAN habarlaryny okamak"""
        while not self._stop_event.is_set():
            try:
                msg = self.bus.recv(timeout=0.1)
                if msg and self.on_message:
                    self.on_message(msg)
            except can.CanError as e:
                print(f"CAN okamak ýalňyşlygy: {e}")
                continue
            except Exception:
                pass

    # ------------------------------------------------------------------
    # DEMO РЕЖИМ - real adapter ýok bolanda synag üçin
    # ------------------------------------------------------------------
    def _start_demo(self):
        """Ýasama CAN maglumatlary döret (synag üçin)"""
        self.connected   = True
        self._stop_event.clear()
        self._demo_thread = threading.Thread(target=self._demo_loop, daemon=True)
        self._demo_thread.start()

    def _demo_loop(self):
        """Ýasama Toyota Corolla 2017 CAN habarlary"""
        speed     = 0.0
        steer     = 0.0
        gas       = 0.0
        t         = 0

        while not self._stop_event.is_set():
            t += 0.05
            # Ýuwaş-ýuwaş üýtgeýän gymmatlar
            speed  = 60 + 20 * abs(round(t % 4 - 2, 2))
            steer  = 45 * round(math.sin(t * 0.5), 3)
            gas    = max(0, min(100, 30 + 20 * round(math.sin(t), 3)))

            # -- SPEED (0xB4) --
            # SPEED : 47|16@0+ → byte5(high), byte6(low)
            spd_raw = int(speed / 0.01)
            d = bytearray(8)
            d[5] = (spd_raw >> 8) & 0xFF
            d[6] = spd_raw & 0xFF
            self._fake_msg(0xB4, d)

            # -- STEER_ANGLE (0x25) --
            st_raw = int(steer / 1.5)
            if st_raw < 0:
                st_raw = st_raw & 0xFFF
            d2 = bytearray(8)
            d2[0] = (st_raw >> 8) & 0x0F
            d2[1] = st_raw & 0xFF
            self._fake_msg(0x25, d2)

            # -- GAS_PEDAL (0x2C1 = 705) --
            d3 = bytearray(8)
            d3[6] = int(gas / 0.5) & 0xFF
            self._fake_msg(0x2C1, d3)

            # -- GAS_PEDAL_HYBRID (0x245 = 581) --
            d3h = bytearray(8)
            d3h[2] = min(255, int(gas * 0.01 / 0.005)) & 0xFF
            self._fake_msg(0x245, d3h)

            # -- BRAKE (0xA6) --
            d4 = bytearray(8)
            d4[0] = 0 if gas > 5 else 3   # BRAKE_AMOUNT: 7|8@0+ → byte 0
            self._fake_msg(0xA6, d4)

            # -- WHEEL_SPEEDS (0xAA) --
            ws_raw = int((speed + 67.67) / 0.01)
            d5 = bytearray(8)
            for i in range(4):
                d5[i*2]   = (ws_raw >> 8) & 0xFF
                d5[i*2+1] = ws_raw & 0xFF
            self._fake_msg(0xAA, d5)

            # -- ENGINE_RPM (0x1C4 = 452) --
            rpm = 800 + speed * 30  # RPM tizlige bagly
            rpm_raw = int(rpm / 0.78125)
            d6 = bytearray(8)
            d6[0] = (rpm_raw >> 8) & 0xFF
            d6[1] = rpm_raw & 0xFF
            d6[3] = 0x08  # ENGINE_RUNNING=1 (bit 27 → byte3 bit3)
            self._fake_msg(0x1C4, d6)

            # -- PCM_CRUISE (0x1D2 = 466) --
            d7 = bytearray(8)
            cruise_active = 1 if speed > 40 else 0
            d7[0] = cruise_active << 5  # CRUISE_ACTIVE at bit 5
            cruise_state = 8 if cruise_active else 0  # 8=adaptive_engaged
            d7[6] = (cruise_state & 0x0F) << 4  # CRUISE_STATE at bits 55|4
            self._fake_msg(0x1D2, d7)

            # -- KINEMATICS (0x24 = 36) --
            # YAW_RATE: 1|10@0+ (0.244,-125) → byte0 bits[1:0], byte1 bits[7:0]
            # ACCEL_X:  17|10@0+ (0.03589,-18.375) → byte2 bits[1:0], byte3 bits[7:0]
            yaw = steer * 0.3  # ýönekeý simulýasiýa
            yaw_raw = max(0, min(1023, int((yaw + 125) / 0.244)))
            ax = 0.5 * math.sin(t * 0.8)
            ax_raw = max(0, min(1023, int((ax + 18.375) / 0.03589)))
            d8 = bytearray(8)
            d8[0] = (yaw_raw >> 8) & 0x03
            d8[1] = yaw_raw & 0xFF
            d8[2] = (ax_raw >> 8) & 0x03
            d8[3] = ax_raw & 0xFF
            self._fake_msg(0x24, d8)

            # -- STEER_TORQUE_SENSOR (0x260 = 608) --
            # STEER_TORQUE_DRIVER: 15|16@0- → bytes 1(high) 2(low)
            # STEER_OVERRIDE: 0|1@0+ → byte0 bit0
            driver_torq = int(steer * 2)
            dt_bytes = driver_torq & 0xFFFF
            d9 = bytearray(8)
            d9[0] = 1 if abs(driver_torq) > 50 else 0  # STEER_OVERRIDE
            d9[1] = (dt_bytes >> 8) & 0xFF              # TORQUE_DRIVER high
            d9[2] = dt_bytes & 0xFF                     # TORQUE_DRIVER low
            self._fake_msg(0x260, d9)

            time.sleep(0.05)

    def _fake_msg(self, can_id, data):
        """Ýasama habar döret we callback çagyr"""
        if self.on_message:
            msg = can.Message(
                arbitration_id=can_id,
                data=bytes(data),
                is_extended_id=False,
                timestamp=time.time()
            )
            self.on_message(msg)
