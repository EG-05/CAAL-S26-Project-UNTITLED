import mmap
import struct
import time
from nbody_visualizer import draw_gui

N = 300
FLOAT_SIZE = 4
FLAG_OFFSET = 4  # byte 0 is flag, data starts at byte 4

with open('shared.mem', 'r+b') as f:
    mm = mmap.mmap(f.fileno(), 0)
    
    while True:
        ## wait until RISC-V sets flag to 1 (done writing)
        while struct.unpack('B', mm[0:1])[0] == 0:
            pass
        
        p_x = []
        p_y = []
        p_z = []
        
        for i in range(N):
            #val = struct.unpack('f', mm[i*FLOAT_SIZE : i*FLOAT_SIZE+FLOAT_SIZE])[0]
            val = struct.unpack('f', mm[FLAG_OFFSET + i*FLOAT_SIZE : FLAG_OFFSET + i*FLOAT_SIZE+FLOAT_SIZE])[0]
            p_x.append(val)
        
        for i in range(N):
            offset = 1200 + i*FLOAT_SIZE
            val = struct.unpack('f', mm[offset : offset+FLOAT_SIZE])[0]
            p_y.append(val)
        
        for i in range(N):
            offset = 2400 + i*FLOAT_SIZE
            val = struct.unpack('f', mm[offset : offset+FLOAT_SIZE])[0]
            p_z.append(val)

        # clear flag — telling RISC-V we're done reading
        mm[0:1] = struct.pack('B', 0)
        mm.flush()

        if not draw_gui(p_x, p_y, p_z):
            break
