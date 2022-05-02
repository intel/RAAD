#include <thread>
#include "trie.h"

NearestExpressions Trie::SearchNearestExpressions(
    const NearestExpression::Expression& target,
    NearestExpression::Cost max_cost,
    size_t max_threads) const {
  enum SearchNearestExpressionAlgorithm {
    TRIE_TRAVERSAL,
    CANDIDATE_GENERATION,
    SYMMETRIC_DELETE
  } algorithm = TRIE_TRAVERSAL;

  switch (algorithm) {
    case TRIE_TRAVERSAL:
      return SearchNearestExpressionsUsingTrieTraversal(target, max_cost,
                                                        max_threads);
    case CANDIDATE_GENERATION:
      return SearchNearestExpressionsUsingCandidateGeneration(target, max_cost);
    case SYMMETRIC_DELETE:
      return SearchNearestExpressionUsingSymmetricDelete(target, max_cost);
    default:
      throw "Unsupported algorithm for searching nearest expressions";
  }
}

// ---------------------------------------------------------------------------
// Symmetric delete spelling correction algorithm that does not use insert/
// replace/transpose but just delete operations. It performs orders of magnitude
// better than Norvig's algorithm
//
// See details -
// https://medium.com/@wolfgarbe/1000x-faster-spelling-correction-algorithm-2012-8701fcd87a5f

void Trie::GenerateExpressionCombinationsUsingDelete(
    const NearestExpression::Expression& target,
    NearestExpression::Cost max_cost,
    ExpressionCombinationsAtCost& combinations) const {
  // Using unordered_map to handle duplicate keys.
  auto perform_deletes_for_distance_one = [&](
      const NearestExpression::Expression& expression,
      NearestExpression::Cost current_cost) {
    for (size_t i = 0; i < expression.size(); i++) {
      // O(N) deletions
      NearestExpression::Expression expression_with_char_delete = expression;
      expression_with_char_delete.erase(i, current_cost);
      std::pair<NearestExpression::Expression,
                NearestExpression::Cost> expression_cost(
                                  expression_with_char_delete, current_cost);
      // duplicate keys will be removed by insert.
      combinations.insert(expression_cost);
    }
  };

  // Expression deletes that are N distance away from 'target' can be obtained
  // from Expression deletes that are N-1 distance away by performing 1-cost
  // edit distance.
  NearestExpression::Cost current_cost = 0;
  combinations[target] = current_cost;
  for (current_cost = 1; current_cost <= max_cost; current_cost++) {
    for (const auto& expression_n_minus_1 : combinations) {
      if (expression_n_minus_1.second == current_cost - 1)
        perform_deletes_for_distance_one(expression_n_minus_1.first,
                                         current_cost);
    }
  }
}

NearestExpressions Trie::SearchNearestExpressionUsingSymmetricDelete(
    const NearestExpression::Expression& target,
    NearestExpression::Cost max_cost) const {
  NearestExpressions result;

  // Generate all combinations of target expression by considering deletes upto
  // edit distance of max_cost.
  ExpressionCombinationsAtCost target_combinations_with_delete;
  GenerateExpressionCombinationsUsingDelete(target, max_cost,
      target_combinations_with_delete);
  
  for (const auto& combination : target_combinations_with_delete) {
    const auto it = symmetric_delete_trie_combinations_.find(combination.first);
    if (it != symmetric_delete_trie_combinations_.end()) {
      for (const auto& line_no : it->second) {
        std::string expression = "";
        result.push_back(NearestExpression(expression, combination.second));

        std::cout << "Found combination: " << combination.first
                  << " at cost:" << combination.second
                  << " line no: " << line_no
                  << std::endl;
      }
    }
  }
  return result;
}

// ---------------------------------------------------------------------------

// Peter Norvig algorithm to generate corrections of possible mis-spelled
// expression. The algorithm generates a set of expressions that are 1, 2.. N
// distances away from target expression and then filters out invalid expressions
// by checking them with dictionary.
//
// Algorithm performs in O(N) time, where N is length of the target expression.
// Algorithm performance does not depend on size of trie/dictionary.
NearestExpressions Trie::SearchNearestExpressionsUsingCandidateGeneration(
    const NearestExpression::Expression& target,
    NearestExpression::Cost max_cost) const {
  NearestExpressions result;

  NearestExpressionSet nearest_expressions;
  GenerateCandidateExpressions(target, max_cost, nearest_expressions);
  for (const auto& nearest_expression : nearest_expressions) {
    // If edited expression is a valid expression then keep it.
    NearestExpression::Expression expression = nearest_expression.GetExpression();
    NearestExpression::Cost cost = nearest_expression.GetCost();
    NearestExpression::NumOccurances occurances;
    float confidence;
    if (LookUp(expression, occurances, confidence)) {
      result.push_back(NearestExpression(expression, cost, occurances));
    }
  }
  nearest_expressions.clear();

  return result;
}

