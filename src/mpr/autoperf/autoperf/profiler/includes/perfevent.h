#ifndef _PERFEVENT_H_
#define _PERFEVENT_H_
#pragma once

#ifdef __cplusplus
extern "C" {
#endif // __cplusplus

#if defined(_WIN32) | defined(_WIN64)
#include <windows.h>
#include <tchar.h>
#endif // defined(_WIN32) | defined(_WIN64)

#include "performanceConstants.h"
#include "papi.h"
#include "pthread.h"
#include "threadmods.h"
#include "xdefines.h"
#include "finetime.h"
#include "cstdlib"
#include <new>
#include "finetime.h"

class xPerf {

private:
  int *perf_event;
  int num_events;
  int event_number_in_global_list;
  int monitoring_event_code; //used input/defined event code to monitor other than TOT_INST. Perfpoint sample TOT_INS and this event
  char *monitoring_event_name;
  int num_of_hw_counters;
  bool eventset_initialized;
  bool event_multiplex;
  int eventSet[xdefines::MAX_THREADS]; //eventSet for each thread

  xPerf() {}

public:
  static xPerf &getInstance() {
    static char buf[sizeof(xPerf)];
    static xPerf *singleton = new(buf) xPerf();
    return *singleton;
  }

  void init() {
    num_events = xdefines::NUM_EVENTS_TO_MONITOR;
    event_multiplex = false;
    eventset_initialized = false;
    printf("Rapid Automated-Analysis for Developers (RAAD)\n");
    /* Init PAPI library */
    int retval = PAPI_library_init(PAPI_VER_CURRENT);
    if (retval != PAPI_VER_CURRENT) {
      fprintf(stderr, "papi_library_init : retval %s, file %s, line %d\n",
              PAPI_strerror(retval), __FILE__, __LINE__);
    }

    printf("Initialized PAPI library\n");

    const PAPI_component_info_t *cmpinfo;

    num_of_hw_counters = PAPI_num_hwctrs();

    fprintf(stdout, "Found %d hw counters!\n", num_of_hw_counters);

    if (num_of_hw_counters <= 0) {
      cmpinfo = PAPI_get_component_info(0);
      fprintf(stderr, "\nComponent %s disabled due to %s\n",
              cmpinfo->name, cmpinfo->disabled_reason);
    }

    if (num_of_hw_counters < num_events) {
      fprintf(stderr, "\n EVENT MULTIPLEX enabled as we found more events(%d) than available counters(%d)\n",
              num_events, num_of_hw_counters);
      event_multiplex = true;
      if (PAPI_multiplex_init() != PAPI_OK) {
        fprintf(stderr, "papi_multiplex_init : retval %s, file %s, line %d\n",
                PAPI_strerror(retval), __FILE__, __LINE__);
      }
    }
    setMonitoringEventCode();
    return;
  }

#if DISABLED
  void initPerfEventsforThread(pthread_t thread_self) {
    int retval = PAPI_thread_init((unsigned long (*)(void)) (thread_self));
    if ( retval != PAPI_OK ) {
      fprintf(stderr, "PAPI_thread_init : retval %s, file %s, line %d\n",
      PAPI_strerror(retval), __FILE__, __LINE__);
    }
    return;
  }
#endif // DISABLED

  int registerThreadForPAPI() {
    int retval = PAPI_register_thread();
    return retval;
  }

  int unregisterThreadForPAPI() {
    int retval = PAPI_unregister_thread();
    return retval;
  }

  void setMonitoringEventCode() {
    char *env_p = std::getenv("PERFPOINT_EVENT_INDEX");
    int event_index_in_list = atoi(env_p);
    //event name can be found at the provided line number of the file "COUNTERS"
    FILE *fp;
    size_t len = 0;
    int64_t nread;
    int i = 0;
    int valid;

    fp = fopen("COUNTERS", "r");
    if (fp == NULL) {
      fprintf(stderr, "PERFPOINT:: cannot open COUNTERS file %s %d\n", __FILE__, __LINE__);

      if (1 != createCountersFile("COUNTERS")) {
        exit(1);
      } else {
        fprintf(stderr, "PERFPOINT:: created COUNTERS file %s %d\n", __FILE__, __LINE__);
        fp = fopen("COUNTERS", "r");
        if (NULL == fp) {
          fprintf(stderr, "PERFPOINT:: error in file read COUNTERS file %s %d\n", __FILE__, __LINE__);
          exit(1);
        }
      }
    }

    monitoring_event_name = NULL;
    nread = getline(&monitoring_event_name, &len, fp);
    valid = (-1 != nread);
    while (valid) {
      if (i == event_index_in_list) {
        printf("Monitoring event name: %s", monitoring_event_name);
        break;
      }
      i++;
      nread = getline(&monitoring_event_name, &len, fp);
      valid = (-1 == nread);
    }
    fclose(fp);

    if (i != event_index_in_list) {
      fprintf(stderr, "PERFPOINT:: wrong input event index %d\n", event_index_in_list);
      exit(1);
    }
    //trim new line char
    if (nread > 0 && monitoring_event_name[nread - 1] == '\n') {
      monitoring_event_name[nread - 1] = '\0';
    }
    monitoring_event_code = 0x0;
    int retval = PAPI_event_name_to_code(monitoring_event_name, &monitoring_event_code);
    if (retval != PAPI_OK) {
      fprintf(stderr, "ERROR: PAPI_event_name_to_code %s File %s Line %d retval %s\n",
              monitoring_event_name, __FILE__, __LINE__, PAPI_strerror(retval));
      exit(1);
    }
    return;
  }

  void setMonitoringEventName() { //from  env variable
    char *env_p = std::getenv("PERFPOINT_EVENT_INDEX");
    event_number_in_global_list = atoi(env_p);
    assert(event_number_in_global_list >= 0 && event_number_in_global_list < NUM_EVENTS);
    return;
  }

  char *getMonitoringEventName() {
    return monitoring_event_name;
  }

  //set TOT_INS and one other event
  void set_perf_events(thread_t *thd) {
    //setMonitoringEventName(); //from  env variable
    int tid = thd->index;
    eventSet[tid] = PAPI_NULL;

    /* create the eventset */
    int retval = PAPI_create_eventset(&eventSet[tid]);
    if (retval != PAPI_OK) {
      fprintf(stderr, "Error : PAPI_create_eventset File %s Line %d retval %d\n",
              __FILE__, __LINE__, retval);
      exit(1);
    }

    if (event_multiplex) {
      if (PAPI_set_multiplex(eventSet[tid]) != PAPI_OK) {
        fprintf(stderr, "Error : PAPI_set_multiplex File %s Line %d retval %d\n",
                __FILE__, __LINE__, retval);
      }
    }

    int native = 0x0;
    char inst_counter_name[] = "PAPI_TOT_INS";
    // unsigned int native = 0x0;
    // retval = PAPI_event_name_to_code("PAPI_TOT_INS",&native); //TOT_INS
    retval = PAPI_event_name_to_code(inst_counter_name, &native); //TOT_INS
    if (retval != PAPI_OK) {
      fprintf(stderr, "ERROR: PAPI_event_code_to_name PAPI_TOT_INS in File %s Line %d retval %s\n",
              __FILE__, __LINE__, PAPI_strerror(retval));
      exit(1);
    }
#ifdef PERFPOINT_DEBUG
    else{
      PAPI_event_code_to_name(native, event_name);
      fprintf(stderr, "Native event code %x for event %s\n", native, event_name);
    }
#endif // PERFPOINT_DEBUG
    retval = PAPI_add_event(eventSet[tid], native);
    if (retval != PAPI_OK) {
      fprintf(stderr, "ERROR: PAPI_add_event File %s Line %d retval %s\n",
              __FILE__, __LINE__, PAPI_strerror(retval));
      fprintf(stderr, "ERROR: For Ubuntu please execute:\n");
      fprintf(stderr, "sudo sh -c 'echo -1 >/proc/sys/kernel/perf_event_paranoid'\n");
    }
    // fprintf( stderr, "Event PAPI_TOT_INS added for thread %d\n", tid );

    // add monitoring event
    retval = PAPI_add_event(eventSet[tid], monitoring_event_code);
    if (retval != PAPI_OK) {
      fprintf(stderr, "ERROR: PAPI_add_event code %u File %s Line %d retval %s\n",
              monitoring_event_code, __FILE__, __LINE__, PAPI_strerror(retval));
      exit(1);
    }
    eventset_initialized = true;
    // fprintf( stderr, "Event code 0x%x added for thread %d\n" ,monitoring_event_code, tid );
    return;
  }

  int start_perf_counters(thread_t *thd, int mark) {
    //int eventSet = set_perf_events();
    assert(eventset_initialized);
    int tid = thd->index;
    thd->current_mark = mark;

    int retval = PAPI_start(eventSet[tid]);
    if (retval != PAPI_OK) {
      fprintf(stderr, "Error : PAPI_start retval %s\n", PAPI_strerror(retval));
    }
    return 1;
  }

  int stop_and_record_perf_counters(thread_t *thd) {
    long long *values;
    values = (long long *) malloc((size_t) num_events * sizeof(long long));
    int tid = thd->index;
    int retval = PAPI_stop(eventSet[tid], values);
    if (retval != PAPI_OK) {
      PRINT_ERROR(retval)
      fprintf(stderr, "Error : PAPI %s File=%s Line=%d retval=%d tid=%d value=%lld\n",
              PAPI_strerror(retval), __FILE__, __LINE__, retval, tid, *values);
    }

    // Record the values in sample
    int next_index = thd->perfRecords.get_next_index();
    (thd->perfRecords.getEntry(next_index))->mark = thd->current_mark;
    for (int i = 0; i < num_events; i++) {
      (thd->perfRecords.getEntry(next_index))->count[i] = values[i];
    }
    return 1;
  }
};

#ifdef __cplusplus
}
#endif // __cplusplus
#endif // _PERFEVENT_H_
