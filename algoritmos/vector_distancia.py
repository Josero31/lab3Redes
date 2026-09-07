"""
Algoritmo 4: Distance Vector Routing (DVR).

Input requerido por el enunciado: "Las Tablas de los Vecinos". Cada
nodo:

  1. Mantiene su propio vector de distancias (dest -> costo).
  2. Envía periódicamente su vector completo a cada vecino (con split
     horizon: no le anuncia a un vecino las rutas cuyo next_hop es
     precisamente ese vecino, para reducir loops/count-to-infinity).
  3. Al recibir el vector de un vecino, guarda esa "tabla del vecino" y
     RECALCULA por completo su propio vector combinando todos los
     vectores de vecinos conocidos + el costo del enlace a cada uno
     (Bellman-Ford), lo que permite reflejar tanto mejoras como
     empeoramientos de ruta en cuanto llega una actualización.
"""
import time

from algoritmos.nodo import BaseNode
from comun import mensaje as msgutil

INF = float("inf")


class DVRNode(BaseNode):
    def __init__(self, node_id, neighbors, weights=None, interval=8, **kwargs):
        super().__init__(node_id, "dvr", neighbors, weights=weights, **kwargs)
        self.interval = interval
        self.distance = {self.id: 0}
        self.neighbor_vectors = {}  # neighbor_id -> {dest: costo}

        for n in self.neighbors:
            self.distance[n] = self.weights.get(n, 1)
            self.routing_table[n] = n

    # ------------------------------------------------------------------ #
    def _routing_loop(self):
        while self._running:
            self.send_vector()
            time.sleep(self.interval)

    def send_vector(self):
        with self.lock:
            vector = dict(self.distance)
            table = dict(self.routing_table)

        for n in self.neighbors:
            # Split horizon: no anunciar a n las rutas cuyo next_hop es n
            filtered = {dest: cost for dest, cost in vector.items() if table.get(dest) != n}
            msg = msgutil.build_message(self.proto, "info", self.id, n,
                                         payload={"vector": filtered}, ttl=1)
            self.send_to_neighbor(n, msg)

    # ------------------------------------------------------------------ #
    def handle_info(self, msg):
        sender = msg["from"]
        vector = msg.get("payload", {}).get("vector", {})
        with self.lock:
            self.neighbor_vectors[sender] = vector
            changed = self._recompute_locked()
        if changed:
            print(f"[{self.id}] DVR: tabla recalculada -> {self.routing_table}")

    def _recompute_locked(self):
        """Bellman-Ford: recalcula self.distance/self.routing_table desde cero
        usando los enlaces directos + los vectores de vecinos guardados.
        Debe llamarse con self.lock ya adquirido."""
        new_distance = {self.id: 0}
        new_next_hop = {}

        for n, w in self.weights.items():
            new_distance[n] = w
            new_next_hop[n] = n

        for neighbor, vector in self.neighbor_vectors.items():
            link_cost = self.weights.get(neighbor, 1)
            for dest, cost in vector.items():
                if dest == self.id:
                    continue
                total = link_cost + cost
                if total < new_distance.get(dest, INF):
                    new_distance[dest] = total
                    new_next_hop[dest] = neighbor

        changed = new_distance != self.distance
        self.distance = new_distance
        self.routing_table = new_next_hop
        return changed
