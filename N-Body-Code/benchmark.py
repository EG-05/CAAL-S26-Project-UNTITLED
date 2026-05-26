import time
import barnes_refactor_ay_m4 as sim # your main file renamed to simulation.py

csv_files = [
    ('solar100.csv',   'Solar'),
    ('solar200.csv',   'Solar'),
    ('solar300.csv',   'Solar'),
    ('cluster500.csv', 'Cluster'),
    ('cluster1000.csv','Cluster'),
    ('cluster5000.csv','Cluster'),
]

print("Running correctness check on solar300.csv...")
sim.init_simulation('solar300.csv')

sim.calculate_acceleration_scalar()
ax_scalar = sim.a_x[:]
ay_scalar = sim.a_y[:]
az_scalar = sim.a_z[:]

sim.init_simulation('solar300.csv')  # reinit because build_tree is called inside
sim.calculate_acceleration_numpy()
ax_numpy = sim.a_x[:]
ay_numpy = sim.a_y[:]
az_numpy = sim.a_z[:]

max_err_x = max(abs(ax_scalar[i] - ax_numpy[i]) for i in range(sim.N))
max_err_y = max(abs(ay_scalar[i] - ay_numpy[i]) for i in range(sim.N))
max_err_z = max(abs(az_scalar[i] - az_numpy[i]) for i in range(sim.N))

print(f"Max absolute error ax: {max_err_x:.2e}")
print(f"Max absolute error ay: {max_err_y:.2e}")
print(f"Max absolute error az: {max_err_z:.2e}")

print("\nRunning benchmark...")
# print(f"{'N':<8} {'Scalar (s)':<14} {'NumPy (s)':<14} {'Speedup':<10}")
# print("-" * 46)
print(f"{'N':<8} {'Scalar (s)':<14} {'NumPy (s)':<14} {'Speedup':<10}")
print("-" * 57)

for csv_file, dataset_type in csv_files:
    sim.init_simulation(csv_file)
    
    start = time.perf_counter()
    sim.calculate_acceleration_scalar()
    scalar_time = time.perf_counter() - start

    sim.init_simulation(csv_file)  # reinit clean tree for numpy run

    start = time.perf_counter()
    sim.calculate_acceleration_numpy()
    numpy_time = time.perf_counter() - start

    speedup = scalar_time / numpy_time if numpy_time > 0 else float('inf')
    print(f"{sim.N:<8} {dataset_type:<12} {scalar_time:<14.4f} {numpy_time:<14.4f} x{speedup:<10.2f}")