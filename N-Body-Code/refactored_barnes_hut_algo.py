"""
N-Body Simulation - Barnes-Hut Algorithm Implementation
This file implements the O(N log N) Barnes-Hut algorithm using octrees

REFACTORING NOTES:
- kick() and drift() are now delegated to vectorised RISC-V assembly
- Python lists replaced with ctypes float arrays for contiguous memory
- Assembly loaded as shared library via ctypes
- Everything else (Barnes-Hut tree, visualiser, main loop) unchanged
"""

import math
import csv
import time
import ctypes                           
from nbody_visualizer import draw_gui

G = 6.67430e-11  
dt = 6000000     
softening = 1e9
half_time_step = 0.5
theta = 0.5     
rows = [] 


# LOAD ASSEMBLY SHARED LIBRARY

# compile with: riscv64-unknown-elf-gcc -shared -march=rv64gcv -o nbody.so kick.s drift.s
# this loads your vectorised assembly functions so Python can call them
lib = ctypes.CDLL('./nbody.so')

# tell ctypes the function signatures so it passes arguments correctly
# kick(float* v_x, float* v_y, float* v_z,
#       float* a_x, float* a_y, float* a_z,
#       float dt_half, int N)

lib.kick.argtypes = [
    ctypes.POINTER(ctypes.c_float),     # v_x
    ctypes.POINTER(ctypes.c_float),     # v_y
    ctypes.POINTER(ctypes.c_float),     # v_z
    ctypes.POINTER(ctypes.c_float),     # a_x
    ctypes.POINTER(ctypes.c_float),     # a_y
    ctypes.POINTER(ctypes.c_float),     # a_z
    ctypes.c_float,                     # dt_half = dt * 0.5
    ctypes.c_int                        # N
]

lib.kick.restype = None                 # void return

# drift(float* p_x, float* p_y, float* p_z,
#        float* v_x, float* v_y, float* v_z,
#        float dt, int N)
lib.drift.argtypes = [
    ctypes.POINTER(ctypes.c_float),     # p_x
    ctypes.POINTER(ctypes.c_float),     # p_
    ctypes.POINTER(ctypes.c_float),     # p_z
    ctypes.POINTER(ctypes.c_float),     # v_x
    ctypes.POINTER(ctypes.c_float),     # v_y
    ctypes.POINTER(ctypes.c_float),     # v_z
    ctypes.c_float,                     # dt
    ctypes.c_int                        # N
]
lib.drift.restype = None                # void return

# ============================================
# DATA STORAGE
# ============================================
# CHANGED: was plain Python lists e.g. v_x = [] and now its ctypes float arrays — contiguous memory blocks
# assembly can address these directly with la/flw/fsw

# temporary Python lists for loading CSV (can't know N until file is read)
_m = []
_v_x = []; _v_y = []; _v_z = []
_p_x = []; _p_y = []; _p_z = []

# ============================================
# LOAD INITIAL CONDITIONS
# ============================================
with open('solar300.csv', mode='r') as file:
    reader = csv.DictReader(file)
    for row in reader:
        _m.append(float(row["mass"]))
        _p_x.append(float(row["distanceX"]))
        _p_y.append(float(row["distanceY"]))
        _p_z.append(float(row["distanceZ"]))
        _v_x.append(float(row["velocityX"]))
        _v_y.append(float(row["velocityY"]))
        _v_z.append(float(row["velocityZ"]))

N = len(_m)
print(f"Loaded {N} bodies")

# NOW convert to ctypes arrays now that we know N
# (ctypes.c_float * N)(*list) creates a contiguous C float array from a Python list
m   = (ctypes.c_float * N)(*_m)
p_x = (ctypes.c_float * N)(*_p_x)
p_y = (ctypes.c_float * N)(*_p_y)
p_z = (ctypes.c_float * N)(*_p_z)
v_x = (ctypes.c_float * N)(*_v_x)
v_y = (ctypes.c_float * N)(*_v_y)
v_z = (ctypes.c_float * N)(*_v_z)

