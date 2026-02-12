import math
import csv
from nbody_visualizer import draw_gui

# Simulation parameters
G = 6.67430e-11  
dt = 8640
softening = 1e9

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
    pass

def kick():
    """Update velocities based on accelerations"""
    "Each kick -> velocity changes with respect to acceleration by half timestep"
    for i in range(N): 
        v_x[i] = a_x[i]*dt*0.5
        v_y[i] = a_y[i]*dt*0.5 
        v_z[i] = a_z[i]*dt*0.5
    pass

def drift():
    """Update positions based on velocities"""
    "Each drift -> position changes with respect to velocity by half timestep"
    for i in range(N): 
        p_x[i] += v_x[i]*dt*0.5
        p_y[i] += v_y[i]*dt*0.5 
        p_z[i] += v_z[i]*dt*0.5
    pass


# Main simulation loop - students just call draw_gui() in their while loop!
while draw_gui(p_x, p_y, p_z):
    # Physics timestep (leapfrog integration)
    kick()
    drift()
    calculate_acceleration()
    kick()
