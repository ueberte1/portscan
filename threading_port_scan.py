"""
Portscan Multithread de Alta Velocidade (CLI)
- Varredura concorrente com filas (queue.Queue) e threads
- Timeout otimizado para evitar travamento
- Resolução de DNS automática (aceita IPs e domínios)
- Detecção do nome do serviço de cada porta aberta
- Medição de tempo decorrido e resumo detalhado
"""

import socket
import threading
import queue
import time
import sys
import argparse
from typing import List

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# Dicionário de serviços comuns
COMMON_SERVICES = {
    21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS",
    80: "HTTP", 110: "POP3", 135: "MS-RPC", 139: "NetBIOS",
    143: "IMAP", 443: "HTTPS", 445: "SMB", 1433: "MSSQL",
    1521: "Oracle", 3306: "MySQL", 3389: "RDP", 5432: "PostgreSQL",
    5900: "VNC", 6379: "Redis", 8080: "HTTP-Proxy", 8443: "HTTPS-Alt"
}

def get_service_name(port: int) -> str:
    if port in COMMON_SERVICES:
        return COMMON_SERVICES[port]
    try:
        return socket.getservbyport(port, "tcp").upper()
    except (socket.error, OSError):
        return "Desconhecido"

def run_threaded_scan(target: str, start_port: int = 1, end_port: int = 1000,
                      num_threads: int = 50, timeout: float = 0.8):
    try:
        ip = socket.gethostbyname(target)
    except socket.gaierror:
        print(f"\n[-] Erro: Não foi possível resolver o alvo '{target}'")
        return

    print("\n" + "=" * 65)
    print(f"🚀 INICIANDO VARREDURA MULTITHREAD")
    print(f"🎯 Alvo: {target} ({ip})")
    print(f"🔢 Portas: {start_port} até {end_port} (Total: {end_port - start_port + 1})")
    print(f"⚡ Threads: {num_threads} | ⏱ Timeout: {timeout}s")
    print("=" * 65 + "\n")

    q = queue.Queue()
    for port in range(start_port, end_port + 1):
        q.put(port)

    open_ports = []
    lock = threading.Lock()
    start_time = time.perf_counter()

    def worker():
        while True:
            try:
                port = q.get_nowait()
            except queue.Empty:
                break

            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(timeout)
                t0 = time.perf_counter()
                try:
                    result = s.connect_ex((ip, port))
                    if result == 0:
                        lat_ms = (time.perf_counter() - t0) * 1000.0
                        service = get_service_name(port)
                        with lock:
                            open_ports.append((port, service, lat_ms))
                            print(f" [+] Porta {port:<5} ABERTA | Serviço: {service:<15} ({lat_ms:.1f}ms)")
                except Exception:
                    pass
                finally:
                    q.task_done()

    threads: List[threading.Thread] = []
    for _ in range(min(num_threads, end_port - start_port + 1)):
        t = threading.Thread(target=worker, daemon=True)
        t.start()
        threads.append(t)

    # Aguarda todas as tarefas da fila terminarem
    q.join()

    elapsed = time.perf_counter() - start_time
    total_ports = end_port - start_port + 1
    speed = total_ports / max(0.01, elapsed)

    print("\n" + "=" * 65)
    print(f"🏁 VARREDURA CONCLUÍDA EM {elapsed:.2f}s ({speed:.1f} portas/s)")
    print(f"🔍 Portas abertas encontradas: {len(open_ports)}")
    if open_ports:
        print("\n  PORTA   SERVIÇO          LATÊNCIA")
        print("  " + "-" * 40)
        open_ports.sort(key=lambda x: x[0])
        for p, s, lat in open_ports:
            print(f"  {p:<7} {s:<16} {lat:.1f}ms")
    print("=" * 65 + "\n")

def main():
    parser = argparse.ArgumentParser(description="Portscan Multithread de Alta Performance (CLI)")
    parser.add_argument("-t", "--target", default="", help="Endereço IP ou Hostname do alvo")
    parser.add_argument("-p", "--ports", default="1-1000", help="Intervalo de portas (ex: 1-1000)")
    parser.add_argument("-w", "--workers", type=int, default=50, help="Quantidade de threads simultâneas (padrão: 50)")
    parser.add_argument("--timeout", type=float, default=0.8, help="Timeout em segundos para cada socket (padrão: 0.8)")

    args = parser.parse_args()

    target = args.target.strip()
    if not target:
        user_input = input("Digite o IP ou Hostname do alvo [padrão: 127.0.0.1]: ").strip()
        target = user_input if user_input else "127.0.0.1"

    # Processa portas
    if "-" in args.ports:
        p_start, p_end = map(int, args.ports.split("-"))
    else:
        p_start = p_end = int(args.ports)

    run_threaded_scan(target=target, start_port=p_start, end_port=p_end,
                      num_threads=args.workers, timeout=args.timeout)

if __name__ == "__main__":
    main()
