#include <limits.h>
#include <stdio.h>
#include "finetime.h"
#include <dirent.h>
#include <assert.h>
#include <stdlib.h>
#include <string.h>
#include <cstring>
#include "papi.h"
// #include "papiStdEventDefs.h"

#define VECTOR_INIT_CAPACITY (32)
#define UNDEFINE  (-1)
#define SUCCESS (0)
extern int TESTS_QUIET;           /* Declared in test_utils.c */
#define CHAR_SINGLE_STRING (2)

#define VECTOR_CREATE(vec) { \
                          vector vec;\
                          vector_init(&vec); \
                          }

// Store and track the stored data
typedef struct sVectorList {
  void **items;
  int capacity;
  int total;
} sVectorList;

// Structure contain the function pointer
typedef struct sVector vector;

struct sVector {
  sVectorList vectorList;

  // Function pointers
  int (*pfVectorTotal)(vector *);

  int (*pfVectorResize)(vector *, int);

  int (*pfVectorAdd)(vector *, void *);

  int (*pfVectorSet)(vector *, int, void *);

  void *(*pfVectorGet)(vector *, int);

  int (*pfVectorDelete)(vector *, int);

  int (*pfVectorFree)(vector *);
};

// Examples 2667000 2666000 2533000 2399000 2266000 2133000 1999000 1866000 1733000 1599000 1466000 1333000 1199000 [kHz]
const double cpu_freq = 1599000; // KHzc

void __get_time(struct timeinfo *ti) {
  unsigned long tlow, thigh;

  asm volatile ("rdtsc"
  : "=a"(tlow),
  "=d"(thigh));

  ti->low = tlow;
  ti->high = thigh;
}

double __count_elapse(struct timeinfo *start, struct timeinfo *stop) {
  double elapsed;

  if (stop->high < start->high) {
    elapsed = (double) (stop->low) + (double) (ULONG_MAX) * (double) (stop->high + ULONG_MAX - start->high) -
              (double) start->low;
  } else {
    elapsed = (double) (stop->low) + (double) (ULONG_MAX) * (double) (stop->high - start->high) - (double) start->low;
  }
  return elapsed;
}

double get_elapse(struct timeinfo *start, struct timeinfo *stop) {
  return __count_elapse(start, stop);
}

/* The following functions are exported to user application. Normally, a special case about using this file is like this.
       	start();
       	*****
 	elapse = stop();
	time = elapsed2us();
 */
void start(struct timeinfo *ti) {
  /* Clear the start_ti and stop_ti */
  __get_time(ti);
  return;
}

/*
 * Stop timing.
 */
double stop(struct timeinfo *begin, struct timeinfo *end) {
  double elapse;
  struct timeinfo stop_ti;

  if (end == NULL) {
    __get_time(&stop_ti);
    elapse = get_elapse(begin, &stop_ti);
  } else {
    __get_time(end);
    elapse = get_elapse(begin, end);
  }

  return elapse;
}

/* Provide a function to turn to elapse time to microseconds. */
unsigned long elapsed2ms(double elapsed) {
  unsigned long ms;
  double cpuFrequency = (double)cpu_freq;
  ms = (unsigned long) ((double)elapsed / cpuFrequency);
  return (ms);
}

int listDirectory(const char *rootDirectory) {
  int status = 0;
  DIR *dir = NULL;
  struct dirent *dent = NULL;
  int dHere;
  int dUp;
  int dHereMatch;
  int followTheWhiteRabbitNeo;

  // Early return for invalid inputs.
  if (!rootDirectory) {
    status = -1;
    return status;
  }

  // Attempt to open dir.
  dir = opendir(rootDirectory);

  // Traverse if directory is valid
  if (dir != NULL) {
    while ((dent = readdir(dir)) != NULL) {
      dHere = (0 == strcmp(dent->d_name, "."));
      dUp = (0 == strcmp(dent->d_name, ".."));
      dHereMatch = ('.' == (*dent->d_name) );
      followTheWhiteRabbitNeo = !(dHere || dUp || dHereMatch);
      if (followTheWhiteRabbitNeo) {
        printf("%s\n", dent->d_name);
      }
    }
    closedir(dir);
  }
  return status;
}

