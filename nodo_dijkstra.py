"""
Algoritmo 1: Dijkstra (estático).

El enunciado indica que Dijkstra SÍ puede usar la topología completa
(input requerido: "Topología (nodos, aristas)") -- es la excepción
explícita a la regla de "no usar los archivos de config para resolver
todo de forma trivial". Por eso este nodo recibe el grafo completo y
calcula su tabla de ruteo una sola vez al arrancar (no se recalcula
dinámicamente, tal como se indica: "no se probará directamente" en
modo dinámico, solo se usa su motor dentro de LSR).
"""
from nodo import BaseNode
from algoritmos.dijkstra import build_next_hop_table


class DijkstraNode(BaseNode):
    def __init__(self, node_id, full_graph, **kwargs):
        neighbors = list(full_graph.get(node_id, {}).keys())
        weights = full_graph.get(node_id, {})
        super().__init__(node_id, "dijkstra", neighbors, weights=weights, **kwargs)
        self.full_graph = full_graph
        self.compute_routes()

    def compute_routes(self):
        next_hop, dist = build_next_hop_table(self.id, self.full_graph)
        with self.lock:
            self.routing_table = next_hop
        print(f"[{self.id}] tabla Dijkstra calculada: {next_hop}")

    def handle_info(self, msg):
        # Dijkstra estático no depende de paquetes de info para operar;
        # se deja el hook por si se quiere forzar un recálculo manual
        # (por ejemplo, tras editar la topología).
        pass
