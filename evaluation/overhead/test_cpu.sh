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

# input: total node numbers reserved
reserve_hop() {
    nhosts=${1}
	reserved_nodes=()
	preserve -t 00:10:00 -# ${nhosts}
	sleep 3
	nodes=($(preserve -long-list | grep gshi |awk 'END{for(i=9;i<=NF;++i)print $i}'))
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

test_cpu() {
    client_node=${reserved_nodes[0]}
    forwarder_node=${reserved_nodes[1]}
    server_node=${reserved_nodes[2]}

    # specify test directory
    eval_dir="ipv8t/evaluation/overhead"
    run_dir="ipv8t/socks5_ipv8/hops"

    # build a 2-hop circuit
    client_run_cmd="cd $run_dir;python multiproxy2.py --client 1"
    forwarder_run_cmd="cd $run_dir;python multiproxy2.py --forwarder 1"
    server_run_cmd="cd $run_dir;python multiproxy2.py --server 1"

    # send run command
    send_screen ${client_node} test ${client_run_cmd}
    send_screen ${forwarder_node} test ${forwarder_run_cmd}
    send_screen ${server_node} test ${server_run_cmd}

    client_eval_cmd="cd ${eval_dir};bash cpu_mem.sh client"
    forwarder_eval_cmd="cd ${eval_dir};bash cpu_mem.sh forwarder"
    server_eval_cmd="cd ${eval_dir};bash cpu_mem.sh server"

    # send evaluation cmd
    send_screen ${client_node} eval ${client_eval_cmd}
    send_screen ${forwarder_node} eval ${forwarder_eval_cmd}
    send_screen ${server_node} eval ${server_eval_cmd}
}

test_cpu_with_forwarding_data() {
    client_node=${reserved_nodes[0]}
    forwarder_node=${reserved_nodes[1]}
    server_node=${reserved_nodes[2]}

    helper_node=${reserved_nodes[3]}

    # specify test directory
    eval_dir="ipv8t/evaluation/overhead"
    run_dir="ipv8t/socks5_ipv8/hops"

    # build a 2-hop circuit
    client_run_cmd="cd $run_dir;python multiproxy2.py --client 1"
    forwarder_run_cmd="cd $run_dir;python multiproxy2.py --forwarder 1"
    server_run_cmd="cd $run_dir;python multiproxy2.py --server 1"

    # send run command
    send_screen ${client_node} test ${client_run_cmd}
    send_screen ${forwarder_node} test ${forwarder_run_cmd}
    send_screen ${server_node} test ${server_run_cmd}
    send_screen ${helper_node} test ${forwarder_run_cmd}

    # send curl cmd
    client_eval_cmd="cd ${eval_dir}; bash test_curl.sh 40000"
    send_screen ${client_node} curl ${client_eval_cmd}

    # waiting for connections
    sleep 4

    # evaluation command
    client_eval_cmd="cd ${eval_dir};bash cpu_mem.sh client_data"
    forwarder_eval_cmd="cd ${eval_dir};bash cpu_mem.sh forwarder_data"
    server_eval_cmd="cd ${eval_dir};bash cpu_mem.sh server_data"

    # send evaluation cmd
    send_screen ${client_node} eval ${client_eval_cmd}
    send_screen ${forwarder_node} eval ${forwarder_eval_cmd}
    send_screen ${server_node} eval ${server_eval_cmd}
}

kill_all() {
	for host in "${reserved_nodes[@]}"; do
	send_screen $host kill "pkill screen"
	done
}

_main() {
    reserve_hop 4
#    test_cpu
    test_cpu_with_forwarding_data
}

# Call `_main` after everything has been defined.
_main "$@"