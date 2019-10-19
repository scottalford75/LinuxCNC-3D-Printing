#ifndef PROBEKINS_H
#define PROBEKINS_H

#define SHMEM_KEY 4711 // a famous and very old-fashioned german perfume brand

typedef double vertex_t[3];
typedef int face_t[3];  // indices into vertex array

typedef face_t *face_ptr ;
typedef vertex_t *vertex_ptr;

typedef struct {
    int n_vertices;
    int n_faces;
    vertex_t vertices[1]; //...n_vertices
    // followed by:
    // face_t faces[1]; // 1..n fac
    // starting at &vertices[n_vertices+1]
} mesh_struct;



#endif /* PROBEKINS_H */
