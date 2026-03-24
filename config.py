# ================================================
# Toyota Corolla 2017 - CAN Sazlamalary
# ================================================

# --- IXXAT Sazlamalary ---
CAN_INTERFACE  = 'ixxat'    # Windows IXXAT driver
CAN_CHANNEL    = 0          # Ilkinji adapter
CAN_BITRATE    = 500000     # Toyota = 500 kbps

# Demo mode (real hardware ýok bolsa True)
DEMO_MODE = False

# --- Toyota Corolla 2017 - Okamak üçin CAN ID-ler ---
ID_STEER_ANGLE  = 0x25     # 37  - Ruletka burçy
ID_WHEEL_SPEEDS = 0xAA     # 170 - 4 tigiriň tizligi
ID_SPEED        = 0xB4     # 180 - Maşyn tizligi
ID_BRAKE        = 0xA6     # 166 - Tormoz
ID_GAS_PEDAL    = 0x2C1    # 705 - Gaz pedaly
ID_PCM_CRUISE   = 0x1D2    # 466 - Kruiz ýagdaýy
ID_KINEMATICS   = 0x24     # 36  - G güýçler
ID_ENGINE_RPM   = 0x1C4    # 452 - Motor RPM
ID_GAS_HYBRID   = 0x245    # 581 - Gaz pedaly (hybrid)
ID_STEER_TORQ   = 0x260    # 608 - Sürüji torque sensory

# --- Gözegçilik üçin CAN ID-ler (ibermek) ---
ID_STEERING_LKA = 0x2E4    # 740 - Ruly buýrugy (STEERING_LKA)
ID_ACC_CONTROL  = 0x343    # 835 - Tizlendirmek/haýallatmak

# --- Çäkler ---
MAX_STEER_TORQUE = 1500    # Maksimum ruly torque
MIN_STEER_TORQUE = -1500   # Minimum ruly torque
MAX_ACCEL_MPS2   = 2.0     # Maksimum tizlendirmek m/s²
MIN_ACCEL_MPS2   = -3.5    # Maksimum haýallatmak m/s²

# --- Ýygylyk ---
STEER_RATE_HZ  = 100       # Ruly buýrugy: 100Hz (her 10ms)
ACCEL_RATE_HZ  = 100       # Gaz buýrugy: 100Hz

# --- Toyota checksum ---
# sum(len, id_high, id_low, data[:-1]) → 0xFF - (sum & 0xFF)

# --- Safety (howpsuzlyk) ---
STEER_TORQUE_RATE_LIMIT  = 15      # Maks Nm üýtgeşme per frame (10ms)
DRIVER_OVERRIDE_THRESHOLD = 100    # Nm — mundan ýokary = sürüji override
WATCHDOG_TIMEOUT_MS      = 200     # ms — buýruk gelmese disengage
OVERRIDE_COOLDOWN_S      = 0.5     # sek — override aýrylandan soň garaşmak
ID_EPS_STATUS            = 0x262   # 610 — EPS ýagdaý habary
