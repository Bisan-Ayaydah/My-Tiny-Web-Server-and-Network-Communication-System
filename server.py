import socket
import threading


TCP_PORT = 8090          # TCP port for client control messages (START/END)
UDP_PORT = 8090          # UDP port for sending numbers
HOST = "0.0.0.0"         # Listen on all network interfaces

# === Global Counters ==
received_count = 0       # Total numbers received via UDP
wrong_order = 0          # Count of numbers received out of order
last_number = -1         # Last number received (for checking order)

# ==== UDP Server  ===
def udp_server():
    global received_count, wrong_order, last_number

    # Create UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((HOST, UDP_PORT))  # Bind to host and UDP port
    print("UDP server running on port 8090...")

    while True:
        # Receive UDP packet
        data, addr = sock.recvfrom(1024)
        number = int(data.decode())  # Convert received bytes to integer

        received_count += 1
        if number != last_number + 1:  # Check for out-of-order packets
            wrong_order += 1
        last_number = number  # Update last number

# === TCP Server ===
def tcp_server():
    global received_count, wrong_order, last_number

    # Create TCP socket
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, TCP_PORT))  # Bind to host and TCP port
    server.listen(5)               # Listen for incoming connections
    print("TCP server running on port 8090...")

    while True:
        # Accept TCP connection from client
        conn, addr = server.accept()
        msg = conn.recv(1024).decode().strip()  # Receive message and remove whitespace

        #  START message
        if msg == "START":
            # Reset counters for new session
            received_count = 0
            wrong_order = 0
            last_number = -1
            print("Client started sending numbers...")
            conn.sendall(b"ACK_START\n")  # Send acknowledgment

        #  END message
        elif msg == "END":
           
            result = f"Total Received = {received_count}, Wrong Order = {wrong_order}\n"
            print(result)               # Print summary to server console
            conn.sendall(result.encode())  # Send summary to client

        conn.close()  # Close the TCP connection

#====== Main 
if __name__ == "__main__":
    # Start UDP server in a separate thread (daemon=True ensures it exits with main program)
    threading.Thread(target=udp_server, daemon=True).start()
    # Run TCP server in main thread
    tcp_server()
