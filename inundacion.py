"""
Algoritmo 2: Flooding.

Cada nodo solo necesita conocer a sus vecinos (input requerido por el
enunciado). Al recibir un paquete de datos que no es para él, lo
reenvía a TODOS sus vecinos (excepto de vuelta al emisor original),
usando el campo "id" del mensaje para no reenviar el mismo paquete
más de una vez (evita tormenta infinita en grafos con ciclos).
"""
from nodo import BaseNode
from comun import mensaje as msgutil


class FloodingNode(BaseNode):
    def __init__(self, node_id, neighbors, **kwargs):
        super().__init__(node_id, "flooding", neighbors, **kwargs)

    def handle_data(self, msg):
        msg_id = msg.get("id")
        with self.lock:
            if msg_id in self.seen_ids:
                return  # ya lo vimos, no reenviar de nuevo
            self.seen_ids.add(msg_id)

        if msg["to"] == self.id:
            print(f"[{self.id}] *** mensaje (flooding) recibido de {msg['from']}: {msg.get('payload')}")
            return

        msg = dict(msg)
        msg["ttl"] -= 1
        if msg["ttl"] <= 0:
            print(f"[{self.id}] TTL agotado, descartando (flooding)")
            return

        for n in self.neighbors:
            if n == msg.get("from"):
                continue
            self.send_to_neighbor(n, msg)

    def send_data(self, dest, payload, ttl=15):
        msg = msgutil.build_message(self.proto, "message", self.id, dest, payload=payload, ttl=ttl)
        with self.lock:
            self.seen_ids.add(msg["id"])
        for n in self.neighbors:
            self.send_to_neighbor(n, msg)

    def handle_info(self, msg):
        # Flooding puro no usa paquetes de info para ruteo.
        pass
