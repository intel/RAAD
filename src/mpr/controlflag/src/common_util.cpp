#include "parser.h"
#include "common_util.h"

extern "C" const TSLanguage *tree_sitter_c();

ManagedTSTree GetTSTree(const std::string& c_source_file,
                        std::string& file_contents) {
  auto fileScanCStr = c_source_file.c_str();
  char buff[FILENAME_MAX]; // Create string buffer to hold path
  std::string current_working_dir(buff);
  std::fstream ifs(fileScanCStr);
  auto validFileAccess = access(fileScanCStr, F_OK) != -1;
  auto fileIsOpen = ifs.is_open();

  if (!validFileAccess) {
    throw cf_file_access_exception("Invalid file access is with " + c_source_file + "at current working directory " + current_working_dir);
  }
  if (!fileIsOpen) {
    throw cf_file_access_exception("Could not open file " + c_source_file + "at current working directory " + current_working_dir);
  }

  std::stringstream buffer;
  buffer << ifs.rdbuf();
  file_contents = buffer.str();

  // We do not report parse errors at file-level. In our case, source code file
  // may contain parse errors. What we look for is control structures do not
  // have parse errors.
  static bool kReportParseError = false;
  return GetTSTree(file_contents, kReportParseError);
}

ManagedTSTree GetTSTree(const std::string& source_code,
                 bool report_parse_errors) {
  // Make parser thread-local so that we do not need to delete and recreate it
  // for every file to be parsed.
  thread_local ParserBase<LANGUAGE_C> CParser;
  TSParser* parser = CParser.GetTSParser();
  TSTree *tree = ts_parser_parse_string(parser, nullptr,
                                        source_code.c_str(),
                                        source_code.length());  
  // We do not check if there is a parse error at file-level, all that we need
  // to check is that conditional statements do not have parse error.
  auto root_node = ts_tree_root_node(tree);
  CParser.ResetTSParser();
  if (report_parse_errors &&
      (ts_node_is_null(root_node) || ts_node_has_error(root_node))) {
    throw cf_parse_error(source_code);
  }

  return ManagedTSTree(tree);
}

void CollectConditionalExpressions(TSNode& node,
    conditional_expressions_t& conditional_expressions) {
  if (ts_node_is_null(node)) { return; }

  uint32_t count = ts_node_child_count(node);
  for (uint32_t i = 0; i < count; i++) {
    auto child = ts_node_child(node, i);
    if (ts_node_is_null(child) || ts_node_has_error(child)) continue;
    if (IsIfStatement(child)) {
      conditional_expressions.push_back(GetIfConditionNode(child));
    }
    CollectConditionalExpressions(child, conditional_expressions);
  }
}

void CollectConditionalExpressions(ManagedTSTree& tree,
    conditional_expressions_t& conditional_expressions) {
  auto root_node = ts_tree_root_node(tree.get());
  CollectConditionalExpressions(root_node, conditional_expressions);
}

std::string delimiter(void) {
  const std::string cToken = "\t";
  return cToken;
}

std::string spaceCleaner(std::string inputExpression) {
  std::string cleanString = inputExpression;
  cleanString.erase(0, cleanString.find_first_not_of(' ')); // Prefixing spaces
  cleanString.erase(cleanString.find_last_not_of(' ')+1); // Suffix spaces
  return cleanString;
}

std::string expressionCleaner(std::string inputExpression) {
  std::string cleanString = inputExpression;
  cleanString= spaceCleaner(cleanString);
  std::vector<char> tokenCleanList = {'\n', '\t', '\v', '\r', '\f'};  // Tokens to clean from code source.
  for (auto& iterItem : tokenCleanList) {
    cleanString.erase(std::remove(cleanString.begin(), cleanString.end(), iterItem), cleanString.end());
  }
  cleanString= spaceCleaner(cleanString);
  return cleanString;
}
