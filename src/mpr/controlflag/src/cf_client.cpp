#include <iostream>
#include <fstream>
#include <sys/types.h>
#include <sys/socket.h>
//#include <arpa/inet.h>
#include <netdb.h>
#include <cstring>
#include <unistd.h>
#include <thread>
#include <string>
#include <vector>

#define SERVER_ADDR "172.25.69.11"
#define SERVER_PORT "4545"

void generate_non_op_expression(std::vector<std::string>& queries) {
  queries.push_back("x");
  queries.push_back("foo(x)");
  queries.push_back("x->p");
  queries.push_back("x.p");
  queries.push_back("x[p]");
  queries.push_back("2");
  queries.push_back("true");
  queries.push_back("0.0");
}

void generate_unary_expressions(std::vector<std::string>& queries) {
  std::vector<std::string> terminals = {"x", "2", "0.0", "true", "foo(x)", "x->f", "x.f", "x[f]"};
  std::vector<std::string> ops = {"!", "-", "~"};
  for (const auto& op : ops) {
    for (const auto& terminal : terminals) {
      queries.push_back(op + terminal);
    }
  }
}

void generate_binary_expressions(std::vector<std::string>& queries) {
  std::vector<std::string> terminals = {"x", "2", "0.0", "true", "foo(x)", "x->f", "x.f", "x[f]"};
  std::vector<std::string> ops = {"+", "-", "*", "/", "%", "^", "&", "|"};
  for (const auto& op : ops) {
    for (const auto& lhs_terminal : terminals) {
      for (const auto& rhs_terminal : terminals) {
        queries.push_back(lhs_terminal + " " + op + " " + rhs_terminal);
      }
    }
  }
}

void generate_expression_queries(std::vector<std::string>& queries) {
  generate_non_op_expression(queries);
  generate_unary_expressions(queries);
  generate_binary_expressions(queries);
}

// ---------------------------------------------------------------------------

int thread_fn(int num_iterations, const std::string& log_file_name) {
  std::ofstream log_file(log_file_name.c_str());

  int client_fd = socket(AF_INET, SOCK_STREAM, 0);
  if (client_fd == -1) {
    log_file << "Error in socket(): " << errno << std::endl;
    return 0;
  }

  struct addrinfo hints;
  struct addrinfo *server_addresses;
  memset(&hints, 0, sizeof(struct addrinfo));
  hints.ai_family = AF_UNSPEC;
  hints.ai_socktype = SOCK_DGRAM;
  hints.ai_flags = AI_NUMERICHOST;
  if (getaddrinfo(SERVER_ADDR, SERVER_PORT, &hints, &server_addresses) != 0) {
    log_file << "Error in getaddrinfo:" << errno << std::endl;
    return 0;
  }

  struct addrinfo *server_addr = server_addresses;
  int server_fd = 0;
  for (; server_addr != NULL; server_addr = server_addr->ai_next) {
    server_fd = socket(server_addr->ai_family, server_addr->ai_socktype,
                       server_addr->ai_protocol);
    if (server_fd == -1)
      continue;

    if (connect(server_fd, server_addr->ai_addr, server_addr->ai_addrlen) != -1) {
      log_file << "Connect successful" << std::endl;
      break;                /* Success */
    }

    //close(server_fd);
  }
  std::vector<std::string> queries;
  generate_expression_queries(queries);

  for (size_t i = 0; i < num_iterations; i++) {
    for (const auto& query : queries) {
      std::string data = "if( " + query + ");";
      size_t len = data.size();
      if (write(server_fd, data.c_str(), len) != len) {
        log_file << "Partial write:" << std::endl;
      } else {
        log_file << "Successful write:" << std::endl;
      }
      
      #define MAX_RESPONSE_SIZE 1024
      char response[MAX_RESPONSE_SIZE];
      memset(response, 0, MAX_RESPONSE_SIZE);
      int nread = read(server_fd, response, MAX_RESPONSE_SIZE);
      if (nread == -1) {
        log_file << "Read error:" << errno << std::endl;
        exit(EXIT_FAILURE);
      }
      log_file << "Received: " << response << std::endl;
    }
  }

  close(server_fd);
  freeaddrinfo(server_addresses);
  
  return 0;
}

int main(int argc, char* argv[]) {
  std::vector<std::thread> clients;
  for (size_t i = 0; i < atoi(argv[1]); i++) {
    std::string dirname = "/local_scratch/";
    std::string log_file_name = dirname + "thread_" + std::to_string(i) + ".log";
    clients.push_back(std::thread(thread_fn, atoi(argv[2]), log_file_name));
  }
  for (auto& client : clients) {
    client.join();
  }
  return 0;
}
