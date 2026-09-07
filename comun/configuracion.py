"""
Carga de archivos de configuración.

Formatos oficiales del enunciado (Anexo):

  topo-*.txt  -> {"type":"topo",  "config": {"A": ["B","C"], "B": ["A"], ...}}
  names-*.txt -> {"type":"names", "config": {"A":"foo@bar.com", "B":"yolo@bar.com", ...}}

Formatos propios, SOLO para pruebas locales en Fase 1 (sockets),
no forman parte del protocolo oficial y no deben usarse para nada
más que levantar los sockets locales de prueba:

  pesos-*.txt   -> {"type":"weights", "config": {"A": {"B":7,"C":3}, ...}}
  puertos-*.txt -> {"A": ["127.0.0.1", 5001], "B": ["127.0.0.1", 5002], ...}
"""
import json


def load_topo(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["config"]


def load_names(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["config"]


def load_weights(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["config"]


def load_ports(path):
    """Solo para Fase 1 (sockets locales): node_id -> (host, port)."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {k: (v[0], int(v[1])) for k, v in data.items()}
