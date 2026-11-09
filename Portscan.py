"""
Portscan Simples (Versão Básica Corrigida e Melhorada)
- Criação de socket individual por tentativa (corrige bug de reuso de socket)
- Timeout configurado (evita que o script fique travado aguardando resposta)
- Suporta IP ou Hostname via entrada do usuário ou padrão 127.0.0.1
"""

import socket
import sys

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

def scan_simple(target: str = "127.0.0.1", start_port: int = 1, end_port: int = 150, timeout: float = 0.5):
    try:
        ip = socket.gethostbyname(target)
    except socket.gaierror:
        print(f"[-] Erro: Não foi possível resolver o endereço '{target}'")
        return

    print("=" * 50)
    print(f"Iniciando varredura simples em: {target} ({ip})")
    print(f"Intervalo de portas: {start_port} até {end_port} (Timeout: {timeout}s)")
    print("=" * 50)

    open_ports = []

    for port in range(start_port, end_port + 1):
        # O socket DEVE ser criado dentro do loop para cada conexão
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            try:
                result = s.connect_ex((ip, port))
                if result == 0:
                    try:
                        service = socket.getservbyport(port, "tcp").upper()
                    except (socket.error, OSError):
                        service = "Desconhecido"
                    print(f"[+] Porta {port:<5} está ABERTA! (Serviço: {service})")
                    open_ports.append(port)
                else:
                    # Porta fechada ou filtrada
                    pass
            except socket.timeout:
                pass
            except Exception as e:
                print(f"[-] Erro na porta {port}: {e}")

    print("=" * 50)
    print(f"Varredura finalizada. Portas abertas encontradas: {len(open_ports)}")
    if open_ports:
        print("Portas abertas:", open_ports)
    print("=" * 50)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        target_host = sys.argv[1]
    else:
        user_input = input("Digite o IP ou Hostname para escanear [padrão 127.0.0.1]: ").strip()
        target_host = user_input if user_input else "127.0.0.1"

    scan_simple(target=target_host, start_port=100, end_port=150)
