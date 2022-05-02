cmake_minimum_required(VERSION 3.4.3)
project(control_flag)
include(ExternalProject)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Choose the type of build, options are: None Debug Release RelWithDebInfo
# MinSizeRel ... 1. Release: high optimization level, no debug
# info, code or asserts. 2. Debug: No optimization, asserts enabled,
# [custom debug (output) code enabled],    debug info included
# in executable (so you can step through the code with a    debugger
# and have address to source-file:line-number translation). 3.
# RelWithDebInfo: optimized, *with* debug info, but no debug (output)
# code or asserts. 4. MinSizeRel: same as Release but optimizing
# for size rather than speed.
set(CMAKE_BUILD_TYPE Release)
#set(CMAKE_BUILD_TYPE RelwithDebInfo)
#set(CMAKE_BUILD_TYPE Debug)

# Add warnings if debugging source => -Wall -Wextra
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -lrt -g -O0 -m64 -static-libgcc -static-libstdc++ -march=native")
set(CMAKE_EXE_LINKER_FLAGS "-static-libgcc -static-libstdc++")
set(CMAKE_FIND_LIBRARY_SUFFIXES .a)
# C++ compile
set(CMAKE_EXE_LINK_DYNAMIC_CXX_FLAGS)
set(CMAKE_SHARED_LIBRARY_CXX_FLAGS)
set(CMAKE_SHARED_LIBRARY_LINK_CXX_FLAGS)
# C Compile
set(CMAKE_EXE_LINK_DYNAMIC_C_FLAGS)
set(CMAKE_SHARED_LIBRARY_C_FLAGS)
set(CMAKE_SHARED_LIBRARY_LINK_C_FLAGS)
# Set RPATH to use for installed targets; append linker search path
set(CMAKE_INSTALL_RPATH "${CMAKE_INSTALL_PREFIX}/${LOFAR_LIBDIR}")
set(CMAKE_INSTALL_RPATH_USE_LINK_PATH TRUE)

set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)

if(NOT EXISTS ${PROJECT_SOURCE_DIR}/src/tree-sitter/tree-sitter)
    execute_process(
        COMMAND git clone https://github.com/tree-sitter/tree-sitter.git ${PROJECT_SOURCE_DIR}/src/tree-sitter/tree-sitter
    )
endif()

if(NOT EXISTS ${PROJECT_SOURCE_DIR}/src/tree-sitter/tree-sitter-c)
    execute_process(
        COMMAND git clone https://github.com/tree-sitter/tree-sitter-c.git ${PROJECT_SOURCE_DIR}/src/tree-sitter/tree-sitter-c
    )
endif()

get_filename_component(TREE_SITTER_INCLUDE src/tree-sitter/tree-sitter/lib/include ABSOLUTE)

include_directories("${PROJECT_SOURCE_DIR}/src")
include_directories("${PROJECT_SOURCE_DIR}/src/tree-sitter/tree-sitter/lib/include")
include_directories("${PROJECT_SOURCE_DIR}/src/tree-sitter/tree-sitter-c/src/tree_sitter")
add_subdirectory(src)

