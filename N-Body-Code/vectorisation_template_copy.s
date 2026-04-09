.section .data
.equ N, 300 
.align 2
filename: .string "shared.mem"
.include "mydata.S"
.equ MMAP_SIZE, N*12+8
.equ PX_OFFSET, 4
.equ PY_OFFSET, N*4+4
.equ PZ_OFFSET, N*8+4
.section .text
_start:
    
    li a0, 10
    li a7, 11
    ecall
    
    addi sp, sp, -16
    li t0, 49
    sb t0, 0(sp)
    li a0, 1
    mv a1, sp
    li a2, 1
    li a7, 64
    ecall
    li t0, 10
    sb t0, 0(sp)
    li a0, 1
    mv a1, sp
    li a2, 1
    li a7, 64
    ecall
    addi sp, sp, 16
    
    li a7, 56
    li a0, -100
    la a1, filename
    li a2, 66
    li a3, 0644
    ecall
    mv s0, a0

    addi sp, sp, -16
    li t0, 50
    sb t0, 0(sp)
    li a0, 1
    mv a1, sp
    li a2, 1
    li a7, 64
    ecall
    li t0, 10
    sb t0, 0(sp)
    li a0, 1
    mv a1, sp
    li a2, 1
    li a7, 64
    ecall
    addi sp, sp, 16

    li t0, -1
    beq s0, t0, exit_error

    li a7, 46
    mv a0, s0
    li a1, MMAP_SIZE
    ecall

    addi sp, sp, -16
    li t0, 51
    sb t0, 0(sp)
    li a0, 1
    mv a1, sp
    li a2, 1
    li a7, 64
    ecall
    li t0, 10
    sb t0, 0(sp)
    li a0, 1
    mv a1, sp
    li a2, 1
    li a7, 64
    ecall
    addi sp, sp, 16

    li a7, 222
    li a0, 0
    li a1, MMAP_SIZE
    li a2, 3
    li a3, 1
    mv a4, s0
    li a5, 0
    ecall
    mv s1, a0

    addi sp, sp, -16
    li t0, 52
    sb t0, 0(sp)
    li a0, 1
    mv a1, sp
    li a2, 1
    li a7, 64
    ecall
    li t0, 10
    sb t0, 0(sp)
    li a0, 1
    mv a1, sp
    li a2, 1
    li a7, 64
    ecall
    addi sp, sp, 16

    li t0, -1
    beq s1, t0, exit_error

    addi sp, sp, -16
    li t0, 53
    sb t0, 0(sp)
    li a0, 1
    mv a1, sp
    li a2, 1
    li a7, 64
    ecall
    li t0, 10
    sb t0, 0(sp)
    li a0, 1
    mv a1, sp
    li a2, 1
    li a7, 64
    ecall
    addi sp, sp, 16

    addi sp, sp, -16
    sd s1, 0(sp)
    call calculate_acc
    ld s1, 0(sp)
    addi sp, sp, 16

    
main_loop:
    
wait_flag:
    lb t0, 0(s1)
    bnez t0, wait_flag

    addi sp, sp, -16
    sd s1, 0(sp)

    call kick
    call drift
    call calculate_acc
    call kick

    ld s1, 0(sp)
    addi sp, sp, 16

    la t0, p_x
    la t1, p_y
    la t2, p_z
    li t3, 0
    li t4, N

write_loop:
    # VECTORIZATION NOTE:
    # load a strip of p_x into a vector register, store 
    # then store the whole strip directly to mmap offset
    # same strip-mining pattern applies here too

    bge t3, t4, write_done
    slli t5, t3, 2

    add t6, t0, t5
    flw ft0, 0(t6)
    li a0, PX_OFFSET
    add t6, s1, a0
    add t6, t6, t5
    fsw ft0, 0(t6)

    add t6, t1, t5
    flw ft0, 0(t6)
    li a0, PY_OFFSET
    add t6, s1, a0
    add t6, t6, t5
    fsw ft0, 0(t6)

    add t6, t2, t5
    flw ft0, 0(t6)
    li a0, PZ_OFFSET
    add t6, s1, a0
    add t6, t6, t5
    fsw ft0, 0(t6)

    addi t3, t3, 1
    j write_loop

