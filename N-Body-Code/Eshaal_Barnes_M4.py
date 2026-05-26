# ============================================
# M4 INDIVIDUAL TASK - 30868 - SYEDA ESHAAL GARDEZI 
# ============================================


import math
import csv
import time 
import numpy as np
from nbody_visualizer import draw_gui


# ============================================
# SIMULATION PARAMETERS
# ============================================
G = 6.67430e-11  # Gravitational constant
dt = 12000        # Time step
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
        a_x.append(0)
        a_y.append(0)
        a_z.append(0)

# ============================================
# M4 - Conversion to NumpyArrays after loading 
# ============================================

m   = np.array(m,   dtype=np.float64)
p_x = np.array(p_x, dtype=np.float64)
p_y = np.array(p_y, dtype=np.float64)
p_z = np.array(p_z, dtype=np.float64)
v_x = np.array(v_x, dtype=np.float64)
v_y = np.array(v_y, dtype=np.float64)
v_z = np.array(v_z, dtype=np.float64)
a_x = np.zeros(len(m), dtype=np.float64)
a_y = np.zeros(len(m), dtype=np.float64)
a_z = np.zeros(len(m), dtype=np.float64)
 
N = len(m)
print(f"Loaded {N} bodies")

# ============================================
# M4 - NODE POOL — NumPy arrays 
# ============================================

MAX_NODES = N * 20

node_mass    = np.zeros(MAX_NODES, dtype=np.float64)
node_com_x   = np.zeros(MAX_NODES, dtype=np.float64)
node_com_y   = np.zeros(MAX_NODES, dtype=np.float64)
node_com_z   = np.zeros(MAX_NODES, dtype=np.float64)

node_is_leaf = np.ones(MAX_NODES,  dtype=np.int32)
node_particle= np.full(MAX_NODES, -1, dtype=np.int32)

node_child   = np.full(MAX_NODES * 8, -1, dtype=np.int32)

node_xmin = np.zeros(MAX_NODES, dtype=np.float64)
node_xmax = np.zeros(MAX_NODES, dtype=np.float64)
node_ymin = np.zeros(MAX_NODES, dtype=np.float64)
node_ymax = np.zeros(MAX_NODES, dtype=np.float64)
node_zmin = np.zeros(MAX_NODES, dtype=np.float64)
node_zmax = np.zeros(MAX_NODES, dtype=np.float64)

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
# M4 - INTERACTION LIST BUILDER 
# ============================================

def build_interaction_list(body_index, root):

    bx = p_x[body_index]
    by = p_y[body_index]
    bz = p_z[body_index]
 
    result = []          # will become the interaction list
    stack  = [root]      # explicit traversal stack
 
    while stack:
        node = stack.pop()
 
        if node_mass[node] == 0.0:
            continue
 
        # Skip self-interaction: leaf node that is the current particle
        if node_is_leaf[node] and node_particle[node] == body_index:
            continue
 
        dx = node_com_x[node] - bx
        dy = node_com_y[node] - by
        dz = node_com_z[node] - bz
        dist_sq = dx*dx + dy*dy + dz*dz
 
        # Avoiding zero-distance 
        if dist_sq < 1e-20:
            continue
 
        dist  = math.sqrt(dist_sq)
        width = node_xmax[node] - node_xmin[node]


        if node_is_leaf[node] or (width / dist < theta):
            result.append(node)
        else:
            # Open this node and push all non-empty children
            base = node * 8
            for k in range(8):
                child = node_child[base + k]
                if child != -1:
                    stack.append(child)
 
    return np.array(result, dtype=np.int32)
 


# ============================================
# M4 - SCALAR FORCE KERNEL (to verify the NumPy version - correctness testing)
# ============================================

def compute_force_scalar(body_index, interaction_list):

    bx = p_x[body_index];  by = p_y[body_index];  bz = p_z[body_index]
    _ax = _ay = _az = 0.0
 
    #iterating over each node
    for node in interaction_list:          
        dx = node_com_x[node] - bx
        dy = node_com_y[node] - by
        dz = node_com_z[node] - bz
        dist_sq   = dx*dx + dy*dy + dz*dz + softening*softening
        dist_cubed = dist_sq * math.sqrt(dist_sq)
        factor    = G * node_mass[node] / dist_cubed
        _ax += factor * dx
        _ay += factor * dy
        _az += factor * dz
 
    return _ax, _ay, _az



