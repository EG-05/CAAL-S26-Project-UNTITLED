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
    2. is_leaf with one body (contains body_index)
    3. Internal node with 8 children (subdivided)
    """
    
    def __init__(self, x_min, x_max, y_min, y_max, z_min, z_max):
        
        # min, max storing and center calc
        self.x_min = x_min
        self.y_min = y_min
        self.z_min = z_min
        self.x_max = x_max
        self.y_max = y_max
        self.z_max = z_max
        self.center_x = (x_min + x_max)/2.0
        self.center_y = (y_min + y_max)/2.0
        self.center_z = (z_min + z_max)/2.0
        self.width = x_max - x_min      # not calculating all because cube so all will be equal
        self.total_mass = 0.0
        self.com_x = 0.0
        self.com_y = 0.0
        self.com_z = 0.0
        self.is_leaf = True
        self.body_index = -1    # no body in there
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
        if x > self.center_x:   # if right add 1
            octant += 1
        if y > self.center_y:   # if top add 2
            octant += 2
        if z > self.center_z:   # if front add 4
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
        x_min = self.x_min
        y_min = self.y_min
        z_min = self.z_min
        x_max = self.x_max
        y_max = self.y_max
        z_max = self.z_max
        
        # x_min -------- center_x -------- x_max -> dividing nodes
        if octant & 1:
            x_min = self.center_x
        else:
            x_max = self.center_x

        if octant & 2:
            y_min = self.center_y
        else:
            y_max = self.center_y

        if octant & 4:
            z_min = self.center_z
        else:
            z_max = self.center_z
        
        return x_min, x_max, y_min, y_max, z_min, z_max

# ============================================
# TREE BUILDING FUNCTIONS
# ============================================

def insert_body(node, body_index):
    """
    Recursively insert a body into the octree.
    
    Algorithm:
    1. Update this node's center of mass and total mass
    2. If node is empty is_leaf: place body here
    3. If node is is_leaf with a body: subdivide and redistribute both bodies
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
    
    
    # TODO: CASE 1 - This is an empty is_leaf
    # If node.is_is_leaf is True AND node.body_index is -1:
    #     Just place the body here
    #     node.body_index = body_index
    #     return
    
    
    # TODO: CASE 2 - This is_leaf already has a body, need to subdivide!
    # If node.is_is_leaf is True AND node.body_index is NOT -1:
    #     
    #     Step 1: Get the existing body's index
    #     old_body_index = node.body_index
    #     
    #     Step 2: Mark this node as no longer a is_leaf
    #     node.body_index = -1
    #     node.is_is_leaf = False
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

    x_min = min(p_x)
    x_max = max(p_x)
    y_min = min(p_y)
    y_max = max(p_y)
    z_min = min(p_z)
    z_max = max(p_z)
    
    # Add padding so bodies aren't exactly on boundaries
    # Calculate padding as 10% of the largest dimension

    max_range = max(x_max - x_min, y_max - y_min, z_max - z_min)
    padding = 0.1 * max_range
    x_min -= padding
    y_min -= padding
    z_min -= padding

    x_max += padding
    y_max += padding
    z_max += padding
    
    root = OctreeNode(x_min, x_max, y_min, y_max, z_min, z_max)
    for i in range(N):
        insert_body(root, i)
    
    return root

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
       - If s/d < theta OR node is a is_leaf: treat as single body
       - Else: recursively calculate from all 8 children
    
    Parameters:
        node: Current OctreeNode
        body_index: Index of body we're calculating force for
        
    Returns:
        (ax, ay, az): Acceleration components in m/s²
    """
    
    if node is None or node.total_mass == 0:
        return 0.0, 0.0, 0.0
    
    bx = p_x[body_index]
    by = p_y[body_index]
    bz = p_z[body_index]
    

    # Vector from body to node's center of mass
    dx = node.com_x - bx
    dy = node.com_y - by
    dz = node.com_z - bz
    
    dist_sq = dx*dx + dy*dy + dz*dz + softening*softening
    dist = math.sqrt(dist_sq)
    
    if dist < 1e-10:
        return 0.0, 0.0, 0.0


    ratio = node.width / dist #s/d formula

    # Depending on the ratio, we either think of the node as a single body or of part of a cluster
    
    # Option A: Approximating
    if ratio < theta or (node.is_leaf and node.body_index != -1):
        
        if node.is_is_leaf and node.body_index == body_index:
            return 0.0, 0.0, 0.0
         
    # Calculate force using node's total mass at center of mass
        dist_cubed = dist_sq * dist
        force_factor = G * node.total_mass / dist_cubed

        ax = force_factor * dx
        ay = force_factor * dy
        az = force_factor * dz     
        return ax, ay, az
    
    # Option B: No, need more precision - recurse to children
    else:
        ax_total = 0.0
        ay_total = 0.0
        az_total = 0.0
     
        for child in node.children:
            if child is not None:
                ax_child, ay_child, az_child = calculate_force_barnes_hut(child, body_index)
                ax_total += ax_child
                ay_total += ay_child
                az_total += az_child
    
        return ax_total, ay_total, az_total
    
    pass


def calculate_acceleration():
    tree = build_tree()
    for i in range(N):
        a_x[i], a_y[i], a_z[i] = calculate_force_barnes_hut(tree, i)


# ============================================
# LEAPFROG INTEGRATION
# ============================================

def kick():
    for i in range(N):
        v_x[i] += a_x[i] * (dt/2.0)
        v_y[i] += a_y[i] * (dt/2.0)
        v_z[i] += a_z[i] * (dt/2.0)


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
print(f"Theta parameter: {theta}")
print(f"Time step: {dt} seconds")

calculate_acceleration()
step = 0
while draw_gui(p_x, p_y, p_z):
    kick()
    drift()
    calculate_acceleration()
    kick()
    step += 1
    if step % 100 == 0:
        print(f"Step{step}")
print(f"Simulation comp yayyyy")
