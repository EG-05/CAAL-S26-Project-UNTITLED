"""
N-Body Simulation - Barnes-Hut Algorithm Implementation
This file implements the O(N log N) Barnes-Hut algorithm using octrees
"""

import math
import csv
from nbody_visualizer import draw_gui

# ============================================
# SIMULATION PARAMETERS
# ============================================
G = 6.67430e-11  # Gravitational constant
dt = 8640        # Time step
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

# ============================================
# LOAD INITIAL CONDITIONS
# ============================================
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

N = len(m)
print(f"Loaded {N} bodies")

# ============================================
# OCTREE NODE CLASS
# ============================================

class OctreeNode:
    """
    Represents a node in the octree.
    Each node represents a cubic region of 3D space.
    
    A node can be:
    1. Empty (no bodies)
    2. Leaf with one body (contains body_index)
    3. Internal node with 8 children (subdivided)
    """
    
    def __init__(self, x_min, x_max, y_min, y_max, z_min, z_max):
        
        # min, max storing and center calc
        self.x.min = x_min
        self.y.min = y_min
        self.z.min = z_min
        self.x.max = x_max
        self.y.max = y_max
        self.z.max = z_max
        self.center.x = (x_min + x_max)/2.0
        self.center.y = (y_min + y_max)/2.0
        self.center.z = (z_min + z_max)/2.0
        self.width = x_max - x_min      # not calculating all because cube so all will be equal
        self.total.mass = 0.0
        self.center.of.mass.x = 0.0
        self.center.of.mass.y = 0.0
        self.center.of.mass.z = 0.0
        self.leaf = True
        self.body.index = -1    # no body in there
        self.children = [None]*8    # making a list of 8 empty slots
    
    def get_octant(self, x, y, z):
        """
        Determine which octant (0-7) a point (x,y,z) belongs to.
        
        Octant numbering uses binary encoding:
        - Bit 0 (value 1): x direction (0=left, 1=right)
        - Bit 1 (value 2): y direction (0=bottom, 1=top)
        - Bit 2 (value 4): z direction (0=back, 1=front)
        
        Examples:
            Octant 0 (binary 000): back, bottom, left
            Octant 1 (binary 001): back, bottom, right
            Octant 7 (binary 111): front, top, right
        
        Parameters:
            x, y, z: Coordinates of the point
            
        Returns:
            octant: Integer from 0 to 7
        """
        octant = 0
        if x > self.center.x:   # if right add 1
            octant += 1
        if y > self.center.y:   # if top add 2
            octant += 2
        if z > self.center.z:   # if front add 4
            octant += 4
        return octant
    
    def get_octant_bounds(self, octant):
        """
        Get the spatial boundaries for a specific octant.
        
        This function subdivides the current node's region into 8 smaller regions.
        
        Parameters:
            octant: Integer from 0 to 7
            
        Returns:
            (x_min, x_max, y_min, y_max, z_min, z_max): Boundaries of the octant
        """
        x_min = self.x.min
        y_min = self.y.min
        z_min = self.z.min
        x_max = self.x.max
        y_max = self.y.max
        z_max = self.z.max
        
        # x_min -------- center_x -------- x_max -> dividing nodes
        if octant & 1:
            x_min = self.center.x
        else:
            x_max = self.center.x

        if octant & 2:
            y_min = self.center.y
        else:
            y_max = self.center.y

        if octant & 4:
            z_min = self.center.z
        else:
            z_max = self.center.z
        
        return x_min, x_max, y_min, y_max, z_min, z_max

# ============================================
# TREE BUILDING FUNCTIONS
# ============================================