int fileSearchDirectory(const char* rootDirectory, const char* fileName, char* foundFilePath) {
  // Returns 1 when file is found, 0 when not found, -1 or -2 for allocation errors
  int foundFile = 0;
#if defined(_WIN32) | defined(_WIN64)
  WIN32_FIND_DATA FindFileData;
  HANDLE hFind;
  size_t foundFilePathSize;

  // Early return for invalid inputs.
  if ((!rootDirectory) || (!fileName)) {
    foundFilePathSize = strlen(foundFilePath);
    memset(foundFilePath, '\0', foundFilePathSize);
    foundFile = -1;
    return foundFile;
  }

  hFind = FindFirstFile(fileName, &FindFileData);
  foundFile = !(INVALID_HANDLE_VALUE == hFind);

  if (foundFile) {
#if ENABLE_DEBUG
    _tprintf (TEXT("Target file is %s\n"), fileName);
    _tprintf (TEXT("The first file found is %s\n"), FindFileData.cFileName);
#endif // ENABLE_DEBUG
    strcpy(foundFilePath, FindFileData.cFileName);
    FindClose(hFind);
  }
  else{
    foundFilePathSize = strlen(foundFilePath);
    memset(foundFilePath, '\0', foundFilePathSize);
    foundFile = -2;
  }
#elif !defined(__linux__)
#error (Unknown file system.) // MAC or something else.
#else
  char *path = NULL;
  char *rootDirectoryNext = NULL;
  struct dirent *dp = NULL;
  DIR *dir = NULL;
  int pValid;
  int dpValid;
  int rootDirectoryNextValid;
  size_t foundFilePathSize;
  const char pathSep = '/';
  int followTheWhiteRabbitNeo;
  int isItNeo;

  // Early return for invalid inputs.
  if ((!rootDirectory) || (!fileName)) {
    foundFilePathSize = strlen(foundFilePath);
    memset(foundFilePath, '\0', foundFilePathSize);
    foundFile = -1;
    return foundFile;
  }

  // Allocate Memory
  path = (char *) malloc(strlen(rootDirectory) + strlen(fileName) + 2);
  dp = (struct dirent *) malloc(sizeof(dirent));
  rootDirectoryNext = (char *) malloc(strlen(path) + strlen(dp->d_name) + 2);

  // Verify pointers
  pValid = (!path);
  dpValid = (!dp);
  rootDirectoryNextValid = (!rootDirectoryNext);

  // Early return for memory allocation issues.
  if (pValid || dpValid || rootDirectoryNextValid) {
    foundFilePathSize = strlen(foundFilePath);
    memset(foundFilePath, '\0', foundFilePathSize);
    foundFile = -2;
    return foundFile;
  }

  // Copy directory location content and open directory.
  strcpy(path, rootDirectory);
  dir = opendir(path);
  // Directory is valid
  if (dir) {
    dp = readdir(dir);
    while (NULL != dp) {
      if ('.' != dp->d_name[0]) {
        strcpy(rootDirectoryNext, path);
        strcat(rootDirectoryNext, &pathSep);
        strcat(rootDirectoryNext, dp->d_name);
        followTheWhiteRabbitNeo = (DT_DIR == dp->d_type);
        if (!followTheWhiteRabbitNeo) {
          isItNeo = strcmp(fileName, (const char *)dp->d_name);
          foundFile = (0 == isItNeo);
          if (1 == foundFile) {
            strcpy(foundFilePath, (const char *) rootDirectoryNext);
          }
        }
        else {
          foundFile = fileSearchDirectory(rootDirectoryNext, fileName, foundFilePath);
        }
#if ENABLE_DEBUG
        if (1 == foundFile) {
          printf("File candidate %s\n", rootDirectoryNext);
        }
#endif // ENABLE_DEBUG
      }
    }
    closedir(dir);
  }
#if ENABLE_DEBUG
  else { fprintf(stderr, "Can't open dir %s: %s", path, strerror(errno)); }
#endif // ENABLE_DEBUG
  free(rootDirectoryNext);
#endif // defined(_WIN32) | defined(_WIN64)
  return foundFile;
}

