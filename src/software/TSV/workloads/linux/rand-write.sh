[global]
direct=1
filename=/dev/nvme0n1
log_avg_msec=500
time_based
ioengine=libaio
percentile_list=1:5:10:20:30:40:50:60:70:80:90:95:99:99.5:99.9:99.95:99.99:99.999:99.9999

[rand-write-4k-qd32]
runtime=120s
bs=4k
iodepth=8
numjobs=2
cpus_allowed=0,1
ioengine=libaio
rw=randwrite
group_reporting
stonewall
