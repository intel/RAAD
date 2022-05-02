cmake_minimum_required(VERSION 3.4.3)
include(ExternalProject)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_subdirectory(tree-sitter)

# Control Flag base library
project(cf_lib)
add_library(cf_lib
  common_util.cpp
  train_and_scan_util.cpp
  tree_abstraction.cpp
  trie.cpp
  result_processing.cpp
  autocorrect.cpp
) 
target_include_directories(cf_lib
  PRIVATE
  ${TREE_SITTER_INCLUDE}
)
install(TARGETS cf_lib
        LIBRARY DESTINATION lib
        ARCHIVE DESTINATION lib)

project(cf_file_scanner)
add_executable(cf_file_scanner cf_file_scanner.cpp)
target_include_directories(cf_file_scanner
  PRIVATE
  ${TREE_SITTER_INCLUDE}
)
target_link_libraries(cf_file_scanner
  cf_lib
  tree-sitter
  tree-sitter-c
  pthread
)
install(TARGETS cf_file_scanner RUNTIME DESTINATION bin)

project(cf_server)
add_executable(cf_server cf_server.cpp)
target_include_directories(cf_server
  PRIVATE
  ${TREE_SITTER_INCLUDE}
)
target_link_libraries(cf_server
  cf_lib
  tree-sitter
  tree-sitter-c
  pthread
)
install(TARGETS cf_server RUNTIME DESTINATION bin)

project(cf_client)
add_executable(cf_client cf_client.cpp)
target_include_directories(cf_client
  PRIVATE
  ${TREE_SITTER_INCLUDE}
)
target_link_libraries(cf_client
  cf_lib
  tree-sitter
  tree-sitter-c
  pthread
)
install(TARGETS cf_client RUNTIME DESTINATION bin)

project(cf_dump_conditional_exprs)
add_executable(cf_dump_conditional_exprs cf_dump_conditional_exprs.cpp)
target_include_directories(cf_dump_conditional_exprs
  PRIVATE
  ${TREE_SITTER_INCLUDE}
)
target_link_libraries(cf_dump_conditional_exprs
  cf_lib
  tree-sitter
  tree-sitter-c
)
install(TARGETS cf_dump_conditional_exprs RUNTIME DESTINATION bin)
