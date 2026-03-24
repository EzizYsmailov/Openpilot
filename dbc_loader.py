"""
DBC faýl menejer.
Proýekt klasörindäki ähli .dbc faýllaryny tapýar,
cantools bilen ýükleýär we maglumatlary berýär.
"""
import os
import glob
import cantools

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Belli signal atlary → proýektiň içki ady
_SIGNAL_MAP = {
    # Tizlik
    'SPEED':               ('speed',       'km/h'),
    'VEHICLE_SPEED':       ('speed',       'km/h'),
    'WHEEL_SPEED':         ('speed',       'km/h'),
    'FORWARD_SPEED':       ('speed',       'km/h'),
    # Ruletka
    'STEER_ANGLE':         ('steer_angle', 'deg'),
    'STEERING_ANGLE':      ('steer_angle', 'deg'),
    'STEER_ANGLE_SENSOR':  ('steer_angle', 'deg'),
    # Gaz
    'GAS_PEDAL':           ('gas_pct',     '%'),
    'ACCELERATOR_PEDAL':   ('gas_pct',     '%'),
    'THROTTLE_POSITION':   ('gas_pct',     '%'),
    # Tormoz
    'BRAKE_AMOUNT':        ('brake',       ''),
    'BRAKE_PRESSED':       ('brake',       ''),
    'BRAKE_PRESSURE':      ('brake',       'N'),
    # RPM
    'RPM':                 ('rpm',         'rpm'),
    'ENGINE_RPM':          ('rpm',         'rpm'),
    # Kruiz
    'CRUISE_ACTIVE':       ('cruise',      ''),
    'CRUISE_STATE':        ('cruise_state',''),
    # Tigir tizligi
    'WHEEL_SPEED_FR':      ('wheel_FR',    'km/h'),
    'WHEEL_SPEED_FL':      ('wheel_FL',    'km/h'),
    'WHEEL_SPEED_RR':      ('wheel_RR',    'km/h'),
    'WHEEL_SPEED_RL':      ('wheel_RL',    'km/h'),
    # Ýörite
    'STEER_TORQUE_DRIVER': ('driver_torq', ''),
    'STEER_OVERRIDE':      ('steer_ovrrd', ''),
}

def find_dbc_files(folder=None):
    """Klasördäki ähli .dbc faýllaryny sanaw hökmünde return et"""
    if folder is None:
        # Default: dbc_files folder
        folder = os.path.join(_SCRIPT_DIR, 'dbc_files')
        if not os.path.exists(folder):
            # Fallback to current dir if dbc_files doesn't exist
            folder = _SCRIPT_DIR
            
    files  = glob.glob(os.path.join(folder, '*.dbc'))
    return sorted([os.path.basename(f) for f in files])


def load_dbc(filename, folder=None):
    """
    DBC faýlyny cantools bilen ýükle.
    Returns: (db, info_dict) ýa-da (None, error_str)
    """
    if folder is None:
        folder = os.path.join(_SCRIPT_DIR, 'dbc_files')
        if not os.path.exists(os.path.join(folder, filename)):
            folder = _SCRIPT_DIR

    filepath = os.path.join(folder, filename)

    if not os.path.isfile(filepath):
        return None, f"Faýl tapylmady: {filepath}"

    try:
        # strict=False allows some errors, but frame ID overflow checks might still happen in newer cantools versions.
        # We catch the error below and return it to the GUI.
        db = cantools.db.load_file(filepath, strict=False)
    except Exception as e:
        return None, f"DBC ýükleme ýalňyşlygy (başga faýl synap görüň): {e}"

    info = analyze_db(db, filename)
    return db, info