write_done:
    li t0, 1
    sb t0, 0(s1)
    j main_loop




# ═══════════════════════════════════════════════════════════════
# KICK FUNCTION
# v[i] += a[i] * dt_half
# vectorisation possible bc eg. v_x[0] & v_x[1] = no dependency

# vectorisation layout: 
#   - The idea is to replace scalar loop with a strip-mining loop
#   - strip mining loop = loading strip of v_x and a_x 
#   - perform operations on whole strip then repeat for v_y, v_z
# ═══════════════════════════════════════════════════════════════

kick:

    addi sp, sp, -32
    sd s0, 0(sp)
    sd s1, 8(sp)
    sd ra, 16(sp)

    # ft0 & dt_half are scalar 
    # vfmul.vf  - multiply vector by scalar float
    
    la t0, dt_val
    flw ft0, 0(t0)          # ft0 = dt
    la t0, half_val
    flw ft1, 0(t0)          # ft1 = 0.5
    fmul.s ft0, ft0, ft1    # ft0 = dt * 0.5


    # no address then slli+add to find i, we use strip mining 
    la t0, v_x
    la t1, a_x
    la t2, v_y
    la t3, a_y
    la t4, v_z
    la t5, a_z


    # VECTORIZATION NOTE:
    # vector version: track how many elements are remaining 
    li s0, 0                    # i = 0
    li s1, N                    # s1 = N


kick_loop:

    # vectors process t0 particles per iteration (t0 = up to VLMAX)
    bge s0, s1, kick_end

    # strip size
    sub a2, s1, s0                    # a2 = remaining = N - i
    vsetvli a2, a2, e32, m1, ta, ma   # a2 = actual vl granted by hardware

    slli t6, s0, 2                   # moving pointers t6 = i * 4

    # v_x[i] += a_x[i] * dt_half

    add a3, t0, t6                   # a3 = &v_x[i]
    add a4, t1, t6                   # a4 = &v_x[i]
    vle32.v v0, (a3)                 # loading strip of v_x into v0 
    vle32.v v1, (a4)                 # loading strip of a_x into v1
    vfmacc.vf v0, ft0, v1            # v0[j] += ft0 * v1[j]
    vse32.v v0, (a3)                 # store back to v_x


    # v_y[i] += a_y[i] * dt_half
    add a3, t2, t6              
    add a4, t3, t6              
    vle32.v v0, (a3)            
    vle32.v v1, (a4)            
    vfmacc.vf v0, ft0, v1       
    vse32.v v0, (a3)            

    # v_z[i] += a_z[i] * dt_half
    add a3, t4, t6              
    add a4, t5, t6              
    vle32.v v0, (a3)            
    vle32.v v1, (a4)            
    vfmacc.vf v0, ft0, v1       
    vse32.v v0, (a3)            

    add s0, s0, a2              # i += vl (not 1, actual granted strip size)
    j kick_loop

kick_end:
    ld s0, 0(sp)
    ld s1, 8(sp)
    ld ra, 16(sp)
    addi sp, sp, 32
    ret


# ═══════════════════════════════════════════════════════════════
# DRIFT FUNCTION
# WHAT IT DOES: p[i] += v[i] * dt   for all i
# WHY VECTORIZABLE: identical reasoning to kick
#                   each particle independent, no conditions
# VECTORIZATION PLAN:
#   - exact same strip-mining structure as kick
#   - swap arrays: v→p (destination), p→v (source)
#   - scalar dt instead of dt_half
#   - no other changes needed
# ═══════════════════════════════════════════════════════════════
drift:
    addi sp, sp, -32
    sd s0, 0(sp)
    sd s1, 8(sp)
    sd ra, 16(sp)

    la t0, p_x
    la t1, v_x
    la t2, p_y 
    la t3, v_y 
    la t4, p_z
    la t5, v_z

    li t6, 0

    # VECTORIZATION NOTE:
    # fa0 = dt is the scalar broadcast value
    # same as ft0 in kick — applies to every element
    la a0, dt_val
    flw fa0, 0(a0)
    li a1, N

