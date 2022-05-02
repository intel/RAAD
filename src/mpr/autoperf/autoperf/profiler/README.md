#1. set environment variable before using the library:
export PERFPOINT_EVENT_INDEX=#num

void setMonitoringEventName(){ //from  env variable
     char* env_p = std::getenv("PERFPOINT_EVENT_INDEX");

Git
https://github.com/plasma-umass/sheriff
https://github.com/UTSASRG/sheriff-1

@inproceedings{Liu:2011:SPD:2048066.2048070,
 author = {Liu, Tongping and Berger, Emery D.},
 title = {SHERIFF: precise detection and automatic mitigation of false sharing},
 booktitle = {Proceedings of the 2011 ACM International Conference on Object-Oriented Programming Systems, Languages, and Applications},
 series = {OOPSLA '11},
 year = {2011},
 isbn = {978-1-4503-0940-0},
 location = {Portland, Oregon, USA},
 pages = {3--18},
 numpages = {16},
 url = {http://doi.acm.org/10.1145/2048066.2048070},
 doi = {http://doi.acm.org/10.1145/2048066.2048070},
 acmid = {2048070},
 publisher = {ACM},
 address = {New York, NY, USA},
 keywords = {false sharing, multi-threaded},
}