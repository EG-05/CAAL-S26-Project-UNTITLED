"""
N-Body Simulation - Barnes-Hut Algorithm Implementation
This file implements the O(N log N) Barnes-Hut algorithm using octrees
"""

import math
import csv
import time 
import numpy as np

# ============================================
# SIMULATION PARAMETERS
# ============================================
G = 6.67430e-11  # Gravitational constant
dt = 6000        # Time step
softening = 1e9  # Softening parameter
theta = 0.5      # Barnes-Hut opening angle (0.5 = good balance)

# # ============================================
# # DATA STORAGE
# # ============================================
# m = []      # masses
# v_x = []    # x velocities
# v_y = []    # y velocities
# v_z = []    # z velocities
# p_x = []    # x positions
# p_y = []    # y positions
# p_z = []    # z positions
# a_x = []    # x accelerations
# a_y = []    # y accelerations
# a_z = []    # z accelerations

# with open('solar300.csv', mode='r') as file:
#     reader = csv.DictReader(file)
#     for row in reader:
#         m.append(float(row["mass"]))
#         p_x.append(float(row["distanceX"]))
#         p_y.append(float(row["distanceY"]))
#         p_z.append(float(row["distanceZ"]))
#         v_x.append(float(row["velocityX"]))
#         v_y.append(float(row["velocityY"]))
#         v_z.append(float(row["velocityZ"]))
#         a_x.append(0); 
#         a_y.append(0); 
#         a_z.append(0)

# N = len(m)
# print(f"Loaded {N} bodies")

# # ============================================
# # NODE POOL (ARRAY-BASED)
# # ============================================
# # N = len(m)
# MAX_NODES = N * 20

# # node_mass = [0.0] * MAX_NODES
# # node_com_x = [0.0] * MAX_NODES
# # node_com_y = [0.0] * MAX_NODES
# # node_com_z = [0.0] * MAX_NODES

# # node_is_leaf = [1] * MAX_NODES
# # node_particle = [-1] * MAX_NODES

# # node_child = [-1] * (MAX_NODES * 8)

# # node_xmin = [0.0] * MAX_NODES
# # node_xmax = [0.0] * MAX_NODES
# # node_ymin = [0.0] * MAX_NODES
# # node_ymax = [0.0] * MAX_NODES
# # node_zmin = [0.0] * MAX_NODES
# # node_zmax = [0.0] * MAX_NODES

# # node_count = 0

# node_mass = np.zeros(MAX_NODES, dtype=np.float64)
# node_com_x = np.zeros(MAX_NODES, dtype=np.float64)
# node_com_y = np.zeros(MAX_NODES, dtype=np.float64)
# node_com_z = np.zeros(MAX_NODES, dtype=np.float64)

# node_is_leaf = np.ones(MAX_NODES, dtype=np.int32)
# node_particle = np.full(MAX_NODES, -1, dtype=np.int32)

# node_child = np.full(MAX_NODES * 8, -1, dtype=np.int32)

# node_xmin = np.zeros(MAX_NODES, dtype=np.float64)
# node_xmax = np.zeros(MAX_NODES, dtype=np.float64)
# node_ymin = np.zeros(MAX_NODES, dtype=np.float64)
# node_ymax = np.zeros(MAX_NODES, dtype=np.float64)
# node_zmin = np.zeros(MAX_NODES, dtype=np.float64)
# node_zmax = np.zeros(MAX_NODES, dtype=np.float64)

# node_count = 0

