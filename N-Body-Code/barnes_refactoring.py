"""
N-Body Simulation - Barnes-Hut Algorithm Implementation
This file implements the O(N log N) Barnes-Hut algorithm using octrees
"""

import math
import csv
import time 
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
MAX_NODES = N * 20

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