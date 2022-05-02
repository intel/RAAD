#ifndef SUFFIX_TREE_H
#define SUFFIX_TREE_H

class SuffixTree {
 public:
  struct suffix_tree_node {
   public:
    suffix_tree_node(char c, bool terminal_node) : c_(c),
      terminal_node_(terminal_node) {
      for (size_t i = 0; i < TRIE_CHAR_COUNT; i++)  
        children_[i] = NULL;
    }

    ~suffix_tree_node() {
      for (size_t i = 0; i < TRIE_CHAR_COUNT; i++) {
        if (children_[i] != NULL)
          delete children_[i];
      }
    }

    char c_;
    std::vector<std::string> matching_expressions_;
    bool terminal_node_;
    struct suffix_tree_node* children_[TRIE_CHAR_COUNT];
  };

 public:
  SuffixTree() : root_(new suffix_tree_node(' ', false)) {}
  ~SuffixTree() { delete root; }

  void Build(const std::string& train_dataset) {
    std::ifstream stream(train_dataset.c_str());

    const std::string ast_expression = "AST_expression:";
    auto is_ast_expression = [&](const std::string& line) -> bool {
      if (line.length() < ast_expression.length())
        return false;
      for (size_t i = 0; i < ast_expression.length(); i++)
        if (line[i] != ast_expression[i])
          return false;
      return true;
    };

    std::string line;
    while (std::getline(stream, line)) {
      // We include original C expressions as comment for AST expression.
      // We do not want to insert C expressions in trie, just AST expressions.
      if (is_ast_expression(line))
        Insert(line.substr(ast_expression.length(), std::string::npos));
    }
  }

 private:
  void Insert(const std::string& str);
  bool LookUp(const std::string& str, size_t& num_occurances,
                    float& confidence) const;
  void Print(const TrieNode *node, const std::string& prefix) const;

 private:
  suffix_tree_node* root_; 
}

#endif // SUFFIX_TREE_H