drift_loop: 

    beqz a1, drift_done         #nothing left ? exit 

    vestvli t6, a1, e32, m1, ta, ma     #t6 = how many elements in THIS particular strip 

    # p_x[i] += v_x[i] * dt
    # VECTOR: load strip v_x, multiply, add to strip p_x
    vle32.v  v0, (t1)               # load strip of v_x 
    vfmul.vf v0, v0, fa0            # v0 = v_x * dt 
    vle32.v  v1, (t0)               # load strip of p_x 
    vfadd.vv v1, v1, v0             # v1 = p_x + (v_x * dt)
    vse32.v  v1,  (t0)              # store back to p_x 

    # p_y[i] += v_y[i] * dt
    vle32.v v0, (t3)                # load strip v_y 
    vfmul.vf v0, v0, fa0            # v0 = v_y *dt 
    vle32.v v1, (t2)                # load strip of p_y
    vfadd.vv v1, v1, v0             # v1 = p_y + (vy *dt )
    vse32.vv (t2)                   # store back into p_y

    # p_z[i] += v_z[i] * dt
    vle32.v v0, (t5)                # load strip v_z 
    vfmul.vf v0, v0, fa0            # v0 = v_z *dt 
    vle32.v v1, (t4)                # load strip of p_z
    vfadd.vv v1, v1, v0             # v1 = p_z + (vz *dt )
    vse32.vv (t4)                   # store back into p_z

    slli a2, t6, 2          # a2 = t6 * 4 (bytes per strip)
    add t0, t0, a2          # p_x pointer forward
    add t1, t1, a2          # v_x pointer forward
    add t2, t2, a2          # p_y pointer forward
    add t3, t3, a2          # v_y pointer forward
    add t4, t4, a2          # p_z pointer forward
    add t5, t5, a2          # v_z pointer forward
    
    sub a1, a1, t6 
    j drift_loop 

drift_done:
    ld s0, 0(sp)
    ld s1, 8(sp)
    ld ra, 16(sp)
    addi sp, sp, 32
    ret

# ═══════════════════════════════════════════════════════════════
# CALCULATE_ACC FUNCTION
# WHAT IT DOES: computes gravitational acceleration for all i
# WHY HARDER TO VECTORIZE:
#   1. current code uses Newton's 3rd law (j starts at i+1)
#      and updates BOTH a[i] and a[j] — this creates a
#      write dependency, cannot vectorize as-is
#   2. has an implicit i==j condition to avoid self-force
#      branches inside vector loops break vectorization
#
# RESTRUCTURE NEEDED BEFORE VECTORIZING:
#   - change inner loop to j = 0..N (not j = i+1)
#   - only update a[i], not a[j]
#   - handle i==j with a MASK not a branch
#
# VECTORIZATION PLAN (after restructure):
#   outer loop over i stays SCALAR (one i at a time)
#   inner loop over j becomes VECTOR:
#   ┌──────────────────────────────────────────────────┐
#   │ for fixed i, load a strip of p_x[j..j+t0]        │
#   │ broadcast p_x[i] as scalar, subtract → strip of dx│
#   │ same for dy, dz                                   │
#   │ compute dist_sq, inv_dist3 for whole strip        │
#   │ generate mask: which lanes have j==i?             │
#   │   → use vid.v to get [0,1,2,...] j indices        │
#   │   → compare with scalar i using vmseq.vx          │
#   │   → this gives a mask register                    │
#   │ apply mask to zero out self-interaction lanes     │
#   │ accumulate force contribution into scalar a[i]    │
#   └──────────────────────────────────────────────────┘
# ═══════════════════════════════════════════════════════════════
calculate_acc:
    addi sp, sp, -80
    sd s0, 0(sp)
    sd s1, 8(sp)
    sd s2, 16(sp)
    sd s3, 24(sp)
    sd s4, 32(sp)
    sd s5, 40(sp)
    sd s6, 48(sp)
    sd s7, 56(sp)
    sd s8, 64(sp)       
    sd s9, 72(sp)       

    la t0, a_x
    la t1, a_y
    la t2, a_z
    li s0, 0
    li s1, N
    fmv.w.x ft11, zero

