.section .data
.equ N, 300 
.align 2
# initialize other values here:

# first n values will be 1st dimension
#( x axis), next n values will be y axis and so on
filename: .string "shared.mem"
.include "mydata.S"
.equ MMAP_SIZE, N*12+8    # make this N*12 + 4 rounded up
.equ PY_OFFSET, N*4+4    # p_y starts here
.equ PZ_OFFSET, N*8+4    # p_z starts here
.section .text
_start:
    
    # # Read VLENB CSR (VLEN in bytes)
    # csrr t0, vlenb       # VLENB = VLEN / 8
    
    # # Print VLENB value
    # mv a0, t0
    # mv a1, sp          # buffer
    # li a2, 1           # length
    # li a7, 64          # sys_write
    # ecall
    
    # Print newline
    li a0, 10
    li a7, 11
    ecall
    
    # Print "1" to show we started
    addi sp, sp, -16
    li t0, 49          # ASCII '1'
    sb t0, 0(sp)
    li a0, 1           # stdout
    mv a1, sp          # buffer
    li a2, 1           # length
    li a7, 64          # sys_write
    ecall
    li t0, 10          # newline
    sb t0, 0(sp)
    li a0, 1
    mv a1, sp
    li a2, 1
    li a7, 64
    ecall
    addi sp, sp, 16
    
    # openat -> returns the file descriptor to the file
    li a7, 56
    li a0, -100
    la a1, filename
    li a2, 66           # O_RDWR | O_CREAT
    li a3, 0644
    ecall
    mv s0, a0

    # Print "2" and the fd value
    addi sp, sp, -16
    li t0, 50          # ASCII '2'
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

    # Check if openat failed
    li t0, -1
    beq s0, t0, exit_error

    # ftruncate - set file size to 16384 bytes
    li a7, 46           # syscall: ftruncate
    mv a0, s0           # fd
    li a1, MMAP_SIZE        # size
    ecall

    # Print "3" to show mmap is about to run
    addi sp, sp, -16
    li t0, 51          # ASCII '3'
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

    # mmap -> returns the base address
    li a7, 222
    li a0, 0
    li a1, MMAP_SIZE
    li a2, 3
    li a3, 1
    mv a4, s0
    li a5, 0
    ecall
    mv s1, a0

    # Print "4" and mmap result
    addi sp, sp, -16
    li t0, 52          # ASCII '4'
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

    # Check if mmap failed (returns -1 on error)
    li t0, -1
    beq s1, t0, exit_error

    # Print "5" to show we're entering main loop
    addi sp, sp, -16
    li t0, 53          # ASCII '5'
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
    
main_loop:
    
    # ============================================================
    # TODO: IMPLEMENT YOUR LEAPFROG ALGORITHM
    # ============================================================
    # Update all your mass position velocity values before writing
    # ============================================================
    
    # s1 is the pointer to the memory mapped file, make sure to save it if used for something else
    # to read from the mmap file in python make sure to research the mmap library.
     # wait until Python clears the flag
wait_flag:
    lb t0, 0(s1)
    bnez t0, wait_flag

    addi sp, sp, -16    # save s1 (mmap pointer) before calls
    sd s1, 0(sp)        # s1 might get clobbered by functions

    call calculate_acc
    call kick
    call drift
    call calculate_acc
    call kick

    ld s1, 0(sp)        # restore s1 (mmap pointer)
    addi sp, sp, 16

    # write p_x, p_y, p_z to mmap
    la t0, p_x
    la t1, p_y
    la t2, p_z
    li t3, 0
    li t4, N

write_loop:
    bge t3, t4, write_done
    slli t5, t3, 2

    add t6, t0, t5
    flw ft0, 0(t6)
    li a0, 4            # p_x offset (flag is byte 0)
    add t6, s1, t5
    fsw ft0, 0(t6)

    add t6, t1, t5
    flw ft0, 0(t6)
    li a0, PY_OFFSET        # p_y offset
    add t6, s1, a0
    add t6, t6, t5
    fsw ft0, 0(t6)

    add t6, t2, t5
    flw ft0, 0(t6)
    li a0, PZ_OFFSET         # p_z offset
    add t6, s1, a0
    add t6, t6, t5
    fsw ft0, 0(t6)

    addi t3, t3, 1
    j write_loop

