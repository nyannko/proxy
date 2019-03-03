#!/usr/bin/env bash

send_screen() {
    ## node ip; session name; command
    echo "ssh to node $1"
	ssh $1 /bin/bash << EOF
	source ~/.bashrc
	screen -dm -S $2
	sleep 0.2
	screen -S $2 -X stuff "${@:3}^M"
EOF
}

kill_all() {
    nodes=($(preserve -long-list | grep gshi |awk 'END{for(i=9;i<=NF;++i)print $i}' ))
    for n in "${nodes[@]}"
	do
		reserved_nodes+=(${n})
		send_screen ${n} kill "pkill screen"
	done
}

kill_all