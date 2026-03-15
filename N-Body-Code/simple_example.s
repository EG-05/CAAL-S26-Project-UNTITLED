.section .data
.align 2

.globl m
.globl p_x
.globl p_y
.globl p_z
.globl v_x
.globl v_y
.globl v_z
.globl a_x
.globl a_y
.globl a_z

# constants
.equ n, 300
.equ dt, 6000000
dt_val: .float 6000000.0
half_val: .float 0.5
G_val: .float 6.67430e-11
softening_val: .float 1e9

# array - 300 floats each
m:             # masses - call address m 300 times with 0.0 float here
    .rept 300 
    .float 0 
    .endr
p_x:           # position
    .rept 300 
    .float 0
    .endr
p_y:                  
    .rept 300 
    .float 0
    .endr
p_z:                  
    .rept 300 
    .float 0
    .endr
v_x:            # velocity
    .rept 300 
    .float 0
    .endr
v_y:                  
    .rept 300 
    .float 0
    .endr
v_z:                  
    .rept 300 
    .float 0
    .endr
a_x:           # acceleration
    .rept 300 
    .float 0
    .endr
a_y:                  
    .rept 300 
    .float 0
    .endr
a_z:                  
    .rept 300 
    .float 0
    .endr

.section .text
.globl main

main:
    # # main loop will go here
    # call kick
    # call drift
    # call calculate_acc
    # call kick

    # li a0, 0        # return code 0
    # li a7, 93       # exit syscall number
    # ecall           # call the OS to exit

    main:
    call load_csv
    call calculate_acc 
    call print_acc_debug
    call kick
    call drift
    call calculate_acc
    call print_acc_debug
    call kick
    call print_results
    li a0, 0
    li a7, 93
    ecall

kick:
    # addi sp, sp, -32    # allocate stack space
    # sd s0, 0(sp)        # save s0
    # sd s1, 8(sp)        # save s1
    # sd ra, 16(sp)       # save return address

    # la t0, v_x              # t0 = base address of v_x
    # la t1, a_x
    # la t2, v_y
    # la t3, a_y
    # la t4, v_z
    # la t5, a_z 
    # li s0, 0                # s0 = i = 0 (loop counter)
    # li s1, 300              # s1 = N = 300 (loop limit)
    # la t0, dt_val
    # flw ft0, 0(t0)
    # la t0, half_val
    # flw ft1, 0(t0)
    # fmul.s ft0, ft0, ft1    # ft0 = ft0*ft1

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
    li s1, 300
    
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

drift_loop: 
    li a1, n 
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
    li s1, 300
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
    la s9, m

    la t0, G_val
    flw ft8, 0(t0)
    la t0, softening_val
    flw ft9, 0(t0)
    fmul.s ft9, ft9, ft9    # softening*softening
    fmv.s ft11, ft9
    li s0, 0                # i = 0
    li s2, 300              # N = 300

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