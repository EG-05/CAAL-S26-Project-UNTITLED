#include <stdio.h>

extern int a[];
extern int c[];
extern void clamp_vector();

int main() {
    clamp_vector();
    printf("=== Clamp Results (values > 255 become 255) ===\n");
    for(int i = 0; i < 8; i++) {
        printf("a[%d] = %d -> c[%d] = %d\n", i, a[i], i, c[i]);
    }
    return 0;
}
