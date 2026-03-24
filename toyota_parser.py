"""
Toyota Corolla 2017 - CAN habarlaryny çözmek (parse)
DBC: toyota_corolla_2017.dbc (birleşdirilen faýl)
cantools bilen DBC ýükleýär, mümkin bolmasa qolda parse edýär.
"""
import os
import cantools
from config import *

# DBC faýlyny ýükle
_DBC_PATH = os.path.join(os.path.dirname(__file__), 'toyota_corolla_2017.dbc')
try:
    _DB = cantools.db.load_file(_DBC_PATH)
    _USE_CANTOOLS = True
    print(f"[DBC] cantools loaded: {_DBC_PATH}")
except Exception as e:
    _DB = None
    _USE_CANTOOLS = False
    print(f"[DBC] cantools failed ({e}), using manual parse")


class ToyotaParser:
    """
    Gelen CAN habaryny okap signal gymmatlaryny return edýär.
    parse(msg) → {'signal_name': value, ...} ýa-da None
    """

    def parse(self, msg):
        mid  = msg.arbitration_id
        data = msg.data

        # cantools bilen parse et (DBC ýüklenen bolsa)
        if _USE_CANTOOLS:
            return self._parse_cantools(mid, data)

        # Qolda parse (fallback)
        if mid == ID_STEER_ANGLE:
            return self._parse_steer_angle(data)
        elif mid == ID_SPEED:
            return self._parse_speed(data)
        elif mid == ID_BRAKE:
            return self._parse_brake(data)
        elif mid == ID_GAS_PEDAL:
            return self._parse_gas_pedal(data)
        elif mid == ID_WHEEL_SPEEDS:
            return self._parse_wheel_speeds(data)
        elif mid == ID_PCM_CRUISE:
            return self._parse_cruise(data)
        elif mid == ID_KINEMATICS:
            return self._parse_kinematics(data)
        return None

    def _parse_cantools(self, mid, data):
        """cantools arkaly DBC-dan signal decode et"""
        try:
            msg_def = _DB.get_message_by_frame_id(mid)
        except KeyError:
            return None

        try:
            decoded = msg_def.decode(data, decode_choices=False)
        except Exception:
            return None

        name = msg_def.name

        if name == 'STEER_ANGLE_SENSOR':
            return {'type': 'steer_angle',
                    'steer_angle': round(decoded.get('STEER_ANGLE', 0), 1)}

        elif name == 'SPEED':
            return {'type': 'speed',
                    'speed': round(decoded.get('SPEED', 0), 1)}

        elif name == 'BRAKE':
            return {'type': 'brake',
                    'brake_amount': int(decoded.get('BRAKE_AMOUNT', 0)),
                    'brake_force':  int(decoded.get('BRAKE_FORCE', 0))}

        elif name == 'GAS_PEDAL':
            return {'type': 'gas',
                    'gas_pct': round(decoded.get('GAS_PEDAL', 0), 1)}

        elif name == 'WHEEL_SPEEDS':
            return {'type': 'wheel_speeds',
                    'FL': round(decoded.get('WHEEL_SPEED_FL', 0), 1),
                    'FR': round(decoded.get('WHEEL_SPEED_FR', 0), 1),
                    'RL': round(decoded.get('WHEEL_SPEED_RL', 0), 1),
                    'RR': round(decoded.get('WHEEL_SPEED_RR', 0), 1)}

        elif name == 'PCM_CRUISE':
            active = bool(decoded.get('CRUISE_ACTIVE', 0))
            state  = int(decoded.get('CRUISE_STATE', 0))
            states = {0:'off', 1:'aktiv', 7:'dur', 8:'ACC aktiv', 11:'3sn taýmer'}
            return {'type': 'cruise',
                    'cruise_active': active,
                    'cruise_state':  states.get(state, str(state))}

        elif name == 'KINEMATICS':
            return {'type': 'kinematics',
                    'yaw':     round(decoded.get('YAW_RATE', 0), 2),
                    'accel_x': round(decoded.get('ACCEL_X', 0), 3)}

        elif name == 'ENGINE_RPM':
            return {'type': 'rpm',
                    'rpm': round(decoded.get('RPM', 0), 0)}

        elif name == 'STEER_TORQUE_SENSOR':
            return {'type': 'steer_torque',
                    'driver_torque': decoded.get('STEER_TORQUE_DRIVER', 0),
                    'eps_torque':    decoded.get('STEER_TORQUE_EPS', 0),
                    'override':      bool(decoded.get('STEER_OVERRIDE', 0))}

        return None

    # ------------------------------------------------------------------
    def _parse_steer_angle(self, d):
        """
        STEER_ANGLE_SENSOR (0x25)
        STEER_ANGLE : 3|12@0- (1.5, 0) deg
        """
        if len(d) < 2:
            return None
        raw = ((d[0] & 0x0F) << 8) | d[1]
        if raw > 2047:
            raw -= 4096
        return {
            'type':        'steer_angle',
            'steer_angle': round(raw * 1.5, 1)    # dereje
        }

    # ------------------------------------------------------------------
    def _parse_speed(self, d):
        """
        SPEED (0xB4)
        SPEED : 47|16@0+ (0.01, 0) km/h
        MSBit=47 → byte5(high), byte6(low)
        Byte4=ENCODER, Byte5-6=SPEED, Byte7=CHECKSUM
        """
        if len(d) < 7:
            return None
        raw = ((d[5] << 8) | d[6])
        return {
            'type':  'speed',
            'speed': round(raw * 0.01, 1)    # km/h
        }

    # ------------------------------------------------------------------
    def _parse_brake(self, d):
        """
        BRAKE (0xA6)
        BRAKE_AMOUNT: 7|8@0+  (1,0)
        BRAKE_FORCE:  23|8@0+ (40,0) N
        """
        if len(d) < 3:
            return None
        return {
            'type':         'brake',
            'brake_amount': d[0],
            'brake_force':  d[2] * 40
        }

    # ------------------------------------------------------------------
    def _parse_gas_pedal(self, d):
        """
        GAS_PEDAL (0x2C1)
        GAS_PEDAL: 55|8@0+ (0.5, 0) %
        Byte 6 → 0-100%
        """
        if len(d) < 7:
            return None
        return {
            'type':     'gas',
            'gas_pct':  round(d[6] * 0.5, 1)    # %
        }

    # ------------------------------------------------------------------
    def _parse_wheel_speeds(self, d):
        """
        WHEEL_SPEEDS (0xAA)
        Her tigir: 16-bit, factor=0.01, offset=-67.67 → km/h
        FL: bytes 2-3, FR: bytes 0-1, RL: bytes 6-7, RR: bytes 4-5
        """
        if len(d) < 8:
            return None
        def ws(hi, lo):
            return round(((hi << 8) | lo) * 0.01 - 67.67, 1)
        return {
            'type': 'wheel_speeds',
            'FL':   ws(d[2], d[3]),
            'FR':   ws(d[0], d[1]),
            'RL':   ws(d[6], d[7]),
            'RR':   ws(d[4], d[5])
        }

    # ------------------------------------------------------------------
    def _parse_cruise(self, d):
        """
        PCM_CRUISE (0x1D2)
        CRUISE_ACTIVE: bit 5 of byte 0
        CRUISE_STATE:  bits 55|4@0+
        """
        if len(d) < 7:
            return None
        active = bool((d[0] >> 5) & 0x01)
        state  = (d[6] >> 4) & 0x0F
        states = {0:'off', 1:'aktiv', 7:'dur', 8:'ACC aktiv', 11:'3sn taýmer'}
        return {
            'type':         'cruise',
            'cruise_active': active,
            'cruise_state':  states.get(state, str(state))
        }

    # ------------------------------------------------------------------
    def _parse_kinematics(self, d):
        """
        KINEMATICS (0x24)
        YAW_RATE:  1|10@0+  (0.244, -125) deg/s
        ACCEL_X:   17|10@0+ (0.03589, -18.375) m/s²
        ACCEL_Y:   33|10@0+ (0.03589, -18.375) m/s²
        """
        if len(d) < 5:
            return None
        yaw_raw  = ((d[0] & 0x03) << 8) | d[1]
        ax_raw   = ((d[2] & 0x03) << 8) | d[3]
        return {
            'type':    'kinematics',
            'yaw':     round(yaw_raw * 0.244 - 125, 2),
            'accel_x': round(ax_raw  * 0.03589 - 18.375, 3)
        }
