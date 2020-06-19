#!/bin/bash

path=$(dirname $(readlink -f "$0"))

PID_EXIST=$(netstat -ntalp |grep 8889 | awk '{print $7}' | awk 'BEGIN{FS="/";OFS=" "} {print $1}')
if [ $PID_EXIST ];then
    echo $PID_EXIST
    kill -9 $PID_EXIST
else
    echo no such pid
fi
