#include <stdio.h>

extern int a[];
extern int b[];
extern int n;
extern int result;
extern void dot_product();

int main() {
    dot_product();

    printf("=== Dot Product Results ===\n");
    printf("Array a: ");
    for(int i = 0; i < n; i++) printf("%d ", a[i]);
    printf("\n");

    printf("Array b: ");
    for(int i = 0; i < n; i++) printf("%d ", b[i]);
    printf("\n");

    printf("Dot product: %d\n", result);

    return 0;
}
