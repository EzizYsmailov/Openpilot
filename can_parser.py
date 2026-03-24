"""
Universal CAN parser - islendik DBC bilen işleýär.
cantools arkaly habarlary decode edip belli internal signallara öwürýär.
"""
from dbc_loader import _SIGNAL_MAP


class CANParser:
    """
    DBC-a esaslanýan universal CAN parser.
    db     = cantools.db obýekti (dbc_loader.load_dbc-dan)
    known  = dbc_loader.analyze_db-dan 'known' dict
    """

    def __init__(self, db, known_signals):
        self._db     = db
        self._known  = known_signals   # {internal: (msg_id, sig_name, unit)}
        # msg_id → list of internal signal names
        self._id_map = {}
        for internal, (mid, sname, unit) in known_signals.items():
            self._id_map.setdefault(mid, []).append(internal)

    # ------------------------------------------------------------------
    def parse(self, msg):
        """
        CAN habary parse et.
        Returns: {'type': 'data', 'values': {internal_name: value, ...}}
                 ýa-da None
        """
        mid  = msg.arbitration_id
        data = msg.data

        # Bu ID bilen gyzyklanýan signallarymyz barmy?
        if mid not in self._id_map:
            return None

        # cantools decode
        try:
            msg_def = self._db.get_message_by_frame_id(mid)
            decoded = msg_def.decode(data, decode_choices=False)
        except Exception:
            return None

        # Biz isleýän signallary çykarmak
        result = {}
        for internal in self._id_map[mid]:
            _, sig_name, unit = self._known[internal]
            if sig_name in decoded:
                val = decoded[sig_name]
                result[internal] = round(float(val), 2) if isinstance(val, float) else val

        if not result:
            return None

        return {'type': 'data', 'values': result}

    # ------------------------------------------------------------------
    def parse_all(self, msg):
        """
        Bu habardaky ähli signallary decode et (raw gözlemek üçin).
        Returns: {'msg_name': str, 'signals': {name: value}} ýa-da None
        """
        try:
            msg_def = self._db.get_message_by_frame_id(msg.arbitration_id)
            decoded = msg_def.decode(msg.data, decode_choices=False)
            return {
                'msg_name': msg_def.name,
                'msg_id':   msg.arbitration_id,
                'signals':  {k: round(float(v), 3) if isinstance(v, float) else v
                             for k, v in decoded.items()}
            }
        except Exception:
            return None

    # ------------------------------------------------------------------
    def get_known_ids(self):
        """Biz gyzyklanýan CAN ID-leri set hökmünde return et"""
        return set(self._id_map.keys())
