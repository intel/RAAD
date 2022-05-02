#ifndef _FINETIME_H
#define _FINETIME_H
#pragma once
#ifdef __cplusplus
extern "C" {
#endif // __cplusplus

#include "papi.h"

#define PAPI_NAME_SIZE (1024)

struct timeinfo {
  unsigned long low;
  unsigned long high;
};

typedef struct entryPAPI_s {
  char name[PAPI_NAME_SIZE];
  unsigned int code;
} entryPAPI_t;

typedef struct counterEntries_s {
  int total_count;
  int available_count;
  int derive_count;
} counterEntries_t;

void start(struct timeinfo *ti);

double stop(struct timeinfo *begin, struct timeinfo *end);

unsigned long elapsed2ms(double elapsed);

int listDirectory(const char *rootDirectory);

int fileSearchDirectory(const char* rootDirectory, const char* fileName, char* foundFilePath);

size_t accessCounters(const int debug, const int print_avail_only,
                      const int check_counter, const int print_event_info,
                      counterEntries_t * counterEntries,
                      entryPAPI_t listPAPI[PAPI_END_idx]);

int createCountersFile(const char * fileName);

void printError(int retval);

#define PRINT_ERROR(retval) {printError(retval);}

#ifdef __cplusplus
}
#endif // __cplusplus
#endif // _FINETIME_H
