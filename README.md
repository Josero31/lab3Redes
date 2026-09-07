# Laboratorio 3 — Algoritmos de Enrutamiento (CC3067 Redes)

Implementación de los 4 algoritmos de enrutamiento pedidos en el enunciado
(Dijkstra, Flooding, Link State Routing y Distance Vector Routing),


## Estructura del proyecto

```
lab3/
├── principal.py            # punto de entrada: levanta UN nodo (CLI)
├── comun/                   # utilidades compartidas por todos los algoritmos
│   ├── mensaje.py           # construir/serializar/parsear el formato de mensaje del enunciado
│   └── configuracion.py     # carga de topo-*.txt, names-*.txt, pesos-*.txt, puertos-*.txt
├── algoritmos/
│   ├── nodo.py               # BaseNode: sockets, hilos forwarding/routing (todos heredan de aquí)
│   ├── dijkstra.py            # motor puro de Dijkstra (sin red) — reutilizado por LSR
│   ├── nodo_dijkstra.py       # Algoritmo 1: Dijkstra estático
│   ├── inundacion.py          # Algoritmo 2: Flooding
│   ├── estado_enlace.py       # Algoritmo 3: Link State Routing (usa dijkstra.py + flooding de LSPs)
│   └── vector_distancia.py    # Algoritmo 4: Distance Vector Routing (Bellman-Ford + split horizon)
└── configuracion/            # archivos de ejemplo (topología de 9 nodos del enunciado)
    ├── topo-ejemplo.txt
    ├── names-ejemplo.txt
    ├── pesos-ejemplo.txt      # solo pruebas locales (no es parte del protocolo oficial)
    └── puertos-ejemplo.txt    # solo Fase 1 / sockets locales
```


## Requisitos

Solo librería estándar de Python 3 (`socket`, `threading`, `json`, `heapq`,
`argparse`). No hay dependencias externas que instalar.

## Cómo correrlo

Cada nodo es un proceso independiente. Abrí una terminal por cada nodo que
quieras levantar (con la topología de ejemplo son 9: A–I).

```bash
# Flooding
python principal.py --id A --algo flooding \
    --topo configuracion/topo-ejemplo.txt \
    --puertos configuracion/puertos-ejemplo.txt

# Dijkstra (estático, usa la topología completa por diseño del enunciado)
python principal.py --id A --algo dijkstra \
    --topo configuracion/topo-ejemplo.txt \
    --pesos configuracion/pesos-ejemplo.txt \
    --puertos configuracion/puertos-ejemplo.txt

# Link State Routing
python principal.py --id A --algo lsr \
    --topo configuracion/topo-ejemplo.txt \
    --pesos configuracion/pesos-ejemplo.txt \
    --puertos configuracion/puertos-ejemplo.txt

# Distance Vector Routing
python principal.py --id A --algo dvr \
    --topo configuracion/topo-ejemplo.txt \
    --pesos configuracion/pesos-ejemplo.txt \
    --puertos configuracion/puertos-ejemplo.txt
```

Repetí el mismo comando cambiando `--id` para B, C, D... hasta I, cada uno
en su propia terminal.

Una vez arriba, en la consola interactiva de cada nodo:

```
send <destino> <texto>   -> envía un mensaje de usuario
table                    -> imprime la tabla de ruteo actual
quit                     -> apaga el nodo
```

### Prueba rápida sin abrir 9 terminales

`test_local.py` levanta los 9 nodos dentro del mismo proceso (con hilos) para
verificar rápidamente que un algoritmo converge y que los mensajes llegan,
sin tener que abrir una terminal por nodo:

```bash
python test_local.py dijkstra   # o: flooding | lsr | dvr
```


