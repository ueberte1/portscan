"""
Módulo de Varredura de Portas (Port Scanner Core)
Responsável pela resolução DNS, mapeamento de serviços, controle multithread e métricas.
"""

import socket
import time
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, List, Tuple, Optional, Dict, Any

# Mapeamento estendido de portas e serviços comuns
COMMON_SERVICES: Dict[int, str] = {
    20: "FTP-Data",
    21: "FTP (Controle)",
    22: "SSH",
    23: "Telnet",
    25: "SMTP",
    53: "DNS",
    67: "DHCP",
    68: "DHCP",
    69: "TFTP",
    80: "HTTP",
    88: "Kerberos",
    110: "POP3",
    111: "RPCBind",
    119: "NNTP",
    123: "NTP",
    135: "MS-RPC",
    137: "NetBIOS-NS",
    138: "NetBIOS-DGM",
    139: "NetBIOS-SSN",
    143: "IMAP",
    161: "SNMP",
    162: "SNMP-Trap",
    389: "LDAP",
    443: "HTTPS",
    445: "SMB (Microsoft-DS)",
    465: "SMTPS",
    514: "Syslog",
    587: "SMTP (Submission)",
    636: "LDAPS",
    993: "IMAPS",
    995: "POP3S",
    1080: "SOCKS",
    1433: "MSSQL",
    1434: "MSSQL-Monitor",
    1521: "Oracle DB",
    2049: "NFS",
    3306: "MySQL",
    3389: "RDP (Área de Trabalho Remota)",
    5432: "PostgreSQL",
    5900: "VNC",
    5901: "VNC-1",
    6379: "Redis",
    8000: "HTTP-Alt",
    8080: "HTTP-Proxy / Tomcat",
    8443: "HTTPS-Alt",
    8888: "HTTP-Alt",
    9000: "SonarQube / PHP-FPM",
    9200: "Elasticsearch",
    27017: "MongoDB",
}

def resolve_target(target: str) -> Tuple[str, str]:
    """
    Resolve um hostname ou IP.
    Retorna uma tupla (ip_resolvido, hostname).
    """
    cleaned = target.strip()
    if cleaned.startswith("http://"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("https://"):
        cleaned = cleaned[8:]
    cleaned = cleaned.split("/")[0].split(":")[0]

    ip = socket.gethostbyname(cleaned)
    try:
        hostname = socket.gethostbyaddr(ip)[0]
    except (socket.herror, socket.gaierror, socket.error):
        hostname = cleaned
    return ip, hostname

def get_service_name(port: int) -> str:
    """Identifica o serviço associado à porta informada."""
    if port in COMMON_SERVICES:
        return COMMON_SERVICES[port]
    try:
        return socket.getservbyport(port, "tcp").upper()
    except (socket.error, OSError):
        return "Desconhecido"

def parse_port_range(port_str: str) -> List[int]:
    """
    Interpreta strings de portas como '80', '1-1000', '80, 443, 8080', '20-25, 80'.
    Retorna uma lista ordenada e sem duplicatas.
    """
    ports = set()
    parts = [p.strip() for p in port_str.split(",") if p.strip()]
    for part in parts:
        if "-" in part:
            sub = part.split("-")
            if len(sub) == 2:
                start, end = int(sub[0]), int(sub[1])
                start, end = max(1, min(start, end)), min(65535, max(start, end))
                ports.update(range(start, end + 1))
        else:
            p = int(part)
            if 1 <= p <= 65535:
                ports.add(p)
    return sorted(list(ports))

class ScanResult:
    def __init__(self, port: int, is_open: bool, latency_ms: float = 0.0,
                 service: str = "", banner: str = "", error_msg: str = ""):
        self.port = port
        self.is_open = is_open
        self.latency_ms = latency_ms
        self.service = service
        self.banner = banner
        self.error_msg = error_msg

    def to_dict(self) -> Dict[str, Any]:
        return {
            "port": self.port,
            "status": "OPEN" if self.is_open else "CLOSED",
            "service": self.service,
            "latency_ms": round(self.latency_ms, 2),
            "banner": self.banner,
        }

class PortScanner:
    """
    Motor multithread de varredura de portas com suporte a interrupção graciosa,
    cálculo de latência e detecção de banners.
    """
    def __init__(self, target_ip: str, timeout: float = 0.8,
                 max_threads: int = 50, grab_banner: bool = False):
        self.target_ip = target_ip
        self.timeout = max(0.05, timeout)
        self.max_threads = max(1, min(max_threads, 500))
        self.grab_banner = grab_banner
        self._stop_event = threading.Event()

    def stop(self) -> None:
        """Sinaliza para parar a varredura imediatamente."""
        self._stop_event.set()

    def is_stopped(self) -> bool:
        return self._stop_event.is_set()

    def scan_port(self, port: int) -> ScanResult:
        """Verifica se uma porta TCP individual está aberta."""
        if self._stop_event.is_set():
            return ScanResult(port, is_open=False, error_msg="Cancelled")

        start_time = time.perf_counter()
        is_open = False
        banner = ""
        error_msg = ""

        # Criação de socket individual com timeout estrito
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(self.timeout)
            try:
                result_code = s.connect_ex((self.target_ip, port))
                if result_code == 0:
                    is_open = True
                    if self.grab_banner:
                        try:
                            # Tenta receber banner padrão (ex: SSH, FTP, SMTP)
                            s.settimeout(0.6)
                            banner = s.recv(1024).decode('utf-8', errors='ignore').strip()
                        except Exception:
                            banner = ""
            except socket.timeout:
                error_msg = "Timeout"
            except socket.error as e:
                error_msg = str(e)
            except Exception as e:
                error_msg = str(e)

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        service = get_service_name(port) if is_open else ""
        return ScanResult(port, is_open=is_open, latency_ms=elapsed_ms,
                          service=service, banner=banner, error_msg=error_msg)

    def scan_ports(self, ports: List[int],
                   callback: Optional[Callable[[ScanResult, int, int], None]] = None) -> List[ScanResult]:
        """
        Executa a varredura concorrente para uma lista de portas.
        O callback recebe: (ScanResult, portas_concluidas, total_portas).
        """
        self._stop_event.clear()
        results: List[ScanResult] = []
        total = len(ports)
        completed = 0
        lock = threading.Lock()

        def worker(p: int):
            nonlocal completed
            if self._stop_event.is_set():
                return None
            res = self.scan_port(p)
            with lock:
                completed += 1
                results.append(res)
                if callback:
                    callback(res, completed, total)
            return res

        with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            # Submete as tarefas
            futures = [executor.submit(worker, p) for p in ports]
            for future in futures:
                if self._stop_event.is_set():
                    executor.shutdown(wait=False, cancel_futures=True)
                    break
                try:
                    future.result()
                except Exception:
                    pass

        # Ordena os resultados pelo número da porta
        results.sort(key=lambda r: r.port)
        return results