int vectorTotal(vector *v) {
  int totalCount = UNDEFINE;
  if (v) {
    totalCount = v->vectorList.total;
  }
  return totalCount;
}

int vectorResize(vector *v, int capacity) {
  int status = UNDEFINE;
  if (v) {
    void **items = (void **) realloc(v->vectorList.items, sizeof(void *) * capacity);
    if (items) {
      v->vectorList.items = items;
      v->vectorList.capacity = capacity;
      status = SUCCESS;
    }
  }
  return status;
}

int vectorPushBack(vector *v, void *item) {
  int status = UNDEFINE;
  if (v) {
    if (v->vectorList.capacity == v->vectorList.total) {
      status = vectorResize(v, v->vectorList.capacity * 2);
      if (UNDEFINE != status) {
        v->vectorList.items[v->vectorList.total++] = item;
      }
    } else {
      v->vectorList.items[v->vectorList.total++] = item;
      status = SUCCESS;
    }
  }
  return status;
}

int vectorSet(vector *v, int index, void *item) {
  int status = UNDEFINE;
  if (v) {
    if ((index >= 0) && (index < v->vectorList.total)) {
      v->vectorList.items[index] = item;
      status = SUCCESS;
    }
  }
  return status;
}

void *vectorGet(vector *v, int index) {
  void *readData = NULL;
  if (v) {
    if ((index >= 0) && (index < v->vectorList.total)) {
      readData = v->vectorList.items[index];
    }
  }
  return readData;
}

int vectorDelete(vector *v, int index) {
  int status = UNDEFINE;
  int i = 0;
  if (v) {
    if ((index < 0) || (index >= v->vectorList.total)) {
      return status;
    }
    v->vectorList.items[index] = NULL;
    for (i = index; (i < v->vectorList.total - 1); ++i) {
      v->vectorList.items[i] = v->vectorList.items[i + 1];
      v->vectorList.items[i + 1] = NULL;
    }
    v->vectorList.total--;
    if ((v->vectorList.total > 0) && ((v->vectorList.total) == (v->vectorList.capacity / 4))) {
      vectorResize(v, v->vectorList.capacity / 2);
    }
    status = SUCCESS;
  }
  return status;
}

int vectorFree(vector *v) {
  int status = UNDEFINE;
  if (v) {
    free(v->vectorList.items);
    v->vectorList.items = NULL;
    status = SUCCESS;
  }
  return status;
}

void vector_init(vector *v) {
  // init function pointers
  v->pfVectorTotal = vectorTotal;
  v->pfVectorResize = vectorResize;
  v->pfVectorAdd = vectorPushBack;
  v->pfVectorSet = vectorSet;
  v->pfVectorGet = vectorGet;
  v->pfVectorFree = vectorFree;
  v->pfVectorDelete = vectorDelete;
  // initialize the capacity and allocate the memory
  v->vectorList.capacity = VECTOR_INIT_CAPACITY;
  v->vectorList.total = 0;
  v->vectorList.items = (void **)malloc(sizeof(void *) * v->vectorList.capacity);
  return;
}

inline void vector_create(vector *vec){
  vec = (vector*) malloc(sizeof(vector));
  if (NULL != vec) {
    vector_init(vec);
  }
  return;
}

