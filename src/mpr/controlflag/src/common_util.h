#ifndef UTIL_H
#define UTIL_H

#include <string>
#include <vector>
#include <sstream>
#include <memory>
#include <sys/time.h>
#include <exception>
#include <iostream>
#include <algorithm>
#include <filesystem>
#include <fstream>
#include <unistd.h>

#include <tree_sitter/api.h>

std::string delimiter(void);
std::string spaceCleaner(std::string inputExpression);
std::string expressionCleaner(std::string inputExpression);

//----------------------------------------------------------------------------
class cf_string_exception: public std::exception {
 public:
  cf_string_exception(const std::string& message) : message_(message) {}
  virtual const char* what() const noexcept { return message_.c_str(); }
 private:
  std::string message_;
};

class cf_file_access_exception: public cf_string_exception {
 public:
  cf_file_access_exception(const std::string& error) :
    cf_string_exception("File access failed: " + error) {
    std::cout << "Error in File" << error << std::endl;
  }
};

class cf_parse_error: public cf_string_exception {
 public:
  cf_parse_error(const std::string& expression) : 
    cf_string_exception("Parse error in expression:" + expression) {}
};

class cf_unexpected_situation: public cf_string_exception {
 public:
  cf_unexpected_situation(const std::string& error) :
    cf_string_exception("Assert failed: " + error) {}
};

inline void cf_assert(bool value, const std::string& message) {
  if (!value) throw cf_unexpected_situation(message);
}

inline void cf_assert(bool value, const std::string& message,
                     const TSNode& node) {
  cf_assert(value, message + ts_node_string(node));
}

//----------------------------------------------------------------------------

typedef TSNode conditional_expression_t;
typedef std::vector<TSNode> conditional_expressions_t;

/// Memory-managed TSTree object representing the abstract syntax tree of given
/// source code.
class TSTreeDeleter {
 public:
  void operator()(TSTree* tree) {
    ts_tree_delete(tree);
  }
};
using ManagedTSTree = std::unique_ptr<TSTree, TSTreeDeleter>;

/// Parse source code from specified file and return TSNode object for the root
/// as well as original source code content.
ManagedTSTree GetTSTree(const std::string& c_source_file,
                        std::string& source_file_contents);

/// Parse source code from specified string and return TSNode
ManagedTSTree GetTSTree(const std::string& source_code,
                        bool report_parse_errors=false);

inline bool IsIfStatement(const TSNode& node) {
  const std::string& kIfStatement = "if_statement";
  return (0 == kIfStatement.compare(ts_node_type(node)));
}

inline bool IsCommentNode(const TSNode& node) {
  const std::string kCommentNode = "comment";
  return (0 == kCommentNode.compare(ts_node_type(node)));
}

inline TSNode GetIfConditionNode(TSNode& if_statement) {
  const std::string& condition = "condition";
  return ts_node_child_by_field_name(if_statement,
                      condition.c_str(), condition.length());
}

#if 0
inline std::string OriginalSourceExpression(const TSNode& conditional_expression,
    const std::string& source_file_contents) {
  size_t start_byte = ts_node_start_byte(conditional_expression);
  size_t end_byte =  ts_node_end_byte(conditional_expression);
  return source_file_contents.substr(start_byte, end_byte - start_byte);
}
#endif


void CollectConditionalExpressions(TSNode& root_node,
    conditional_expressions_t& conditional_expressions);

void CollectConditionalExpressions(ManagedTSTree& tree,
    conditional_expressions_t& conditional_expressions);

//----------------------------------------------------------------------------
// A simple microsec precisoon timer for profiling

class Timer {
 public:
  inline int StartTimer() {
    struct timezone *tz = NULL;
    return gettimeofday(&start_tv_, tz);
  }

  inline int StopTimer() {
    struct timezone *tz = NULL;
    return gettimeofday(&end_tv_, tz);
  }

  inline struct timeval TimerDiffToTimeval() const {
    static const suseconds_t kMicroSecs = 1000000;
    auto timeval2microsec = [&](const struct timeval& tv) {
      return tv.tv_sec * kMicroSecs + tv.tv_usec;
    };

    suseconds_t diff_microsec = timeval2microsec(end_tv_) -
                                timeval2microsec(start_tv_);
    struct timeval diff_tv = {.tv_sec = diff_microsec / kMicroSecs,
                              .tv_usec = diff_microsec % kMicroSecs};
    return diff_tv;
  }

  inline std::string TimerDiff() const {
    struct timeval diff_tv = TimerDiffToTimeval();
    std::ostringstream ret_string;
    ret_string << diff_tv.tv_sec << ".";
    ret_string.width(3);
    ret_string.fill('0');
    // Print only 3 decimal points in millisecs.
    ret_string << diff_tv.tv_usec / 1000;
    return ret_string.str();
  }

  private:
    struct timeval start_tv_;
    struct timeval end_tv_;
};

#endif  // UTIL_H
