#/bin/sh

function print_usage() {
  echo -n "Usage: $1 -t <training_data>"
  echo " -d <directory_to_scan_for_anomalous_patterns>"
  echo "Optional:"
  echo " [-c max_cost_for_autocorrect]              (default: 2)"
  echo " [-n max_number_of_results_for_autocorrect] (default: 5)"
  echo " [-j number_of_scanning_threads]            (default: num_cpus_on_systems)"
  echo " [-o output_log_dir]                        (default: /tmp)"
  echo " [-a anomaly_threshold]                     (default: 5.0)"

  exit
}

OUTPUT_DIR="/tmp"
MAX_AUTOCORRECT_COST=2
MAX_AUTOCORRECT_RESULTS=5
NUM_SCAN_THREADS=`nproc`
ANOMALY_THRESHOLD=5

while getopts d:t:o:c:n:j:a: flag
do
  case "${flag}" in
    d) SCAN_DIR=${OPTARG};;
    t) TRAIN_FILE=${OPTARG};;
    o) OUTPUT_DIR=${OPTARG};;
    c) MAX_AUTOCORRECT_COST=${OPTARG};;
    n) MAX_AUTOCORRECT_RESULTS=${OPTARG};;
    j) NUM_SCAN_THREADS=${OPTARG};;
    a) ANOMALY_THRESHOLD=${OPTARG};;
  esac
done

if [ "${SCAN_DIR}" = "" ] || [ "${TRAIN_FILE}" = "" ] ||
   [ ! -d "${SCAN_DIR}" ] || [ ! -f "${TRAIN_FILE}" ] ||
   [ ! -d "${OUTPUT_DIR}" ]
then
  echo "ERROR: $0 requires training data file and a directory to scan for anomalies"
  print_usage $0
fi

SCAN_FILE_LIST=`mktemp -p ~/tmp`
find "${SCAN_DIR}" -iname "*.[c|h|C|H|cc|cxx|cpp|hpp|c++|inl]" -type f > ${SCAN_FILE_LIST}

../bin/cf_file_scanner -t ${TRAIN_FILE} -l ${SCAN_FILE_LIST} \
-c ${MAX_AUTOCORRECT_COST} \
-n ${MAX_AUTOCORRECT_RESULTS} \
-j ${NUM_SCAN_THREADS} \
-o ${OUTPUT_DIR} \
-a ${ANOMALY_THRESHOLD}

rm ${SCAN_FILE_LIST}
