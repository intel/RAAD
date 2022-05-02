#ifndef RECORD_ENTRIES_HH_
#define RECORD_ENTRIES_HH_
#pragma once
extern "C++" {
#include "performanceConstants.h"
#include <errno.h>
#include <stddef.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include "mm.hh"
#include "xdefines.h"
// Each thread will have a class liked this. Thus, we can avoid
// memory allocation when we are trying to record a synchronization event.
// The total number of entries for each thread is
// xdefines::MAX_SYNCEVENT_ENTRIES. Thus, there is no need to reclaim it. When an
// epoch is finished, we will call
template<class Entry>
class RecordEntries {
public:
  RecordEntries() {}

  void initialize(int entries) {
    void *ptr;
    size_t _size;

    _size = alignup(entries * sizeof(Entry), xdefines::PageSize);
    ptr = MM::mmapAllocatePrivate(_size);
    if (ptr == NULL) {
      printf("%d fail to allocate sync event pool entries \n", getpid());
      ::abort();
    }

    //  PRINF("recordentries.h::initialize at _cur at %p. memory from %p to
    //  0x%lx\n", &_cur, ptr,
    // (((unsigned long)ptr) + _size));
    // start to initialize it.
    _start = (Entry *) ptr;
    _cur = 0;
    _total = entries;
    return;
  }

#if DISABLED
  Entry* alloc() {
    Entry* entry = NULL;

  //	PRINF("allocEntry, _cur %ld\n", _cur);
    if(_cur < _total) {
      int val = __atomic_fetch_add(&_cur,1, __ATOMIC_RELAXED);
      entry = (Entry*)&_start[val];
    } else {
      // There are no enough entries now; re-allocate new entries now.
      printf("Not enough entries, now _cur %lu, _total %lu at %p!!!\n", _cur, _total, &_cur);
      ::abort();
    }
    return entry;
  }
#endif // DISABLED

  size_t get_next_index() {
    // int val = __atomic_fetch_add(&_cur,1, __ATOMIC_RELAXED);
    int val = __sync_fetch_and_add(&_cur, 1);

    if (val < _total) {
      return val;
    } else {
      // There are no enough entries now; re-allocate new entries now.
      printf("Not enough entries, now _cur %ld, _total %lu at %ld!!!\n",
             _cur,
             _total,
             (size_t)(&_cur));
      ::abort();
    }
  }

  void cleanup() {
    // _iter = 0;
    _cur = 0;
  }

  inline Entry *getEntry(size_t index) { return &_start[index]; }

  size_t getEntriesNumb() { return _cur; }

private:
  Entry *_start;
  int64_t _total;
  volatile size_t _cur;
};
}
#endif // RECORD_ENTRIES_HH_
