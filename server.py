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

def add_header(parsed_http, header_name, header_value):
    parsed_http["headers"] = (
        parsed_http["headers"] + "\r\n" + f"{header_name}: {header_value}"
    )
    return parsed_http

def get_content_length(raw_headers_bytes):
    # busca el header content-length en bytes crudos
    headers_text = raw_headers_bytes.decode(errors="ignore")
    for line in headers_text.split("\r\n"):
        if line.lower().startswith("content-length:"):
            return int(line.split(":", 1)[1].strip())
    return None

def replace_forbidden_words(body, forbidden_words):
    # forbidden_words es una lista de dicts de una sola clave: {"palabra": "reemplazo"}
    for word_dict in forbidden_words:
        for word, replacement in word_dict.items():
            body = body.replace(word, replacement)
    return body

def set_content_length(parsed_http, new_length):
    # recalcula content-length despues de modificar el body
    new_lines = []
    for line in parsed_http["headers"].split("\r\n"):
        if line.lower().startswith("content-length:"):
            new_lines.append(f"Content-Length: {new_length}")
        else:
            new_lines.append(line)
    parsed_http["headers"] = "\r\n".join(new_lines)
    return parsed_http

# esta función recibe un mensaje HTTP completo sin importar si el buffer de 
# recepción 'buff_size' es más chico que el mensaje total.
# Primero acumula bytes hasta encontrar "\r\n\r\n" y luego si el HEAD trae content-length sigue leyendo hasta 
# completar exactamente esa cantidad de bytes de BODY o hasta que el otro lado cierre la conexión
# si se pide explícitamente con read_body_until_close.

def receive_full_message(connection_socket, buff_size, end_sequence, read_body_until_close=False):
    end_bytes = end_sequence.encode()
    full_message = b""

    # seguimos pidiendo mas bytes de a buff_size hasta encontrar
    # "\r\n\r\n". 
    # Esto funciona sin importar si buff_size es mas chico
    # que el total de headers, porque no dejamos de iterar hasta encontrar
    # el separador, asi sabemos que el HEAD llego completo
    while not contains_end_of_message(full_message, end_bytes):
        chunk = connection_socket.recv(buff_size)
        if not chunk:
            return full_message
        full_message += chunk

    header_end_index = full_message.find(end_bytes) + len(end_bytes)
    headers_part = full_message[:header_end_index]
    body_part = full_message[header_end_index:]

    # mientras leiamos el HEAD puede que ya haya llegado
    # parte o todo el body pegado en el mismo recv. Miramos
    # content-length para saber cuanto body falta
    content_length = get_content_length(headers_part)

    if content_length is not None:
        # sabemos exactamente cuantos bytes de body esperar
        while len(body_part) < content_length:
            chunk = connection_socket.recv(buff_size)
            if not chunk:
                break
            body_part += chunk
    elif read_body_until_close:
        # no hay content-length
        # seguimos leyendo hasta que el otro lado cierre la conexion
        while True:
            chunk = connection_socket.recv(buff_size)
            if not chunk:
                break
            body_part += chunk
    # si no hay content-length y no pedimos leer hasta el cierre asumimos que no hay body

    return headers_part + body_part


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
            student_name = config["student_name"]
            forbidden_words = config["forbidden_words"]

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

        # agregamos nuestro header antes de reenviar al servidor real
        parsed_http = add_header(parsed_http, "X-ElQuePregunta", student_name)
        request_to_send = create_HTTP_message(parsed_http)

        prsv_socket.sendall(request_to_send)

        # recibimos la respuesta completa del servidor real, respetando
        # content-length o leyendo hasta el cierre si no viene ese header
        response_message = receive_full_message(
            prsv_socket,
            buff_size,
            end_of_message,
            read_body_until_close=True
        )
        parsed_response = parse_HTTP_message(response_message)

        # reemplazamos las palabras prohibidas en el body de la respuesta
        parsed_response["body"] = replace_forbidden_words(
            parsed_response["body"], forbidden_words
        )

        # recalculamos content-length usando el largo en bytes 
        # porque el reemplazo puede cambiar el largo del body
        new_body_bytes = parsed_response["body"].encode()
        parsed_response = set_content_length(parsed_response, len(new_body_bytes))

        response_to_send = create_HTTP_message(parsed_response)
        new_socket.sendall(response_to_send)

        # cerramos ambas conexiones
        prsv_socket.close()
        new_socket.close()
