#/bin/sh

function print_usage() {
  echo -n "Usage: $1 -d <directory_to_mine_patterns_from>" 
  echo " -o <output_file_to_store_training_data>"
  echo "Optional:"
  echo "[-n number_of_processes_to_use_for_mining]  (default: num_cpus_on_system)"
  echo "[-v debug script flag]  (default: 0, off = 0, on = 1)"
  echo "I.E."
  echo "./mine_patterns.sh -d ../src -o cf_self_director_training_data.ts"
  exit
}

# Default values, access total threads.
NUM_MINER_PROCS=`nproc`
DEBUG_STATUS=1
CURRENT_TIME=$(date "+%Y-%m-%d-%H-%M-%S")
start=`date +%s.%N`

# Parse arguments
while getopts d:o:n:v: flag
do
  case "${flag}" in
    d) TRAIN_DIR=${OPTARG};;
    o) OUTPUT_FILE=${OPTARG};;
    n) NUM_MINER_PROCS=${OPTARG};;
    v) DEBUG_STATUS=${OPTARG};;
    *) UNKNOWN_ARG=${OPTARG};;
  esac
done

if [ "${DEBUG_STATUS}" = "1" ]
then
  echo "Args: Train Directory=${TRAIN_DIR}"
  echo "Output File          =${OUTPUT_FILE}"
  echo "Total Processes      =${NUM_MINER_PROCS}"
  echo "Debug Flag           =${DEBUG_STATUS}"
  echo "Unknown args         =${UNKNOWN_ARG}"
fi

if [ "${TRAIN_DIR}" = "" ]
then
  echo "ERROR: $0 requires a directory to mine patterns and an output file to store them"
  print_usage "$0"
  echo "NOTE: Try full path. I.E. /home/git/repo"
fi

TRAIN_DIR_PATH=`realpath ${TRAIN_DIR}`
echo "Full train file path: ${TRAIN_DIR_PATH}"

if [ ! -d "${TRAIN_DIR}" ]
then
  echo "ERROR: $0 requires a directory to mine patterns and an output file to store them"
  print_usage "$0"
  echo " NOTE: Try full dir path I.E. ${TRAIN_DIR}=>${TRAIN_DIR_PATH}"
fi

if [ "${OUTPUT_FILE}" = "" ]
then
  echo "ERROR: $0 requires an output file to store them."
  print_usage "$0"
  echo " NOTE: I.E. cf_magic_${CURRENT_TIME}.ts"
fi

OUTPUT_FILE_PATH=`realpath ${OUTPUT_FILE}`
echo "Full output file path ${OUTPUT_FILE_PATH}"

# Inquire user to save previous data.
if [ -f "${OUTPUT_FILE}" ]
then
  echo "ERROR: Output file exists. We don't want to over-write it, so backup content or delete file."
  echo " [I.E.]"
  echo " cp ${OUTPUT_FILE} ${OUTPUT_FILE}_${CURRENT_TIME}.bak"
  echo " rm -f ${OUTPUT_FILE}"
  print_usage 0
fi

TMP_DIR=`mktemp -d -p /tmp`
TMP_FULL_FILE_PATH=`realpath ${TMP_DIR}`
echo "Full temp file path: ${TMP_FULL_FILE_PATH}"
FILE_LIST=${TMP_DIR}/file_list.txt
find "${TRAIN_DIR}" -iname "*.[c|h|C|H|cc|cxx|cpp|hpp|c++|inl]" -type f > "${FILE_LIST}"

function dump_condition_expressions() {
  # Access file content
  id=`echo "$1" | cut -d ':' -f 1`
  f=`echo  "$1" | cut -d ':' -f 2-`
  # Run content through control flag conditional expression tokenizer
  ../bin/cf_dump_conditional_exprs "$f" 100 "${id}" >> "$2"
}
export -f dump_condition_expressions

if ! command -v parallel &> /dev/null
then
  echo "[SERIAL] execution..."
  for id_f in `cat $FILE_LIST`;
  do
    dump_condition_expressions $id_f | tee -a ${OUTPUT_FILE}
  done
else
  echo "[PARALLEL] execution..."
  cat ${FILE_LIST} | parallel --eta --bar --progress \
    -I% -j ${NUM_MINER_PROCS} dump_condition_expressions % ${TMP_DIR}/proc_{%}.log
  ls ${TMP_DIR}/proc_*.log > ${TMP_DIR}/concatFile.log
  for id_f in `cat ${TMP_DIR}/concatFile.log`;
  do
    cat  $id_f >> ${OUTPUT_FILE}
  done
fi

if [ "${DEBUG_STATUS}" = "1" ]
then
  echo "All temp files"
  ls ${TMP_DIR}
else
  rm -rf ${TMP_DIR}
fi

end=`date +%s.%N`
echo "Execution Time in Seconds:"
echo "${end} - ${start}" | bc -l