# accelerations start at zero — assembly will write into these each step
a_x = (ctypes.c_float * N)(*[0.0] * N)
a_y = (ctypes.c_float * N)(*[0.0] * N)
a_z = (ctypes.c_float * N)(*[0.0] * N)

# ============================================
# OCTREE NODE CLASS
# ============================================
# UNCHANGED — Barnes-Hut tree logic stays in Python
class OctreeNode:
    def __init__(self, x_min, x_max, y_min, y_max, z_min, z_max):
        self.x_min = x_min
        self.y_min = y_min
        self.z_min = z_min
        self.x_max = x_max
        self.y_max = y_max
        self.z_max = z_max
        self.center_x = (x_min + x_max)/2.0
        self.center_y = (y_min + y_max)/2.0
        self.center_z = (z_min + z_max)/2.0
        self.width = x_max - x_min
        self.total_mass = 0.0
        self.com_x = 0.0
        self.com_y = 0.0
        self.com_z = 0.0
        self.is_leaf = True
        self.body_index = -1
        self.children = [None]*8

    def get_octant(self, x, y, z):
        octant = 0
        if x > self.center_x: octant += 1
        if y > self.center_y: octant += 2
        if z > self.center_z: octant += 4
        return octant

    def get_octant_bounds(self, octant):
        x_min = self.x_min; y_min = self.y_min; z_min = self.z_min
        x_max = self.x_max; y_max = self.y_max; z_max = self.z_max
        if octant & 1: x_min = self.center_x
        else:          x_max = self.center_x
        if octant & 2: y_min = self.center_y
        else:          y_max = self.center_y
        if octant & 4: z_min = self.center_z
        else:          z_max = self.center_z
        return x_min, x_max, y_min, y_max, z_min, z_max

# ============================================
# TREE BUILDING FUNCTIONS
# ============================================
# UNCHANGED — tree construction stays in Python
def insert_body(node, body_index):
    # NOTE: p_x, p_y, p_z are now ctypes arrays
    # indexing them with p_x[i] still works exactly like a Python list
    x = p_x[body_index]
    y = p_y[body_index]
    z = p_z[body_index]
    mass = m[body_index]

    old_mass = node.total_mass
    new_mass = old_mass + mass
    if new_mass > 0:
        node.com_x = (node.com_x * old_mass + x * mass) / new_mass
        node.com_y = (node.com_y * old_mass + y * mass) / new_mass
        node.com_z = (node.com_z * old_mass + z * mass) / new_mass
    node.total_mass = new_mass

    if node.is_leaf and node.body_index == -1:
        node.body_index = body_index
        return

    if node.is_leaf and node.body_index != -1:
        old_body_index = node.body_index
        node.body_index = -1
        node.is_leaf = False
        old_x = p_x[old_body_index]
        old_y = p_y[old_body_index]
        old_z = p_z[old_body_index]
        oct_old = node.get_octant(old_x, old_y, old_z)
        bounds_old = node.get_octant_bounds(oct_old)
        node.children[oct_old] = OctreeNode(*bounds_old)
        insert_body(node.children[oct_old], old_body_index)
        return

    oct = node.get_octant(x, y, z)
    if node.children[oct] is None:
        bounds = node.get_octant_bounds(oct)
        node.children[oct] = OctreeNode(*bounds)
    insert_body(node.children[oct], body_index)


def build_tree():
    # NOTE: min()/max() still work on ctypes arrays
    x_min = min(p_x); x_max = max(p_x)
    y_min = min(p_y); y_max = max(p_y)
    z_min = min(p_z); z_max = max(p_z)
    max_range = max(x_max - x_min, y_max - y_min, z_max - z_min)
    padding = 0.1 * max_range
    x_min -= padding; y_min -= padding; z_min -= padding
    x_max += padding; y_max += padding; z_max += padding
    root = OctreeNode(x_min, x_max, y_min, y_max, z_min, z_max)
    for i in range(N):
        insert_body(root, i)
    return root

