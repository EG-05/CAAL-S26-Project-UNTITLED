.section .data
.align 2

# Input array
.global a
a: .word -5, 10, -3, 7, -1, 0, -9, 4, 2, -6

.global n
n: .word 10

.global result
result: .word 0

.section .text
.global count_negatives

count_negatives:
    la a0, a               # a0 = base address of input array
    lw a1, n               # a1 = number of elements
    li t2, 0               # t2 = running total count

count_loop:
    beqz a1, count_done     # if n == 0, done

    vsetvli t0, a1, e32, m1, ta, ma     # t0 = number of elements this iteration

    # Loading vector annd creating mask ( mask[i] = 1 where a[i] < 0 )
    vle32.v v0, (a0)                
    vmslt.vx v1, v0, zero          

    # Counting no. of -ve values and adding to total 
    vcpop.m t1, v1           
    add t2, t2, t1             

    # Advancing pointer + decrementing thecounter
    slli t3, t0, 2      # t3 = t0 * 4 (bytes)
    add a0, a0, t3      # advancing input pointerr
    sub a1, a1, t0      # n -= processed count

    j count_loop

count_done:
    la t0, result
    sw t2, 0(t0)
    ret
