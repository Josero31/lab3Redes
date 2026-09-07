"""
BaseNode: clase base que todos los algoritmos (Flooding, Dijkstra, LSR, DVR)
extienden. Se encarga de la parte "de red" (sockets TCP, hilos) para que cada
algoritmo solo tenga que preocuparse por su lógica de ruteo.

Cada nodo corre, como pide el enunciado, dos procesos/hilos en paralelo:
  - forwarding: hilo servidor que recibe conexiones/mensajes entrantes
    (_serve_forever / _handle_conn / _dispatch) y decide si el paquete es
    para nosotros o si hay que reenviarlo (forward_data).
  - routing: hilo (_routing_loop) que cada algoritmo puede sobreescribir para
    enviar periódicamente HELLO, LSPs o vectores de distancia, y para
    recalcular su tabla de ruteo.
"""
import socket
import threading
import time

from comun import mensaje as msgutil


class BaseNode:
    def __init__(self, node_id, proto, neighbors, addresses, host="127.0.0.1",
                 port=None, weights=None):
        """
        node_id:   id de este nodo (ej. "A")
        proto:     "flooding" | "dijkstra" | "lsr" | "dvr"
        neighbors: lista de ids de vecinos directos
        addresses: dict node_id -> (host, port)  (para Fase 1, sockets locales)
        weights:   dict neighbor_id -> costo del enlace (default: costo 1)
        """
        self.id = node_id
        self.proto = proto
        self.neighbors = list(neighbors)
        self.addresses = addresses
        self.host = host
        self.port = port if port is not None else addresses[node_id][1]
        self.weights = weights if weights is not None else {n: 1 for n in self.neighbors}

        self.routing_table = {}   # dest -> next_hop
        self.seen_ids = set()     # dedup de paquetes (flooding / LSPs)

        self.lock = threading.Lock()
        self._server_socket = None
        self._running = False

    # ------------------------------------------------------------------ #
    # Arranque / apagado
    # ------------------------------------------------------------------ #
    def start(self):
        self._running = True
        threading.Thread(target=self._serve_forever, name=f"{self.id}-forwarding", daemon=True).start()
        threading.Thread(target=self._routing_loop, name=f"{self.id}-routing", daemon=True).start()
        # Descubrimiento inicial de vecinos
        self.send_hello_to_neighbors()

    def stop(self):
        self._running = False
        if self._server_socket:
            try:
                self._server_socket.close()
            except OSError:
                pass

    # ------------------------------------------------------------------ #
    # Hilo de forwarding: servidor TCP
    # ------------------------------------------------------------------ #
    def _serve_forever(self):
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_socket.bind((self.host, self.port))
        self._server_socket.listen(20)
        print(f"[{self.id}] escuchando en {self.host}:{self.port} (proto={self.proto})")
        while self._running:
            try:
                conn, _ = self._server_socket.accept()
            except OSError:
                break
            threading.Thread(target=self._handle_conn, args=(conn,), daemon=True).start()

    def _handle_conn(self, conn):
        buf = b""
        with conn:
            while True:
                try:
                    data = conn.recv(4096)
                except OSError:
                    break
                if not data:
                    break
                buf += data
                while b"\n" in buf:
                    line, buf = buf.split(b"\n", 1)
                    if not line.strip():
                        continue
                    try:
                        msg = msgutil.parse_line(line.decode("utf-8"))
                    except Exception as e:
                        print(f"[{self.id}] error parseando mensaje: {e}")
                        continue
                    self._dispatch(msg)

    def _send_raw(self, host, port, msg):
        try:
            with socket.create_connection((host, port), timeout=3) as s:
                s.sendall(msgutil.serialize(msg).encode("utf-8"))
        except OSError as e:
            print(f"[{self.id}] no se pudo enviar a {host}:{port} -> {e}")

    def send_to_neighbor(self, neighbor_id, msg):
        addr = self.addresses.get(neighbor_id)
        if addr is None:
            print(f"[{self.id}] direccion desconocida para vecino {neighbor_id}")
            return
        self._send_raw(addr[0], addr[1], msg)

    def broadcast_to_neighbors(self, msg, exclude=None):
        for n in self.neighbors:
            if n == exclude:
                continue
            self.send_to_neighbor(n, msg)

    # ------------------------------------------------------------------ #
    # Dispatch de paquetes entrantes (forwarding)
    # ------------------------------------------------------------------ #
    def _dispatch(self, msg):
        mtype = msg.get("type")
        if mtype == "hello":
            self.handle_hello(msg)
        elif mtype in ("message", "data"):
            self.handle_data(msg)
        elif mtype == "info":
            self.handle_info(msg)
        elif mtype == "echo":
            self.handle_echo(msg)
        else:
            print(f"[{self.id}] tipo de mensaje desconocido: {mtype}")

    # ---- Handlers por defecto (los algoritmos sobreescriben lo que necesiten) ----
    def handle_hello(self, msg):
        print(f"[{self.id}] HELLO recibido de {msg['from']}")

    def handle_echo(self, msg):
        print(f"[{self.id}] ECHO de {msg['from']}: {msg.get('payload')}")

    def handle_data(self, msg):
        """Paquete de datos de usuario: si es para mí, imprimir; si no, reenviar."""
        if msg["to"] == self.id:
            print(f"[{self.id}] *** mensaje recibido de {msg['from']}: {msg.get('payload')}")
            return
        self.forward_data(msg)

    def forward_data(self, msg):
        msg["ttl"] -= 1
        if msg["ttl"] <= 0:
            print(f"[{self.id}] TTL agotado, descartando paquete hacia {msg['to']}")
            return
        next_hop = self.routing_table.get(msg["to"])
        if next_hop is None:
            print(f"[{self.id}] sin ruta conocida hacia {msg['to']}, descartando")
            return
        self.send_to_neighbor(next_hop, msg)

    def handle_info(self, msg):
        """Paquetes de info (tablas/LSP/DV). Cada algoritmo lo implementa."""
        raise NotImplementedError

    # ------------------------------------------------------------------ #
    # Utilidades comunes
    # ------------------------------------------------------------------ #
    def send_hello_to_neighbors(self):
        for n in self.neighbors:
            m = msgutil.build_message(self.proto, "hello", self.id, n, payload="")
            self.send_to_neighbor(n, m)

    def send_data(self, dest, payload, ttl=15):
        """Envía un mensaje de usuario hacia `dest` usando la tabla de ruteo."""
        msg = msgutil.build_message(self.proto, "message", self.id, dest, payload=payload, ttl=ttl)
        self.handle_data(msg)

    def _routing_loop(self):
        """Hilo de routing por defecto (no hace nada). Los algoritmos dinámicos
        (LSR, DVR) lo sobreescriben para enviar HELLO/LSP/DV periódicamente."""
        while self._running:
            time.sleep(5)

    def print_table(self):
        print(f"--- Tabla de ruteo de {self.id} ---")
        if not self.routing_table:
            print("  (vacía)")
        for dest, nh in sorted(self.routing_table.items()):
            print(f"  {dest} -> {nh}")
