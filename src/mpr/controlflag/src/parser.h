#ifndef PARSER_H
#define PARSER_H

#include <thread>
#include "tree_sitter/api.h"

extern "C" const TSLanguage *tree_sitter_c();

enum Language {
  LANGUAGE_C
};

template <Language L> inline const TSLanguage* GetTSLanguage();
template <> inline const TSLanguage* GetTSLanguage<LANGUAGE_C> (){
  return tree_sitter_c();
}

template<Language L>
class ParserBase {
 public:
  ParserBase() {
    parser_ = ts_parser_new();
    ts_parser_set_language(parser_, GetTSLanguage<L>());
  }

  ~ParserBase() {
    if (parser_) {
      ts_parser_delete(parser_);
      parser_ = NULL;
    }
  }

  void ResetTSParser() {
    if (parser_) {
      ts_parser_reset(parser_);
    }
  }

  TSParser* GetTSParser() {
    return parser_;
  } 

 private:
  TSParser* parser_ = NULL;
};

#endif  // PARSER_H
