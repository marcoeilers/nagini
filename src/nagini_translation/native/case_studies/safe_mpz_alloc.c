
#include <stdlib.h>
#include <gmp.h>


int allocation_failed = 0;

void *safe_malloc(size_t size) {
    void *ptr = malloc(size);
    if (!ptr) {
        allocation_failed = 1;
        return NULL; // GMP will still call abort(), so we can't recover unless we avoid using GMP here
    }
    return ptr;
}

void *safe_realloc(void *ptr, size_t old_size, size_t new_size) {
    void *new_ptr = realloc(ptr, new_size);
    if (!new_ptr) {
        allocation_failed = 1;
        return NULL;
    }
    return new_ptr;
}

void safe_free(void *ptr, size_t size) {
    free(ptr);
}

int mpz_safe_init(mpz_t x) {
    mp_set_memory_functions(safe_malloc, safe_realloc, safe_free);
    mpz_init(x);
    if(allocation_failed) {
        allocation_failed = 0; 
        return -1; 
    }
    return 0;
}