# Distributed Key-Value Store

A scalable and lightweight distributed key-value store system with master-volume architecture for efficient data storage and retrieval.

## Features

- **Distributed Architecture**:
  - **Master Server**: Handles metadata and key-to-volume mappings.
  - **Volume Servers**: Store data on disk and manage key-value operations.

- **Core Operations**:
  - `PUT`: Store a key-value pair.
  - `GET`: Retrieve the value for a key.
  - `DELETE`: Remove a key-value pair.

- **Scalability**:
  - Distributes data across multiple volume servers.
  - Easy addition of new volume servers for increased capacity.

- **Conflict Handling**:
  - Prevents duplicate `PUT` or invalid `DELETE` operations.

## Project Structure

- **`serve.py`**: Core implementation of the master and volume server logic.
- **`start.sh`**: Script to start the master and volume servers.
- **`test.py`**: Unit tests for verifying functionality.
- **Dockerfile**: Environment setup for containerized deployment.

## Setup

### Start the Master Server at port 4000
```bash
./master /tmp/cachedb/
```
### Start the Master Server at port 4001
```bash
./volume /tmp/volume1/ localhost:4000
PORT=3002 ./volume -p 4002 /tmp/volume2/ localhost:4000
```
## Usage
`PUT`
curl -X PUT -d bengaluru localhost:4000/city
<br/>
`GET` curl localhost:4000/wehave
<br/>
`DELETE` curl -X DELETE localhost:4000/city

## API Endpoints

### Master Server
`http://<master_host>:4000`

### Volume Servers
- `http://<volume_host>:4001`
- `http://<volume_host>:4002`

### Endpoints
- **`PUT /<key>`**: Store a value.
- **`GET /<key>`**: Retrieve a value.
- **`DELETE /<key>`**: Remove a key-value pair.

### Requirements
- requests 
- plyvel
- xattr

## Acknowledgement
- George Hotz : https://github.com/geohot/minikeyvalue.