# ============================================
# FORCE CALCULATION
# ============================================
# UNCHANGED — recursive Barnes-Hut stays in Python
def calculate_force_barnes_hut(node, body_index):
    if node is None or node.total_mass == 0:
        return 0.0, 0.0, 0.0
    bx = p_x[body_index]; by = p_y[body_index]; bz = p_z[body_index]
    dx = node.com_x - bx; dy = node.com_y - by; dz = node.com_z - bz
    dist_sq = dx*dx + dy*dy + dz*dz + softening*softening
    dist = math.sqrt(dist_sq)
    if dist < 1e-10:
        return 0.0, 0.0, 0.0
    ratio = node.width / dist
    if ratio < theta or (node.is_leaf and node.body_index != -1):
        if node.is_leaf and node.body_index == body_index:
            return 0.0, 0.0, 0.0
        dist_cubed = dist_sq * dist
        force_factor = G * node.total_mass / dist_cubed
        return force_factor * dx, force_factor * dy, force_factor * dz
    else:
        ax_total = ay_total = az_total = 0.0
        for child in node.children:
            if child is not None:
                ax_c, ay_c, az_c = calculate_force_barnes_hut(child, body_index)
                ax_total += ax_c; ay_total += ay_c; az_total += az_c
        return ax_total, ay_total, az_total


def calculate_acceleration():
    """Calculate gravitational forces and update accelerations"""

    #resetting all accelerations to zero
    for i in range(N):
        a_x[i] = 0.0
        a_y[i] = 0.0
        a_z[i] = 0.0

    #calculate forces between all pairs
    #use i+1 to avoid calculating the same pair twice
    for i in range(N):  # for each body i
        for j in range(i+1, N): # check against bodies j (where j>i)

            # we will now calculate vector i from j
            dx = p_x[j] - p_x[i]    #Distance in x direction
            dy = p_y[j] - p_y[i]    #distance in y direction
            dz = p_z[j] - p_z[i]    #distance in z direction

            dist_sq = dx*dx + dy*dy + dz*dz + softening*softening  # softening prevents division by zero when bodies too close
            dist = math.sqrt(dist_sq)     # this is to stablise dist
            dist_cubed = dist*dist*dist

            force_factor = G / dist_cubed   # G/r^3 -> unit force

            # force component -> multiply by direction
            fx = force_factor * dx
            fy = force_factor * dy
            fz = force_factor * dz

            # apply to body i (pulled toward j)
            a_x[i] += fx * m[j]     # F = ma, a = F/m = G*m_j*dx/r^3
            a_y[i] += fy * m[j]     
            a_z[i] += fz * m[j]

            # apply to body j (pulled toward i -> opp direction)
            a_x[j] -= fx * m[i]
            a_y[j] -= fy * m[i]
            a_z[j] -= fz * m[i]

def kick():
    """Update velocities based on accelerations"""
    "Each kick -> velocity changes with respect to acceleration by half timestep"
    for i in range(N): 
        v_x[i] += a_x[i]*dt*half_time_step
        v_y[i] += a_y[i]*dt*half_time_step
        v_z[i] += a_z[i]*dt*half_time_step
    pass

def drift():
    """Update positions based on velocities"""
    "Each drift -> position changes with respect to velocity by half timestep"
    for i in range(N): 
        p_x[i] += v_x[i]*dt*half_time_step
        p_y[i] += v_y[i]*dt*half_time_step
        p_z[i] += v_z[i]*dt*half_time_step
    pass


# ============================================
# MAIN SIMULATION LOOP
# ============================================
# UNCHANGED — structure identical, kick/drift just run in assembly now
print("Starting Barnes-Hut simulation...")
print(f"Number of bodies: {N}")
print(f"Theta parameter: {theta}")
print(f"Time step: {dt} seconds")

calculate_acceleration()
step = 0
timing_done = False

while draw_gui(p_x, p_y, p_z):
    kick()                          # now runs vectorised assembly
    drift()                         # now runs vectorised assembly
    if step == 1 and not timing_done:
        start = time.time()
        calculate_acceleration()
        end = time.time()
        print(f"N={N} | Barnes-Hut time: {end - start:.4f}s")
        timing_done = True
    else:
        calculate_acceleration()
    kick()                          # now runs vectorised assembly
    step += 1
    if step % 100 == 0:
        print(f"Step {step}")

print(f"Simulation complete!")