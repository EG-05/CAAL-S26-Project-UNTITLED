"""
N-Body Simulation - Barnes-Hut Algorithm Implementation
This file implements the O(N log N) Barnes-Hut algorithm using octrees
"""

import math
import csv
import time 
import numpy as np 
from nbody_visualizer import draw_gui

# ============================================
# SIMULATION PARAMETERS
# ============================================
G = 6.67430e-11  # Gravitational constant
dt = 6000        # Time step
softening = 1e9  # Softening parameter
theta = 0.5      # Barnes-Hut opening angle (0.5 = good balance)

# ============================================
# DATA STORAGE
# ============================================
m = []      # masses
v_x = []    # x velocities
v_y = []    # y velocities
v_z = []    # z velocities
p_x = []    # x positions
p_y = []    # y positions
p_z = []    # z positions
a_x = []    # x accelerations
a_y = []    # y accelerations
a_z = []    # z accelerations

with open('solar300.csv', mode='r') as file:
    reader = csv.DictReader(file)
    for row in reader:
        m.append(float(row["mass"]))
        p_x.append(float(row["distanceX"]))
        p_y.append(float(row["distanceY"]))
        p_z.append(float(row["distanceZ"]))
        v_x.append(float(row["velocityX"]))
        v_y.append(float(row["velocityY"]))
        v_z.append(float(row["velocityZ"]))
        a_x.append(0); 
        a_y.append(0); 
        a_z.append(0)

N = len(m)
print(f"Loaded {N} bodies")

# ============================================
# NODE POOL (ARRAY-BASED)
# ============================================
# N = len(m)
MAX_NODES = 5000 * 20

node_mass = [0.0] * MAX_NODES
node_com_x = [0.0] * MAX_NODES
node_com_y = [0.0] * MAX_NODES
node_com_z = [0.0] * MAX_NODES

node_is_leaf = [1] * MAX_NODES
node_particle = [-1] * MAX_NODES

node_child = [-1] * (MAX_NODES * 8)

node_xmin = [0.0] * MAX_NODES
node_xmax = [0.0] * MAX_NODES
node_ymin = [0.0] * MAX_NODES
node_ymax = [0.0] * MAX_NODES
node_zmin = [0.0] * MAX_NODES
node_zmax = [0.0] * MAX_NODES

node_count = 0

node_count = 0

# M4: NumPy-backed mirror arrays for O(1) gather in compute_force_numpy
# These mirror node_com_x/y/z and node_mass but as contiguous np arrays
# so NumPy can index them directly without list comprehensions
np_node_com_x = np.zeros(MAX_NODES)
np_node_com_y = np.zeros(MAX_NODES)
np_node_com_z = np.zeros(MAX_NODES)
np_node_mass  = np.zeros(MAX_NODES)

# ============================================
# HELPERS
# ============================================

def allocate_node():
    global node_count
    idx = node_count
    node_count += 1
    return idx


def get_octant(i, x, y, z):
    cx = (node_xmin[i] + node_xmax[i]) / 2
    cy = (node_ymin[i] + node_ymax[i]) / 2
    cz = (node_zmin[i] + node_zmax[i]) / 2

    octant = 0
    if x > cx: octant += 1
    if y > cy: octant += 2
    if z > cz: octant += 4
    return octant


def set_child_bounds(parent, child, octant):
    cx = (node_xmin[parent] + node_xmax[parent]) / 2
    cy = (node_ymin[parent] + node_ymax[parent]) / 2
    cz = (node_zmin[parent] + node_zmax[parent]) / 2

    node_xmin[child] = cx if (octant & 1) else node_xmin[parent]
    node_xmax[child] = node_xmax[parent] if (octant & 1) else cx

    node_ymin[child] = cy if (octant & 2) else node_ymin[parent]
    node_ymax[child] = node_ymax[parent] if (octant & 2) else cy

    node_zmin[child] = cz if (octant & 4) else node_zmin[parent]
    node_zmax[child] = node_zmax[parent] if (octant & 4) else cz


