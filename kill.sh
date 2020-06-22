#!/bin/bash

path=$(dirname $(readlink -f "$0"))
files=$(ls ${path}/pid)
for filename in $files
do
    kill -9 ${filename}
    rm ${path}/pid/${filename}
done

while true
do
    PID_EXIST=$(netstat -ntalp |grep 8889 | awk '{print $7}' | awk 'BEGIN{FS="/";OFS=" "} {print $1}')
    if [ ! -n "$PID_EXIST" ];then
        break
    else
        echo $PID_EXIST
        kill -9 $PID_EXIST
    fi
done
