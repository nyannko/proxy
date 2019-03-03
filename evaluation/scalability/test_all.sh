#!/usr/bin/env bash
# test scalability of nodes in ranges
# input $1: nodes
# bash test_all.sh will test nodes from 1-300

# 300
end=$1

number=(1)
# step == 10
for i in `seq 10 10 ${end}`; do
    number+=(${i})
done

# for remaining nodes
for i in "${number[@]}"; do
    echo "testing for case....." $i
    bash test_scalability.sh ${i}
    sleep 5m;
    printf -v file_suffix "%04d" ${i}
    bash merge.sh $file_suffix;
    # kill screen process for all nodes
    bash kill_all.sh;
    # cancel reservation
    test_id=$(preserve -long-list | grep gshi | awk 'END{{print $1}}')
    preserve -c ${test_id}
    sleep 3s
    rm ~/ipv8t/evaluation/scalability/scalability_res/file*
done