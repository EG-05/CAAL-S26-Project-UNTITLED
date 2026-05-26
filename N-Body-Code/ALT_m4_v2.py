"""
N-Body Simulation - Barnes-Hut Algorithm Implementation
This file implements the O(N log N) Barnes-Hut algorithm using octrees

M4: Scalar vs NumPy comparison with explicit-stack tree traversal
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

N = 0
MAX_NODES = 0
node_count = 0

# Node pool arrays (allocated per load)
node_mass = []
node_com_x = []
node_com_y = []
node_com_z = []
node_is_leaf = []
node_particle = []
node_child = []
node_xmin = []
node_xmax = []
node_ymin = []
node_ymax = []
node_zmin = []
node_zmax = []

# ============================================
# FILES TO BENCHMARK
# ============================================
FILES = [
    'solar100.csv',
    'solar300.csv',
    'cluster500.csv',
    'cluster1000.csv',
    'cluster5000.csv',
]

# ============================================
# LOAD FILE
# ============================================
def load_file(filename):
    global m, p_x, p_y, p_z, v_x, v_y, v_z, a_x, a_y, a_z
    global N, MAX_NODES
    global node_mass, node_com_x, node_com_y, node_com_z
    global node_is_leaf, node_particle, node_child
    global node_xmin, node_xmax, node_ymin, node_ymax, node_zmin, node_zmax
    global node_count

    m=[]; p_x=[]; p_y=[]; p_z=[]
    v_x=[]; v_y=[]; v_z=[]
    a_x=[]; a_y=[]; a_z=[]

    with open(filename, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            m.append(float(row["mass"]))
            p_x.append(float(row["distanceX"]))
            p_y.append(float(row["distanceY"]))
            p_z.append(float(row["distanceZ"]))
            v_x.append(float(row["velocityX"]))
            v_y.append(float(row["velocityY"]))
            v_z.append(float(row["velocityZ"]))
            a_x.append(0.0); a_y.append(0.0); a_z.append(0.0)

    N = len(m)
    MAX_NODES = N * 20
    reset_pool()


def reset_pool():
    global node_mass, node_com_x, node_com_y, node_com_z
    global node_is_leaf, node_particle, node_child
    global node_xmin, node_xmax, node_ymin, node_ymax, node_zmin, node_zmax
    global node_count

    node_mass    = [0.0] * MAX_NODES
    node_com_x   = [0.0] * MAX_NODES
    node_com_y   = [0.0] * MAX_NODES
    node_com_z   = [0.0] * MAX_NODES
    node_is_leaf = [1]   * MAX_NODES
    node_particle= [-1]  * MAX_NODES
    node_child   = [-1]  * (MAX_NODES * 8)
    node_xmin    = [0.0] * MAX_NODES
    node_xmax    = [0.0] * MAX_NODES
    node_ymin    = [0.0] * MAX_NODES
    node_ymax    = [0.0] * MAX_NODES
    node_zmin    = [0.0] * MAX_NODES
    node_zmax    = [0.0] * MAX_NODES
    node_count   = 0


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
# SCALAR FORCE CALCULATION (ORIGINAL — recursive)
# ============================================

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
    
# ============================================
# NUMPY FORCE — BATCH GROUP TRAVERSAL
# ============================================
# KEY IDEA: Instead of walking the tree N times (once per body),
# walk it ONCE and process ALL N bodies at each node simultaneously.
#
# At each tree node:
#   1. Compute distance from node COM to ALL bodies (vectorized NumPy)
#   2. Bodies where width/dist < theta → accumulate force (vectorized)
#   3. Bodies where width/dist >= theta → push to children
#
# This makes the heavy math (sqrt, divisions, multiplications) fully
# vectorized over large arrays instead of doing them one body at a time.

def calculate_acceleration_NumPy():
    """
    Batch/group Barnes-Hut: traverse tree once, process all bodies
    simultaneously at each node using vectorized NumPy operations.
    """
    root = build_tree()

    # Convert body positions to NumPy arrays
    bx = np.array(p_x, dtype=np.float64)
    by = np.array(p_y, dtype=np.float64)
    bz = np.array(p_z, dtype=np.float64)

    # Accumulator arrays for acceleration
    ax_arr = np.zeros(N, dtype=np.float64)
    ay_arr = np.zeros(N, dtype=np.float64)
    az_arr = np.zeros(N, dtype=np.float64)

    soft_sq = softening * softening

    # Stack holds (node_index, body_indices_array)
    # Start: ALL bodies interact with root node
    all_bodies = np.arange(N, dtype=np.int32)
    stack = [(root, all_bodies)]

    while stack:
        node_idx, bodies = stack.pop()

        if node_idx == -1 or node_mass[node_idx] == 0 or len(bodies) == 0:
            continue

        # --- Vectorized: distance from ALL bodies to this node's COM ---
        dx = node_com_x[node_idx] - bx[bodies]
        dy = node_com_y[node_idx] - by[bodies]
        dz = node_com_z[node_idx] - bz[bodies]

        dist_sq = dx*dx + dy*dy + dz*dz + soft_sq
        dist = np.sqrt(dist_sq)

        # Skip bodies at essentially zero distance
        valid = dist > 1e-10

        if node_is_leaf[node_idx]:
            # LEAF NODE: compute force for all valid bodies (except self)
            particle = node_particle[node_idx]

            if particle >= 0:
                # Exclude the body that IS this particle (self-interaction)
                self_mask = bodies == particle
                valid = valid & ~self_mask

            if np.any(valid):
                v_bodies = bodies[valid]
                vdx = dx[valid]
                vdy = dy[valid]
                vdz = dz[valid]
                vdist_sq = dist_sq[valid]
                vdist = dist[valid]

                # Vectorized force: F = G * M / r^3 * dr
                dist_cubed = vdist_sq * vdist
                factor = G * node_mass[node_idx] / dist_cubed

                ax_arr[v_bodies] += factor * vdx
                ay_arr[v_bodies] += factor * vdy
                az_arr[v_bodies] += factor * vdz

        else:
            # INTERNAL NODE: split bodies into "use approx" vs "recurse"
            width = node_xmax[node_idx] - node_xmin[node_idx]
            ratio = width / dist  # vectorized ratio for all bodies

            use_approx = valid & (ratio < theta)
            need_recurse = valid & ~use_approx

            # --- Bodies that CAN use the monopole approximation ---
            if np.any(use_approx):
                a_bodies = bodies[use_approx]
                adx = dx[use_approx]
                ady = dy[use_approx]
                adz = dz[use_approx]
                adist_sq = dist_sq[use_approx]
                adist = dist[use_approx]

                dist_cubed = adist_sq * adist
                factor = G * node_mass[node_idx] / dist_cubed

                ax_arr[a_bodies] += factor * adx
                ay_arr[a_bodies] += factor * ady
                az_arr[a_bodies] += factor * adz

            # --- Bodies that MUST recurse into children ---
            if np.any(need_recurse):
                recurse_bodies = bodies[need_recurse]
                base = node_idx * 8
                for k in range(8):
                    child = node_child[base + k]
                    if child != -1:
                        stack.append((child, recurse_bodies))

    # Write results back to the acceleration lists
    for i in range(N):
        a_x[i] = float(ax_arr[i])
        a_y[i] = float(ay_arr[i])
        a_z[i] = float(az_arr[i])


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
# M4 BENCHMARK + CORRECTNESS
# ============================================

import sys
sys.setrecursionlimit(50000)  # for large N scalar recursion

print("=" * 70)
print("  M4 BENCHMARK — Scalar (recursive) vs NumPy (explicit stack)")
print("=" * 70)

# --- Correctness check on first available file ---
print("\n--- Correctness Check (solar100.csv) ---")
load_file('solar100.csv')

calculate_acceleration()  # scalar
ax_s = a_x[:]; ay_s = a_y[:]; az_s = a_z[:]

calculate_acceleration_NumPy()  # numpy + stack
err_x = max(abs(ax_s[i] - a_x[i]) for i in range(N))
err_y = max(abs(ay_s[i] - a_y[i]) for i in range(N))
err_z = max(abs(az_s[i] - a_z[i]) for i in range(N))
print(f"Max absolute error — ax: {err_x:.2e}  ay: {err_y:.2e}  az: {err_z:.2e}")
print()

# --- Benchmark table across all files ---
print(f"{'File':<20} {'N':<6} {'Scalar (s)':<14} {'NumPy (s)':<13} {'Speedup'}")
print("-" * 65)

# Use the first file to warm up JIT / caches
load_file('solar100.csv')
calculate_acceleration()
calculate_acceleration_NumPy()

for fname in FILES:
    try:
        load_file(fname)

        # Scalar (recursive)
        t0 = time.perf_counter()
        calculate_acceleration()
        t_scalar = time.perf_counter() - t0

        # NumPy (explicit stack + vectorized force)
        t0 = time.perf_counter()
        calculate_acceleration_NumPy()
        t_numpy = time.perf_counter() - t0

        speedup = t_scalar / t_numpy if t_numpy > 0 else float('inf')
        print(f"{fname:<20} {N:<6} {t_scalar:<14.4f} {t_numpy:<13.4f} {speedup:.2f}x")

    except FileNotFoundError:
        print(f"{fname:<20} FILE NOT FOUND — skipping")
    except RecursionError:
        print(f"{fname:<20} {N:<6} RECURSION LIMIT HIT (N too large for scalar)")

print()
print("=" * 70)

# ============================================
# MAIN SIMULATION LOOP (uses NumPy version)
# ============================================
# Load default file for simulation
load_file('solar300.csv')
print(f"\nStarting Barnes-Hut simulation with {N} bodies...")
print(f"Theta: {theta} | dt: {dt}s")

calculate_acceleration_NumPy()
step = 0

while draw_gui(p_x, p_y, p_z):
    kick()
    drift()
    calculate_acceleration_NumPy()
    kick()
    step += 1
    if step % 100 == 0:
        print(f"Step {step}")

print("Simulation complete")