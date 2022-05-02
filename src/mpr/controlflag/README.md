# ControlFlag: A Self-supervised Idiosyncratic Pattern Detection System for Software Control Structures

ControlFlag is a self-supervised idiosyncratic pattern detection system that
learns typical patterns that occur in control structures of high-level
programming language such as C/C++ by mining these patterns from open-source
repositories (on GitHub and other version control systems). It then applies
learned patterns to detect anomalous patterns in user's code.

## Brief technical description

ControlFlag's pattern anomaly detection system can be used for various problems
such as typographical error detection, flagging a missing NULL check to
name a few. *This PoC demonstrates ControlFlag's application in typographical
error detection.*

Figure below shows ControlFlag's two main phases: (1) pattern
mining phase, and (2) scanning for anomalous patterns phase. The pattern mining
phase is a "training phase" that mines typical patterns in user-provided GitHub
repositories and then builds a decision-tree from the mined patterns. The scanning
phase, on the other hand, applies the mined patterns to look for anomalies in
user-specified target repositories.

![ControlFlag design](/projects/controlflag/docs/controlflag_design.jpg)

More details can be found in our MLforSys NeurIPS'20
paper (https://arxiv.org/abs/2011.03616).

## Directory structure (evolving)
- `src`: Source code for ControlFlag for typographical error detection system
- `scripts`: Scripts for pattern mining and scanning for anomalies
- `quick_start`: Scripts to run quick start tests
- `github`: Scripts and data for downloading GitHub repos
  It also contains pre-processed training data containing patterns mined from
6000 GitHub repositories using C as their primary language.

## Install

#### Requirements

- CMake 3.4.3 or above
- C++17 compatible compiler
- [Tree-sitter](https://github.com/tree-sitter/tree-sitter.git) parser (downloaded automatically as part of cmake)
- [GNU parallel](https://www.gnu.org/software/parallel/) (optional, if you want
  to generate your own training data)

#### Build

```
$ cd controlflag
$ cmake .
$ make -j
```

`cf_dump_conditional_exprs` and `cf_file_scanner` binaries should be created under `bin`.

## Using ControlFlag

### Quick start

#### Using patterns obtained from 6000 GitHub repos to scan repository of your choice

Download the training data first
([link](https://intel-my.sharepoint.com/:u:/p/niranjan_hasabnis/EQLfSmIfqkdCjCYejcmn248BD_4YK17u9Ygl-M_Cd_4Z3g?e=2AncAq)).
You will need to be logged in with Intel account to download. If you get
permission problem, pls email [Niranjan Hasabnis](mailto:niranjan.hasabnis@intel.com?subject=[ControlFlag]%20GitHub%20repo).

```
$ wget https://intel-my.sharepoint.com/:u:/p/niranjan_hasabnis/EQLfSmIfqkdCjCYejcmn248BD_4YK17u9Ygl-M_Cd_4Z3g?e=2AncAq
$ (optional) md5sum c_lang_if_stmts_6000_gitrepos.ts.tgz
1ba954d9716765d44917445d3abf8e85
$ tar -zxf c_lang_if_stmts_6000_gitrepos.ts.tgz
```

To scan code of your choice, use below command:

```
$ scripts/scan_for_anomalies.sh -d <your_directory> -t c_lang_if_stmts_6000_gitrepos.ts -o <output_directory_to_store_log_files>
```

Once the run is complete (which could take time depending on your system and the
number of C programs in your repository,) refer to [the section below to
understand scan output](#understanding-scan-output).

#### Mining patterns from a small repo and applying them to another small repo

In this test, we will mine patterns from
[Glb-director](https://github.com/github/glb-director.git) project of GitHub and
apply them to flag anomalies in GitHub's [brubeck](https://github.com/github/brubeck.git) project.

Simply run below command:
```
cd quick_start && ./test1.sh
```

If everything goes well, you can see output from scanner in `test1_scan_output`
directory. Look for "Potential anomaly" label in it by `grep "Potential anomaly"
-C 5 \*.log`, and you should see output like below:

```
thread_6.log-Level:TWO Expression:(parenthesized_expression (binary_expression ("==") (identifier) (non_terminal_expression))) found in training dataset:
Source file: brubeck/src/server.c:266:5:(s == sizeof(fdsi))
thread_6.log-Autocorrect search took 0.000 secs
thread_6.log:Potential anomaly
thread_6.log-Did you mean:(parenthesized_expression (binary_expression ("==") (identifier) (non_terminal_expression))) with editing cost:0 and occurances: 1
thread_6.log-Did you mean:(parenthesized_expression (binary_expression ("==") (identifier) (null))) with editing cost:1 and occurances: 25
thread_6.log-Did you mean:(parenthesized_expression (binary_expression ("==") (identifier) (identifier))) with editing cost:1 and occurances: 5
thread_6.log-Did you mean:(parenthesized_expression (binary_expression (">=") (identifier) (non_terminal_expression))) with editing cost:1 and occurances: 3
thread_6.log-Did you mean:(parenthesized_expression (binary_expression ("==") (non_terminal_expression) (non_terminal_expression))) with editing cost:1 and occurances: 2
```
The anomaly is flagged for `brubeck/src/server.c` at line number `266`.

### Detailed steps

1. __Pattern Mining phase__ (if you want to generate training data yourself)

If you do not want to generate training data yourself, go to [Evaluation step below](#evaluation-or-scanning-for-anomalies-in-c-code-from-test-repo).

In this phase, we mine the idiosyncratic patterns that appear in the control
structures of high-level language such as C. *This PoC mines patterns from `if`
statements that appear in C programs.*

If you want to use your own repository for mining patterns, jump to Step 1.2.

1.1 __Downloading Top-100 GitHub repos for C language__

Steps below show how to download Top-100 GitHub repos for C language
(`c100.txt`) and generate training data. `training_repo_dir` is a directory
where the command below will clone all the repos.

```
$ cd github
$ python download_repos.py -f c100.txt -o <training_repo_dir> -m clone -p 5
```

1.2 __Mining patterns from downloaded repositories__

You can use your own repository to mine for expressions by passing it in
place of <training_repo_dir>.

`mine_patterns.sh` script helps for this. It's usage is as below:

```
Usage: ./mine_patterns.sh -d <directory_to_mine_patterns_from> -o <output_file_to_store_training_data>
Optional:
[-n number_of_processes_to_use_for_mining]  (default: num_cpus_on_system)
```

We use it as:
```
$ scripts/mine_patterns.sh -d <training_repo_dir> -o <training_data_file>
```

`<training_dat_file>` contains conditional expressions in C language and
their AST (abstract syntax tree) representations for all the `if` statements
found in the specified GitHub repos. You can view this file as a text file, if
you want.

## Evaluation (or scanning for anomalies in C code from test repo)

We can run `scan_for_anomalies.sh` script to scan target directory of interest.
It's usage is as below.
```
Usage: ./scan_for_anomalies.sh -t <training_data> -d <directory_to_scan_for_anomalous_patterns>
Optional:
 [-c max_cost_for_autocorrect]              (default: 2)
 [-n max_number_of_results_for_autocorrect] (default: 5)
 [-j number_of_scanning_threads]            (default: num_cpus_on_systems)
 [-o output_log_dir]                        (default: tmp)
 [-a anomaly_threshold]                     (default: 5.0)
```

```
scripts/scan_for_anomalies.sh -d <test_directory> -t <training_data_file> -o <output_log_dir>
```

As a part of scanning for anomalies, ControlFlag also suggests a possible
corrections in case a conditional expression is flagged as anomaly. `25` is the
`max_cost` for correction -- how close should the correction suggested be to
possibly mistyped expression. Increasing `max_cost` leads to suggesting more
corrections. ___If you feel that the number of anomalies that are reported are
high, consider reducing `anomaly_threshold` even lower to `1.0` or less___.

### Understanding scan output

Under `output_log_dir` you will find multiple log files corresponding to
the scan output from different scanner threads. Potential anomalies are reported
with "Potential anomaly" as a label for them. Command below will report log files
containing atleast one anomaly.

```
$ grep "Potential anomaly" <output_log_dir>/thread_*.log
```

A sample anomaly report looks like below:
```
Level:<ONE or TWO> Expression: <AST_for_anomalous_expression>
Source file and line number: <C code with line number having the anomaly>
Potential anomaly
Did you mean ...
```
Text after "Did you mean" are possible corrections that one can do to correct
the anomalous expression.

### Graphical Interface

path: scripts/py3API.py
#### Requirement 
* Python: 3.8+
#### Execute
* python py3API.py