void vector_test(int version) {
  int i = 0;
  // Note the items need to be allocated on the heap before passing
  //  to vector library since the vector design used void *.
  // init vector
  vector v;
  if (0 == version) {
    vector *vp = NULL;
    v = *vp;
    vector_create(&v);
  }
  else {
    //VECTOR_CREATE(v)
    vector_init(&v);
  }

  // Add data in vector
  v.pfVectorAdd(&v, (void*)"Test\n");
  v.pfVectorAdd(&v, (void*)"123...\n");
  v.pfVectorAdd(&v, (void*)"456...\n");
  //print the data and type cast it
  for (i = 0; i < v.pfVectorTotal(&v); i++) {
    printf("%s", (char *) v.pfVectorGet(&v, i));
  }
  // Set the data at index 0
  v.pfVectorSet(&v, 0, (void*)"Overwrite\n");
  printf("\n\n\nVector list after changes\n\n\n");
  // Print the data and type cast it
  for (i = 0; i < v.pfVectorTotal(&v); i++) {
    printf("%s", (char *) v.pfVectorGet(&v, i));
  }
  return;
}

int is_derived(PAPI_event_info_t *info, char retVal[CHAR_SINGLE_STRING]) {
  int retInt = 1;
  retVal [0] = 'Y';

  if (strlen(info->derived) == 0) {
    retVal[0] = 'N';
    retInt = 0;
  }
  else if (0 == strcmp(info->derived, "NOT_DERIVED")) {
    retVal[0] = 'N';
    retInt = 0;
  }
  else if (0 == strcmp(info->derived, "DERIVED_CMPD")) {
    retVal[0] = 'N';
    retInt = 0;
  }
  retVal [1] = '\0';
  return retInt;
}

int checkCounter(int eventcode) {
  int EventSet = PAPI_NULL;
  int retCode = 1;
  if (PAPI_create_eventset(&EventSet) != PAPI_OK) { retCode = 0; }
  if (PAPI_add_event(EventSet, eventcode) != PAPI_OK) { retCode = 0; }
  if (PAPI_cleanup_eventset(EventSet) != PAPI_OK) { retCode = 0; }
  if (PAPI_destroy_eventset(&EventSet) != PAPI_OK) { retCode = 0; }
  return retCode;
}