# VECTORIZATION NOTE:
# this reset loop zeros out a_x, a_y, a_z
# it is trivially vectorizable — same as kick/drift
# use vmv.v.x to fill a vector register with 0.0
# then vse32.v to store whole strip at once
reset_loop:
    bge s0, s1, reset_end
    slli t3, s0, 2
    add t4, t0, t3
    fsw ft11, 0(t4)          # a_x[i] = 0.0
    add t4, t1, t3
    fsw ft11, 0(t4)          # a_y[i] = 0.0
    add t4, t2, t3
    fsw ft11, 0(t4)          # a_z[i] = 0.0
    addi s0, s0, 1
    j reset_loop

reset_end:
    la s3, p_x
    la s4, p_y
    la s5, p_z
    la s6, a_x
    la s7, a_y
    la s8, a_z
    la s9, mass_grid

    la t0, G_val
    flw ft8, 0(t0)
    la t0, softening_val
    flw ft9, 0(t0)
    fmv.s ft11, ft9
    li s0, 0
    li s2, N

# VECTORIZATION NOTE:
# outer loop over i STAYS SCALAR
# you fix i and vectorize everything inside over j
# each i iteration: load p_x[i] once as scalar broadcast
# then the inner loop loads strips of p_x[j], subtracts broadcast
outer_loop:
    bge s0, s2, outer_end
    addi s1, s0, 1          # j = i+1  ← THIS MUST CHANGE TO j=0
                            # for vectorization you need full j=0..N
                            # so that j indices are contiguous
                            # and you can use vid.v to track which j==i