# ============================================
# INSERT BODY
# ============================================

def insert_body(i, body_index):
    x = p_x[body_index]
    y = p_y[body_index]
    z = p_z[body_index]
    mass = m[body_index]

    # update COM
    old_mass = node_mass[i]
    new_mass = old_mass + mass

    if new_mass > 0:
        node_com_x[i] = (node_com_x[i] * old_mass + x * mass) / new_mass
        node_com_y[i] = (node_com_y[i] * old_mass + y * mass) / new_mass
        node_com_z[i] = (node_com_z[i] * old_mass + z * mass) / new_mass

    node_mass[i] = new_mass

    # M4: mirror into NumPy arrays so compute_force_numpy can gather with direct
    # indexing (np_node_com_x[idx]) instead of slow list comprehensions
    np_node_mass[i]  = new_mass
    np_node_com_x[i] = node_com_x[i]
    np_node_com_y[i] = node_com_y[i]
    np_node_com_z[i] = node_com_z[i]

    # CASE 1: empty leaf
    if node_is_leaf[i] and node_particle[i] == -1:
        node_particle[i] = body_index
        return

    # CASE 2: leaf with body → subdivide
    if node_is_leaf[i]:
        old_body = node_particle[i]
        node_particle[i] = -1
        node_is_leaf[i] = 0

        oct_old = get_octant(i, p_x[old_body], p_y[old_body], p_z[old_body])

        child = allocate_node()
        node_child[i * 8 + oct_old] = child
        set_child_bounds(i, child, oct_old)

        insert_body(child, old_body)

    # CASE 3: insert new body
    octant = get_octant(i, x, y, z)
    child = node_child[i * 8 + octant]

    if child == -1:
        child = allocate_node()
        node_child[i * 8 + octant] = child
        set_child_bounds(i, child, octant)

    insert_body(child, body_index)


# ============================================
# BUILD TREE
# ============================================

# def build_tree():
#     global node_count
#     node_count = 0

#     root = allocate_node()

#     node_xmin[root] = min(p_x)
#     node_xmax[root] = max(p_x)
#     node_ymin[root] = min(p_y)
#     node_ymax[root] = max(p_y)
#     node_zmin[root] = min(p_z)
#     node_zmax[root] = max(p_z)

#     for i in range(N):
#         insert_body(root, i)

#     return root

def build_tree():
    global node_count

    for i in range(node_count):
        node_mass[i]     = 0.0
        node_com_x[i]    = 0.0
        node_com_y[i]    = 0.0
        node_com_z[i]    = 0.0
        node_is_leaf[i]  = 1
        node_particle[i] = -1
        for k in range(8):
            node_child[i * 8 + k] = -1

    node_count = 0
    root = allocate_node()

    x_min = min(p_x); x_max = max(p_x)
    y_min = min(p_y); y_max = max(p_y)
    z_min = min(p_z); z_max = max(p_z)

    # 10% padding
    max_range = max(x_max - x_min, y_max - y_min, z_max - z_min)
    padding = 0.1 * max_range
    x_min -= padding; x_max += padding
    y_min -= padding; y_max += padding
    z_min -= padding; z_max += padding

    node_xmin[root] = x_min; node_xmax[root] = x_max
    node_ymin[root] = y_min; node_ymax[root] = y_max
    node_zmin[root] = z_min; node_zmax[root] = z_max

    for i in range(N):
        insert_body(root, i)

    return root

# ============================================
# FORCE CALCULATION
# ============================================

