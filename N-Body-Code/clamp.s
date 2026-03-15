.section .data
.align 2

.global a
a: .word 100, 200, 255, 300, 50, 400, 128, 256

.global c       # Array holding clamped results
c: .word 0, 0, 0, 0, 0, 0, 0, 0

n: .word 8      #No. of elements in array 

.section .text
.global clamp_vector


# Each element in a[], if value > 255 set it to 255, else keep it in c[]

clamp_vector:
    la a0, a        # base address of a
    la a1, c        # base address of c
    lw a2, n        # no. of elements to process

clamp_loop:
    beqz a2, clamp_done           # if no elements left, then you exit

    vsetvli t0, a2, e32, m1, ta, ma     # setting vector length, t0 are all the elements this batch
    vle32.v v2, (a0)                    
    li t1, 255
    vmv.v.x v1, t1                      
    vmsgt.vx v0, v2, t1              # mask: 1 where a[i] > 255
    vmerge.vvm v3, v2, v1, v0        # v3[i] = mask ? 255 : a[i]
    vse32.v v3, (a1)                 # storing results to c1

    slli t1, t0, 2          # t1 = t0 * 4 (bytes)
    add a0, a0, t1          # advancing input pointer
    add a1, a1, t1          # advancing output pointer
    sub a2, a2, t0          # n -= processed count
    j clamp_loop

clamp_done:
    ret