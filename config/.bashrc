# .bashrc

# Source global definitions
if [ -f /etc/bashrc ]; then
	. /etc/bashrc
fi

# Uncomment the following line if you don't like systemctl's auto-paging feature:
# export SYSTEMD_PAGER=

# User specific aliases and functions
module load gcc
module load slurm 
module load prun

export LD_LIBRARY_PATH=$HOME/libsodium_stable/lib
export PYTHONPATH=$HOME/ipv8t

alias ll="ls -alF"
alias vi="vim"
alias tcp="lsof -i -n -P | grep TCP"

alias l="preserve -long-list"
alias b="preserve -t 00:05:00 -#"
alias c="preserve -c"

# work dir
#w='/home/gshi/ipv8t/socks5_ipv8/hops'
# evaluation dir
#e='/home/gshi/ipv8t/evaluation/hops'

 # work dir
w="$HOME/ipv8t/socks5_ipv8/hops"
e="$HOME/ipv8t/evaluation/scalability"



