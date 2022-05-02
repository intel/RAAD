#include "train_and_scan_util.h"
#include "trie.h"
#include "common_util.h"

template <TreeLevel L>
void TrainAndScanUtil::ReportPossibleCorrections(const Trie& trie,
    const conditional_expression_t& conditional_expression,
    std::ostream& log_file, std::ostream& cvs_file) const {
  std::string conditional_expression_str = NodeToShortString<L>(
    conditional_expression);
  
  // We maintain different expression cache per level since
  // there is no sharing of expressions between different
  // trie levels.
  static NearestExpressionsCache<L> expression_cache(scan_config_);

  // Search for nearest expressions based on edit distance. 
  NearestExpressions nearest_expressions;

  // Lookup in cache. If that fails, insert into cache.
  if (expression_cache.LookUp(conditional_expression_str,
                              nearest_expressions) == false) {
    Timer timer_trie_search;
    timer_trie_search.StartTimer();
    nearest_expressions = trie.SearchNearestExpressions(
          conditional_expression_str, scan_config_.max_cost_,
          scan_config_.num_threads_);
    timer_trie_search.StopTimer();

    if (scan_config_.log_level_ >= LogLevel::DEBUG) {
      log_file << "Autocorrect search took "
               << timer_trie_search.TimerDiff() << " secs" << std::endl;
    }

    // Sort and rank results based on distance and occurrence.
    trie.SortAndRankResults(nearest_expressions);
    expression_cache.Insert(conditional_expression_str, nearest_expressions);
  }

  // Select only max results asked by the user.
  NearestExpressions top_n_nearest_expressions;
  size_t max_autocorrections = scan_config_.max_autocorrections_;
  for (auto nearest_expression : nearest_expressions) {
    top_n_nearest_expressions.push_back(nearest_expression);
    top_n_nearest_expressions.push_back(nearest_expression);
    --max_autocorrections;
    if (max_autocorrections <= 0)
      break;
  }

  auto print_autocorrect_results = [&](const bool debugInfo, const std::string& status) {
    for (auto nearest_expression : top_n_nearest_expressions) {
      std::string long_expression = ExpressionCompacter::Get().Expand(
            nearest_expression.GetExpression());
      cvs_file << status << delimiter()
               << expressionCleaner(long_expression) << delimiter()
               << nearest_expression.GetCost() << delimiter()
               << nearest_expression.GetNumOccurances() << delimiter();
      if ((debugInfo and status == "Okay") or (status == "Anomaly")) {
        log_file << "Expression is " << status << std::endl;
        log_file << "Did you mean:" << expressionCleaner(long_expression)
                 << " with editing cost:" << nearest_expression.GetCost()
                 << " and occurrences: " << nearest_expression.GetNumOccurances()
                 << std::endl;
      }
    }
    log_file << std::endl;
  };

  bool debuginfo = scan_config_.log_level_ >= LogLevel::INFO;
  if (trie.IsPotentialAnomaly(top_n_nearest_expressions, scan_config_.anomaly_threshold_)) {
    print_autocorrect_results(debuginfo, "Anomaly");
  }
  else {
    print_autocorrect_results(debuginfo, "Okay");
  }
}

template <TreeLevel L>
bool TrainAndScanUtil::ScanExpressionForAnomaly(const Trie& trie, 
    const conditional_expression_t& conditional_expression,
    std::ostream& log_file, std::ostream& cvs_file) const {
  float confidence = 0.0;
  size_t num_occurrances = 0;
  bool found_in_training_dataset = trie.LookUp(
    NodeToShortString<L>(conditional_expression), num_occurrances, confidence);

  // Pretty print
  auto print_details = [&](const std::string& status) {
    try {
      log_file << "Level:" << LevelToString<L>()
             << " Expression:" << expressionCleaner(NodeToString<L>(conditional_expression))
             << " " << status
             << " in training dataset: ";
      cvs_file << LevelToString<L>() << delimiter()
               << expressionCleaner(NodeToString<L>(conditional_expression)) << delimiter()
               << status << delimiter();
    } catch(std::exception& e) {
      // NodeToString can throw exception. Just skip printing in that case.
    }
  };
  print_details(found_in_training_dataset ? "found" : "not found");
  
  // Suggest expressions that are close to current expression. 
  ReportPossibleCorrections<L>(trie, conditional_expression, log_file);
  return found_in_training_dataset;
}