#ORGINAL IMPLEMENTATION
def calculate_force_barnes_hut(i, body_index):
    if i == -1 or node_mass[i] == 0:
        return 0.0, 0.0, 0.0

    bx = p_x[body_index]
    by = p_y[body_index]
    bz = p_z[body_index]

    dx = node_com_x[i] - bx
    dy = node_com_y[i] - by
    dz = node_com_z[i] - bz

    dist_sq = dx*dx + dy*dy + dz*dz + softening*softening
    dist = math.sqrt(dist_sq)

    if dist < 1e-10:
        return 0.0, 0.0, 0.0

    width = node_xmax[i] - node_xmin[i]
    ratio = width / dist

    # Approximation
    if ratio < theta or node_is_leaf[i]:

        if node_is_leaf[i] and node_particle[i] == body_index:
            return 0.0, 0.0, 0.0

        dist_cubed = dist_sq * dist
        factor = G * node_mass[i] / dist_cubed

        return factor * dx, factor * dy, factor * dz

    # Recurse
    ax = ay = az = 0.0

    for k in range(8):
        child = node_child[i * 8 + k]
        if child != -1:
            cx, cy, cz = calculate_force_barnes_hut(child, body_index)
            ax += cx
            ay += cy
            az += cz

    return ax, ay, az

def calculate_acceleration():
    root = build_tree()
    for i in range(N):
        a_x[i], a_y[i], a_z[i] = calculate_force_barnes_hut(root, i)
    
#ORIGINAL IMPLEMENTATION END 

#interaction list collector  -M4
def collect_interaction_list(root, body_index):
    result = []
    stack = [root]
    bx, by, bz = p_x[body_index], p_y[body_index], p_z[body_index]

    while stack:
        i = stack.pop()
        if i == -1 or node_mass[i] == 0:
            continue

        dx = node_com_x[i] - bx
        dy = node_com_y[i] - by
        dz = node_com_z[i] - bz
        dist_sq = dx*dx + dy*dy + dz*dz + softening*softening
        dist = math.sqrt(dist_sq)

        if dist < 1e-10:
            continue

        width = node_xmax[i] - node_xmin[i]

        if (width / dist) < theta or node_is_leaf[i]:
            if node_is_leaf[i] and node_particle[i] == body_index:
                continue
            result.append(i)
        else:
            for k in range(8):
                child = node_child[i * 8 + k]
                if child != -1:
                    stack.append(child)

    return result

# def collect_interaction_list (start_node, body_index, result):

#     # EXPLICIT STACK: no more recursion limits
#     stack = [start_node]
#     # same as above
#     if node_idx == -1 or node_mass[node_idx] == 0:
#         return 
    
#     bx = p_x[body_index]
#     by = p_y[body_index]
#     bz = p_z[body_index]

#     dx = node_com_x[node_idx] - bx
#     dy = node_com_y[node_idx] - by
#     dz = node_com_z[node_idx] - bz

#     dist_sq = dx*dx + dy*dy + dz*dz + softening*softening
#     dist = math.sqrt(dist_sq)

#     if dist < 1e-10:
#         return

#     width = node_xmax[node_idx] - node_xmin[node_idx]
#     ratio = width / dist

#     # Approximation
#     if ratio < theta or node_is_leaf[node_idx]:

#         if node_is_leaf[node_idx] and node_particle[node_idx] == body_index:
#             return     #skipping leaf 
#         # dist_cubed = dist_sq * dist
#         # factor = G * node_mass[node_idx] / dist_cubed

#         result.append(node_idx) #NO computation -- collection
#         return

#         # return factor * dx, factor * dy, factor * dz

#     # Recurse
#     # ax = ay = az = 0.0

#     for k in range(8):
#         child = node_child[node_idx * 8 + k]
#         if child != -1:
#             collect_interaction_list(child, body_index, result)
#     #         ax += cx
#     #         ay += cy
#     #         az += cz
#     # return ax, ay, az

#NUMPY FORCE KERNEL - M4
def compute_force_numpy(bodyIdx, interaction_list):
    if not interaction_list:
        return 0.0, 0.0, 0.0

    idx = np.array(interaction_list, dtype=np.int32)  # one allocation

    # Direct NumPy gather — no list comprehension
    dx = np_node_com_x[idx] - p_x[bodyIdx]
    dy = np_node_com_y[idx] - p_y[bodyIdx]
    dz = np_node_com_z[idx] - p_z[bodyIdx]
    masses = np_node_mass[idx]

    dist_sq = dx*dx + dy*dy + dz*dz + softening*softening
    f = masses * dist_sq ** -1.5 * G

    return float(np.dot(f, dx)), float(np.dot(f, dy)), float(np.dot(f, dz))