def analyze_db(db, filename=''):
    """
    DBC içindäki habarlary we signallary analize et.
    Haýsy maşyna degişlidigini we näme edip bolýandygyny kesgitle.
    """
    msg_names = {m.name for m in db.messages}
    # msg_ids mapping: name -> id
    msg_ids = {m.name: m.frame_id for m in db.messages}
    
    sig_names = {s.name for m in db.messages for s in m.signals}

    # Marka/model keşik et
    brand = _detect_brand(filename, msg_names, sig_names)

    # Gözegçilik mümkinçilikleri barla
    has_steering = _has_steering_control(db, msg_names)
    has_accel    = _has_accel_control(db, msg_names)
    
    capabilities = {
        'steering':   has_steering,
        'accel':      has_accel,
        'toyota_lka': 'STEERING_LKA' in msg_names,
        'toyota_acc': 'ACC_CONTROL'  in msg_names,
    }

    # Control Message IDs (for dynamic usage)
    control_ids = {
        'STEERING_LKA': msg_ids.get('STEERING_LKA'),
        'ACC_CONTROL':  msg_ids.get('ACC_CONTROL'),
    }

    # Möhüm signal ID-lerini tap
    known_signals = _find_known_signals(db)

    return {
        'filename':     filename,
        'brand':        brand,
        'msg_count':    len(db.messages),
        'sig_count':    sum(len(m.signals) for m in db.messages),
        'capabilities': capabilities,
        'control_ids':  control_ids,
        'known':        known_signals,
        'msg_names':    msg_names,
    }

def _detect_brand(filename, msg_names, sig_names):
    fn = filename.lower()
    if any(x in fn for x in ['toyota', 'lexus', 'prius', 'corolla', 'rav4', 'camry']):
        return 'Toyota/Lexus'
    if any(x in fn for x in ['honda', 'acura']):
        return 'Honda/Acura'
    if any(x in fn for x in ['vw', 'volkswagen', 'audi', 'skoda', 'seat']):
        return 'VW Group'
    if any(x in fn for x in ['gm', 'chevrolet', 'cadillac', 'buick']):
        return 'GM'
    if any(x in fn for x in ['bmw']):
        return 'BMW'
    if any(x in fn for x in ['mercedes', 'benz']):
        return 'Mercedes'
    if any(x in fn for x in ['hyundai', 'kia']):
        return 'Hyundai/Kia'
    if any(x in fn for x in ['ford', 'lincoln']):
        return 'Ford/Lincoln'
    if 'STEERING_LKA' in msg_names or 'ACC_CONTROL' in msg_names:
        return 'Toyota/Lexus'
    return 'Näbelli'


def _has_steering_control(db, msg_names):
    control_msgs = {'STEERING_LKA', 'STEERING_LTA', 'LKAS_HUD',
                    'STEERING_CONTROL', 'LKAS_OUTPUT'}
    return bool(control_msgs & msg_names)


def _has_accel_control(db, msg_names):
    control_msgs = {'ACC_CONTROL', 'ACCEL_COMMAND', 'LONG_CONTROL'}
    return bool(control_msgs & msg_names)


def _find_known_signals(db):
    """
    DBC-dan belli signal atlaryny tap.
    Return: {internal_name: (msg_id, signal_name, unit)}
    Dublikat signal ady bolsa, habar ady signal adyny öz içine alýanyny saýlaýar.
    """
    found = {}
    for msg in db.messages:
        for sig in msg.signals:
            if sig.name in _SIGNAL_MAP:
                internal, unit = _SIGNAL_MAP[sig.name]
                if internal not in found:
                    found[internal] = (msg.frame_id, sig.name, unit)
                elif sig.name in msg.name:
                    # Signal ady habar adynda bar → has gowy laýyklyk
                    found[internal] = (msg.frame_id, sig.name, unit)
    return found


def get_all_messages_info(db):
    """
    DBC-daky ähli habarlary yzgiderli sanaw hökmünde return et.
    GUI üçin habar/signal agajy döretmek üçin ulanylýar.
    """
    result = []
    for msg in sorted(db.messages, key=lambda m: m.frame_id):
        sigs = []
        for sig in msg.signals:
            sigs.append({
                'name':   sig.name,
                'unit':   sig.unit or '',
                'min':    sig.minimum,
                'max':    sig.maximum,
            })
        result.append({
            'id':      msg.frame_id,
            'id_hex':  hex(msg.frame_id),
            'name':    msg.name,
            'length':  msg.length,
            'signals': sigs,
        })
    return result