template <TreeLevel L>
bool TrainAndScanUtil::ScanExpressionForAnomaly(const Trie& trie, 
    const std::string& source_file_contents,
    const conditional_expression_t& conditional_expression,
    std::ostream& log_file, const std::string& test_file,
    std::ostream& cvs_file) const {
  float confidence = 0.0;
  size_t num_occurrances = 0;
  bool found_in_training_dataset = false;
  try {
    trie.LookUp(NodeToShortString<L>(conditional_expression),
                num_occurrances, confidence);
  } catch(std::exception& e) {
    log_file << "Error: " << e.what() << std::endl;
    return false;
  }
  log_file << __FILE__ << ":" << __LINE__ << std::endl;
  cvs_file << __FILE__ << delimiter()
           << __LINE__ << delimiter();

  // Pretty print
  auto print_details = [&](const std::string& status) {
    log_file << "Level:" << LevelToString<L>()
             << " Expression:" << expressionCleaner(NodeToString<L>(conditional_expression))
             << " " << status
             << " in training dataset: ";
    cvs_file << LevelToString<L>() << delimiter()
             << expressionCleaner(NodeToString<L>(conditional_expression)) << delimiter()
             << status << delimiter();

    if (test_file != "" && source_file_contents != "") {
      TSPoint start = ts_node_start_point(conditional_expression);
      log_file << "Source file: " << test_file << ":"
               << start.row << ":" << start.column << ":";
      cvs_file << test_file << delimiter()
               << start.row << delimiter()
               << start.column << delimiter();

      log_file << expressionCleaner(OriginalSourceExpression(conditional_expression, source_file_contents)) << std::endl;
      cvs_file << expressionCleaner(OriginalSourceExpression(conditional_expression, source_file_contents)) << delimiter();
    }
  };
  print_details(found_in_training_dataset ? "found" : "not found");
  
  log_file << __FILE__ << ":" << __LINE__ << std::endl;
  cvs_file << __FILE__ << delimiter() << __LINE__ << delimiter();
  // Suggest expressions that are close to current expression. 
  ReportPossibleCorrections<L>(trie, conditional_expression, log_file, cvs_file);
  cvs_file << std::endl;
  return found_in_training_dataset;
}

int TrainAndScanUtil::ScanExpression(const std::string& expression,
    std::ostream& log_file, std::ostream& cvs_file) const {
  ManagedTSTree ts_tree;
  try {
    static bool kReportParseErrors = true;
    ts_tree = GetTSTree(expression, kReportParseErrors);
  } catch (std::exception& e) {
    log_file << "Error: "
             << e.what()
             << " ... skipping"
             << std::endl;
    return 0;
  }
  conditional_expressions_t conditional_expressions;
  CollectConditionalExpressions(ts_tree, conditional_expressions);
  if (conditional_expressions.size() == 0) {
    log_file << "Error: No control structures (e.g., if statement) "
             << "found in the input"
             << std::endl;
    return 0;
  }
  
  for (auto expression : conditional_expressions) {
     ScanExpressionForAnomaly<LEVEL_ONE>(trie_level1_, "", expression,
                                         log_file, "", cvs_file);
  }
  return 0;
}

int TrainAndScanUtil::ScanFile(const std::string& test_file,
    std::ostream& log_file, std::ostream& cvs_file) const {
  // Test it on if statements from evaluation source file.a
  ManagedTSTree ts_tree;
  std::string source_file_contents;
  try {
    ts_tree = GetTSTree(test_file, source_file_contents);
  } catch (std::exception& e) {
    log_file << "Error:" << e.what() << " ... skipping" << std::endl;
    return 0;
  }

  conditional_expressions_t conditional_expressions;
  CollectConditionalExpressions(ts_tree, conditional_expressions);

  size_t num_expressions_found = 0;
  size_t num_expressions_not_found = 0; 
  size_t num_total_expressions = 0;
  size_t level1_hit = 0, level1_miss = 0;
  size_t level2_hit = 0, level2_miss = 0;

  for (auto expression : conditional_expressions) {
    bool is_level1_hit = ScanExpressionForAnomaly<LEVEL_ONE>(trie_level1_,
                          source_file_contents, expression, log_file,
                          test_file, cvs_file);
    bool is_level2_hit = ScanExpressionForAnomaly<LEVEL_TWO>(trie_level2_,
                          source_file_contents, expression, log_file,
                          test_file, cvs_file);
    if (is_level1_hit) level1_hit++; else level1_miss++;
    if (is_level2_hit) level2_hit++; else level2_miss++;
    if (is_level1_hit || is_level2_hit) num_expressions_found++;
    else num_expressions_not_found++;
    num_total_expressions++;
  }

  if (scan_config_.log_level_ >= LogLevel::DEBUG) {
    log_file  << "SUMMARY " << test_file
              << ":Total/Found/Not_found/L1_hit/L1_miss/L2_hit/L2_miss="
              << num_total_expressions << ","
              << num_expressions_found << ","
              << num_expressions_not_found << ","
              << level1_hit << "," << level1_miss << ","
              << level2_hit << "," << level2_miss
              << std::endl;
  }

  return 0;
}
  
int TrainAndScanUtil::ReadTrainingDatasetFromFile(
      const std::string& train_dataset,
      std::ostream& log_file) {
  log_file << "Training: start." << std::endl;

  timer_trie_build_level1_.StartTimer();
  trie_level1_.Build<LEVEL_ONE>(train_dataset);
  timer_trie_build_level1_.StopTimer();
  log_file  << "Trie L1 build took: "
            << timer_trie_build_level1_.TimerDiff()
            << "s"
            << std::endl;
  //trie_level1_.Print(false);
  //trie_level1_.PrintEditDistancesinTrainingSet();
  //exit(0);

  timer_trie_build_level2_.StartTimer();
  trie_level2_.Build<LEVEL_TWO>(train_dataset);
  timer_trie_build_level2_.StopTimer();
  log_file << "Trie L2 build took: "
            << timer_trie_build_level2_.TimerDiff()
            << "s"
            << std::endl;

  log_file << "Training: complete." << std::endl;
  
  //trie_level2_.Print(false);
  //exit(0);

  return 0;
}
