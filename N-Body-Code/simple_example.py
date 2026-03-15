import math
import time
import csv
from nbody_visualizer import draw_gui

# Simulation parameters
G = 6.67430e-11  
dt = 8640
softening = 1e9
half_time_step = 0.5

# Particle data - you can create classes for these as well or a single list
#I have them separated in lists.
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

# Load initial conditions
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

# Students write their physics code here
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

            dist_sq = dx**2 + dy**2 + dz**2 + softening**2  # softening prevents division by zero when bodies too close
            dist = dist_sq**0.5     # this is to stablise dist
            dist_cubed = dist**3

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



# time it once before the loop starts
start = time.time()
calculate_acceleration()
end = time.time()
print(f"N={N} | Naive time: {end - start:.4f}s")

step = 0

# Main simulation loop - students just call draw_gui() in their while loop!

while draw_gui(p_x, p_y, p_z):
    # Physics timestep (leapfrog integration)
    kick()
    drift()
    calculate_acceleration()
    kick()