# def compute_force_numpy(bodyIdx, interaction_list): 
#     if not interaction_list: 
#         return 0.0, 0.0, 0.0
    
#     idx = np.array(interaction_list)

#     cx = np.array([node_com_x[i] for i in idx])
#     cy = np.array([node_com_y[i] for i in idx])
#     cz = np.array([node_com_z[i] for i in idx])

#     dx = cx - p_x[bodyIdx]
#     dy = cy - p_y[bodyIdx]
#     dz = cz - p_z[bodyIdx]

#     mass_arr= np.array([node_mass[i] for i in idx])
#     dist_sq = dx*dx + dy*dy + dz*dz + softening*softening

#     inv_dist = dist_sq ** -1.5  #VECTORIZED, NO LOOP -- running on whole arr at once

#     #each element
#     f = G * mass_arr * inv_dist 

#     return float(np.sum(f*dx)), float(np.sum(f*dy)), float(np.sum(f*dz))


#new calculatr acceleration wiring both implementationss



def calculate_acceleration_NumPy():
    root = build_tree()
    for i in range(N):
        lst = collect_interaction_list(root, i)   #  returns list
        a_x[i], a_y[i], a_z[i] = compute_force_numpy(i, lst)

# ============================================
# LEAPFROG INTEGRATION
# ============================================
def kick():
    for i in range(N):
        v_x[i] += a_x[i] * (dt / 2.0)
        v_y[i] += a_y[i] * (dt / 2.0)
        v_z[i] += a_z[i] * (dt / 2.0)

def drift():
    for i in range(N):
        p_x[i] += v_x[i] * dt
        p_y[i] += v_y[i] * dt
        p_z[i] += v_z[i] * dt

# ============================================
# MAIN SIMULATION LOOP
# ============================================
print("Starting Barnes-Hut simulation...")
print(f"Number of bodies: {N}")
print(f"Theta: {theta} | dt: {dt}s")

calculate_acceleration()
step = 0
timing_done = False


#-----------------------------------------------------------------------------------------
# M4 BENCHMARK + CORRECTNESS

# --- Correctness: max absolute acceleration error scalar vs NumPy ---
print("\n--- M4 Correctness Check ---")
calculate_acceleration()                    #ORGINAL SCALE
ax_s, ay_s, az_s = a_x[:], a_y[:], a_z[:] # snapshot scalar result

calculate_acceleration_NumPy()              # numpy version
err = max(abs(ax_s[i] - a_x[i]) for i in range(N))
print(f"Max absolute error: {err:.2e}")

# --- Correctness: centre-of-mass conservation over 5 leapfrog steps ---
# COM must not drift — no external forces in the system
def centre_of_mass():
    total_m = sum(m)
    cx = sum(m[i]*p_x[i] for i in range(N)) / total_m
    cy = sum(m[i]*p_y[i] for i in range(N)) / total_m
    cz = sum(m[i]*p_z[i] for i in range(N)) / total_m
    return cx, cy, cz

def total_kinetic_energy():
    # KE only — PE is O(N^2), too slow for a quick conservation check
    return 0.5 * sum(m[i]*(v_x[i]**2 + v_y[i]**2 + v_z[i]**2) for i in range(N))

print("\n--- Centre-of-Mass & Energy Conservation (5 steps, NumPy path) ---")
com0 = centre_of_mass()
ke0  = total_kinetic_energy()
for _ in range(5):
    kick(); drift(); calculate_acceleration_NumPy(); kick()
