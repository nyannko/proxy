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
	# ssh $1 /bin/bash $cmd & 2>&1 >> result_$node_$instance.dat
}

# check nodes number and reserve hops
check_input() {
    input=$1
    client_num=$((${input}/50))
    # if the node number equals to zero, then let client_num = 1
    if [[ ${client_num} -eq 0 ]]; then
        client_num=1
    fi
    server_num=${client_num} # client : server = 1 : 1
    echo "We will reserve ${client_num} clients and ${server_num} servers"
    total_nodes=$((${client_num}+${server_num}))
    reserve_hop ${total_nodes}
}

################## reserve nodes for testing ##############################
# 第一件事需要弄明白为什么要/可以这么写。
# input: total node numbers reserved
reserve_hop() {
    nhosts=${1}
	reserved_nodes=()
	preserve -t 06:00:00 -# ${nhosts}
	sleep 3
	nodes=($(preserve -long-list | grep gshi |awk 'END{for(i=9;i<=NF;++i)print $i}' ))
	test_id=$(preserve -long-list | grep gshi | awk 'END{{print $1}}')
	for n in "${nodes[@]}"
	do
		reserved_nodes+=(${n})
	done
}

test_hop1() {
    client_nodes=()
    server_nodes=()
    # choose clients from the reserved nodes
    for client in `seq 0 $((${client_num}-1))`; do
        index=$((client))
        client_nodes[index]=${reserved_nodes[index]}
    done
    # debug: verify client nodes
    echo "${client_nodes[@]}"

    # choose server from the reserved nodes, the number is the same as clients
    p_index=${client_num}
    for server in `seq 0 $((${server_num}-1))`; do
        index=$((server))
        server_nodes[index]=${reserved_nodes[p_index]}
        ((p_index++))
    done

    # kill all screen sessions before testing
    for host in "${reserved_nodes[@]}"; do
        send_screen $host kill "screen -wipe; pkill screen"
    done

    # specify test directory
    eval_dir="ipv8t/evaluation/scalability"
    run_dir="ipv8t/socks5_ipv8/hops"

    # run server proxy
    for i in `seq 0 $((${server_num}-1))`; do
        run_server_command="cd $run_dir; python multiproxy2.py --server 50"
        server=${server_nodes[i]};
        echo "run server ${server} ${!server}"
        send_screen ${server} run1 ${run_server_command}
        echo "server run command sent to ${server}"
    done

	# run client proxy
	for i in `seq 0 $((${client_num}-1))`; do
        run_client_command="cd $run_dir; python multiproxy2.py --client 50"
        client=${client_nodes[i]};
        echo "run client ${client} ${!client}"
        send_screen ${client} run1 ${run_client_command}
        echo "client run command sent to ${client}"
    done

    sleep 3

    # test_latency="bash test_latency.sh"
	test_throughput="bash test_throughput.sh"

    # evaluation
    # open 50 ports for client 1-i
    for i in `seq 0 $((${client_num}-1))`;do
        for port in `seq 40000 40049`;do
            echo "port $port $test_throughput";
            client=${client_nodes[i]};
            # get value from client_node1
            send_screen ${client} "eval${port}" "cd ${eval_dir}; ${test_throughput} ${port} ${i}"
        done
    done
	echo "done"
}

_main() {
    check_input $1
    test_hop1
}

_main "$@"
