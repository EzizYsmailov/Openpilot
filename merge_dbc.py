"""
opendbc generator faýllaryny birleşdirip toyota_corolla_2017.dbc döredýär.
Çeşme: opendbc/dbc/generator/toyota/

Ulanyş:
    python merge_dbc.py
    python merge_dbc.py --opendbc D:/opendbc-master/opendbc-master/opendbc/dbc
"""
import os
import sys
import re

# opendbc ýoly - default: bu skriptiň ýanyndaky opendbc-master
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_OPENDBC = os.path.join(
    _SCRIPT_DIR, '..', 'opendbc-master',
    'opendbc-master', 'opendbc', 'dbc'
)


def find_opendbc(custom_path=None):
    candidates = [
        custom_path,
        DEFAULT_OPENDBC,
        r'D:\opendbc-master\opendbc-master\opendbc\dbc',
        r'C:\opendbc-master\opendbc-master\opendbc\dbc',
    ]
    for p in candidates:
        if p and os.path.isdir(p):
            return os.path.abspath(p)
    return None


def read_dbc(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def extract_messages(content):
    """
    DBC faýlyndan diňe BO_, SG_, CM_, VAL_ setirlerini çykarmak.
    Header (VERSION, NS_, BS_, BU_) we IMPORT setirlerini geçirýär.
    """
    lines      = content.splitlines()
    result     = []
    in_ns      = False

    for line in lines:
        stripped = line.strip()

        # NS_ blokyny geç (girintili setirler NS_: blogynyň içi)
        if stripped.startswith('NS_ :') or stripped == 'NS_:':
            in_ns = True
            continue

        if in_ns:
            # NS_ blogy - girintili ýa-da boş setir bolsa içindedir
            if line and not line[0].isspace() and stripped != '':
                in_ns = False
                # Bu setir NS_-den soňky setir, ony hem barla
            else:
                continue

        # Gerek däl setirler
        if (stripped.startswith('VERSION') or
                stripped.startswith('BS_:') or
                stripped.startswith('BS_ :') or
                stripped.startswith('BU_:') or
                stripped.startswith('BU_ :')):
            continue

        # IMPORT direktiwasyny geç
        if re.match(r'CM_\s+"IMPORT\s+', stripped):
            continue

        result.append(line)

    # Köp boş setirleri azalt
    text = '\n'.join(result)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def merge_toyota_corolla_2017(dbc_root):
    gen_dir = os.path.join(dbc_root, 'generator', 'toyota')

    # Birleşdiriljek faýllar (tertip möhüm: base faýllar öňi)
    source_files = [
        ('_toyota_2017.dbc',         'Toyota 2017+ base messages'),
        ('_toyota_adas_standard.dbc', 'ADAS standard messages (TSS 1.x)'),
        ('toyota_new_mc_pt.dbc',      'New MC platform (Corolla 2017 specific)'),
    ]

    # Faýllaryň barlygy barla
    for fname, _ in source_files:
        fpath = os.path.join(gen_dir, fname)
        if not os.path.isfile(fpath):
            print(f"ÝALŇYŞLYK: Faýl tapylmady: {fpath}")
            return False

    # --- Birleşdirilmiş DBC ---
    merged_parts = []

    # 1. Header
    merged_parts.append('VERSION ""\n')
    merged_parts.append('NS_ :\n\n')
    merged_parts.append('BS_:\n')
    merged_parts.append('BU_: XXX DSU HCU EPS IPAS CGW BGM\n')
    merged_parts.append(
        '\nCM_ "Toyota Corolla 2017 - Merged DBC";\n'
        'CM_ "Generated from opendbc generator/toyota/ files";\n'
        'CM_ "Sources: _toyota_2017 + _toyota_adas_standard + toyota_new_mc_pt";\n'
    )

    # 2. Her faýldan habarlar
    seen_ids = set()
    for fname, desc in source_files:
        fpath   = os.path.join(gen_dir, fname)
        content = read_dbc(fpath)
        body    = extract_messages(content)

        if not body:
            continue

        # Duplicate BO_ ID-lerini aýyr
        final_lines = []
        skip_block  = False
        for line in body.splitlines():
            m = re.match(r'^BO_\s+(\d+)\s+', line)
            if m:
                msg_id = int(m.group(1))
                if msg_id in seen_ids:
                    skip_block = True
                else:
                    seen_ids.add(msg_id)
                    skip_block = False
            elif skip_block and (line.startswith(' SG_') or line.strip() == ''):
                continue
            elif line.strip().startswith(('CM_', 'VAL_')):
                # CM_ we VAL_ setirlerini hemişe goş
                final_lines.append(line)
                continue
            if not skip_block:
                final_lines.append(line)

        merged_parts.append(f'\nCM_ "=== {desc} ({fname}) ===";\n')
        merged_parts.append('\n'.join(final_lines))
        merged_parts.append('\n')

    result = '\n'.join(merged_parts)

    # Çykyş faýly
    out_path = os.path.join(_SCRIPT_DIR, 'toyota_corolla_2017.dbc')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(result)

    msg_count = len(seen_ids)
    print(f"[OK] Birleşdirildi → {out_path}")
    print(f"     opendbc çeşme: {dbc_root}")
    print(f"     Faýllar: {[f for f,_ in source_files]}")
    print(f"     Jemi habar (BO_): {msg_count}")
    return True


if __name__ == '__main__':
    custom = None
    if '--opendbc' in sys.argv:
        idx = sys.argv.index('--opendbc')
        if idx + 1 < len(sys.argv):
            custom = sys.argv[idx + 1]

    dbc_root = find_opendbc(custom)

    if not dbc_root:
        print("ÝALŇYŞLYK: opendbc/dbc/ klasöri tapylmady!")
        print()
        print("Ulanyş:")
        print("  python merge_dbc.py --opendbc D:/opendbc-master/opendbc-master/opendbc/dbc")
        sys.exit(1)

    print(f"[opendbc] {dbc_root}")
    ok = merge_toyota_corolla_2017(dbc_root)
    sys.exit(0 if ok else 1)