# ============================================
# M4 - NUMPY VECTORISED FORCE KERNEL (For-loop on the interaction list replaced by whole-array operations)
# ============================================
 
def compute_force_numpy(body_index, interaction_list):

    bx = p_x[body_index]
    by = p_y[body_index]
    bz = p_z[body_index]
 
    # Fetch all node data in one indexed array access (vluxei32.v)

    cx = node_com_x[interaction_list]       # shape: (len(ilist),)
    cy = node_com_y[interaction_list]
    cz = node_com_z[interaction_list]
    nm = node_mass[interaction_list]
 
    # Displacement vectors: vfsub.vv 
    dx = cx - bx
    dy = cy - by
    dz = cz - bz
 
    # Squared distance + softening: vfmul.vv + vfmacc.vv 
    dist_sq = dx*dx + dy*dy + dz*dz + softening*softening
 
    inv_dist3 = dist_sq ** -1.5  
 
    # Force magnitude per node: vfmul.vv 
    factor = G * nm * inv_dist3             
 
    # Each np.sum collapses the whole interaction vector to one float.
    _ax = np.sum(factor * dx)
    _ay = np.sum(factor * dy)
    _az = np.sum(factor * dz)
 
    return float(_ax), float(_ay), float(_az)
 

def calculate_acceleration():
    root = build_tree()
    for i in range(N):
        ilist = build_interaction_list(i, root)
        a_x[i], a_y[i], a_z[i] = compute_force_numpy(i, ilist)


# ============================================
# M4 - CORRECTNESS TEST  (run once at startup)
# ============================================
 
def correctness_test(root, n_sample=20):

    indices = np.random.choice(N, size=min(n_sample, N), replace=False)
    errs_x, errs_y, errs_z = [], [], []
 
    for i in indices:
        ilist = build_interaction_list(i, root)
        if len(ilist) == 0:
            continue
        sx, sy, sz = compute_force_scalar(i, ilist)
        nx, ny, nz = compute_force_numpy(i, ilist)
        errs_x.append(abs(sx - nx))
        errs_y.append(abs(sy - ny))
        errs_z.append(abs(sz - nz))
 
    print("=== CORRECTNESS TEST ===")
    print(f"  Max |err| ax: {max(errs_x):.3e}")
    print(f"  Max |err| ay: {max(errs_y):.3e}")
    print(f"  Max |err| az: {max(errs_z):.3e}")
    print("  (expect < 1e-12 for identical arithmetic)")
 
 
# ============================================
# M4 - PERFORMANCE BENCHMARK
# ============================================
 
def benchmark(root, n_trials=3):

    # Pre-build all interaction lists so we time only the kernel
    lists = [build_interaction_list(i, root) for i in range(N)]
 
    # --- Scalar ---
    t0 = time.perf_counter()
    for _ in range(n_trials):
        for i in range(N):
            compute_force_scalar(i, lists[i])
    t_scalar = (time.perf_counter() - t0) / n_trials
 
    # --- NumPy ---
    t0 = time.perf_counter()
    for _ in range(n_trials):
        for i in range(N):
            compute_force_numpy(i, lists[i])
    t_numpy = (time.perf_counter() - t0) / n_trials
 
    print("=== PERFORMANCE BENCHMARK ===")
    print(f"  N = {N}")
    print(f"  Scalar : {t_scalar:.4f} s")
    print(f"  NumPy  : {t_numpy:.4f} s")
    print(f"  Speedup: {t_scalar / t_numpy:.2f}x")



# ============================================
# M4 - LEAPFROG INTEGRATION (numpy version)
# ============================================
def kick():
    global v_x, v_y, v_z
    v_x += a_x * (dt * 0.5)
    v_y += a_y * (dt * 0.5)
    v_z += a_z * (dt * 0.5)
 
def drift():
    global p_x, p_y, p_z
    p_x += v_x * dt
    p_y += v_y * dt
    p_z += v_z * dt


# ============================================
# MAIN SIMULATION LOOP
# ============================================
print("Starting Barnes-Hut simulation...")
print(f"Number of bodies: {N}")
print(f"Theta: {theta} | dt: {dt}s")

root = build_tree()
 
correctness_test(root)
benchmark(root)
 
calculate_acceleration()
 
step = 0
timing_done = False


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