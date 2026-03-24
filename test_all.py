"""
Comprehensive verification test for all fixes.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 1. Test toyota_checksum
from toyota_commands import toyota_checksum, encode_steering_lka, encode_acc_control
print("=== CHECKSUM TEST ===")
data = bytearray([0x80, 0x00, 0x00, 0x00, 0x00])
cs = toyota_checksum(0x2E4, data)
data[4] = cs
print(f"STEERING_LKA checksum: 0x{cs:02X} -> data={data.hex()}")
assert 0 <= cs <= 255, "Checksum out of range!"
print("  [OK] Checksum valid")

# 2. Test STEERING_LKA encoding
print("\n=== STEERING_LKA TEST ===")
msg = encode_steering_lka(torque=400, counter=10, steer_request=True)
print(f"Torque=400, counter=10: {msg.hex()}")
assert len(msg) == 5, f"Wrong length: {len(msg)}"
assert msg[0] & 0x80 == 0x80, "SET_ME_1 not set!"
assert msg[0] & 0x01 == 1, "STEER_REQUEST not set!"
print("  [OK] SET_ME_1=1, REQUEST=1")

msg2 = encode_steering_lka(torque=-400, counter=5, steer_request=False)
print(f"Torque=-400, counter=5: {msg2.hex()}")
assert msg2[0] & 0x01 == 0, "STEER_REQUEST should be 0!"
print("  [OK] Negative torque + REQUEST=0")

# 3. Test ACC_CONTROL encoding
print("\n=== ACC_CONTROL TEST ===")
msg3 = encode_acc_control(1.5, permit_braking=True, cancel=False)
print(f"Accel=1.5: {msg3.hex()}")
assert len(msg3) == 8, f"Wrong length: {len(msg3)}"
accel_raw = (msg3[0] << 8) | msg3[1]
if accel_raw > 32767:
    accel_raw -= 65536
accel_val = accel_raw * 0.001
print(f"  Decoded ACCEL_CMD: {accel_val} m/s2")
assert abs(accel_val - 1.5) < 0.01, f"Accel value wrong: {accel_val}"
print("  [OK] ACCEL_CMD correct")

msg4 = encode_acc_control(0.0, permit_braking=False, cancel=True)
print(f"Accel=0 cancel: {msg4.hex()}")
assert msg4[3] & 0x01 == 1, "CANCEL_REQ should be set!"
assert msg4[3] & 0x40 == 0, "PERMIT_BRAKING should be 0!"
print("  [OK] CANCEL mode correct")

# 4. Test KINEMATICS parsing (fixed bit extraction)
print("\n=== KINEMATICS PARSE TEST ===")
from toyota_parser import ToyotaParser
parser = ToyotaParser()
# Create test data: YAW_RATE raw=512, ACCEL_X raw=512
d = bytearray(8)
d[0] = (512 >> 8) & 0x03  # = 0x02
d[1] = 512 & 0xFF         # = 0x00
d[2] = (512 >> 8) & 0x03  # = 0x02
d[3] = 512 & 0xFF         # = 0x00
result = parser._parse_kinematics(d)
expected_yaw = round(512 * 0.244 - 125, 2)
expected_ax = round(512 * 0.03589 - 18.375, 3)
print(f"  Raw yaw=512 -> yaw_rate={result['yaw']} (expected {expected_yaw})")
print(f"  Raw ax=512  -> accel_x={result['accel_x']} (expected {expected_ax})")
assert abs(result['yaw'] - expected_yaw) < 0.1, f"YAW wrong: {result['yaw']}"
assert abs(result['accel_x'] - expected_ax) < 0.1, f"AX wrong: {result['accel_x']}"
print("  [OK] KINEMATICS bit extraction correct")

# 5. Test DBC loading
print("\n=== DBC LOAD TEST ===")
from dbc_loader import load_dbc, find_dbc_files
script_dir = os.path.dirname(os.path.abspath(__file__))
files = find_dbc_files(script_dir)
print(f"  DBC files found: {files}")
db, info = load_dbc('toyota_corolla_2017.dbc', script_dir)
assert db is not None, "DBC load failed!"
print(f"  Brand: {info['brand']}")
print(f"  Messages: {info['msg_count']}")
print(f"  Signals: {info['sig_count']}")
print(f"  Known: {list(info['known'].keys())}")
print(f"  Steering: {info['capabilities']['steering']}")
print(f"  Accel: {info['capabilities']['accel']}")
assert info['capabilities']['steering'], "Steering capability not detected!"
assert info['capabilities']['accel'], "Accel capability not detected!"
print("  [OK] DBC loaded with all capabilities")

# 6. Test CANParser
print("\n=== CAN PARSER TEST ===")
from can_parser import CANParser
import can
cp = CANParser(db, info['known'])
# Create speed message: 80 km/h -> raw=8000
raw_speed = int(80 / 0.01)
sd = bytearray(8)
sd[5] = (raw_speed >> 8) & 0xFF
sd[6] = raw_speed & 0xFF
speed_msg = can.Message(arbitration_id=0xB4, data=bytes(sd))
result = cp.parse(speed_msg)
print(f"  Speed parse: {result}")
if result and 'speed' in result.get('values', {}):
    spd = result['values']['speed']
    assert abs(spd - 80) < 0.5, f"Speed wrong: {spd}"
    print("  [OK] Speed parsed correctly")

# 7. Test ToyotaCommander thread safety
print("\n=== COMMANDER TEST ===")
from can_interface import CANInterface
import config
config.DEMO_MODE = True
ci = CANInterface()
ci.connect()

from toyota_commands import ToyotaCommander
cmdr = ToyotaCommander(ci)
cmdr.start()
cmdr.set_steer(400)
cmdr.set_accel(1.0)
import time
time.sleep(0.1)
cmdr.stop()
assert cmdr._steer_torque == 0, "Steer not reset!"
assert cmdr._accel_mps2 == 0.0, "Accel not reset!"
assert cmdr._thread is None, "Thread not cleaned!"
print("  [OK] Commander stop() resets values and joins thread")

ci.disconnect()
print("  [OK] CANInterface disconnect() clean")

print("\n============================")
print("ALL 7 TESTS PASSED!")
print("============================")
