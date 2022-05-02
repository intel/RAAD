#include <iostream>
#include <string>
#include <unistd.h>
#include <thread>
#include <filesystem>

#include "train_and_scan_util.h"
#include "trie.h"
  
struct FileScannerArgs {
  std::string train_dataset_ = "";
  std::string eval_source_file_ = "";
  std::string eval_source_file_list_ = "";
  std::string log_dir_ = "tmp";
  TrainAndScanUtil::ScanConfig scan_config_;
};

static int handle_command_args(int argc, char* argv[], FileScannerArgs& args) {
  auto print_usage = [&]() {
    std::cerr << "Usage: " << argv[0] << std::endl
           << "  -t if_statements_to_train_on " << std::endl
           << "  {-e source_file_to_scan |"
           << "   -l file_containing_list_of_source_files_to_scan}"
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
           << std::endl
           << "Example: -t data/c_lang_if_stmts_6000_gitrepos.ts -o data/tmp_results_anomalies -l data/adp.ilcf -v 2"
           << std::endl;
  };

  int opt;
  while ((opt = getopt(argc, argv, "v:t:e:c:n:l:j:o:a:")) != -1) {
    switch (opt) {
      case 't': args.train_dataset_ = optarg; break;
      case 'e': args.eval_source_file_ = optarg; break;
      case 'l': args.eval_source_file_list_ = optarg; break;
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
  if (args.train_dataset_ == "" ||
      (args.eval_source_file_ == "" && args.eval_source_file_list_ == "")) {
    print_usage();
    return EXIT_FAILURE;
  }
  return EXIT_SUCCESS;
}

static int AddEvalFileNamesIntoList(const FileScannerArgs& file_scanner_args,
  std::vector<std::string>& eval_file_names) {
  auto pStatus = EXIT_SUCCESS;
  if (file_scanner_args.eval_source_file_ != "")
    eval_file_names.push_back(file_scanner_args.eval_source_file_);
  else {
    std::string line;
    auto fileScanCStr = file_scanner_args.eval_source_file_list_.c_str();
    char buff[FILENAME_MAX]; // Create string buffer to hold path
    std::string current_working_dir(buff);
    std::filesystem::path dir (current_working_dir);
    std::filesystem::path file (fileScanCStr);
    std::filesystem::path absFilePath = fileScanCStr;
    std::filesystem::path full_path = dir / file;
    std::filesystem::path abPath = canonical(absFilePath);

    std::ifstream stream(full_path.c_str());
    auto validFileAccess = access(full_path.c_str(), F_OK) != -1;
    auto fileIsOpen = stream.is_open();
    if (!validFileAccess){
      pStatus = EXIT_FAILURE;
      throw cf_file_access_exception("File access failed:" + file_scanner_args.eval_source_file_list_ +
                                     " at working directory " + current_working_dir +
                                     " with full path " + abPath.c_str());
    }
    else if (!fileIsOpen) {
      pStatus = EXIT_FAILURE;
      throw cf_file_access_exception("File open failed:" +
                                      file_scanner_args.eval_source_file_list_ + " at working directory " +
                                      current_working_dir + " with full path " + abPath.c_str());
    }
    else {
      while (std::getline(stream, line)) {
        eval_file_names.push_back(line);
      }
    }
  }
  return pStatus;
}



int main(int argc, char* argv[]) {
  std::cout << "Input tokens are: \n";
  for(int i = 0; i < argc; ++i){
    std::cout << argv[i] << '\n';
  }
  FileScannerArgs file_scanner_args;

  int status = 0;
  status = handle_command_args(argc, argv, file_scanner_args);
  if (status != EXIT_SUCCESS) {
    return status;
  }

  std::vector<std::string> eval_file_names;
  status = AddEvalFileNamesIntoList(file_scanner_args, eval_file_names);
  if (status != EXIT_SUCCESS) {
    return status;
  }

  try {
    TrainAndScanUtil train_and_scan_util(file_scanner_args.scan_config_);
    status = train_and_scan_util.ReadTrainingDatasetFromFile(
                file_scanner_args.train_dataset_, std::cout);

    // Perform multi-threaded inference / scan for bugs.
    std::atomic<size_t> file_index (0);
    std::atomic<size_t> printed_file_index (-1);
    size_t tenth_eval_file_names = eval_file_names.size() < 10 ?
                                   eval_file_names.size() :
                                   eval_file_names.size() / 10;

    auto thread_scan_fn = [&](const size_t thread_num,
                              const std::string& log_file_name,
                              const std::string& cvs_file_name) {
      std::ofstream log_file(log_file_name.c_str());
      std::ofstream cvs_file(cvs_file_name.c_str());

      // Greedy multi-threading: scan next file if current is complete.    
      while (file_index.load() < eval_file_names.size()) {
        // Grab file to scan for bugs.
        std::string& eval_file = eval_file_names[file_index.load()];
        file_index++;
        log_file << "[TID=" << std::this_thread::get_id() << "] "
                 << "Scanning File: " << eval_file << std::endl;

        // Scan.
        status = train_and_scan_util.ScanFile(eval_file, log_file, cvs_file);
        
        // Report progress at every 10th % point.
        if (file_index.load() % tenth_eval_file_names == 0 &&
            printed_file_index.load() < file_index.load())
        std::cout << "Scan progress:" << file_index.load() << "/"
                  << eval_file_names.size() << " ... in progress" << std::endl;
        std::cout.flush();
        printed_file_index = file_index.load();
      }

      log_file.close();
      std::string cvs_header_file_name = file_scanner_args.log_dir_ + "/header.cvs";
      // Pretty print CVS file header
      auto cvs_print_details = [&](const int& status) {
        if (status != 0) {
          cvs_file << "Source-File-Level_0-0" << delimiter()
                   << "Line-In-Code_0-0" << delimiter()
                   << "Detect-Level_0-0" << delimiter()
                   << "Expression-Literal_0-0" << delimiter()
                   << "Training-Set-Found-Status_0-0" << delimiter()

                   << "Source-File-Level_1-0" << delimiter()
                   << "Line-In-Code_1-0" <<  delimiter()
                   << "Character-Offset_1-0" << delimiter()
                   << "Expression-Literal_1-0" << delimiter()

                   << "Source-File-Level_2-0" << delimiter()
                   << "Line-In-Code_2-0" << delimiter()
                   << "Expression-Health_2-0" << delimiter()

                   << "Expression-Class_3-0" << delimiter()
                   << "Edit-Cost_3-0" << delimiter()
                   << "Occurrences_3-0" << delimiter()

                   << "Expression-Class_3-1" << delimiter()
                   << "Edit-Cost_3-1" << delimiter()
                   << "Occurrences_3-1" << delimiter()

                   << "Expression-Class_3-2" << delimiter()
                   << "Edit-Cost_3-2" << delimiter()
                   << "Occurrences_3-2" << delimiter()

                   << "Expression-Class_3-3" << delimiter()
                   << "Edit-Cost_3-3" << delimiter()
                   << "Occurrences_3-3" << delimiter()
                   << std::endl;
        }
      };
      cvs_print_details(1);
      cvs_file.close();
    };

    // Start scanner threads and wait for join.
    std::vector<std::thread> scanner_threads;
    std::cout << "Storing logs in " << file_scanner_args.log_dir_ << std::endl;
    for (size_t i = 0; i < file_scanner_args.scan_config_.num_threads_; i++) {
      std::string log_file_name = file_scanner_args.log_dir_ + "/thread_" +
                                  std::to_string(i) + ".log";
      std::string cvs_file_name = file_scanner_args.log_dir_ + "/thread_" +
                                  std::to_string(i) + ".cvs";
      scanner_threads.push_back(std::thread(thread_scan_fn, i, log_file_name, cvs_file_name));
    }
    for (auto& scanner_thread : scanner_threads) {
      scanner_thread.join();
    }
  } catch (std::exception& e) {
    std::cerr << "Error: " << e.what() << std::endl;
  }
  return 0;
}
