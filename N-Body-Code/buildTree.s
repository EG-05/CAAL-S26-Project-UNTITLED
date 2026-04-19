    .data

    .align 4
node_mass:      .space 4 * MAX_NODES 
node_com_x:     .space 4 * MAX_NODES
node_com_y:     .space 4 * MAX_NODES
node_com_z:     .space 4 * MAX_NODES
node_xmin:      .space 4 * MAX_NODES
node_xmax:      .space 4 * MAX_NODES
node_ymin:      .space 4 * MAX_NODES
node_ymax:      .space 4 * MAX_NODES
node_zmin:      .space 4 * MAX_NODES
node_zmax:      .space 4 * MAX_NODES
node_is_leaf:   .space 4 * MAX_NODES
node_particle:  .space 4 * MAX_NODES
node_child:     .space 4 * MAX_NODES * 8

p_x:            .space 4 * MAX_BODIES
p_y:            .space 4 * MAX_BODIES
p_z:            .space 4 * MAX_BODIES
m:              .space 4 * MAX_BODIES

node_count:     .word 0
N_bodies:       .word 0

const_half:     .float 0.5
const_0p1:      .float 0.1
const_0:        .float 0.0
 
    .text
    .global allocate_node
    .global get_octant
    .global set_child_bounds
    .global insert_body
    .global build_tree

allocate_node:
    la t0, node_count
    lw t1, 0(t0)
    addi t2, t1, 1
    sw t2, 0(t0)
    mv a0, t1
    ret

get_octant:
    la t0, node_xmin
    la t1, node_xmin
    la t2, node_xmin
    la t3, node_xmin
    la t4, node_xmin
    la t5, node_xmin
    slli t6, a0, 2 
    
    # cx = (xmin[i] + xmax[i]) / 2
    add t0, t0, t6
    flw ft3, 0(t0)          # ft3 = xmin[i]
    add t1, t1, t6
    flw ft4, 0(t1)          # ft4 = xmax[i]
    fadd.s ft3, ft3, ft4    # ft3 = xmin + xmax
    la t0, const_half
    flw t0, 0(a0)           # ft0 = 0.5
    fmul.s ft3, ft3, ft0    # ft3 = cx

    # cy = (ymin[i] + ymax[i]) / 2
    add t2, t2, t6
    add  t2, t2, t6
    flw  ft4, 0(t2)              
    add  t3, t3, t6
    flw  ft5, 0(t3)
    fadd.s ft4, ft4, ft5
    fmul.s ft4, ft4, ft0

    # cz = (zmin[i] + zmax[i]) / 2
    add  t4, t4, t6
    flw  ft5, 0(t4)
    add  t5, t5, t6
    flw  ft6, 0(t5)
    fadd.s ft5, ft5, ft6
    fmul.s ft5, ft5, ft0

    li a0, 0                    # octant = 0
    flt.s t0, ft3, fa0          # t0 = (cx < x)
    or  a0, a0, t0              # octant |= bit0
    flt.s t0, ft4, fa1          # t0 = (cy < y)
    slli t0, t0, 1
    or  a0, a0, t0              # octant |= bit1
    flt.s t0, ft5, fa2          # t0 = (cz < z)
    slli t0, t0, 2
    or   a0, a0, t0             # octant |= bit2
 
# set_child_bounds (parent, child, octant)
# a0 = parent (node index)
# a1 = child (node index)
# a2 = octant (0-7)

#FOR EACH AXIS, THE CHILD INEHRITS --> (MIN, CENTRE) , or , (CENTRE, MAX) -- depending on octant bit 
set_child_bounds: 
    addi, sp, sp, -32 
    sw s0, 0(sp)
    sw s1, 4(sp)
    sw s2, 8(sp)
    sw s3, 8(sp)
    sw s4, 12(sp)

    mv s0, a0   # s0 - parent
    mv s1, a1   # s1 - child     
    mv s2, a2   # s2 - octant

    # ---BYTE OFFSETS---
    slli s3, s0, 2      #parent byte offset 
    la t0, const_half 
    flw ft0, 0(t0)      #ft0 = 0.5

    #--- X AXIS 
    la t1, node_xmin
    la t2, node_xmax
    add t3, t1, s3      #&node_xmin[parent]
    flw ft1, 0(t3)      #ft1 = xmin[parent]
    slli t4, s1, 2 
    add t5, t2, t3      #&node_xmax[parent]
    flw ft2, 0(t5)      #ft2 = xmax[parent]
    fadd.s ft3, ft1, ft2 
    fmul.s ft3, ft3, ft0    #ft3 = cx

    andi t0, s2, 1      #bit0 of octant 
    beqz t0, .Lx_Low 
    # x is in upper half -> child xmin = cx, child xmax = xmax[parent]
    add t5, t1, t4      #&node_xmin[child]
    fsw ft3, 0(t5)      #node_xmin[child] = cx
    add t5, t2, t4      #&node_xmac[child]
     j    .Lx_done
     
.Lx_low:
    # x is in lower half → child xmin = xmin[parent], child xmax = cx
    add  t5, t1, t4
    fsw  ft1, 0(t5)              # node_xmin[child] = xmin[parent]
    add  t5, t2, t4
    fsw  ft3, 0(t5)              # node_xmax[child] = cx
.Lx_done:

# --------Y ++







