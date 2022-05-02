#include <algorithm>
#include <vector>
#include <utility>
#include <queue>

#include "trie.h"
#include "common_util.h"
#include "tree_abstraction.h"

void Trie::Insert(const std::string& expression, size_t line_no,
                  size_t contributor_id) {
  std::string short_expr =
    ExpressionCompacter::Get().Compact(expression);

  struct TrieNode *node = this->root_;
  for (size_t i = 0; i < short_expr.length(); i++) {
    char c = short_expr[i];
    // Increment occurances for every node along the path
    // to keep track of number of occurances of different prefixes.
    node->num_occurances_++;
    auto child_iterator = node->children_.find(c);
    if (child_iterator == node->children_.end()) {
      node->children_[c] = new TrieNode(c);
      node = node->children_[c];
    } else {
      node = child_iterator->second;
    }
    // Insert this char into the alphabet list supported by this trie.
    // This info is used in auto-correction feature.
    alphabets_.insert(c);
  }
  node->num_occurances_++;  // num occurances for leaf nodes.
  node->terminal_node_ = true;
  if (node->pattern_contributors_.find(contributor_id) ==
      node->pattern_contributors_.end()) {
    // initialize to 0.
    node->pattern_contributors_[contributor_id] = 0;
  }
  node->pattern_contributors_[contributor_id]++;

#if 0
  static size_t count = 0;
  if (count == 1000) {
    for (const auto& combinations : symmetric_delete_trie_combinations_)
      std::cout << combinations.first << std::endl;
  }
  count++;

  ExpressionCombinationsAtCost target_combinations_with_delete;
  GenerateExpressionCombinationsUsingDelete(short_expr, 2,
      target_combinations_with_delete);
  for (const auto& combination : target_combinations_with_delete) {
    symmetric_delete_trie_combinations_[combination.first].insert(line_no);
  }
#endif
}

bool Trie::LookUp(const std::string& str, size_t& num_occurances,
                        float& confidence) const {
  struct TrieNode *node = root_;

  const bool kFound = true;
  for (size_t i = 0; i < str.length(); i++) {
    auto child_iterator = node->children_.find(str[i]);
    if (child_iterator == node->children_.end())
      return !kFound;
    else
      node = child_iterator->second;
  }

  if (node->terminal_node_ == false)
    return false;

  num_occurances = node->num_occurances_;
  confidence = node->confidence_;
  return kFound;
}

#if 0
void Trie::VisitAllLeafNodes(VisitorCallbackFn callback_fn) const {
   std::function<void(const TrieNode*, const std::string&)> visitor_helper = 
      [&](const TrieNode* node, const std::string& path_prefix) {
    // Root's character is dummy char and not a valid char from all of trie's
    // expressions. So skip it.
    const std::string& new_path_prefix = node == root_ ? path_prefix :
      path_prefix + node->c_;

    if (node->terminal_node_) {
      callback_fn(new_path_prefix, node->num_occurances_);
    }
    for (const auto& child : node->children_) {
      visitor_helper(child.second, new_path_prefix);
    }
  };
  const std::string& kRootPrefix = "";
  visitor_helper(root_, kRootPrefix);
}
#endif

void Trie::VisitAllLeafNodes(VisitorCallbackFn callback_fn) const {
  // DFS based tree traversal.
  using queue_element_t = std::pair<const TrieNode*, std::string>;
  std::queue<queue_element_t> q;
  std::string kRootPathPrefix = "";
  q.push(queue_element_t(root_, kRootPathPrefix));

  while (!q.empty()) {
    auto node_prefix_pair = q.front();
    q.pop();
    const TrieNode* node = node_prefix_pair.first;
    const std::string& path_prefix = node_prefix_pair.second;
    
    if (node->terminal_node_) {
      callback_fn(path_prefix, node->num_occurances_,
                  node->pattern_contributors_);
    }

    for (const auto& child : node->children_) {
      q.push(queue_element_t(child.second, path_prefix + child.second->c_));
    }
  }
}

void Trie::Print(bool sorted) const {
  struct Path {
    std::string path_string_;
    size_t num_occurances_;
    PatternContributorsMap pattern_contributors_;

    Path(std::string path_string, size_t num_occurances,
         const PatternContributorsMap& pattern_contributors) {
      path_string_ = path_string;
      num_occurances_ = num_occurances;
      pattern_contributors_ = pattern_contributors;
    }
  };

  std::vector<struct Path> paths;
  VisitAllLeafNodes([&](const std::string& path_string, size_t num_occurances,
                        const PatternContributorsMap& pattern_contributors) {
    //std::pair<std::string, size_t> path(path_string, num_occurances);
    Path path(path_string, num_occurances, pattern_contributors);
    paths.push_back(path);
  });

  if (sorted) {
    auto sort_by_occurances = [](Path p1, Path p2) {
      return p1.num_occurances_ >= p2.num_occurances_;
    };
    std::sort(paths.begin(), paths.end(), sort_by_occurances);
  }

  for (const auto& path : paths) {
    std::cout << ExpressionCompacter::Get().Expand(path.path_string_)
              << "," << path.num_occurances_ << ","
              << path.pattern_contributors_.size();
    for (const auto& contributor : path.pattern_contributors_) {
      std::cout << ",(" << contributor.first << ";" << contributor.second << ")";
    }
    std::cout << std::endl;
  }
}

void Trie::PrintEditDistancesinTrainingSet() const {
  VisitAllLeafNodes([&](const std::string& path_string, size_t num_occurances,
                        const PatternContributorsMap& pattern_contributors) {
    //std::pair<std::string, size_t> path(path_string, num_occurances);
    const NearestExpression::Cost kMaxEditDistance = 3;
    const size_t kMaxThreads = 1;
    auto nearest_expressions = SearchNearestExpressions(path_string,
                                                        kMaxEditDistance,
                                                        kMaxThreads);
    std::cout << "Expression is: " << ExpressionCompacter::Get().Expand(path_string)
              << std::endl;
    if (IsPotentialAnomaly(nearest_expressions, 1)) {
      std::cout << "Potential anomaly" << std::endl;
    }
    for (auto nearest_expression : nearest_expressions) {
      std::string long_expression = ExpressionCompacter::Get().Expand(
            nearest_expression.GetExpression());
      std::cout << "Did you mean:" << long_expression
               << " with editing cost:" << nearest_expression.GetCost()
               << " and occurances: " << nearest_expression.GetNumOccurances()
               << std::endl;
    }
    std::cout << std::endl;

  });
}
