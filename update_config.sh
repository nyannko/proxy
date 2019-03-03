#!/usr/bin/env bash
# update .bashrc/.vimrc for all servers

declare -a remotes=("fs0" "fs1" "fs2" "fs3" "fs4" "fs5")

for remote in "${remotes[@]}"; do
#    scp ./config/.bashrc gshi@${remote}:~/.bashrc
    rsync -v ./config/.bashrc gshi@${remote}:~/.bashrc
    rsync -v ./config/.vimrc gshi@${remote}:~/.vimrc
done