write_done:
    # set flag to 1 (RISC-V done writing)
    li t0, 1
    sb t0, 0(s1)       #settig flag 1
    j main_loop

kick:

    addi sp, sp, -32
    sd s0, 0(sp)
    sd s1, 8(sp)
    sd ra, 16(sp)

    # load float constants FIRST
    la t0, dt_val
    flw ft0, 0(t0)          # ft0 = dt
    la t0, half_val
    flw ft1, 0(t0)          # ft1 = 0.5
    fmul.s ft0, ft0, ft1    # ft0 = dt * 0.5

    # THEN load array addresses
    la t0, v_x              # t0 = v_x
    la t1, a_x              # t1 = a_x
    la t2, v_y              # t2 = v_y
    la t3, a_y              # t3 = a_y
    la t4, v_z              # t4 = v_z
    la t5, a_z              # t5 = a_z

    li s0, 0
    li s1, N
    
kick_loop:
    bge s0, s1, kick_end    # s0 >= 300, exit
    slli t6, s0, 2          # t6 = i * 4

    # v_x[i] += a_x[i]*dt*half_time_step
    add a0, t0, t6          # a0 = address of v_x[i]
    add a1, t1, t6          # a1 = address of a_x[i]
    flw fa0, 0(a0)          # load v_x[i]
    flw fa1, 0(a1)          # load a_x[i]
    fmul.s fa1, fa1, ft0    # fa1 = a_x[i]*dt*half_time_step
    fadd.s fa0, fa0, fa1    # v_x[i] += fa1
    fsw fa0, 0(a0)         # store back

    # v_y[i] += a_y[i]*dt*half_time_step
    add a0, t2, t6          # a0 = address of v_y[i]
    add a1, t3, t6          # a1 = address of a_y[i]
    flw fa0, 0(a0)          # load v_y[i]
    flw fa1, 0(a1)          # load a_y[i]
    fmul.s fa1, fa1, ft0    # fa1 = a_y[i]*dt*half_time_step
    fadd.s fa0, fa0, fa1    # v_y[i] += fa1
    fsw fa0, 0(a0)         # store back

    # v_z[i] += a_z[i]*dt*half_time_step
    add a0, t4, t6          # a0 = address of v_z[i]
    add a1, t5, t6          # a1 = address of a_z[i]
    flw fa0, 0(a0)          # load v_z[i]
    flw fa1, 0(a1)          # load a_z[i]
    fmul.s fa1, fa1, ft0    # fa1 = a_z[i]*dt*half_time_step
    fadd.s fa0, fa0, fa1    # v_z[i] += fa1
    fsw fa0, 0(a0)          # store back

    addi s0, s0, 1          # i++
    j kick_loop             # repeat

kick_end:
    ld s0, 0(sp)        # restore s0
    ld s1, 8(sp)        # restore s1
    ld ra, 16(sp)       # restore return address
    addi sp, sp, 32     # free stack space
    ret

drift:
    addi sp, sp, -32    # allocate stack space
    sd s0, 0(sp)        # save s0
    sd s1, 8(sp)        # save s1
    sd ra, 16(sp)       # save return address

    # drift function 
    la t0, p_x          #base address of p_x
    la t1, v_x          #base address of v_x 

    la t2, p_y 
    la t3, v_y 

    la t4, p_z
    la t5, v_z

    li t6, 0            # i = 0 (loop counter)

    # load dt * 0.5  for float constant 
    la a0, dt_val
    flw fa0, 0(a0)        # fa0 = dt
    la a0, half_val
    flw fa3, 0(a0)        # fa3 = 0.5
    fmul.s fa0, fa0, fa3  # fa0 = dt * 0.5
    li a1, N

