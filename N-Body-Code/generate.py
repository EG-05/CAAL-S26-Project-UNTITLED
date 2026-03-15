import csv

# Configuration
INPUT_FILE = 'solar300.csv'
OUTPUT_FILE = 'mydata.S'  # Output assembly file
N = 300  # Number of particles

# storage for columns
mass = []
px, py, pz = [], [], []
vx, vy, vz = [], [], []

try:
    with open(INPUT_FILE, 'r') as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            if count >= N: 
                break
            
            # Parse and store in lists
            mass.append(row['mass'])
            
            px.append(row['distanceX'])
            py.append(row['distanceY'])
            pz.append(row['distanceZ'])
            
            vx.append(row['velocityX'])
            vy.append(row['velocityY'])
            vz.append(row['velocityZ'])
            
            count += 1
            
    # Pad with zeros if CSV has fewer than N lines
    while count < N:
        mass.append("0.0")
        for lst in [px, py, pz, vx, vy, vz]: 
            lst.append("0.0")
        count += 1

except FileNotFoundError:
    print(f"Error: Could not find {INPUT_FILE}")
    exit()

def write_block(f, label, data_lists):
    f.write(f"{label}:\n")
    # Loop through the lists (e.g., first px, then py, then pz)
    for data_list in data_lists:
        f.write(f"    # --- Component Block ({len(data_list)} values) ---\n")
        # Print in chunks of 5 values per line for readability
        for i in range(0, len(data_list), 5):
            chunk = data_list[i:i+5]
            f.write(f"    .float {', '.join(chunk)}\n")

# --- WRITE THE ASSEMBLY CODE TO FILE ---
try:
    with open(OUTPUT_FILE, 'w') as f:
        f.write(f"# Generated Data Section for N={N}\n")
        f.write(".global G\n")
        f.write("G: .float 6.67430e-11\n\n")

        # 1. Position Grid (Must be X block, then Y block, then Z block)
        write_block(f, "p_x", [px])
        f.write("\n")
        write_block(f, "p_y", [py])
        f.write("\n")
        write_block(f, "p_z", [pz])
        f.write("\n")

        # 2. Mass Grid (Just one block of masses)
        write_block(f, "mass_grid", [mass])
        f.write("\n")

        # 3. Velocity Grid (X block, then Y block, then Z block)
        write_block(f, "v_x", [vx])
        f.write("\n")
        write_block(f, "v_y", [vy])
        f.write("\n")
        write_block(f, "v_z", [vz])
        f.write("\n")

        # 4. Acceleration Grid (Initialize to zero)
        f.write("a_x:\n")
        f.write(f"    .rept {N}\n")
        f.write("    .float 0.0\n")
        f.write("    .endr\n")
        
        f.write("a_y:\n")
        f.write(f"    .rept {N}\n")
        f.write("    .float 0.0\n")
        f.write("    .endr\n")
        
        f.write("a_z:\n")
        f.write(f"    .rept {N}\n")
        f.write("    .float 0.0\n")
        f.write("    .endr\n")
    
    print(f"Successfully wrote assembly data to {OUTPUT_FILE}")
    print(f"Generated {N} particles")
    
except IOError as e:
    print(f"Error writing to {OUTPUT_FILE}: {e}")
    exit()