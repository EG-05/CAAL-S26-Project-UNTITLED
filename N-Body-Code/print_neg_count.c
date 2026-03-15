#include <stdio.h>

extern int a[];
extern int n;
extern int result;
extern void count_negatives();

int main() {
    count_negatives();

    printf("=== Negative Count Results ===\n");
    printf("Array: ");
    for(int i = 0; i < n; i++) {
        printf("%d ", a[i]);
    }
    printf("\n");
    printf("Number of negative values: %d\n", result);

    return 0;
}
