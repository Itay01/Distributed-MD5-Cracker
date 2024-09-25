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

## Code

### `server.py`

```python
import socket
import threading
import json

# Constants
TARGET_HASH = 'EC9C0F7EDCC18A98B1F31853B1813301'.upper()
START_NUMBER = 0
END_NUMBER = 1 * 10**10 - 1
BLOCK_SIZE_PER_CORE = 100000

# Global variables
lock = threading.Lock()
current_number = START_NUMBER
found = False
found_number = None

clients = []
assigned_work = {}


def handle_client(conn, addr):
    """
    Handles communication with a connected client.
    Receives messages from the client, processes them, and sends responses.
    Manages the assignment of work blocks to the client.

    Args:
        conn (socket.socket): The socket connection to the client.
        addr (tuple): The address of the client.
    """
    global current_number, found, found_number
    print(f"Client {addr} connected.")
    buffer = ""
    client_cores = 1  # Default to 1 core if not specified
    try:
        while True:
            data = conn.recv(1024).decode()
            if not data:
                break

            buffer += data
            while '\n' in buffer:
                message_str, buffer = buffer.split('\n', 1)
                try:
                    message = json.loads(message_str)
                except json.JSONDecodeError as e:
                    print(f"JSON decode error from {addr}: {e}")
                    continue

                if message['type'] == 'register':
                    # Handle client registration
                    cores = message['cores']
                    client_cores = cores
                    with lock:
                        clients.append({'conn': conn, 'cores': cores})
                    print(f"Registered client {addr} with {cores} cores.")

                elif message['type'] == 'request_work':
                    # Handle client's request for work
                    with lock:
                        if conn in assigned_work:
                            assigned_work.pop(conn)

                        if found:
                            # If the target number has been found, notify the client to stop
                            response = {'type': 'stop'}
                            send_message(conn, response)
                            continue

                        block_size = BLOCK_SIZE_PER_CORE * client_cores
                        start = current_number
                        end = min(current_number + block_size - 1, END_NUMBER)
                        if start > END_NUMBER:
                            # No more work to assign
                            response = {'type': 'no_work'}
                            send_message(conn, response)
                            continue

                        current_number = end + 1
                        work = {'start': start, 'end': end}
                        assigned_work[conn] = work

                    # Send the assigned work to the client
                    response = {
                        'type': 'work',
                        'start': work['start'],
                        'end': work['end'],
                        'target_hash': TARGET_HASH
                    }
                    send_message(conn, response)

                elif message['type'] == 'found':
                    # Client reports that it has found the target number
                    with lock:
                        if conn in assigned_work:
                            assigned_work.pop(conn)

                        if not found:
                            found = True
                            found_number = message['number']
                            print(f"Found number: {found_number}")

                    # Notify all clients to stop
                    notify_all_clients()

    except Exception as e:
        print(f"Error with client {addr}: {e}")
    finally:
        # Clean up when client disconnects
        with lock:
            if conn in assigned_work:
                work = assigned_work.pop(conn)
                current_number = work['start']
            clients[:] = [c for c in clients if c['conn'] != conn]
        conn.close()
        print(f"Client {addr} disconnected.")


def notify_all_clients():
    """
    Notifies all connected clients to stop processing.
    Sends a 'stop' message to each client.
    """
    with lock:
        for client in clients:
            try:
                response = {'type': 'stop'}
                send_message(client['conn'], response)
            except Exception as e:
                print(f"Error notifying client: {e}")


def send_message(conn, message):
    """
    Sends a JSON message to a client over the socket connection.

    Args:
        conn (socket.socket): The socket connection to the client.
        message (dict): The message to send.
    """
    try:
        message_str = json.dumps(message) + '\n'
        conn.sendall(message_str.encode())
    except Exception as e:
        print(f"Error sending message: {e}")


def server_main(host='0.0.0.0', port=5000):
    """
    Main server function that accepts client connections and starts client handler threads.

    Args:
        host (str): The host IP address to bind the server socket to.
        port (int): The port number to bind the server socket to.
    """
    global found
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen()
    server.settimeout(1.0)
    print(f"Server listening on {host}:{port}")

    try:
        while not found:
            try:
                conn, addr = server.accept()
                client_thread = threading.Thread(target=handle_client, args=(conn, addr))
                client_thread.start()
            except socket.timeout:
                continue
    except KeyboardInterrupt:
        print("Server shutting down due to KeyboardInterrupt.")
    finally:
        server.close()
        if found:
            print(f"Number {found_number} found. Shutting down server.")
        else:
            print("Server shutting down.")


if __name__ == "__main__":
    server_main()
```