void Trie::GenerateCandidateExpressions(
    const NearestExpression::Expression& target,
    NearestExpression::Cost max_cost,
    NearestExpressionSet& result) const {
  // Using set instead of vector to filter out duplicate edits.

  auto perform_edits_for_distance_one = [&](
      const NearestExpression::Expression& expression,
      NearestExpression::Cost current_cost) {
    for (size_t i = 0; i < expression.size(); i++) {
      for (const auto& c : alphabets_) { /* O(N) replacements */
        NearestExpression::Expression expression_with_char_replace = expression;
        // Replacement - perform character replacements that are 1-edit away.
        expression_with_char_replace.replace(i, current_cost, current_cost, c);
        result.insert(NearestExpression(expression_with_char_replace, current_cost));
      }

      for (const auto& c : alphabets_) { /* O(N+1) insertions */
        NearestExpression::Expression expression_with_char_insert = expression;
        // Insert - Insert a character leading to 1-edit distance.
        expression_with_char_insert.insert(i, current_cost, c);
        result.insert(NearestExpression(expression_with_char_insert, current_cost));
      }

      // O(N) deletions
      NearestExpression::Expression expression_with_char_delete = expression;
      expression_with_char_delete.erase(i, current_cost);
      result.insert(NearestExpression(expression_with_char_delete, current_cost));
    }
  };

  // ExpressionEdits that are N distance away from 'target' can be obtained
  // from ExpressionEdits that are N-1 distance away by performing 1-cost
  // edit distance.
  NearestExpression::Cost current_cost = 0;
  result.insert(NearestExpression(target, current_cost));
  for (current_cost = 1; current_cost <= max_cost; current_cost++) {
    for (const auto& expression_n_minus_1 : result) {
      if (expression_n_minus_1.GetCost() == current_cost - 1)
        perform_edits_for_distance_one(expression_n_minus_1.GetExpression(),
                                       current_cost);
    }
  }
}

//---------------------------------------------------------------------------
// Algorithm to generate corrections of possibly mis-spelled expression
// Algorithm goes over whole trie (in other words, training dataset) and
// calculates levenshtein distance between valid strings from trie and
// target expression.
//
// Algorithm performs in O(N) time, where N is number of words in dictionary.
NearestExpressions Trie::SearchNearestExpressionsUsingTrieTraversal (
    const NearestExpression::Expression& target,
    NearestExpression::Cost max_cost,
    size_t max_threads) const {
  // Visit every expression from training dataset/trie and check if
  // it is within max_cost edit distance. If it is, then add to
  // result set.
  std::atomic<size_t> path_index (0);
  NearestExpressions nearest_expressions;
  std::shared_mutex mutex;
  auto calculate_edit_distance_fn = [&]() {
    while(path_index.load() < all_trie_paths.size()) {
      const auto& path_occurrences = all_trie_paths[path_index.load()];
      path_index++;
      const std::string& trie_path = path_occurrences.first;
      size_t num_occurrences = path_occurrences.second;

      NearestExpression::Cost current_cost =
          CalculateEditDistance(trie_path, target);
      if (current_cost <= max_cost) {
        std::unique_lock lock(mutex);
        nearest_expressions.push_back(NearestExpression(trie_path,
                                      current_cost, num_occurrences)); 
      }
    }
  };

  std::vector<std::thread> edit_distance_calculator_threads;
  for (size_t i = 0; i < max_threads; i++) {
    edit_distance_calculator_threads.push_back(std::thread(
                                                calculate_edit_distance_fn));
  }
  for (auto& calculator_thread : edit_distance_calculator_threads) {
    calculator_thread.join();
  }

  return nearest_expressions;
}

// Calculate edit distance between source and target expressions.
NearestExpression::Cost Trie::CalculateEditDistance(const std::string& source,
    const std::string& target) const {
  // Edit distance is calculated by using (M+1)*(N+1) table, where M is length
  // of source and N is length of target. We don't need to allocate
  // whole M*N table though - to calculate a row, we just need its predecessor
  // row. In other words, we can only calculate whole table using 2*N memory.

  // Initialize table's row 0 to calculate distance between "" and target.
  std::string current_expression = "";
  std::vector<NearestExpression::Cost> current_row(target.length() + 1);
  for (size_t i = 0; i < target.length() + 1; i++)
    current_row[i] = i;

  // Save edit distances for current row so that we can use it calculate
  // edit distances for next row.
  auto previous_row = current_row;
  for (const char& source_char : source) {
    current_expression += source_char;
    current_row[0] = current_expression.length();

    // cost of inserting, deleting or replacing one char
    const NearestExpression::Cost kNoEditCost = 0;
    const NearestExpression::Cost kReplaceCost = 1;
    const NearestExpression::Cost kInsertCost = 1;
    const NearestExpression::Cost kDeleteCost = 1;

    auto min_of_3 = [](NearestExpression::Cost a, NearestExpression::Cost b,
                       NearestExpression::Cost c) {
      return std::min(std::min(a, b), c);
    };

    for (size_t i = 1; i < target.length() + 1; i++) {
      NearestExpression::Cost substitution_cost = kNoEditCost;
      if (source_char != target[i - 1])
        substitution_cost = kReplaceCost;
      current_row[i] = min_of_3(current_row[i - 1] + kInsertCost,
                                previous_row[i] + kDeleteCost,
                                previous_row[i - 1] + substitution_cost);
    }
    previous_row = current_row;
  }

  return current_row[target.length()];
}

