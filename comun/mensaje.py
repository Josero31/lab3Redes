"""
Utilidades para construir, serializar y parsear los mensajes que viajan
entre nodos, siguiendo el formato JSON definido en el enunciado del
Laboratorio 3 (CC3067 - Redes):

{
  "proto": "dijkstra|flooding|lsr|dvr",
  "type": "message|echo|info|hello",
  "from": "foo@bar.com/123",
  "to": "yolo@bar.com/777",
  "ttl": 5,
  "headers": [...],
  "payload": "..."
}

Se agrega un campo extra "id" (no rompe el formato base, el enunciado
permite agregar elementos) para poder deduplicar paquetes en Flooding
y en la difusión de LSPs de Link State Routing.
"""
import json
import itertools

_counter = itertools.count(1)


def build_message(proto, type_, frm, to, payload="", ttl=5, headers=None, msg_id=None):
    """Construye un dict con la estructura de mensaje del protocolo."""
    return {
        "id": msg_id if msg_id is not None else next(_counter),
        "proto": proto,
        "type": type_,
        "from": frm,
        "to": to,
        "ttl": ttl,
        "headers": headers or [],
        "payload": payload,
    }


def serialize(msg):
    """Convierte el mensaje a una línea JSON terminada en \\n (framing simple sobre TCP)."""
    return json.dumps(msg) + "\n"


def parse_line(line):
    """Parsea una línea JSON de vuelta a dict."""
    return json.loads(line)
