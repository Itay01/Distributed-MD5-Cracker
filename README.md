# Distributed MD5 Hash Cracker

This project implements a distributed system where a server delegates computational tasks to multiple clients. The goal is to find a specific 10-digit number whose MD5 hash matches a given target hash. The server assigns ranges of numbers to each connected client, and the clients compute the hashes in parallel using multiple CPU cores.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Setup](#setup)
- [Running the Server](#running-the-server)
- [Running the Client](#running-the-client)
- [Multiple Clients](#multiple-clients)
- [Expected Result](#expected-result)
- [Notes](#notes)
- [Troubleshooting](#troubleshooting)

## Overview

- **Server (`server.py`)**: Manages connected clients, assigns work ranges, and coordinates the search for the target number.
- **Client (`client.py`)**: Connects to the server, requests work, and uses multiple CPU cores to search for the target number within the assigned range.

## Prerequisites

- **Python 3.x** installed on both server and client machines.
- Required Python standard libraries (no external packages needed):
  - `socket`
  - `threading`
  - `json`
  - `hashlib`
  - `multiprocessing`
  - `sys`
  - `os`

## Setup

1. **Clone the repository** or **download** the `server.py` and `client.py` files to your local machine.

2. **Ensure both scripts are in the same directory** if running on the same machine, or distribute them to the appropriate server and client machines.

## Running the Server

1. **Open a terminal** on the machine you want to run the server.

2. **Navigate** to the directory containing `server.py`:

   ```bash
   cd /path/to/your/directory
   ```

3. **Run the server** using the following command:

   ```bash
   python server.py
   ```

   The server will start listening on all network interfaces (`0.0.0.0`) at port `5000`.

4. **Server Output**:

   You should see output similar to:

   ```
   Server listening on 0.0.0.0:5000
   ```

## Running the Client

1. **Open a terminal** on the client machine (can be the same as the server).

2. **Navigate** to the directory containing `client.py`:

   ```bash
   cd /path/to/your/directory
   ```

3. **Run the client** using the following command:

   ```bash
   python client.py [server_host] 5000
   ```

   Replace `[server_host]` with the IP address or hostname of the server. If the client is on the same machine as the server, you can use `localhost` or `127.0.0.1`.

   **Example**:

   ```bash
   python client.py localhost 5000
   ```

4. **Client Output**:

   The client will register with the server and begin processing assigned work. Output may look like:

   ```
   Received work: 0 - 99999
   ```

## Multiple Clients

You can run multiple clients to distribute the workload further. Simply repeat the client steps on additional machines or terminals.

## Expected Result

After running the server and one or more clients, the system will compute to find the 10-digit number whose MD5 hash matches the target hash defined in the server code.

The **result** of the computation is:

```
3735928559
```

Once the number is found:

- The client that found the number will notify the server.
- The server will notify all other clients to stop processing.
- The server will output:

  ```
  Found number: 3735928559
  Number 3735928559 found. Shutting down server.
  ```

- The clients will output:

  ```
  Received stop signal from server.
  ```

## Notes

- Ensure that your firewall settings allow communication over port `5000` if running across different machines.
- The server and clients must be able to communicate over the network; verify connectivity if you encounter issues.
- The target hash and search range are defined in `server.py` and can be modified as needed.

## Troubleshooting

- **Connection Refused**: If the client cannot connect to the server, ensure the server is running and the correct `server_host` and `server_port` are specified.
- **Firewall Issues**: Check that your firewall or antivirus software is not blocking the connection.
- **Python Version**: Ensure that both the server and client are running the same version of Python 3.

---

By following these instructions, you can run the server and client scripts successfully and see the computation result `3735928559`.