com1 = centre_of_mass()
ke1  = total_kinetic_energy()
print(f"COM drift: dx={com1[0]-com0[0]:.3e}  dy={com1[1]-com0[1]:.3e}  dz={com1[2]-com0[2]:.3e}")
print(f"KE change: {abs(ke1-ke0)/max(ke0,1e-30)*100:.4f}%")

# --- Benchmark: one row per available CSV file ---
# M4: loop over all solar/cluster files — only times the force calculation,
# not tree build, to isolate scalar vs NumPy kernel difference
FILES = [
    'solar100.csv',
    'solar300.csv',
    'cluster500.csv',
    'cluster1000.csv',
    'cluster5000.csv',
]

print(f"\n M4 Benchmark")
print(f"{'File':<22} {'N':<6} {'Scalar (s)':<14} {'NumPy (s)':<13} {'Speedup'}")
print("-" * 62)

for fname in FILES:
    try:
        # M4: load each file into temp lists, swap globals, time both, restore
        tmp_m, tmp_px, tmp_py, tmp_pz = [], [], [], []
        tmp_vx, tmp_vy, tmp_vz = [], [], []
        with open(fname, mode='r') as f:
            rdr = csv.DictReader(f)
            for row in rdr:
                tmp_m.append(float(row["mass"]))
                tmp_px.append(float(row["distanceX"]))
                tmp_py.append(float(row["distanceY"]))
                tmp_pz.append(float(row["distanceZ"]))
                tmp_vx.append(float(row["velocityX"]))
                tmp_vy.append(float(row["velocityY"]))
                tmp_vz.append(float(row["velocityZ"]))

        n_file = len(tmp_m)

        # snapshot originals so GUI simulation is unaffected after benchmarking
        orig_N  = N
        orig_m  = m[:]
        orig_px = p_x[:]; orig_py = p_y[:]; orig_pz = p_z[:]
        orig_vx = v_x[:]; orig_vy = v_y[:]; orig_vz = v_z[:]
        orig_ax = a_x[:]; orig_ay = a_y[:]; orig_az = a_z[:]

        # swap in file data
        globals()['N'] = n_file
        m[:] = tmp_m
        p_x[:] = tmp_px; p_y[:] = tmp_py; p_z[:] = tmp_pz
        v_x[:] = tmp_vx; v_y[:] = tmp_vy; v_z[:] = tmp_vz
        # resize acceleration lists to match new N
        a_x.clear(); a_y.clear(); a_z.clear()
        a_x.extend([0.0]*n_file); a_y.extend([0.0]*n_file); a_z.extend([0.0]*n_file)

        t0 = time.perf_counter()
        calculate_acceleration()        # scalar
        t_scalar = time.perf_counter() - t0

        t0 = time.perf_counter()
        calculate_acceleration_NumPy()  # numpy
        t_numpy = time.perf_counter() - t0

        speedup = t_scalar / t_numpy if t_numpy > 0 else float('inf')
        print(f"{fname:<22} {n_file:<6} {t_scalar:<14.4f} {t_numpy:<13.4f} {speedup:.2f}x")

        # restore original data so GUI runs correctly
        globals()['N'] = orig_N
        m[:] = orig_m
        p_x[:] = orig_px; p_y[:] = orig_py; p_z[:] = orig_pz
        v_x[:] = orig_vx; v_y[:] = orig_vy; v_z[:] = orig_vz
        a_x.clear(); a_y.clear(); a_z.clear()
        a_x.extend(orig_ax); a_y.extend(orig_ay); a_z.extend(orig_az)

    except FileNotFoundError:
        print(f"{fname:<22} NOT FOUND — skipped")

#-----------------------------------------------------------------------------------------

while draw_gui(p_x, p_y, p_z):
    kick()
    drift()
    if step == 1 and not timing_done:
        start = time.time()
        calculate_acceleration()
        end = time.time()
        print(f"N={N} | Barnes-Hut time: {end - start:.4f}s")
        timing_done = True

    else:
        calculate_acceleration()
    kick()
    step += 1
    if step % 100 == 0:
        print(f"Step {step}")

print("Simulation complete")