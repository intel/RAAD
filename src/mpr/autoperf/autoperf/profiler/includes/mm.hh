#ifndef _MM_H_
#define _MM_M_
#pragma once
extern "C++" {
#include "performanceConstants.h"
#include <errno.h>
#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>

class MM {
public:

#define ALIGN_TO_CACHELINE(size) (size % MM_MAGIC == 0 ? size : (size + MM_MAGIC) / MM_MAGIC * MM_MAGIC)

  static void *mmapAllocatePrivate(size_t sz, void *startaddr = NULL, int fd = -1) {
    return allocate(false, sz, fd, startaddr);
  }

private:
  static void *allocate(bool isShared, size_t sz, int fd, void *startaddr) {
    int protInfo = PROT_READ | PROT_WRITE;
    int sharedInfo = isShared ? MAP_SHARED : MAP_PRIVATE;
    sharedInfo |= ((fd == -1) ? MAP_ANONYMOUS : 0);
    sharedInfo |= ((startaddr != (void *) 0) ? MAP_FIXED : 0);
    sharedInfo |= MAP_NORESERVE;

    void *ptr = mmap(startaddr, sz, protInfo, sharedInfo, fd, 0);
    if (ptr == MAP_FAILED) {
      printf("Couldn't do mmap (%s) : startaddr %p, sz %lu, protInfo=%d, "
             "sharedInfo=%d\n",
             strerror(errno), startaddr, sz, protInfo, sharedInfo);
      abort();
    }
    return ptr;
  }
};

}
#endif // _MM_H_
