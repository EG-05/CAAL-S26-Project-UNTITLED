#include <stdio.h>
#include <stdlib.h>

// arrays defined in assembly
extern float m[];
extern float p_x[], p_y[], p_z[];
extern float v_x[], v_y[], v_z[];
extern float a_x[], a_y[], a_z[];

void load_csv() {
    FILE *f = fopen("solar300.csv", "r");
    if (!f) {
        printf("Error: could not open solar300.csv\n");
        return;
    }
    char line[512];
    fgets(line, sizeof(line), f); // skip header line

    int i = 0;
    while(fgets(line, sizeof(line), f) && i < 300) {
        sscanf(line, "%f,%f,%f,%f,%f,%f,%f",
            &m[i], &p_x[i], &p_y[i], &p_z[i],
            &v_x[i], &v_y[i], &v_z[i]);
        i++;
    }
    fclose(f);
    printf("Loaded %d bodies from CSV\n", i);
}

// void print_results() {
//     printf("=== First 3 bodies after one step ===\n");
//     for(int i = 0; i < 3; i++) {
//         printf("Body %d: px=%.6f py=%.6f pz=%.6f\n", i, p_x[i], p_y[i], p_z[i]);
//         printf("Body %d: vx=%.6f vy=%.6f vz=%.6f\n", i, v_x[i], v_y[i], v_z[i]);
//         printf("Body %d: ax=%.6f ay=%.6f az=%.6f\n", i, a_x[i], a_y[i], a_z[i]);
//     }
// }

void print_results() {
    printf("=== First 3 bodies after one step ===\n");
    for(int i = 0; i < 3; i++) {
        printf("Body %d: px=%.6f py=%.6f pz=%.6f\n", i, p_x[i], p_y[i], p_z[i]);
        printf("Body %d: vx=%.6f vy=%.6f vz=%.6f\n", i, v_x[i], v_y[i], v_z[i]);
        printf("Body %d: ax=%.6f ay=%.6f az=%.6f\n", i, a_x[i], a_y[i], a_z[i]);
    }
}

void print_acc_debug() {
    printf("=== Acceleration debug (first 3) ===\n");
    printf("ax[0]=%.10f ay[0]=%.10f az[0]=%.10f\n", a_x[0], a_y[0], a_z[0]);
    printf("ax[1]=%.10f ay[1]=%.10f az[1]=%.10f\n", a_x[1], a_y[1], a_z[1]);
    printf("ax[2]=%.10f ay[2]=%.10f az[2]=%.10f\n", a_x[2], a_y[2], a_z[2]);
}