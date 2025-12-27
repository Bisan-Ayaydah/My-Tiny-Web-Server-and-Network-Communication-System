import socket
import os
import hashlib
import random
import string

HOST = "0.0.0.0"
PORT = 8099

sessions = {}

def generate_session_id():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=32))

def send_response(conn, status, content_type, body, extra_headers=""):
    header = f"HTTP/1.1 {status}\r\nContent-Type: {content_type}\r\n{extra_headers}\r\n"
    conn.sendall(header.encode() + body)

def serve_file(conn, path):
    if not os.path.exists(path):
        return False

    ext = path.split(".")[-1]
    types = {
        "html": "text/html",
        "css": "text/css",
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg"
    }
    content_type = types.get(ext, "text/plain")

    with open(path, "rb") as f:
        content = f.read()

    send_response(conn, "200 OK", content_type, content)
    return True

def handle_register(request, conn):
    if "POST" not in request:
        serve_file(conn, "register.html")
        return

    body = request.split("\r\n\r\n")[1]
    params = dict(x.split("=") for x in body.split("&"))

    username = params["username"]
    password = params["password"]

    hashed = hashlib.sha256(password.encode()).hexdigest()

    with open("data.txt", "a") as f:
        f.write(f"{username}:{hashed}\n")

    html = "<h2>Account created! <a href='/login'>Login now</a></h2>"
    send_response(conn, "200 OK", "text/html", html.encode())

def extract_cookie(headers):
    for h in headers:
        if "Cookie:" in h:
            parts = h.split("session_id=")
            if len(parts) > 1:
                return parts[1].split(";")[0].strip()
    return None

def handle_login(request, conn):
    if "POST" not in request:
        serve_file(conn, "login.html")
        return

    body = request.split("\r\n\r\n")[1]
    params = dict(x.split("=") for x in body.split("&"))

    username = params["username"]
    password = params["password"]

    hashed = hashlib.sha256(password.encode()).hexdigest()

    valid = False
    with open("data.txt", "r") as f:
        for line in f:
            usr, pwd = line.strip().split(":")
            if usr == username and pwd == hashed:
                valid = True
                break

    if not valid:
        html = "<h2>Invalid username or password. <a href='/login'>Try again</a></h2>"
        send_response(conn, "200 OK", "text/html", html.encode())
        return

    session_id = generate_session_id()
    sessions[session_id] = username

    extra = (
        f"Set-Cookie: session_id={session_id}; Path=/;\r\n"
        "Location: /protected\r\n"
    )
    send_response(conn, "302 Found", "text/html", b"", extra_headers=extra)

def handle_protected(request, conn, headers):
    session_id = extract_cookie(headers)
    if session_id in sessions:
        serve_file(conn, "protected.html")
    else:
        send_response(conn, "302 Found", "text/html", b"", extra_headers="Location: /login\r\n")

def handle_logout(request, conn, headers):
    session_id = extract_cookie(headers)
    if session_id in sessions:
        sessions.pop(session_id)
    extra = "Set-Cookie: session_id=deleted\r\nLocation: /login\r\n"
    send_response(conn, "302 Found", "text/html", b"", extra_headers=extra)

def send_error_page(conn, ip, port):
    with open("error404.html", "r") as f:
        html = f.read()
    html = html.replace("{IP}", ip).replace("{PORT}", str(port))
    send_response(conn, "404 Not Found", "text/html", html.encode())

def handle_request(conn, addr):
    request = conn.recv(8000).decode(errors="ignore")
    if not request:
        return

    # Print request in terminal
    print("\n================= HTTP REQUEST RECEIVED =================")
    print(request)
    print("========================================================\n")

    first = request.split("\n")[0]
    method, path, *_ = first.split()
    headers = request.split("\r\n")

    # Serve main pages
    if path in ["/", "/index.html", "/main_en.html", "/en"]:
        serve_file(conn, "main_en.html")
        return
    if path == "/ar":
        serve_file(conn, "main_ar.html")
        return

    # User actions
    if path == "/register":
        handle_register(request, conn)
        return
    if path == "/login":
        handle_login(request, conn)
        return
    if path == "/protected":
        handle_protected(request, conn, headers)
        return
    if path == "/logout":
        handle_logout(request, conn, headers)
        return

    # 307 Redirects
    if path == "/chat":
        print("GET /chat → redirecting to ChatGPT (307)")
        send_response(conn, "307 Temporary Redirect", "text/html",
                      b"", extra_headers="Location: https://chat.openai.com/\r\n")
        return
    elif path == "/cf":
        print("GET /cf → redirecting to Cloudflare (307)")
        send_response(conn, "307 Temporary Redirect", "text/html",
                      b"", extra_headers="Location: https://www.cloudflare.com/\r\n")
        return
    elif path == "/rt":
        print("GET /rt → redirecting to Ritaj (307)")
        send_response(conn, "307 Temporary Redirect", "text/html",
                      b"", extra_headers="Location: https://ritaj.birzeit.edu/\r\n")
        return

    # Serve static files
    file_path = path.lstrip("/")
    if serve_file(conn, file_path):
        return

    # If file not found, send 404
    send_error_page(conn, addr[0], addr[1])

def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen(5)
        print(f"Server running on port {PORT}...")

        while True:
            conn, addr = s.accept()
            try:
                handle_request(conn, addr)
            except Exception as e:
                print("ERROR handling request:", e)
            finally:
                conn.close()

if __name__ == "__main__":
    start_server()
