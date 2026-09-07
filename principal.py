"""
Punto de entrada para levantar UN nodo de la red, en el modo/algoritmo
que se indique por línea de comandos. Fase 1 del laboratorio: usa
sockets TCP locales (ver configuracion/puertos-ejemplo.txt).

Ejemplos:

  python principal.py --id A --algo flooding --topo configuracion/topo-ejemplo.txt \
      --puertos configuracion/puertos-ejemplo.txt

  python principal.py --id A --algo dijkstra --topo configuracion/topo-ejemplo.txt \
      --pesos configuracion/pesos-ejemplo.txt --puertos configuracion/puertos-ejemplo.txt

  python principal.py --id A --algo lsr --topo configuracion/topo-ejemplo.txt \
      --pesos configuracion/pesos-ejemplo.txt --puertos configuracion/puertos-ejemplo.txt

  python principal.py --id A --algo dvr --topo configuracion/topo-ejemplo.txt \
      --pesos configuracion/pesos-ejemplo.txt --puertos configuracion/puertos-ejemplo.txt

Una vez arriba, en la consola interactiva:
  send <destino> <texto>   -> envía un mensaje de usuario
  table                    -> imprime la tabla de ruteo actual
  quit                     -> apaga el nodo
"""
import argparse

from comun import configuracion
from algoritmos.inundacion import FloodingNode
from algoritmos.nodo_dijkstra import DijkstraNode
from algoritmos.estado_enlace import LSRNode
from algoritmos.vector_distancia import DVRNode


def construir_pesos(node_id, topo, pesos_cfg):
    """Costo de cada enlace saliente de node_id. Si no hay archivo de pesos,
    se asume costo 1 para todos los enlaces (como en Flooding)."""
    if pesos_cfg and node_id in pesos_cfg:
        return dict(pesos_cfg[node_id])
    return {n: 1 for n in topo.get(node_id, [])}


def main():
    ap = argparse.ArgumentParser(description="Nodo de enrutamiento - Laboratorio 3 (CC3067 Redes)")
    ap.add_argument("--id", required=True, help="ID de este nodo, ej. A")
    ap.add_argument("--algo", required=True, choices=["flooding", "dijkstra", "lsr", "dvr"])
    ap.add_argument("--topo", required=True, help="archivo topo-*.txt")
    ap.add_argument("--puertos", required=True, help="archivo puertos-*.txt (solo Fase 1, sockets locales)")
    ap.add_argument("--pesos", help="archivo pesos-*.txt opcional (costos de enlace)")
    ap.add_argument("--host", default="127.0.0.1")
    args = ap.parse_args()

    topo = configuracion.load_topo(args.topo)
    direcciones = configuracion.load_ports(args.puertos)
    pesos_cfg = configuracion.load_weights(args.pesos) if args.pesos else None

    if args.id not in topo:
        raise SystemExit(f"El nodo '{args.id}' no aparece en {args.topo}")

    vecinos = topo.get(args.id, [])
    pesos = construir_pesos(args.id, topo, pesos_cfg)
    host, port = direcciones[args.id]

    if args.algo == "flooding":
        nodo = FloodingNode(args.id, vecinos, addresses=direcciones, host=host, port=port, weights=pesos)
    elif args.algo == "dijkstra":
        grafo_completo = {n: construir_pesos(n, topo, pesos_cfg) for n in topo}
        nodo = DijkstraNode(args.id, grafo_completo, addresses=direcciones, host=host, port=port)
    elif args.algo == "lsr":
        nodo = LSRNode(args.id, vecinos, weights=pesos, addresses=direcciones, host=host, port=port)
    elif args.algo == "dvr":
        nodo = DVRNode(args.id, vecinos, weights=pesos, addresses=direcciones, host=host, port=port)
    else:
        raise SystemExit("Algoritmo no soportado")

    nodo.start()
    print(f"Nodo {args.id} iniciado con algoritmo '{args.algo}'. "
          f"Comandos: send <destino> <texto> | table | quit")

    try:
        while True:
            linea = input("> ").strip()
            if not linea:
                continue
            if linea == "quit":
                break
            elif linea == "table":
                nodo.print_table()
            elif linea.startswith("send "):
                partes = linea.split(" ", 2)
                if len(partes) < 3:
                    print("uso: send <destino> <texto>")
                    continue
                _, destino, payload = partes
                nodo.send_data(destino, payload)
            else:
                print("comando no reconocido")
    except (KeyboardInterrupt, EOFError):
        pass
    finally:
        nodo.stop()


if __name__ == "__main__":
    main()
