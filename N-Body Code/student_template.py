from nbody_visualizer import draw_gui

# Your particle positions different arrays, or a single list which contains all particles
p_x = [0, 100, -100]     # x positions
p_y = [0, 0, 0]          # y positions  
p_z = [0, 50, -50]       # z positions

# Main loop - just call draw_gui() with your position lists!
while draw_gui(p_x, p_y, p_z):
    # Write your physics code here
    # Update p_x, p_y, p_z each frame
    
    # Example: make particles slowly drift
    p_x[1] += 0.5
    p_x[2] -= 0.5