def init_simulation(filename):
    global m, p_x, p_y, p_z, v_x, v_y, v_z, a_x, a_y, a_z
    global N, MAX_NODES, node_count
    global node_mass, node_com_x, node_com_y, node_com_z
    global node_is_leaf, node_particle, node_child
    global node_xmin, node_xmax, node_ymin, node_ymax, node_zmin, node_zmax

    m = []; p_x = []; p_y = []; p_z = []
    v_x = []; v_y = []; v_z = []
    a_x = []; a_y = []; a_z = []

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
            a_x.append(0.0)
            a_y.append(0.0)
            a_z.append(0.0)

    N = len(m)
    MAX_NODES = N * 20
    node_count = 0

    node_mass    = np.zeros(MAX_NODES, dtype=np.float64)
    node_com_x   = np.zeros(MAX_NODES, dtype=np.float64)
    node_com_y   = np.zeros(MAX_NODES, dtype=np.float64)
    node_com_z   = np.zeros(MAX_NODES, dtype=np.float64)
    node_is_leaf = np.ones(MAX_NODES,  dtype=np.int32)
    node_particle= np.full(MAX_NODES, -1, dtype=np.int32)
    node_child   = np.full(MAX_NODES * 8, -1, dtype=np.int32)
    node_xmin    = np.zeros(MAX_NODES, dtype=np.float64)
    node_xmax    = np.zeros(MAX_NODES, dtype=np.float64)
    node_ymin    = np.zeros(MAX_NODES, dtype=np.float64)
    node_ymax    = np.zeros(MAX_NODES, dtype=np.float64)
    node_zmin    = np.zeros(MAX_NODES, dtype=np.float64)
    node_zmax    = np.zeros(MAX_NODES, dtype=np.float64)

    #print(f"Loaded {N} bodies from {filename}")

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
# FORCE CALCULATION - numpy
# ============================================


def col_interaction_list(i, body_index, interaction_list):
    # base case: if index -1 or mass[i] = 0 which mean zero gravity
    if i == -1 or node_mass[i] == 0:
        return

    bx = p_x[body_index]
    by = p_y[body_index]
    bz = p_z[body_index]

    dx = node_com_x[i] - bx
    dy = node_com_y[i] - by
    dz = node_com_z[i] - bz

    dist_sq = dx*dx + dy*dy + dz*dz + softening*softening
    dist = math.sqrt(dist_sq)

    if dist < 1e-10:
        return
    
    width = node_xmax[i] - node_xmin[i]
    ratio = width/dist

    if ratio < theta or node_is_leaf[i]:    # if node < theta meaning node far away, dont look at its children and append node[i]
        if node_is_leaf[i] and node_particle[i] == body_index: # no children
            return
        interaction_list.append(i)
        return
    for k in range(8):                      # if node too close + not a leaf -> function recursively goes deep into each octreee
        child = node_child[i * 8 + k]
        if child != -1:
            col_interaction_list(child, body_index, interaction_list)

def col_interaction_list_iterative(body_index, root, interaction_list):
    stack = [root]

    bx = p_x[body_index]
    by = p_y[body_index]
    bz = p_z[body_index]

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
        ratio = width/dist

        if ratio < theta or bool(node_is_leaf[i]):    # if node < theta meaning node far away, dont look at its children and append node[i]
            if bool(node_is_leaf[i]) and node_particle[i] == body_index: # no children
                continue
            interaction_list.append(i)
            
        else:
            for k in range(8):                      # if node too close + not a leaf -> function recursively goes deep into each octreee
                child = node_child[i * 8 + k]
                if child != -1:
                    stack.append(child)

def calculate_force_numpy(body_index, interaction_list):
    if len(interaction_list) == 0:
        return 0.0, 0.0, 0.0
    il = np.asarray(interaction_list, dtype=np.int32)   # optimised int vector
    dx = node_com_x[il] - p_x[body_index]
    dy = node_com_y[il] - p_y[body_index]
    dz = node_com_z[il] - p_z[body_index]
    masses = node_mass[il]
    dist_sq = dx*dx + dy*dy + dz*dz + softening*softening
    ind_dist = dist_sq ** -1.5              # dist^-3 = (dist^2)^-1.5 because F * deltax / m1
    f = G * masses *ind_dist
    return float(np.sum(f * dx)), float(np.sum(f * dy)), float(np.sum(f * dz))

