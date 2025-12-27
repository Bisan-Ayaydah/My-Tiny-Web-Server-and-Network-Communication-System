import socket
import sys


SERVER = sys.argv[1]       # Get server IP address from command-line argument
MAX_NUM = 1000000          # Maximum number to send via UDP


# Send START message via TCP
try:
    # Create a TCP socket
    tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp.connect((SERVER, 8090))      # Connect to the server on port 8090
    tcp.sendall(b"START\n")          # Send "START" message to initiate session

    # Try to receive server response
    try:
        response = tcp.recv(1024).decode()  # Receive up to 1024 bytes
        print(response)                     # Print ACK_START from server
    except socket.error:
        print("No response from server for START")

    tcp.close()  # Close TCP connection after sending START
except Exception as e:
    print("Error sending START:", e)
    sys.exit(1)    # Exit program if there is an error

# ============
# Send numbers via UDP

try:
    # Create a UDP socket
    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Send numbers 0 to MAX_NUM, one per UDP packet
    for i in range(MAX_NUM + 1):
        udp.sendto(str(i).encode(), (SERVER, 8090))  # Convert number to bytes and send

    udp.close()  # Close UDP socket after sending all numbers
except Exception as e:
    print("Error sending UDP packets:", e)
    sys.exit(1)    # Exit program if there is an error

# ====================
# Send END message via TCP

try:
    # Create a TCP socket
    tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp.connect((SERVER, 8090))      # Connect to the server on port 8090
    tcp.sendall(b"END\n")            # Send "END" message to indicate completion

    # Try to receive server response with total counts
    try:
        response = tcp.recv(1024).decode()  # Receive server summary
        print(response)                     # Print total received and wrong order counts
    except socket.error:
        print("No response from server for END")

    tcp.close()  # Close TCP connection
except Exception as e:
    print("Error sending END:", e)
    sys.exit(1)    # Exit program if there is an error
