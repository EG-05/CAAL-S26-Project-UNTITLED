.section .data
.align 2

#array a , b 
.global a 
a: .word 1, 2, 3, 4, 5, 6, 7, 8

.global b #array b
b: .word 8, 7, 6, 5, 4, 3, 2, 1

.global n
n: .word 8

# storing result
.global result
result: .word 0

.section .text
.global dot_product

# dot_product a[i]*b[i] for i and sums them up
# i.e. 1*8 + 2*7 + 3*6 + 4*5 + 5*4 + 6*3 + 7*2 + 8*1 = 120

dot_product:
    #a0-a1 basse addresses and a2 = no. of elements 
    la a0, a    
    la a1, b    
    lw a2, n    

    # Initialising sum vector to 0. length, then 0
    vsetvli t0, a2, e32, m1, ta, ma     
    vmv.v.i v3, 0                       

dot_loop:
    beqz a2, dot_done    # if n == 0 then done

    vsetvli t0, a2, e32, m1, ta, ma   # t0 = elements to process

    # Loading vectors 
    vle32.v v0, (a0)                    
    vle32.v v1, (a1)                    

    # Multiplying v2 = a[i] * b[i], then adding to v3 (accumulator)
    vmul.vv v2, v0, v1
    vadd.vv v3, v3, v2

    # Advancing pointers and decrementing counter
    slli t1, t0, 2      # t1 = t0 * 4 (bytes)
    add a0, a0, t1      # pointer a - advancing 
    add a1, a1, t1      # pointer b - advancing 
    sub a2, a2, t0      # n -= processed count

    j dot_loop


dot_done:
    # We use vredsum to reduce v3 to a single sum 
    vmv.v.i v4, 0                 
    vredsum.vs v4, v3, v4         # v4[0] = sum of all elements in v3

    # Extracting the sum from v4[0]
    vmv.x.s t0, v4                      

    # Storing result
    la t1, result
    sw t0, 0(t1)
    ret


