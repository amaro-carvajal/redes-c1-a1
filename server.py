import socket
import json
import sys

def parse_HTTP_message(http_message: bytes):
    decode = http_message.decode()
    splitdecode = decode.split('\r\n\r\n', 1)
    sline = splitdecode[0].split('\r\n', 1)[0]
    headers = splitdecode[0].split('\r\n', 1)[1] if len(splitdecode[0].split('\r\n', 1)) > 1 else ""
    body = splitdecode[1] if len(splitdecode) > 1 else ""
    pHTTP = {"sline": sline, "headers": headers, "body": body}
    return pHTTP

def create_HTTP_message(decode_http_message: dict[str]):
    encode_http_message = (decode_http_message["sline"] + "\r\n" + decode_http_message["headers"] + "\r\n\r\n" +         decode_http_message["body"]).encode()
    return encode_http_message

def get_host_port(parsed_http):
    headers = parsed_http["headers"].split("\r\n")

    for header in headers:
        if header.lower().startswith("host:"):
            host_value = header.split(":", 1)[1].strip()

            if ":" in host_value:
                host, port = host_value.rsplit(":", 1)
                return host, int(port)

            return host_value, 80
        
    raise ValueError("No se encontró el header Host")

# esta función se encarga de recibir el mensaje completo desde el cliente
# en caso de que el mensaje sea más grande que el tamaño del buffer 'buff_size', esta función va esperar a que
# llegue el resto. Para saber si el mensaje ya llegó por completo, se busca el caracter de fin de mensaje (parte de nuestro protocolo inventado)

def receive_full_message(connection_socket, buff_size, end_sequence):
    end_bytes = end_sequence.encode()
    # recibimos la primera parte del mensaje
    full_message = connection_socket.recv(buff_size)

    # verificamos si la secuencia de fin ya está en el buffer
    while not contains_end_of_message(full_message, end_bytes):
        recv_message = connection_socket.recv(buff_size)
        if not recv_message:
            break
        full_message += recv_message

    # Retornamos directamente los bytes completados sin alterar el mensaje
    return full_message


def contains_end_of_message(message_bytes, end_bytes):
    return end_bytes in message_bytes


def remove_end_of_message(full_message, end_sequence):
    index = full_message.rfind(end_sequence)
    return full_message[:index]

def is_blocked(parsed_http, blocked_sites):
    req_line = parsed_http["sline"].split()
    site = req_line[1]

    # quitamos http://
    if site.startswith("http://"):
        site = site[len("http://"):]

    site = site.rstrip("/")

    print("SITE:", repr(site))
    print("BLOCKED:", blocked_sites)

    for blocked in blocked_sites:
        if site == blocked.rstrip("/"):
            return True

    return False

def send_forbidden(client_socket):
    html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>403 Forbidden</title>
</head>
<body>
    <h1>403 Forbidden</h1>
    <p>Este sitio está bloqueado.</p>
    <img src="/gato.png">
</body>
</html>"""

    body = html.encode()

    headers = (
        "HTTP/1.1 403 Forbidden\r\n"
        "Content-Type: text/html; charset=utf-8\r\n"
        f"Content-Length: {len(body)}\r\n"
        "Connection: close\r\n"
        "\r\n"
    )

    client_socket.sendall(headers.encode() + body)

if __name__ == "__main__":

    if len(sys.argv) > 1:
        json_path = sys.argv[1]

        with open(json_path, 'r', encoding='utf-8') as file:
            config = json.load(file)
            blocked_sites = config["blocked"]
            proxy_ip = config["proxy_ip"]
            proxy_port = config["proxy_port"]

    else:
        print("Error: Debe ingresar la ruta del archivo JSON. ")
        sys.exit(1)

    # tamaño del buffer y secuencia que indica
    # el final de los headers HTTP
    buff_size = 4
    end_of_message = "\r\n\r\n"

    # direccion donde escuchara nuestro proxy
    server_socket_address = (proxy_ip, proxy_port)

    print("Creando socket - Proxy")

    # socket que escucha conexiones de clientes
    server_socket = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )

    server_socket.bind(server_socket_address)

    server_socket.listen(3)

    print("... Esperando clientes")

    while True:

        # cliente -> proxy
        new_socket, new_socket_address = server_socket.accept()

        # recibimos el request HTTP del cliente
        recv_message = receive_full_message(
            new_socket,
            buff_size,
            end_of_message
        )

        # parseamos el mensaje solamente para conocer el Host
        parsed_http = parse_HTTP_message(recv_message)

        host, port = get_host_port(parsed_http)

        req_line = parsed_http["sline"].split()
        site = req_line[1]

        if site.endswith("/gato.png"):

            with open("gato.png", "rb") as file:
                image = file.read()

            headers = (
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: image/png\r\n"
                f"Content-Length: {len(image)}\r\n"
                "Connection: close\r\n"
                "\r\n"
            )

            new_socket.sendall(
                headers.encode() + image
            )

            new_socket.close()
            continue

        if is_blocked(parsed_http, blocked_sites):
            send_forbidden(new_socket)
            new_socket.close()
            continue

        # proxy -> servidor real
        prsv_socket = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM
        )

        prsv_socket.connect((host, port))

        # reenviamos exactamente el request recibido
        prsv_socket.sendall(recv_message)

        # recibimos la respuesta del servidor
        # y la enviamos directamente al cliente
        while True:

            response = prsv_socket.recv(4096)

            if not response:
                break

            new_socket.sendall(response)

        # cerramos ambas conexiones
        prsv_socket.close()
        new_socket.close()
