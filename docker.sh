#!/bin/bash
docker build -t kv_store -f Dockerfile .
docker run --hostname localhost -p 4000:4000 -p 4001:4001 -p 4002:4002 --name kv --rm kv_store bash -c "cd /tmp && ./start.sh"