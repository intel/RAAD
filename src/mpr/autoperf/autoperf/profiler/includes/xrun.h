#ifndef _XRUN_H_
#define _XRUN_H_
#pragma once
extern "C++" {

#include <signal.h>
#include <new>

class xrun {

private:

  xrun() {}

public:

  static xrun &getInstance() {
    static char buf[sizeof(xrun)];
    static xrun *singleton = new(buf) xrun();
    return *singleton;
  }

  /// @brief Initialize the system.
  void initialize() {
    installSignalHandler();
    xthread::getInstance().initialize();
    fprintf(stderr, "xrun initialize before xmemory initialize\n");
    // _memory.initialize();
  }

  void finalize(void) {
    xthread::getInstance().finalize();
  }

  /// @brief Install a handler for KILL signals.
  void installSignalHandler() {
    struct sigaction siga;

    // Point to the handler function.
    siga.sa_flags = SA_RESTART | SA_NODEFER;

    siga.sa_handler = sigHandler;
    if (sigaction(SIGINT, &siga, NULL) == -1) {
      perror("installing SIGINT failed\n");
      exit(-1);
    }
#ifdef USING_SIGUSR2
    if (sigaction(SIGUSR2, &siga, NULL) == -1) {
      perror ("installing SIGUSR2 failed\n");
      exit (-1);
    }
#endif // USING_SIGUSR2
  }

  static void sigHandler(int signum) {
    if (signum == SIGINT) {
      fprintf(stderr, "Received SIGINT, Genearting Report\n");
      xthread::getInstance().finalize();
      exit(0);
    } else if (signum == SIGUSR2) {
      fprintf(stderr, "Receiving SIGUSR2, check false sharing now:\n");
      // xmemory::getInstance().reportFalseSharing();
      // xthread::getInstance().finalize();
    }
  }
  /// The memory manager (for both heap and globals).
  //  xmemory&     _memory;
};

}

#endif // _XRUN_H_
