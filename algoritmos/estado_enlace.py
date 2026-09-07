"""
Algoritmo 3: Link State Routing (LSR).

Input requerido por el enunciado: "Las Tablas de los demás Nodos (de
ella se deriva la Topología)". Cada nodo:

  1. Conoce solo sus enlaces directos (vecino -> costo).
  2. Empaqueta esa info en un LSP (Link State Packet) y lo difunde a
     TODA la red por flooding (reutilizando la misma idea del
     algoritmo de Flooding: reenviar a todos menos por donde llegó,
     con dedup por id y por número de secuencia).
  3. Cada nodo va armando su propia base de datos de topología a
     partir de los LSPs que recibe de todos los demás.
  4. Con esa topología derivada, corre Dijkstra (algoritmos/dijkstra.py)
     para calcular su tabla de ruteo -> misma implementación reutilizada
     del algoritmo 1, cumpliendo el requisito de modularidad.
"""
import time

from algoritmos.nodo import BaseNode
from comun import mensaje as msgutil
from algoritmos.dijkstra import build_next_hop_table


class LSRNode(BaseNode):
    def __init__(self, node_id, neighbors, weights=None, hello_interval=8, **kwargs):
        super().__init__(node_id, "lsr", neighbors, weights=weights, **kwargs)
        self.hello_interval = hello_interval
        # topologia derivada de los LSPs: node -> {vecino: costo}
        self.topology = {self.id: dict(self.weights)}
        self.lsp_seq = {self.id: 0}   # ultimo numero de secuencia visto por origen
        self._my_seq = 0

    # ------------------------------------------------------------------ #
    def _routing_loop(self):
        while self._running:
            self.send_lsp()
            time.sleep(self.hello_interval)

    def send_lsp(self):
        with self.lock:
            self._my_seq += 1
            seq = self._my_seq
            self.lsp_seq[self.id] = seq
        payload = {"origin": self.id, "seq": seq, "links": self.weights}
        msg = msgutil.build_message(self.proto, "info", self.id, "*", payload=payload, ttl=15)
        with self.lock:
            self.seen_ids.add(msg["id"])
        self.broadcast_to_neighbors(msg)

    # ------------------------------------------------------------------ #
    def handle_info(self, msg):
        payload = msg.get("payload", {})
        origin = payload.get("origin")
        seq = payload.get("seq", 0)
        links = payload.get("links", {})
        msg_id = msg.get("id")

        with self.lock:
            if msg_id in self.seen_ids:
                return
            self.seen_ids.add(msg_id)
            if seq <= self.lsp_seq.get(origin, -1):
                return  # LSP vieja o duplicada, se descarta
            self.lsp_seq[origin] = seq
            self.topology[origin] = links

        self.recompute_routes()

        # Reflooding del LSP hacia el resto de la red (menos por donde llegó)
        fwd = dict(msg)
        fwd["ttl"] -= 1
        if fwd["ttl"] > 0:
            self.broadcast_to_neighbors(fwd, exclude=None)

    def recompute_routes(self):
        with self.lock:
            graph = {node: dict(links) for node, links in self.topology.items()}
        # asegura que todo vecino mencionado exista como nodo en el grafo
        for node, links in list(graph.items()):
            for neigh in links:
                graph.setdefault(neigh, {})

        next_hop, dist = build_next_hop_table(self.id, graph)
        with self.lock:
            self.routing_table = next_hop
        print(f"[{self.id}] LSR: tabla recalculada -> {next_hop}")