size_t accessCounters(const int debug, const int print_avail_only,
                   const int check_counter, const int print_event_info,
                   counterEntries_t * counterEntries,
                   entryPAPI_t listPAPI[PAPI_END_idx]) {
  // int print_avail_only = PAPI_PRESET_ENUM_AVAIL;
  // int check_counter = 0;
  // Constant hardware info for this device
  const PAPI_hw_info_t *hwinfo = PAPI_get_hardware_info();
  // Variables to change runtime
  PAPI_event_info_t info;
  entryPAPI_t entryBuffer;
  int i;
  int retval;
  int event_code;
  int codeEvent;
  int validEvent;
  char deriveString[CHAR_SINGLE_STRING];

  // Init variables
  size_t listPAPISize = 0;
  unsigned int filter = (unsigned int) (-1);
  int tot_count = 0;
  int avail_count = 0;
  int deriv_count = 0;

  /* Init PAPI */
  retval = PAPI_library_init(PAPI_VER_CURRENT);
  if ((PAPI_VER_CURRENT != retval) && (1 == debug)) {
    fprintf(stderr, "%s %d %s %d", __FILE__, __LINE__, "PAPI_library_init", retval);
    exit(1);
  }

  // Stop of error occurs.
  retval = PAPI_set_debug(PAPI_VERB_ESTOP); // PAPI_VERB_ECONT
  if ((PAPI_OK != retval) && (1 == debug)) {
    fprintf(stderr, "%s %d %s %d", __FILE__, __LINE__, "PAPI_set_debug", retval);
    exit(2);
  }

  if (1 == debug) {
    printf("================================================================================\n");
    printf("  PAPI CPU Information\n");
    printf("================================================================================\n");
    printf("Number of CPUs per NUMA Node %d\n", hwinfo->ncpu);
    printf("Number of hdw threads per core %d\n", hwinfo->threads);
    printf("Number of cores per socket %d\n", hwinfo->cores);
    printf("Number of sockets %d\n", hwinfo->sockets);
    printf("Total Number of NUMA Nodes %d\n", hwinfo->nnodes);
    printf("Total number of CPUs in the entire system %d\n", hwinfo->totalcpus);
    printf("Vendor number of CPU %d\n", hwinfo->vendor);
    printf("Vendor string of CPU %s\n", hwinfo->vendor_string);
    printf("Model number of CPU %d\n", hwinfo->model);
    printf("Model string of CPU %s\n", hwinfo->model_string);
    printf("Revision of CPU %f\n", hwinfo->revision);
    printf("cpuid family %d\n", hwinfo->cpuid_family);
    printf("cpuid model %d\n", hwinfo->cpuid_model);
    printf("cpuid stepping %d\n", hwinfo->cpuid_stepping);
    printf("Maximum supported CPU speed %d\n", hwinfo->cpu_max_mhz);
    printf("Minimum supported CPU speed %d\n", hwinfo->cpu_min_mhz);
    printf("Running in virtual machine %d\n", hwinfo->virtualized);
    printf("Vendor for virtual machine %s\n", hwinfo->virtual_vendor_string);
    printf("Version of virtual machine %s\n", hwinfo->virtual_vendor_version);
  }

  /* Print *ALL* Events */
  for (i = 0; i < 2; i++) {
    // set the event code to fetch preset events the first time through loop and user events the second time through the loop
    if (0 == i) {
      event_code = 0 | PAPI_PRESET_MASK;
    } else {
      event_code = 0 | PAPI_UE_MASK;
    }

    /* For consistency, always ASK FOR the first event, if there is not one then nothing to process */
    if (PAPI_OK != PAPI_enum_event(&event_code, PAPI_ENUM_FIRST)) {
      continue;
    }

    // print heading to show which kind of events follow
    if (1 == debug) {
      if (0 == i) {
        printf("================================================================================\n");
        printf("  PAPI Preset Events\n");
        printf("================================================================================\n");
      }
      else {
        printf("\n");       // put a blank line after the presets before starting the user events
        printf("================================================================================\n");
        printf("  User Defined Events\n");
        printf("================================================================================\n");
      }

      printf("    Name        Code    ");
      if (!print_avail_only) {
        printf("Avail ");
      }
      printf("Derive Description (Note)\n");
    }

    do {
      // Note #include "papi_common_strings.h"
      codeEvent = PAPI_get_event_info(event_code, &info);
      validEvent = (PAPI_OK == codeEvent);
      // hwi_presets_t _papi_hwi_presets[0][0][0]  is the name contains papi names
      if (validEvent) {
        // if this is a user defined event or its a preset and matches the preset event filters, display its information
        if ((1 == i) || (filter & info.event_type)) {
          if (print_avail_only) {
            if ((info.count) && ((check_counter && checkCounter(event_code)) || !check_counter)) {
              if (1 == debug) {
                is_derived(&info, deriveString);
                printf("%-13s%#x  %-5s%s",
                       info.symbol,
                       info.event_code,
                       deriveString,
                       info.long_descr);
              }
              snprintf(entryBuffer.name, sizeof(entryBuffer.name), "%s", info.symbol);
              entryBuffer.code = info.event_code;
              memcpy(&listPAPI[listPAPISize], (void*)(&entryBuffer), sizeof(entryPAPI_t));
              listPAPISize++;
            }
            if (1 == debug) {
              if (info.note[0]) { printf(" (%s)", info.note); }
              printf("\n");
            }
          }
          else {
            if (1 == debug) {
              is_derived(&info, deriveString);
              printf("%-13s%#x  %-6s%-4s %s",
                     info.symbol,
                     info.event_code,
                     (info.count ? "Yes" : "No"),
                     deriveString,
                     info.long_descr);
            }
            snprintf(entryBuffer.name, sizeof(entryBuffer.name), "%s", info.symbol);
            entryBuffer.code = info.event_code;
            memcpy(&listPAPI[listPAPISize], (void*)(&entryBuffer), sizeof(entryPAPI_t));
            listPAPISize++;
            if (1 == debug) {
              if (info.note[0]) {
                printf(" (%s)", info.note);
              }
              printf("\n");
            }
          }
          tot_count++;
          if ((info.count) && ((check_counter && checkCounter(event_code)) || !check_counter)) {
            avail_count++;
          }
          is_derived(&info, deriveString);
          if ('Y' == deriveString[0]) {
            deriv_count++;
          }
        }
      }
    } while (PAPI_OK == PAPI_enum_event(&event_code, print_avail_only));
  }

  if (1 == debug) {
    printf("--------------------------------------------------------------------------------\n");
    if (!print_event_info) {
      if (print_avail_only) {
        printf("Of %d available events, %d ", avail_count, deriv_count);
      }
      else {
        printf("Of %d possible events, %d are available, of which %d ",
               tot_count, avail_count, deriv_count);
      }
      if (1 == deriv_count) {
        printf("is derived.\n\n");
      } else {
        printf("are derived.\n\n");
      }
    }
  }
  counterEntries->total_count = tot_count;
  counterEntries->available_count = avail_count;
  counterEntries->derive_count = deriv_count;

  return listPAPISize;
}