inner_loop:
    # SCALAR: processes one (i,j) pair at a time
    # VECTOR:  processes one i with a STRIP of j at a time
    #
    # CURRENT PROBLEM WITH THIS LOOP STRUCTURE:
    # updates a[j] as well as a[i]
    # if two strips overlap in their j ranges this causes conflicts
    # SOLUTION: remove the a[j] updates, only update a[i]
    # accept the 2x more work, gain clean vectorization
    bge s1, s2, inner_end

    slli t0, s0, 2
    slli t1, s1, 2

    # dx = p_x[j] - p_x[i]
    # VECTOR: broadcast p_x[i] as scalar
    #         load strip of p_x[j] into vector register
    #         vfsub.vf gives you strip of dx in one instruction
    add t2, s3, t0
    add t3, s3, t1
    flw ft0, 0(t2)
    flw ft3, 0(t3)
    fsub.s ft0, ft3, ft0

    # dy, dz: same pattern as dx
    add t2, s4, t0
    add t3, s4, t1
    flw ft1, 0(t2)
    flw ft3, 0(t3)
    fsub.s ft1, ft3, ft1

    add t2, s5, t0
    add t3, s5, t1
    flw ft2, 0(t2)
    flw ft3, 0(t3)
    fsub.s ft2, ft3, ft2

    # dist_sq = dx*dx + dy*dy + dz*dz + softening
    # VECTOR: all of these become element-wise vector ops
    #         vfmul.vv for squares, vfadd.vv for sums
    #         vfadd.vf to add scalar softening to whole strip
    fmul.s ft3, ft0, ft0
    fmul.s ft4, ft1, ft1
    fmul.s ft5, ft2, ft2
    fadd.s ft3, ft3, ft4
    fadd.s ft3, ft3, ft5
    fadd.s ft3, ft3, ft11

    # dist, dist_cubed, G/dist_cubed
    # VECTOR: vfsqrt.v for sqrt on whole strip
    #         then two vfmul.vv for cubing
    #         then vfdiv.vf or vfrdiv.vf for G/dist_cubed
    fsqrt.s ft4, ft3
    fmul.s ft5, ft4, ft4
    fmul.s ft5, ft5, ft4
    fdiv.s ft6, ft8, ft5

    fmul.s ft0, ft6, ft0
    fmul.s ft1, ft6, ft1
    fmul.s ft2, ft6, ft2
    
    slli t0, s0, 2
    slli t1, s1, 2
    add t2, s9, t0
    add t3, s9, t1
    flw ft7, 0(t2)          # m[i]
    flw fa0, 0(t3)          # m[j]

    # ─────────────────────────────────────────────────
    # THE i==j MASKING PROBLEM
    # ─────────────────────────────────────────────────
    # current code avoids self-interaction by starting j=i+1
    # in vectorized version j goes 0..N so j WILL equal i
    # at that point dx=dy=dz=0, dist=0, division by zero!
    #
    # SOLUTION — generate a mask:
    # 1. use vid.v to fill a vector with [j, j+1, j+2, ...]
    #    (the actual j indices for this strip)
    # 2. use vmseq.vx to compare each lane with scalar i
    #    → produces a mask register: 1 where j==i, 0 elsewhere
    # 3. use this mask with vmerge or masked instructions
    #    to zero out the contribution from the j==i lane
    # result: self-interaction lane contributes 0 to a[i]
    # no branch needed anywhere
    # ─────────────────────────────────────────────────

    # a_x[i] += fx * m[j]
    # VECTOR: vfmul.vv strip of fx with strip of m[j]
    #         then use vfredusum.vs to SUM the whole strip
    #         into a single scalar, add that to a_x[i]
    add t4, s6, t0
    flw ft9, 0(t4)
    fmul.s ft10, ft0, fa0
    fadd.s ft9, ft9, ft10
    fsw ft9, 0(t4)

    add t4, s7, t0
    flw ft9, 0(t4)
    fmul.s ft10, ft1, fa0
    fadd.s ft9, ft9, ft10
    fsw ft9, 0(t4)

    add t4, s8, t0
    flw ft9, 0(t4)
    fmul.s ft10, ft2, fa0
    fadd.s ft9, ft9, ft10
    fsw ft9, 0(t4)

    # a_x[j] -= fx * m[i]
    # VECTORIZATION NOTE:
    # THIS ENTIRE BLOCK GOES AWAY in the vector version
    # you no longer update a[j] inside this loop
    # each particle's acceleration is computed when i==that particle
    # 2x more work but no write conflicts, clean vectorization
    add t4, s6, t1
    flw ft9, 0(t4)
    fmul.s ft10, ft0, ft7
    fsub.s ft9, ft9, ft10
    fsw ft9, 0(t4)

    add t4, s7, t1          
    flw ft9, 0(t4)         
    fmul.s ft10, ft1, ft7   
    fsub.s ft9, ft9, ft10   
    fsw ft9, 0(t4) 

    add t4, s8, t1          
    flw ft9, 0(t4)         
    fmul.s ft10, ft2, ft7   
    fsub.s ft9, ft9, ft10   
    fsw ft9, 0(t4)          

    addi s1, s1, 1
    j inner_loop
inner_end:
    addi s0, s0, 1
    j outer_loop
outer_end:
    ld s0, 0(sp)
    ld s1, 8(sp)
    ld s2, 16(sp)
    ld s3, 24(sp)
    ld s4, 32(sp)
    ld s5, 40(sp)
    ld s6, 48(sp)
    ld s7, 56(sp)
    ld s8, 64(sp)       
    ld s9, 72(sp)       
    addi sp, sp, 80     
    ret

exit_error:
    li a7, 93
    li a0, 1
    ecall
    j .

exit_gracefully:
    li a7, 93
    li a0, 0
    ecall