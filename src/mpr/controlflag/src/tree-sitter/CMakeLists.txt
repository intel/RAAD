cmake_minimum_required(VERSION 3.4.3)
include(ExternalProject)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Tree Sitter Library
project(tree-sitter)
add_library(tree-sitter STATIC
  tree-sitter/lib/src/lib.c
)
target_include_directories(tree-sitter
  PRIVATE
  tree-sitter/lib/src
  tree-sitter/lib/include
)
install(TARGETS tree-sitter
        LIBRARY DESTINATION lib
        ARCHIVE DESTINATION lib)

# Tree Sitter C Library
project(tree-sitter-c)
add_library(tree-sitter-c STATIC
  tree-sitter-c/src/parser.c
)
target_include_directories(tree-sitter-c
  PRIVATE
  tree-sitter-c/src
)
install(TARGETS tree-sitter-c
        LIBRARY DESTINATION lib
        ARCHIVE DESTINATION lib)
