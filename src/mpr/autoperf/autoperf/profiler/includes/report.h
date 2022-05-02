#ifndef _REPORT_H_
#define _REPORT_H_
#pragma once
extern "C++" {

#include "performanceConstants.h"
#include<iostream>
#include<fstream>
#include<sstream>
#include<string>
#include "xdefines.h"
#include "recordentries.hh"
#include<map>
#include<vector>
#include<string.h>


class Report {

private:
  char _curFilename[MAXBUFSIZE];
  std::fstream fs;

  Report() {}


public:
  static Report &getInstance() {
    static Report instance;
    return instance;
  }

  void reportOpen() {
    fs.open("perf_data.csv", std::fstream::out); // @todo jdtarang Hard code
  }

  void reportClose() {
    fs.close();
  }

#if DISABLED
  std::string exec(const char* cmd) {
    FILE* pipe = popen(cmd, "r");
    if (!pipe) return "ERROR";
    char buffer[128];
    std::string result = "";
    while (!feof(pipe)) {
        if (fgets(buffer, 128, pipe) != NULL)
            result += buffer;
    }
    pclose(pipe);
    return result;
  }

  void setFileName(){
    int count = readlink("/proc/self/exe", _curFilename, MAXBUFSIZE);
    if (count <= 0 || count >= MAXBUFSIZE)
    {
      fprintf(stderr, "Failed to get current executable file name\n" );
      exit(1);
    }
    _curFilename[count] = '\0';

  }

  std::string get_call_stack_string( long *call_stack ){

    char buf[MAXBUFSIZE];
    std::string stack_str="";

    int j=0;
    while(call_stack[j] != 0 ) {
      //printf("%#lx\n", m->stacks[i][j]);  
      sprintf(buf, "addr2line -e %s  -a 0x%lx  | tail -1", _curFilename, call_stack[j] );
      std::string source_line =  exec(buf);

      if(source_line[0] != '?') { // not found
        //get the file name only
        std::size_t found = source_line.find_last_of("/\\");
        source_line = source_line.substr(found+1);
        stack_str += source_line.erase(source_line.size()-1); // remove the newline at the end
        stack_str += " ";
      }
      j++;
    }
    return stack_str;
  }
#endif // DISABLED

  void write_results_header() {
    fs << "Mark_id" << ", " << "NTHREADS" << "," << "PAPI_TOT_INS" << ", "
       << xPerf::getInstance().getMonitoringEventName();
    fs << "\n";
    return;
  }

  void write_results(RecordEntries<perf_record_t> &records, int total_threads) {

    int total_records = records.getEntriesNumb();
    // fprintf(stderr, "\n\nPERFPOINT :: Number of records %d\n", total_records);
    for (int i = 0; i < total_records; i++) {
      fs << records.getEntry(i)->mark;
      fs << ", " << total_threads;
      //for(int j=0; j<NUM_EVENTS; j++){
      //	fs << ", " << records.getEntry(i)->count[j] ;
      //}

      fs << ", " << records.getEntry(i)->count[0];
      fs << ", " << records.getEntry(i)->count[1];
      fs << "\n";
    }

    return;
  }

};

}

#endif // _REPORT_H_
