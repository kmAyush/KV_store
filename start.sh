#!/bin/bash
trap "trap - SIGTERM && kill -- -$$" SIGINT SIGTERM EXIT

PORT=4001 ./volume /tmp/volume1/ &
PORT=4002 ./volume /tmp/volume2/ &

./master localhost:4001,localhost:4002 /tmp/cachedb/