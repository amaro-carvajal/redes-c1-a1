# Proxy HTTP

## Configuración

El programa recibe la ruta de un archivo JSON al ejecutarse.

Cree un archivo llamado:

```text
config.json
```

con una estructura como la siguiente:

```json
{
    "proxy_ip": "192.168.1.100",
    "proxy_port": 8000
    "user": "--su email--",
    "blocked": ["www.dcc.uchile.cl", "cc4303.bachmann.cl/secret"],
    "forbidden_words": [{"proxy": "[REDACTED]"}, {"DCC": "[FORBIDDEN]"}, {"biblioteca": "[???]"}]
}
```

### Campos

* `user`: correo del usuario.
* `proxy_ip`: dirección IP donde se ejecutará el proxy.
* `proxy_port`: puerto utilizado por el proxy.
* `blocked`: dominios o rutas que serán bloqueados.
* `forbidden_words`: palabras que serán reemplazadas en el contenido HTTP.

## Ejecución

Ejecute:

```bash
python3 proxy.py config.json
```

El proxy comenzará a escuchar en la IP y puerto definidos en `config.json`.

Por ejemplo:

```text
192.168.64.3:8000
```

## Pruebas con curl

### Página permitida

```bash
curl http://cc4303.bachmann.cl/ -x 192.168.64.3:8000
```

### Página bloqueada

```bash
curl -i http://cc4303.bachmann.cl/secret -x 192.168.64.3:8000
```

La respuesta esperada comienza con:

```text
HTTP/1.1 403 Forbidden
```

## Imagen de bloqueo

El archivo:

```text
gato.png
```

debe estar en la misma carpeta que `proxy.py`.

La página `403 Forbidden` incluye la imagen mediante:

```html
<img src="/gato.png">
```

El navegador realiza una segunda solicitud HTTP para obtener esta imagen desde el proxy.

## Estructura sugerida

```text
.
├── proxy.py
├── gato.png
├── config.json
├── README.md
└── .gitignore
```

## `.gitignore`

Se recomienda no subir el archivo de configuración personal:

```gitignore
config.json

__pycache__/
*.pyc

venv/
.venv/

.DS_Store
.vscode/
```

El contenido de ejemplo de `config.json` se encuentra documentado en este README, por lo que cada usuario puede crear su propia configuración local antes de ejecutar el proxy.