def insert_body(node, body_index):
    """
    Recursively insert a body into the octree.
    
    Algorithm:
    1. Update this node's center of mass and total mass
    2. If node is empty leaf: place body here
    3. If node is leaf with a body: subdivide and redistribute both bodies
    4. If node is internal: insert into appropriate child
    
    Parameters:
        node: The current OctreeNode
        body_index: Index of the body in the global arrays (p_x, p_y, p_z, m)
    """
    
    # TODO: Get the body's position and mass from global arrays
    # x = p_x[body_index]
    # y = p_y[body_index]
    # z = p_z[body_index]
    # mass = m[body_index]
    
    
    # TODO: Update this node's center of mass
    # Use the formula: new_COM = (old_COM * old_mass + new_pos * new_mass) / (old_mass + new_mass)
    # 
    # old_mass = node.total_mass
    # new_mass = old_mass + mass
    # 
    # if new_mass > 0:
    #     node.com_x = (node.com_x * old_mass + x * mass) / new_mass
    #     node.com_y = ?
    #     node.com_z = ?
    # 
    # node.total_mass = new_mass
    
    
    # TODO: CASE 1 - This is an empty leaf
    # If node.is_leaf is True AND node.body_index is -1:
    #     Just place the body here
    #     node.body_index = body_index
    #     return
    
    
    # TODO: CASE 2 - This leaf already has a body, need to subdivide!
    # If node.is_leaf is True AND node.body_index is NOT -1:
    #     
    #     Step 1: Get the existing body's index
    #     old_body_index = node.body_index
    #     
    #     Step 2: Mark this node as no longer a leaf
    #     node.body_index = -1
    #     node.is_leaf = False
    #     
    #     Step 3: Get the old body's position
    #     old_x = p_x[old_body_index]
    #     old_y = ?
    #     old_z = ?
    #     
    #     Step 4: Find which octant the old body belongs to
    #     octant = node.get_octant(old_x, old_y, old_z)
    #     
    #     Step 5: Create a child node for that octant
    #     bounds = node.get_octant_bounds(octant)
    #     node.children[octant] = OctreeNode(*bounds)
    #     
    #     Step 6: Recursively insert the old body into the child
    #     insert_body(node.children[octant], old_body_index)
    
    
    # TODO: CASE 3 - This is an internal node
    # Find which child octant the new body should go into
    # octant = node.get_octant(x, y, z)
    # 
    # If child doesn't exist, create it
    # if node.children[octant] is None:
    #     bounds = node.get_octant_bounds(octant)
    #     node.children[octant] = OctreeNode(*bounds)
    # 
    # Recursively insert into the child
    # insert_body(node.children[octant], body_index)
    
    pass


def build_tree():
    """
    Build the complete octree from all bodies.
    
    Algorithm:
    1. Find the boundaries that encompass all bodies
    2. Add some padding so bodies aren't exactly on edges
    3. Create root node with these boundaries
    4. Insert all bodies into the tree
    
    Returns:
        root: The root OctreeNode of the tree
    """
    
    # TODO: Find the minimum and maximum positions in each dimension
    # x_min = min(p_x)
    # x_max = max(p_x)
    # y_min = ?
    # y_max = ?
    # z_min = ?
    # z_max = ?
    
    
    # TODO: Add padding so bodies aren't exactly on boundaries
    # Calculate padding as 10% of the largest dimension
    # max_range = max(x_max - x_min, y_max - y_min, z_max - z_min)
    # padding = 0.1 * max_range
    # 
    # x_min -= padding
    # x_max += padding
    # y_min -= padding
    # ... (add padding to all 6 boundaries)
    
    
    # TODO: Create the root node
    # root = OctreeNode(x_min, x_max, y_min, y_max, z_min, z_max)
    
    
    # TODO: Insert all bodies into the tree
    # for i in range(N):
    #     insert_body(root, i)
    
    
    # TODO: Return the root node
    # return root
    
    pass

# ============================================
# FORCE CALCULATION FUNCTIONS
# ============================================

