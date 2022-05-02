#ifndef TRAIN_AND_SCAN_UTIL_H
#define TRAIN_AND_SCAN_UTIL_H

#include <iostream>
#include <string>
#include <atomic>
#include <shared_mutex>
#include <mutex>

#include "trie.h"
#include "common_util.h"
#include <tree_sitter/api.h>
  
//----------------------------------------------------------------------------
// Class that provides Train and Scan functions of ControlFlag system
class TrainAndScanUtil {
 public:
  enum LogLevel {
    MIN = 0,
    ERROR = MIN,
    INFO,
    DEBUG,
    MAX = DEBUG
  };

  struct ScanConfig {
    size_t max_cost_ = 2;
    TreeLevel max_level_ = LEVEL_MAX;
    size_t max_autocorrections_ = 5;
    size_t num_threads_ = 1;
    float anomaly_threshold_ = 5;
    LogLevel log_level_ = LogLevel::ERROR;
  };

  friend class NearestExpressionCache;

  TrainAndScanUtil(const ScanConfig& config) : scan_config_(config) {}

  int ReadTrainingDatasetFromFile(const std::string& train_dataset,
                                  std::ostream& log_file);
  int ScanFile(const std::string& test_file, std::ostream& log_file, std::ostream& cvs_file) const;
  int ScanExpression(const std::string& expression, std::ostream& log_file, std::ostream& cvs_file) const;
  
 private:

  template <TreeLevel L>
  void ReportPossibleCorrections(const Trie& trie,
      const conditional_expression_t& conditional_expression,
      std::ostream& log_file, std::ostream& cvs_file) const;

  template <TreeLevel L>
  bool ScanExpressionForAnomaly(const Trie& trie, 
      const conditional_expression_t& conditional_expression,
      std::ostream& log_file, std::ostream& cvs_file) const;

  template <TreeLevel L>
  bool ScanExpressionForAnomaly(const Trie& trie, 
      const std::string& source_file_contents,
      const conditional_expression_t& conditional_expression,
      std::ostream& log_file, const std::string& test_file, std::ostream& cvs_file) const;

 private:
  Trie trie_level1_;
  Trie trie_level2_;
  Timer timer_trie_build_level1_;
  Timer timer_trie_build_level2_;

  ScanConfig scan_config_;
};

/// Cache nearest expressions for a given expression so that we
/// minimize computing nearest expressions over trie for every
/// given expression. Cache is shared by all the scanner threads.
template <TreeLevel L>
class NearestExpressionsCache {
  public:
    bool LookUp(const NearestExpression::Expression& conditional_expression,
                NearestExpressions& nearest_expressions) {
      // shared lock for concurrent reads
      std::shared_lock lock(mutex_);
      const auto iter = cache_.find(conditional_expression);
      if (iter == cache_.end()) {
        miss_++;
        return false;
      } else {
        nearest_expressions = iter->second;
        hit_++;
        return true;
      }
    }

    void Insert(const NearestExpression::Expression& conditional_expression,
                NearestExpressions& nearest_expressions) {
      // unique lock for writing
      std::unique_lock lock(mutex_);
      cache_[conditional_expression] = nearest_expressions;
    }

    NearestExpressionsCache(const TrainAndScanUtil::ScanConfig& scan_config) :
        hit_(0), miss_(0), log_level_(scan_config.log_level_) {}
    ~NearestExpressionsCache() {
      if (log_level_ == TrainAndScanUtil::LogLevel::DEBUG)
        std::cout << "ExpressionCache statistics: hit/miss="
                  << hit_.load() << "/" << miss_.load() << std::endl;
    }

  private:
    std::shared_mutex mutex_;
    std::unordered_map<NearestExpression::Expression,
                       NearestExpressions> cache_;
    std::atomic<size_t> hit_;
    std::atomic<size_t> miss_;
    TrainAndScanUtil::LogLevel log_level_;
};

#endif  // TRAIN_AND_SCAN_UTIL_H