### `client.py`

```python
import os
import sys
import socket
import json
import hashlib
import multiprocessing

def worker(start, end, target_hash, result_queue):
    """
    Worker function that searches for the target hash within a given range.
    Computes MD5 hashes of numbers in the specified range and compares them with the target hash.
    If the target hash is found, puts the corresponding number into the result queue.

    Args:
        start (int): The start of the range to search.
        end (int): The end of the range to search.
        target_hash (str): The target MD5 hash to find.
        result_queue (multiprocessing.Queue): Queue to communicate the found number back to the main process.
    """
    for number in range(start, end + 1):
        num_str = f"{number:010d}"  # Format number as a 10-digit zero-padded string
        hash_result = hashlib.md5(num_str.encode()).hexdigest().upper()
        if hash_result == target_hash:
            result_queue.put(num_str)
            return

def send_message(conn, message):
    """
    Sends a JSON-encoded message over the socket connection.

    Args:
        conn (socket.socket): The socket connection to the server.
        message (dict): The message to send.
    """
    try:
        message_str = json.dumps(message) + '\n'
        conn.sendall(message_str.encode())
    except Exception as e:
        print(f"Error sending message: {e}")

def process_work(server_host, server_port, cores):
    """
    Main client function that connects to the server, requests work, and processes it.
    Utilizes multiple CPU cores by spawning worker processes.

    Args:
        server_host (str): The server's hostname or IP address.
        server_port (int): The server's port number.
        cores (int): Number of CPU cores to utilize.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((server_host, server_port))
        # Register with the server
        register_message = {'type': 'register', 'cores': cores}
        send_message(s, register_message)

        buffer = ""
        while True:
            # Request work from the server
            request = {'type': 'request_work', 'cores': cores}
            send_message(s, request)

            data = s.recv(4096).decode()
            if not data:
                break

            buffer += data
            while '\n' in buffer:
                # Extract full message from buffer
                message_str, buffer = buffer.split('\n', 1)
                try:
                    message = json.loads(message_str)
                except json.JSONDecodeError as e:
                    print(f"JSON decode error from server: {e}")
                    continue

                if message['type'] == 'work':
                    # Received a block of work
                    start = message['start']
                    end = message['end']
                    target_hash = message.get('target_hash')
                    if not target_hash:
                        print("No target hash received.")
                        return

                    print(f"Received work: {start} - {end}")

                    total = end - start + 1
                    per_process = total // cores
                    processes_list = []
                    result_queue = multiprocessing.Queue()

                    # Start worker processes
                    for i in range(cores):
                        process_start = start + i * per_process
                        # Ensure the last process covers up to 'end'
                        process_end = start + (i + 1) * per_process - 1 if i < cores - 1 else end
                        p = multiprocessing.Process(
                            target=worker,
                            args=(process_start, process_end, target_hash, result_queue)
                        )
                        processes_list.append(p)
                        p.start()

                    found_number = None
                    while True:
                        try:
                            # Check if any worker found the number
                            found_number = result_queue.get_nowait()
                            break
                        except multiprocessing.queues.Empty:
                            # Exit loop if all processes have finished
                            if all(not p.is_alive() for p in processes_list):
                                break

                    # Terminate all worker processes
                    for p in processes_list:
                        p.terminate()

                    if found_number:
                        # Notify server that the number was found
                        found_message = {'type': 'found', 'number': found_number}
                        send_message(s, found_message)
                        print(f"Found the number: {found_number}")
                        return

                elif message['type'] == 'stop':
                    # Server instructs to stop processing
                    print("Received stop signal from server.")
                    return

                elif message['type'] == 'no_work':
                    # No more work available from the server
                    print("No more work available. Exiting.")
                    return

def get_cpu_cores():
    """
    Returns the number of CPU cores available on the system.

    Returns:
        int: Number of CPU cores.
    """
    return os.cpu_count()

if __name__ == "__main__":
    """
    Entry point of the client script.
    Parses command-line arguments and initiates work processing.
    """
    if len(sys.argv) != 3:
        print("Usage: python client.py [server_host] [server_port]")
        sys.exit(1)

    server_host = sys.argv[1]
    server_port = int(sys.argv[2])
    cores = get_cpu_cores()
    process_work(server_host, server_port, cores)
```

---

By following these instructions, you can run the server and client scripts successfully and see the computation result `3735928559`.
