#ifndef TREE_H
#define TREE_H

template <typename TreeNodeType, typename NodeInfoType> 
class Tree {
 public:
  void Build(const std::string& training_datset) {
  }

  void Print(const TreeNodeType* node, const std::string& prefix) const = 0;

 private:
  void Insert(const std::string& expression) = 0;
}

#endif  // TREE_H
