#include "suffix_tree.h"

void SuffixTree::Insert(const std::string& str) {
  struct suffix_tree_node *node = this->root_;

  for (size_t i = 0; i < str.length(); i++) {
    char c = str[i];
    int child_index = Char2ChildIndex(c);
    assert(child_index < TRIE_CHAR_COUNT && child_index >= 0);
    assert(node != NULL);
    // Increment occurances for every node along the path
    // to keep track of number of occurances of different prefixes.
    node->num_occurances_++;
    if (node->children_[child_index] == NULL) {
      node->children_[child_index] = new TrieNode(c);
    }
    node = node->children_[child_index];
  }
  node->num_occurances_++;  // num occurances for leaf nodes.
  node->terminal_node_ = true;
}
