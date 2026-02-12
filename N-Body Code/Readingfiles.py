import pandas as pd

class Body:
    def __init__(self, mass, pos, vel, acc=None):
        """
        Initialize a Body object.
        
        :param mass: Mass of the body (float)
        :param pos: Position as a list [x, y, z] (list of floats)
        :param vel: Velocity as a list [vx, vy, vz] (list of floats)
        :param acc: Acceleration as a list [ax, ay, az] (list of floats, defaults to [0, 0, 0])
        """
        self.mass = mass
        self.pos = pos  # [x, y, z]
        self.vel = vel  # [vx, vy, vz]
        self.acc = acc if acc is not None else [0.0, 0.0, 0.0]  # [ax, ay, az]

    def __repr__(self):
        return f"Body(mass={self.mass}, pos={self.pos}, vel={self.vel}, acc={self.acc})"

def load_bodies_from_csv(filename):
    """
    Load initial conditions from a CSV file and create a list of Body objects.
    
    Assumes the CSV has columns: mass, distanceX, distanceY, distanceZ, velocityX, velocityY, velocityZ
    Acceleration is initialized to [0, 0, 0] by default.
    
    :param filename: Path to the CSV file (str)
    :return: List of Body objects
    """
    bodies = []
    df = pd.read_csv(filename)
    
    for _, row in df.iterrows():
        mass = row['mass']
        pos = [row['distanceX'], row['distanceY'], row['distanceZ']]
        vel = [row['velocityX'], row['velocityY'], row['velocityZ']]
        bodies.append(Body(mass, pos, vel))
    
    return bodies

# Example usage for the three files (assuming they are in the same directory)
# Note: The first file is named "cluster500.scv" in your message, but it's likely a typo for "cluster500.csv"
cluster_bodies = load_bodies_from_csv('cluster500.csv')  # Assuming it's .csv
solar_bodies = load_bodies_from_csv('solar100.csv')
stable_random_bodies = load_bodies_from_csv('stable_random_system100.csv')

# You can now use these lists of Body objects in your simulation
# For example, print the first body from each system
print("First body from cluster500:", cluster_bodies[0] if cluster_bodies else "No bodies loaded")
print("First body from solar100:", solar_bodies[0] if solar_bodies else "No bodies loaded")
print("First body from stable_random_system100:", stable_random_bodies[0] if stable_random_bodies else "No bodies loaded")