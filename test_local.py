"""
Prueba rápida en un solo proceso: levanta los 9 nodos de configuracion/topo-ejemplo.txt
usando el algoritmo indicado, espera a que converjan las tablas de ruteo, y envía un
mensaje de A a H para confirmar que el forwarding funciona de punta a punta.

Uso:
    python test_local.py dijkstra
    python test_local.py flooding
    python test_local.py lsr
    python test_local.py dvr
"""
import sys
import time

from comun import configuracion
from algoritmos.inundacion import FloodingNode
from algoritmos.nodo_dijkstra import DijkstraNode
from algoritmos.estado_enlace import LSRNode
from algoritmos.vector_distancia import DVRNode

TOPO = "configuracion/topo-ejemplo.txt"
PESOS = "configuracion/pesos-ejemplo.txt"
PUERTOS = "configuracion/puertos-ejemplo.txt"


def construir_pesos(node_id, topo, pesos_cfg):
    if pesos_cfg and node_id in pesos_cfg:
        return dict(pesos_cfg[node_id])
    return {n: 1 for n in topo.get(node_id, [])}


def main():
    algo = sys.argv[1] if len(sys.argv) > 1 else "dijkstra"

    topo = configuracion.load_topo(TOPO)
    direcciones = configuracion.load_ports(PUERTOS)
    pesos_cfg = configuracion.load_weights(PESOS)

    nodos = {}
    for nid, vecinos in topo.items():
        host, port = direcciones[nid]
        pesos = construir_pesos(nid, topo, pesos_cfg)

        if algo == "flooding":
            nodos[nid] = FloodingNode(nid, vecinos, addresses=direcciones, host=host, port=port)
        elif algo == "dijkstra":
            grafo_completo = {n: construir_pesos(n, topo, pesos_cfg) for n in topo}
            nodos[nid] = DijkstraNode(nid, grafo_completo, addresses=direcciones, host=host, port=port)
        elif algo == "lsr":
            nodos[nid] = LSRNode(nid, vecinos, weights=pesos, addresses=direcciones,
                                  host=host, port=port, hello_interval=2)
        elif algo == "dvr":
            nodos[nid] = DVRNode(nid, vecinos, weights=pesos, addresses=direcciones,
                                  host=host, port=port, interval=2)
        else:
            raise SystemExit(f"algoritmo desconocido: {algo}")

    for n in nodos.values():
        n.start()

    espera = 1 if algo in ("flooding", "dijkstra") else 6
    print(f"Esperando {espera}s a que converja ({algo})...")
    time.sleep(espera)

    nodos["A"].print_table()
    print("Enviando mensaje de A a H...")
    nodos["A"].send_data("H", f"hola desde A ({algo})")
    time.sleep(1)

    for n in nodos.values():
        n.stop()


if __name__ == "__main__":
    main()