size_t getCountersInfoEasy(counterEntries_t * counterEntries, entryPAPI_t listPAPI[PAPI_END_idx]) {
  const int debug = 0;
  const int print_avail_only = PAPI_PRESET_ENUM_AVAIL;
  const int check_counter = 0;
  const int print_event_info = 0;
  return accessCounters(debug, print_avail_only, check_counter, print_event_info, counterEntries, listPAPI);
}

int createCountersFile(const char * fileName) {
  size_t j;
  size_t totalEntriesPAPI;
  int status = 0;
  FILE *fp;
  counterEntries_t counterEntries;
  entryPAPI_t listPAPI[PAPI_END_idx];
  char * buffer = (char*) malloc(sizeof(char)*(PAPI_NAME_SIZE+1));
  size_t minStrSize;

  for(size_t j = 0; j < (size_t)PAPI_END_idx; j++) {
    memset(listPAPI[j].name, '\0', sizeof(listPAPI[j].name));
    listPAPI[j].code = 0;
  }

  if (NULL == buffer) {
    status = -1;
    fprintf(stderr, "%s %d \n", __FILE__, __LINE__);
  }

  if (NULL == fileName) {
    status = -2;
    fprintf(stderr, "%s %d \n", __FILE__, __LINE__);
  }
  else {
    totalEntriesPAPI = getCountersInfoEasy(&counterEntries, listPAPI);

    fp = fopen(fileName, "w");
    if (NULL == fp) {
      fprintf(stderr, "PERFPOINT:: cannot open %s file\n", fileName);
      status = -3;
      fprintf(stderr, "%s %d \n", __FILE__, __LINE__);
    }
    else {
      for (j = 0; j < totalEntriesPAPI; j++) {
        minStrSize = sizeof(buffer) > sizeof(listPAPI[j].name) ? sizeof(buffer): sizeof(listPAPI[j].name);
        snprintf(buffer, minStrSize, "%s\n", listPAPI[j].name);
        fputs(buffer, fp);
      }
      status = 1;
    }
  }
  free(buffer);
  fclose(fp);
  return status;
}

void printError(int retval) {
  fprintf(stderr, "[ERROR]: Code=%s, retval=%d, File=%s, Line=%d\n",
          PAPI_strerror(retval), retval, __FILE__, __LINE__);
  return;
}