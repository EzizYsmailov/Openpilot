
import os
import glob
import cantools

dbc_dir = 'dbc_files'
files = glob.glob(os.path.join(dbc_dir, '*.dbc'))
print(f"Checking {len(files)} DBC files...")

for f in files:
    try:
        db = cantools.db.load_file(f, strict=False)
        msg_names = {m.name for m in db.messages}
        
        has_steer = 'STEERING_LKA' in msg_names or 'STEERING_CONTROL' in msg_names
        has_acc   = 'ACC_CONTROL' in msg_names or 'ACCEL_COMMAND' in msg_names
        
        if has_steer or has_acc:
            print(f"MATCH: {os.path.basename(f)}")
            if has_steer: print("  - Has STEERING")
            if has_acc:   print("  - Has ACCEL")
            
    except Exception as e:
        # print(f"Error loading {os.path.basename(f)}: {e}")
        pass