def calculate_acceleration_numpy():
    root = build_tree()
    for i in range(N):
        il = []
        # col_interaction_list(root, i, il)
        col_interaction_list_iterative(i, root, il)
        a_x[i], a_y[i], a_z[i] = calculate_force_numpy(i, il)

# ============================================
# FORCE CALCULATION - scalar
# ============================================

def calculate_force_barnes_hut_scalar(i, body_index):
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
            cx, cy, cz = calculate_force_barnes_hut_scalar(child, body_index)
            ax += cx
            ay += cy
            az += cz

    return ax, ay, az

import numpy as np

def calculate_acceleration_scalar():
    root = build_tree()
    for i in range(N):
        a_x[i], a_y[i], a_z[i] = calculate_force_barnes_hut_scalar(root, i)

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
# print("\nRunning correctness check...")
# print(f"Number of bodies: {N}")
# print(f"Theta: {theta} | dt: {dt}s")
 
# calculate_acceleration_scalar()
# ax_scalar = a_x[:]
# ay_scalar = a_y[:]
# az_scalar = a_z[:]
 
# calculate_acceleration_numpy()
# ax_numpy = a_x[:]
# ay_numpy = a_y[:]
# az_numpy = a_z[:]
 
# max_err_x = max(abs(ax_scalar[i] - ax_numpy[i]) for i in range(N))
# max_err_y = max(abs(ay_scalar[i] - ay_numpy[i]) for i in range(N))
# max_err_z = max(abs(az_scalar[i] - az_numpy[i]) for i in range(N))
 
# print(f"Max absolute error ax: {max_err_x:.2e}")
# print(f"Max absolute error ay: {max_err_y:.2e}")
# print(f"Max absolute error az: {max_err_z:.2e}")

# print("\nRunning benchmark...")
# print(f"{'N':<8} {'Scalar (s)':<14} {'NumPy (s)':<14} {'Speedup':<10}")
# print("-" * 46)

# # scalar
# start = time.perf_counter()
# calculate_acceleration_scalar()
# scalar_time = time.perf_counter() - start

# # numpy
# start = time.perf_counter()
# calculate_acceleration_numpy()
# numpy_time = time.perf_counter() - start

# speedup = scalar_time / numpy_time if numpy_time > 0 else float('inf')
# print(f"{N:<8} {scalar_time:<14.4f} {numpy_time:<14.4f} {speedup:<10.2f}x")

if __name__ == "__main__":
    init_simulation('solar300.csv')
    
    print("\nRunning correctness check...")
    print(f"Number of bodies: {N}")
    print(f"Theta: {theta} | dt: {dt}s")
    
    calculate_acceleration_scalar()
    ax_scalar = a_x[:]
    ay_scalar = a_y[:]
    az_scalar = a_z[:]
    
    calculate_acceleration_numpy()
    ax_numpy = a_x[:]
    ay_numpy = a_y[:]
    az_numpy = a_z[:]
    
    max_err_x = max(abs(ax_scalar[i] - ax_numpy[i]) for i in range(N))
    max_err_y = max(abs(ay_scalar[i] - ay_numpy[i]) for i in range(N))
    max_err_z = max(abs(az_scalar[i] - az_numpy[i]) for i in range(N))
    
    print(f"Max absolute error ax: {max_err_x:.2e}")
    print(f"Max absolute error ay: {max_err_y:.2e}")
    print(f"Max absolute error az: {max_err_z:.2e}")

    print("\nRunning benchmark...")
    print(f"{'N':<8} {'Scalar (s)':<14} {'NumPy (s)':<14} {'Speedup':<10}")
    print("-" * 46)

    start = time.perf_counter()
    calculate_acceleration_scalar()
    scalar_time = time.perf_counter() - start

    start = time.perf_counter()
    calculate_acceleration_numpy()
    numpy_time = time.perf_counter() - start

    speedup = scalar_time / numpy_time if numpy_time > 0 else float('inf')
    print(f"{N:<8} {scalar_time:<14.4f} {numpy_time:<14.4f} {speedup:<10.2f}x")