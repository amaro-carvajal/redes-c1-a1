# Proxy HTTP

Proxy HTTP desarrollado en Python para la Actividad 1 de CC4303 - Redes.

## Requisitos

- Python 3
- Archivo de configuración `config.json`

El programa utiliza únicamente las librerías estándar permitidas para la actividad:

- `socket`
- `json`
- `sys`

No se requieren librerías externas.

## Configuración

Cree un archivo llamado `config.json` con una estructura como la siguiente:

```json
{
    "student_name": "Nombre Apellido",
    "proxy_ip": "192.168.1.100",
    "proxy_port": 8000,
    "blocked": [
        "www.dcc.uchile.cl",
        "cc4303.bachmann.cl/secret"
    ],
    "forbidden_words": [
        {"proxy": "[REDACTED]"},
        {"DCC": "[FORBIDDEN]"},
        {"biblioteca": "[???]"}
    ]
}
```

### Campos

- `student_name`: nombre utilizado en el header `X-ElQuePregunta`.
- `proxy_ip`: dirección IP donde se ejecutará el proxy.
- `proxy_port`: puerto donde escuchará el proxy.
- `blocked`: dominios o rutas que serán bloqueados.
- `forbidden_words`: palabras que serán reemplazadas y sus respectivos reemplazos.

## Ejecución

Ejecute el programa indicando la ruta al archivo de configuración:

```bash
python3 server.py config.json
```

El proxy comenzará a escuchar en la dirección y puerto definidos en `config.json`.

## Estructura del proyecto

```text
.
├── server.py
├── gato.png
├── config.json
├── README.md
└── .gitignore
```

El archivo `gato.png` debe encontrarse junto a `server.py`, ya que es utilizado en la respuesta enviada al acceder a recursos bloqueados.
