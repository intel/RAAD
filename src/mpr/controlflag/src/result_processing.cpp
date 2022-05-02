#include <algorithm>
#include "trie.h"

void Trie::SortAndRankResults(NearestExpressions& nearest_expressions) const {
  // We have N results, where each result contains a cost and number of
  // occurances. We will now rank these results on their likelyhood of
  // suggesting correct change.

#if 0
  size_t total_occurances = 0;
  for (auto result : results) {
    total_occurances += std::get<TUPLE_OCCURANCES_INDEX>(result);
  }

  auto get_expression_score = [&](const nearest_expression_t& e) {
    size_t distance = std::get<TUPLE_COST_INDEX>(e);
    size_t num_occurances = std::get<TUPLE_OCCURANCES_INDEX>(e);
    float fraction_occurances = num_occurances / total_occurances;
    float distance_weight = 1 / (distance + 1);
    return fraction_occurances * distance_weight * 100;
  };
#endif

  auto sort_expressions_by_score = [](const NearestExpression& e1,
                                      const NearestExpression& e2) -> bool {
    // Higher score is better.
    //return get_expression_score(e1) < get_expression_score(e2);
    // Sort by cost. If cost is same, then sort by occurances.
    // Lower the cost is better. Higher the occurances are better.
    return e1.GetCost() == e2.GetCost()
           ? e1.GetNumOccurances() > e2.GetNumOccurances()
           : e1.GetCost() < e2.GetCost();
  };

  std::sort(nearest_expressions.begin(), nearest_expressions.end(),
            sort_expressions_by_score);
}

bool Trie::IsPotentialAnomaly(const NearestExpressions& expressions,
                              float anomaly_threshold) const {
  // If the percentage of the number of occurances at edit distance 0 are below
  // anomaly_threshold in comparison to the total of maximum number of
  // occurances at other edit distances (1, 2, ..) then
  // that likely indicates a potential anomaly.
  
  // Generate edit distance (cost) -> max occurances map.
  std::unordered_map<NearestExpression::Cost,
                     NearestExpression::NumOccurances> max_occurances_at_cost;
  for (const auto& expression : expressions) {
    auto cost = expression.GetCost();
    auto occurances = expression.GetNumOccurances();
    auto it = max_occurances_at_cost.find(cost);
    if (it == max_occurances_at_cost.end())
      max_occurances_at_cost[cost] = occurances;
    else
      max_occurances_at_cost[cost] = std::max(it->second, occurances);
  }

  // Calculate total of max occurances at all the cost levels.
  float total_occurances = 0;
  for (const auto& cost_occurance : max_occurances_at_cost) {
    // Using 1/cost+1 as a weight or probability to use max occurances.
    // Errors that are 1 distance away are more likely than those that are 2
    // distance away.
    float weight = 1.0; // For costs 0 and 1, we want to use full weight.
    if (cost_occurance.first > 1) 
      weight = static_cast<float>(1) / (cost_occurance.first + 1);
    float weighted_max_occurances = weight *
                                    static_cast<float>(cost_occurance.second);
    total_occurances += weighted_max_occurances;
  }
  
  // Calculate percentage of every cost from total cost.
  std::unordered_map<NearestExpression::Cost, float> percent_occurances_at_cost;
  float lowest_percent = 100;
  for (const auto& cost_occurance : max_occurances_at_cost) {
    auto cost = cost_occurance.first;
    auto occurance = cost_occurance.second;
    percent_occurances_at_cost[cost] = (occurance * 100 ) / total_occurances;
    lowest_percent = std::min(lowest_percent, percent_occurances_at_cost[cost]);
  }

  const NearestExpression::Cost kZeroCost = 0;
  if (percent_occurances_at_cost.find(kZeroCost) !=
      percent_occurances_at_cost.end()) {
    if (percent_occurances_at_cost[kZeroCost] < anomaly_threshold &&
        percent_occurances_at_cost[kZeroCost] == lowest_percent)
      return true;
  }
  return false;
}
