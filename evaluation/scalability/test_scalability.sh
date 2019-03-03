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

cleanup() {
     ssh $1 /bin/bash killall -KILL $cmd
}

# input: task name: the name of bash script
# port: proxy port number
# id: distinguish filenames
# nodes: input node numbers
test_n_nodes() {
    task=$1
    port=$2
    id=$3
    nodes=$4

    # check the number of nodes before send the command
    if [[ "${nodes}" -lt 100 ]]; then
        echo "nodes number less than 100"
        repeat_num=`seq 40000 $((40000+${nodes}))`
    elif [[ "${nodes}" -eq 100 ]]; then
        repeat_num=`seq 40000 40099`
    fi

	for port in repeat_num ;do
        echo "port ${port} ${task}"
	    send_screen $client_node "eval${port}" "cd $eval_dir; ${task} ${port} ${id} >> ./scalability_res/file${port}.txt";
	done
}

################## reserve nodes for testing ##############################

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

# cancel reservation
cancel_hop() {
    preserve -c test_id
}

## check input
check_input() {
    min_node=$1
    max_node=$2
    if [ $# -eq 1 ]; then
        max_node=$1
        echo "We will start $1 clients"
    fi

    # for example, input is 299, then clients=1, remaining_client=1, server_node=1
    # the number of client nodes for 100 port number
    clients=$((${max_node} / 100))
    echo "reserve ${clients} client nodes"
    # the number of remaining client nodes
    remaining_client=$((${max_node} % 100))
    if [[ ${remaining_client} -gt 0 ]]; then
        special_client=1
        echo "Need to reserve ${special_client} more client node"
    fi

    # the number of server node
    server_node=1
    echo "reserve ${server_node} server node"

    # zero for default special_client number
    client_nodes=$((${clients}+${special_client:-0}))
    total_nodes=$((${clients}+${special_client:-0}+${server_node}))

    echo "We will reserve ${total_nodes}"
    reserve_hop ${total_nodes}
}

get_nodes() {
    # get nodes
    if [[ ! -f reserved_nodes.txt ]]; then
        # cancel the reservation
        preserve -c ${test_id}
        reserve_hop ${total_nodes}
        # write reserved nodes to file
        echo "save reserved nodes to file"
        printf "%s\n" "${reserved_nodes[@]}" > reserved_nodes.txt
    else
        # read reserved nodes from file
        reserved_nodes=()
        filename="reserved_nodes.txt"
        while read -r line; do
            name="$line"
            reserved_nodes+=(${name})
            echo "Name read from file - $name"
        done < "$filename"
        echo ${reserved_nodes[0]}
        echo ${reserved_nodes[1]}
    fi
}
######################### test local hop1 #################################
# 1. run server proxy
# 2. run client proxy
# 3. open ten curl sessions in clients
###########################################################################
test_hop1() {
    # assign the server node
    server_node=${reserved_nodes[0]}
	echo ${server_node}

    # assign client nodes: client_node1=${reserved_nodes[0]}
    echo ${reserved_nodes[@]}
    client_node=()
    for client_num in `seq 1 $clients`; do
        index=$((client_num-1))
        client_node[index]=${reserved_nodes[client_num]}
    done

    # assign remaining client node if exists
    if [[ ${remaining_client} -gt 0 ]]; then
        ((client_num++))
        special_client=${reserved_nodes[client_num]}
        echo " get special client ${special_client}"
    fi


	# kill all screen sessions before testing,
	# example: send $server_node kill "pkill screen"
	for host in "${reserved_nodes[@]}"; do
	send_screen $host kill "screen -wipe;pkill screen"
	done

    # specify test directory
    eval_dir="ipv8t/evaluation/scalability"
    run_dir="ipv8t/socks5_ipv8/hops"

    # run server proxy
	run_server_command="cd $run_dir; python multiproxy.py --server 1"
	send_screen $server_node run2 $run_server_command
	echo "server run command sent to ${server_node}"

	# run client proxy
	for i in `seq 1 ${clients}`; do
        run_client_command="cd $run_dir; python multiproxy.py --client 100"
        client=${client_node[$((i-1))]};
        echo "run client ${client} ${!client}"
        send_screen ${client} run1 $run_client_command
        echo "client run command sent to ${client}"
    done

    run_client_command="cd $run_dir; python multiproxy.py --client ${remaining_client}"
    send_screen ${special_client} run1 $run_client_command
    echo "client run command sent to ${special_client}"

    sleep 5

	test_latency="bash test_latency.sh"
	test_throughput="bash test_throughput.sh"

    # evaluation
    # open 100 ports for client 1-i
    for i in `seq 1 ${clients}`;do
        for port in `seq 40000 40099`;do
            echo "port $port $test_throughput";
            client=${client_node[$((i-1))]};
            # get value from client_node1
            send_screen ${client} "eval${port}" "cd $eval_dir; $test_throughput ${port} ${i}"
        done
    done

    # open 1-100 ports for special client if exists
    if [[ ${remaining_client} -gt 0 ]]; then
        for port in `seq 40000 $((40000+$((remaining_client-1))))`;do
            echo "port $port $test_throughput"
            send_screen ${special_client} "eval${port}" "cd $eval_dir; $test_throughput ${port} "special_client" "
        done
	fi
	echo "done"
}

kill_all() {
	for host in "${reserved_nodes[@]}"; do
	send_screen $host kill "pkill screen"
	done
}

_main() {
    check_input $1
    # start test
    test_hop1
}

# Call `_main` after everything has been defined.
_main "$@"

# test connections
# for i in `seq 0 100`;do curl  -s -o /dev/null --proxy socks5h://127.0.0.1:$((40000+${i})) -I www.google.com ;echo "$? $((40000+${i}))"; done

# bash test_scalability.sh ;sleep 5m;bash merge.sh 0025;bash kill_all.sh;