.section .data
.align 2

# constants
.equ n, 300
.equ dt, 6000000
.equ half_dt, 0

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
    # main loop will go here
    call kick
    call drift
    call calculate_acc
    call kick

kick:
    la t0, v_x
    la t1, v_y
    ret

drift:
    # drift function goes here
    ret

calculate_acc:
    # calculate_acceleration goes here
    ret


