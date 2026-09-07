# Proxy HTTP

Proxy HTTP desarrollado en Python para la Actividad 1 de CC4303 - Redes.

## Requisitos

- Python 3
- Archivo de configuración `config.json`

No se requieren librerías externas.

## Configuración

Cree un archivo `config.json` con la siguiente estructura:

```json
{
    "user": "correo@ejemplo.com",
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