drift_loop: 
    # li a1, n 
    bge t6, a1, drift_done   #if  i >= N -- exit 

    slli a2, t6, 2      #offset = i * 4 
    
    #------------------- p_x[i] += v_x[i]*dt*half_time_step ----------------------------#
    add a3, t1, a2          #address of v_x[i] 
    flw fa1, 0(a3)          # fa1 = v_x[i]
    fmul.s fa1, fa1, fa0     # fa1 = v_x[i] * halfdt 

    add a3, t0, a2          #address of p_x[i]
    flw fa2, 0(a3)          # fa2 = v_x[i]
    fadd.s fa2, fa2, fa1    # fa2 = p_x[i] + v_x[i] * halfdt
    fsw fa2, 0(a3)          # store back

    # ------------------- p_y[i] += v_y[i]*dt*half_time_step ---------------------------- # 
    add a3, t3, a2          #address of v_y[i] 
    flw fa1, 0(a3)          # fa1 = v_y[i]
    fmul.s fa1, fa1, fa0     # fa1 = v_y[i] * halfdt 

    add a3, t2, a2          #address of p_y[i]
    flw fa2, 0(a3)          # fa2 = p_y[i]
    fadd.s fa2, fa2, fa1    # fa2 = p_y[i] + v_y[i] * halfdt
    fsw fa2, 0(a3)          # store back

    # ------------------- p_z[i] += v_z[i]*dt*half_time_step ---------------------------- # 
    add a3, t5, a2          #address of v_z[i] 
    flw fa1, 0(a3)          # fa1 = p_z[i]
    fmul.s fa1, fa1, fa0     # fa1 = v_z[i] * halfdt 

    add a3, t4, a2          #address of p_z[i]
    flw fa2, 0(a3)          # fa2 = p_z[i]
    fadd.s fa2, fa2, fa1    # fa2 = p_z[i] + v_z[i] * halfdt
    fsw fa2, 0(a3)          # store back

    addi t6, t6, 1           # i + + 
    j drift_loop 

drift_done:
    ld s0, 0(sp)        # restore s0
    ld s1, 8(sp)        # restore s1
    ld ra, 16(sp)       # restore return address
    addi sp, sp, 32     # free stack space     
    ret

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
    fmv.w.x ft11, zero       # ft0 = 0.0 (float zero)

# for i in range(N):
    # a_x[i] = 0.0
    # a_y[i] = 0.0
    # a_z[i] = 0.0
reset_loop:
    bge s0, s1, reset_end
    slli t3, s0, 2          # t3 = s0*4
    add t4, t0, t3          # address of a_x[i]
    fsw ft11, 0(t4)          # a_x[i] = 0.0
    add t4, t1, t3          # address of a_y[i]
    fsw ft11, 0(t4)          # a_y[i] = 0.0
    add t4, t2, t3          # address of a_z[i]
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
    fmul.s ft9, ft9, ft9    # softening*softening
    fmv.s ft11, ft9
    li s0, 0                # i = 0
    li s2, N              # N = 300

outer_loop:
    bge s0, s2, outer_end   # if i>=300 exit
    addi s1, s0, 1          # j = i + 1
