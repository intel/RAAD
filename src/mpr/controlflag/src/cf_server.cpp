#include <iostream>
#include <sys/types.h>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <netdb.h>
#include <cstring>

#include "train_and_scan_util.h"

struct CFServerArgs {
  std::string train_dataset_ = "";
  std::string log_dir_ = "tmp";
  int server_port_ = 4545;
  TrainAndScanUtil::ScanConfig scan_config_;
};

static int handle_command_args(int argc, char* argv[], CFServerArgs& args) {
  auto print_usage = [&]() {
    std::cerr << "Usage: " << argv[0] << std::endl
           << "  -t if_statements_to_train_on " << std::endl
           << std::endl
           << "  [-p server_port]                           (default: 4545)"
           << std::endl
           << "  [-c max_cost_for_autocorrect]              (default: 2)"
           << std::endl
           << "  [-n max_number_of_results_for_autocorrect] (default: 5)"
           << std::endl
           << "  [-j number_of_scanning_threads]            (default: 1)"
           << std::endl
           << "  [-o output_log_dir]                        (default: tmp)"
           << std::endl
           << "  [-a anomaly_threshold]                     (default: 5.0)"
           << std::endl
           << "  [-v log_level ]                            (default: 0 {ERROR, 0}, {INFO, 1}, {DEBUG, 2})"
           << std::endl;
  };

  int opt;
  while ((opt = getopt(argc, argv, "v:t:c:n:j:o:a:p:")) != -1) {
    switch (opt) {
      case 'p': args.server_port_ = atoi(optarg); break;
      case 't': args.train_dataset_ = optarg; break;
      case 'o': args.log_dir_ = optarg; break;
      // Fixing the max cost to 2 to keep autocorrection time reasonable.
      case 'c': args.scan_config_.max_cost_ = std::max(0, atoi(optarg)); break;
      case 'n': args.scan_config_.max_autocorrections_ =
                  std::max(0, atoi(optarg)); break;
      case 'j': args.scan_config_.num_threads_ = std::max(1, atoi(optarg));
                break;
      case 'a': args.scan_config_.anomaly_threshold_ = atof(optarg); break;
      case 'v': if (atoi(optarg) >= TrainAndScanUtil::LogLevel::MIN &&
                    atoi(optarg) <= TrainAndScanUtil::LogLevel::MAX) {
                  args.scan_config_.log_level_ =
                    static_cast<TrainAndScanUtil::LogLevel>(atoi(optarg));
                }
                break;
      default: /* '?' */
          print_usage();
          return EXIT_FAILURE;
    }
  }
  if (args.train_dataset_ == "") {
    print_usage();
    return EXIT_FAILURE;
  }
  return EXIT_SUCCESS;
}

static int HandleRequest(const TrainAndScanUtil& train_and_scan_util,
                const std::string expression, int server_fd,
                struct sockaddr_in client_addr,
                socklen_t client_addr_len) {
  std::ostringstream response;
  std::ostringstream responseCVS;
  train_and_scan_util.ScanExpression(expression, response, responseCVS);
  if (sendto(server_fd, response.str().c_str(), response.str().size(), 0,
      reinterpret_cast<struct sockaddr*>(&client_addr),
      client_addr_len) != response.str().size()) {
    std::cerr << "Error sending response:" << response.str() << std::endl;
    return -1;
  }
  if (sendto(server_fd, responseCVS.str().c_str(), responseCVS.str().size(), 0,
             reinterpret_cast<struct sockaddr*>(&client_addr),
             client_addr_len) != responseCVS.str().size()) {
    std::cerr << "Error sending response cvs:" << responseCVS.str() << std::endl;
    return -2;
  }
  return 0;
}

static int StartServer(const TrainAndScanUtil& train_and_scan_util,
    const CFServerArgs& server_args) {
  int server_fd = socket(AF_INET, SOCK_DGRAM, 0);
  if (server_fd == -1) {
    std::cerr << "Error in socket(): " << errno << std::endl;
    return server_fd;
  }

  struct sockaddr_in server_addr;
  server_addr.sin_family = AF_UNSPEC;
  server_addr.sin_port = htons(server_args.server_port_);
  server_addr.sin_addr.s_addr = htonl(INADDR_ANY);
  if (bind(server_fd, reinterpret_cast<struct sockaddr *>(&server_addr),
           sizeof(server_addr)) == -1) {
    std::cerr << "Error in bind():" << errno << std::endl;
    return -1;
  }

#if 0
  static int kConnectionBacklog = 1024;
  int status = listen(server_fd, kConnectionBacklog);
  if (status != 0) {
    std::cerr << "Error in listen(): " << errno << std::endl;
  }

  int client_fd = accept(server_fd,
                         reinterpret_cast<struct sockaddr *>(&client_addr),
                         &client_addr_len);
  if (client_fd == -1) {
    std::cerr << "Error in accept(): " << errno << std::endl;
  }
#endif

  while (true) {
    struct sockaddr_in client_addr;
    socklen_t client_addr_len = sizeof(client_addr);

    #define MAX_REQUEST_SIZE 1024
    char request[MAX_REQUEST_SIZE];
    memset(request, 0, MAX_REQUEST_SIZE);

    int nread = recvfrom(server_fd, request, MAX_REQUEST_SIZE, 0,
           (struct sockaddr *) &client_addr, &client_addr_len);
    if (nread == -1)
       continue;

    char client_host[NI_MAXHOST], client_port[NI_MAXSERV];
    if (getnameinfo(reinterpret_cast<struct sockaddr*>(&client_addr),
                    client_addr_len, client_host, NI_MAXHOST,
                    client_port, NI_MAXSERV, NI_NUMERICSERV) == 0) {
      std::cout << "Got request from client:" << client_host << ",port no:"
                << client_port << ",request:" << request << std::endl;
    }

    HandleRequest(train_and_scan_util, request, server_fd, client_addr, client_addr_len);
  }
  return 0;
}


int main(int argc, char* argv[]) {
  CFServerArgs server_args;
  int status = 0;
  status = handle_command_args(argc, argv, server_args);
  if (status != EXIT_SUCCESS) return status;

  try {
    // Load training data first.
    TrainAndScanUtil train_and_scan_util(server_args.scan_config_);
    status = train_and_scan_util.ReadTrainingDatasetFromFile(
                server_args.train_dataset_, std::cout);

    // Start server
    status = StartServer(train_and_scan_util, server_args);
  } catch (std::exception& e) {
    std::cerr << "Error: " << e.what() << std::endl;
  }
  return 0;
}

