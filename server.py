# server.py

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