def calculate_force_barnes_hut(node, body_index):
    """
    Calculate gravitational force on a body using Barnes-Hut approximation.
    
    Algorithm (recursive):
    1. If node is empty, return zero force
    2. Calculate distance from body to node's center of mass
    3. Calculate s/d ratio (node width / distance)
    4. Decision:
       - If s/d < theta OR node is a leaf: treat as single body
       - Else: recursively calculate from all 8 children
    
    Parameters:
        node: Current OctreeNode
        body_index: Index of body we're calculating force for
        
    Returns:
        (ax, ay, az): Acceleration components in m/s²
    """
    
    # TODO: BASE CASE - Empty node
    # if node is None or node.total_mass == 0:
    #     return 0.0, 0.0, 0.0
    
    
    # TODO: Get the body's position
    # bx = p_x[body_index]
    # by = p_y[body_index]
    # bz = p_z[body_index]
    
    
    # TODO: Calculate vector from body to node's center of mass
    # dx = node.com_x - bx
    # dy = ?
    # dz = ?
    
    
    # TODO: Calculate distance with softening
    # dist_sq = dx*dx + dy*dy + dz*dz + softening*softening
    # dist = math.sqrt(dist_sq)
    
    
    # TODO: Avoid self-interaction
    # If distance is very small (< 1e-10), this is the same body
    # if dist < 1e-10:
    #     return 0.0, 0.0, 0.0
    
    
    # TODO: Calculate s/d ratio
    # s = node width, d = distance
    # ratio = node.width / dist
    
    
    # TODO: DECISION - Should we approximate this node as a single body?
    
    # OPTION A: Yes, approximate (if ratio < theta OR this is a leaf)
    # if ratio < theta or (node.is_leaf and node.body_index != -1):
    #     
    #     Don't calculate force from a body on itself
    #     if node.is_leaf and node.body_index == body_index:
    #         return 0.0, 0.0, 0.0
    #     
    #     Calculate force using node's total mass at center of mass
    #     dist_cubed = dist_sq * dist
    #     force_factor = G * node.total_mass / dist_cubed
    #     
    #     ax = force_factor * dx
    #     ay = force_factor * dy
    #     az = force_factor * dz
    #     
    #     return ax, ay, az
    
    
    # OPTION B: No, need more precision - recurse to children
    # else:
    #     
    #     Initialize total acceleration
    #     ax_total = 0.0
    #     ay_total = 0.0
    #     az_total = 0.0
    #     
    #     Loop through all 8 children
    #     for child in node.children:
    #         if child is not None:
    #             Recursively calculate force from this child
    #             ax_child, ay_child, az_child = calculate_force_barnes_hut(child, body_index)
    #             
    #             Add to total
    #             ax_total += ax_child
    #             ay_total += ay_child
    #             az_total += az_child
    #     
    #     return ax_total, ay_total, az_total
    
    pass


def calculate_acceleration():
    """
    Calculate accelerations for all bodies using Barnes-Hut algorithm.
    
    Algorithm:
    1. Build the octree from current positions
    2. For each body, use the tree to calculate acceleration
    
    This is called once per timestep.
    """
    
    # TODO: Build the tree
    # tree = build_tree()
    
    
    # TODO: Calculate acceleration for each body
    # for i in range(N):
    #     Calculate force from the tree
    #     a_x[i], a_y[i], a_z[i] = calculate_force_barnes_hut(tree, i)
    
    pass

# ============================================
# LEAPFROG INTEGRATION
# ============================================

def kick():
    """
    KICK step: Update velocities by half timestep.
    
    Formula: v = v + a * (dt/2)
    """
    
    # TODO: Loop through all bodies
    # for i in range(N):
    #     Update each velocity component
    #     v_x[i] += a_x[i] * (dt / 2.0)
    #     v_y[i] += ?
    #     v_z[i] += ?
    
    pass


def drift():
    """
    DRIFT step: Update positions by full timestep.
    
    Formula: p = p + v * dt
    """
    
    # TODO: Loop through all bodies
    # for i in range(N):
    #     Update each position component
    #     p_x[i] += v_x[i] * dt
    #     p_y[i] += ?
    #     p_z[i] += ?
    
    pass

# ============================================
# MAIN SIMULATION LOOP
# ============================================

print("Starting Barnes-Hut simulation...")
print(f"Number of bodies: {N}")
print(f"Theta parameter: {theta}")
print(f"Time step: {dt} seconds")

# TODO: Initial acceleration calculation
# Must call this once before the loop starts
# calculate_acceleration()


# TODO: Main loop
# step = 0
# while draw_gui(p_x, p_y, p_z):
#     
#     LEAPFROG INTEGRATION with Barnes-Hut:
#     1. Kick (half step)
#     kick()
#     
#     2. Drift (full step)
#     drift()
#     
#     3. Calculate acceleration (this rebuilds the tree!)
#     calculate_acceleration()
#     
#     4. Kick (half step)
#     kick()
#     
#     Increment step counter
#     step += 1
#     
#     Print progress every 100 steps
#     if step % 100 == 0:
#         print(f"Step {step}")

# print(f"Simulation complete after {step} steps")