inner_loop:
    bge s1, s2, inner_end

    #write here
    slli t0, s0, 2          # t0 = i * 4
    slli t1, s1, 2          # t1 = j * 4

    # dx = p_x[j] - p_x[i]
    add t2, s3, t0          # t2 = address of p_x[i]
    add t3, s3, t1          # t1 = address of p_x[j]
    flw ft0, 0(t2)          # ft0 = p_x[i]
    flw ft3, 0(t3)          # ft1 = p_x[j]
    fsub.s ft0, ft3, ft0    # ft0 = dx = p_x[j] - p_x[i]

    # dx = p_y[j] - p_y[i]
    add t2, s4, t0          # t2 = address of p_y[i]
    add t3, s4, t1          # t1 = address of p_y[j]
    flw ft1, 0(t2)          # ft0 = p_y[i]
    flw ft3, 0(t3)          # ft1 = p_y[j]
    fsub.s ft1, ft3, ft1    # ft0 = dx = p_y[j] - p_y[i]

    # dx = p_z[j] - p_z[i]
    add t2, s5, t0          # t2 = address of p_z[i]
    add t3, s5, t1          # t1 = address of p_z[j]
    flw ft2, 0(t2)          # ft0 = p_z[i]
    flw ft3, 0(t3)          # ft1 = p_z[j]
    fsub.s ft2, ft3, ft2    # ft0 = dx = p_z[j] - p_z[i]

    fmul.s ft3, ft0, ft0    # ft3 = dx*dx
    fmul.s ft4, ft1, ft1    # ft4 = dy*dy
    fmul.s ft5, ft2, ft2    # ft5 = dz*dz
    fadd.s ft3, ft3, ft4    # ft3 = dx*dx + dy*dy
    fadd.s ft3, ft3, ft5    # ft3 = ft3 + dz*dz
    fadd.s ft3, ft3, ft11    # ft3 = ft3 + ft9 (softening*softening) -> dist_sq
    fsqrt.s ft4, ft3        # ft4 = dist -> dist = math.sqrt(dist_sq)
    fmul.s ft5, ft4, ft4    # ft5 = dist*dist
    fmul.s ft5, ft5, ft4    # ft5 = dist*dist*dist -> dist_cubed
    fdiv.s ft6, ft8, ft5    # ft6 = G/dist_cubed
    fmul.s ft0, ft6, ft0
    fmul.s ft1, ft6, ft1
    fmul.s ft2, ft6, ft2
    
    slli t0, s0, 2
    slli t1, s1, 2
    add t2, s9, t0
    add t3, s9, t1
    flw ft7, 0(t2)          # ft7 = m[i]
    flw fa0, 0(t3)          # ft8 = m[j]

    # a_x[i] += fx * m[j]
    add t4, s6, t0          # t4 = address of a_x[i]
    flw ft9, 0(t4)          # ft9 = a_x[i]
    fmul.s ft10, ft0, fa0   # ft10 = fx * m[j]
    fadd.s ft9, ft9, ft10   # ft9 = a_x[i] + fx*m[j]
    fsw ft9, 0(t4)          # store back to a_x[i]

    # a_y[i] += fy * m[j] 
    add t4, s7, t0
    flw ft9, 0(t4)
    fmul.s ft10, ft1, fa0
    fadd.s ft9, ft9, ft10
    fsw ft9, 0(t4)

    # a_z[i] += fz * m[j]
    add t4, s8, t0
    flw ft9, 0(t4)
    fmul.s ft10, ft2, fa0
    fadd.s ft9, ft9, ft10
    fsw ft9, 0(t4)

    # a_x[j] -= fx * m[i]
    add t4, s6, t1          # t4 = address of a_x[j]
    flw ft9, 0(t4)          # ft9 = a_x[j]
    fmul.s ft10, ft0, ft7   # ft10 = fx * m[i]
    fsub.s ft9, ft9, ft10   # ft9 = a_x[j] - fx*m[i]
    fsw ft9, 0(t4)          # store back to a_x[j]

    # a_y[j] -= fy * m[i]
    add t4, s7, t1          
    flw ft9, 0(t4)         
    fmul.s ft10, ft1, ft7   
    fsub.s ft9, ft9, ft10   
    fsw ft9, 0(t4) 

    # a_z[j] -= fz * m[i]
    add t4, s8, t1          
    flw ft9, 0(t4)         
    fmul.s ft10, ft2, ft7   
    fsub.s ft9, ft9, ft10   
    fsw ft9, 0(t4)          

    addi s1, s1, 1          # j++
    j inner_loop
inner_end:
    addi s0, s0, 1          # i++
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
# You can write functions here and call them in the main loop:


# Error handler
exit_error:
    li a7, 93          # syscall: exit
    li a0, 1           # exit code 1 (error)
    ecall
    j .

# Graceful exit
exit_gracefully:
    li a7, 93
    li a0, 0
    ecall