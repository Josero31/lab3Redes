"""
Motor puro del algoritmo de Dijkstra (camino más corto), sin nada de red.
Se reutiliza tanto para el algoritmo "Dijkstra" standalone como dentro de
Link State Routing (LSR), como pide el enunciado ("deben manejar alta
modularidad en sus clases y archivos").
"""
import heapq


def dijkstra(graph, source):
    """
    graph: dict node -> dict neighbor -> peso
    return: (dist, prev)
      dist[node] = costo mínimo desde source
      prev[node] = nodo anterior en el camino más corto desde source
    """
    dist = {node: float("inf") for node in graph}
    prev = {node: None for node in graph}
    dist[source] = 0
    pq = [(0, source)]
    visited = set()

    while pq:
        d, u = heapq.heappop(pq)
        if u in visited:
            continue
        visited.add(u)
        for v, w in graph.get(u, {}).items():
            if v not in dist:
                continue
            nd = d + w
            if nd < dist[v]:
                dist[v] = nd
                prev[v] = u
                heapq.heappush(pq, (nd, v))

    return dist, prev


def build_next_hop_table(source, graph):
    """
    Corre Dijkstra desde `source` y devuelve la tabla de ruteo como
    dict dest -> next_hop (el primer salto hacia ese destino), junto
    con el dict de distancias.
    """
    dist, prev = dijkstra(graph, source)
    next_hop = {}

    for dest in graph:
        if dest == source or prev.get(dest) is None:
            continue
        # Retrocede desde dest hasta encontrar el vecino directo de source
        node = dest
        while prev[node] is not None and prev[node] != source:
            node = prev[node]
        if prev[node] == source:
            next_hop[dest] = node

    return next_hop, dist
