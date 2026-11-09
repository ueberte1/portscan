# ⚡ PortScan Pro - Varredor de Portas TCP com Interface Gráfica

Um scanner de portas TCP moderno, multithread e de alta velocidade para Windows, desenvolvido em Python. O projeto inclui uma **Interface Gráfica completa e intuitiva (GUI)** e versões aprimoradas para linha de comando (CLI).

---

## 🔍 O que havia de errado no código original?

1. **Bug Crítico de Reutilização de Socket (`Portscan.py`)**:
   - O comando `with socket.socket(...) as s:` estava **fora do loop** `for`. Quando a primeira porta falhava ou conectava, o socket entrava em estado inválido e as chamadas subsequentes falhavam com erros de socket do sistema operacional.
2. **Falta de Timeout (`settimeout`)**:
   - Sem definir um timeout explícito, conexões em portas filtradas ou fechadas dependiam do tempo limite padrão do sistema operacional (cerca de 20 a 30 segundos por porta). Com isso, varrer 100 portas podia levar dezenas de minutos.
3. **Valores Estáticos e Rígidos**:
   - O IP estava fixo como `'enter ip'`, sem opção de passar hostnames (como `localhost` ou `google.com`), sem resolução de DNS e com intervalo de portas restrito.
4. **Ausência de Interface Gráfica e Exportação**:
   - Não havia interface visual, barra de progresso, botão de cancelamento, mapeamento de serviços nem exportação dos resultados.

---

## ✨ Principais Melhorias Implementadas

- **🖥️ Interface Gráfica Moderna (GUI)**:
  - Design limpo com tema escuro tecnológico.
  - Suporte a alta resolução (High-DPI no Windows).
  - **Barra de Progresso** e contador em tempo real (`X / Y` portas).
  - **Cards com Métricas ao Vivo**: portas analisadas, total de portas abertas (em verde), fechadas, tempo decorrido e velocidade de varredura (portas por segundo).
  - **Atalhos Rápidos de Portas**:
    - *Top 25 Portas* (HTTP, HTTPS, SSH, FTP, MySQL, RDP, etc.)
    - *Web & Banco de Dados*
    - *Padrão (1-1024)*
    - *Varredura Completa (1-65535)*
  - **Resolução Automática de Nomes de Domínio / DNS**: Digite tanto `127.0.0.1` quanto `localhost` ou domínios.
  - **Identificação de Serviços**: Mapeia automaticamente portas conhecidas para seus protocolos (ex: 80 -> HTTP, 443 -> HTTPS, 22 -> SSH, 3306 -> MySQL, 3389 -> RDP).
  - **Tabela Interativa**:
    - Campo de busca/filtro instantâneo.
    - Opção de exibir apenas portas abertas.
    - Clique com o botão direito para copiar IP:Porta ou dados da linha.
  - **Aba de Console**: Histórico de logs detalhado e colorido em tempo real.
  - **Controle Total**: Botões para **Iniciar**, **Cancelar/Parar**, **Limpar** e **Exportar Relatório** (formatos `.csv`, `.txt` ou `.json`).

- **⚡ Motor Concorrente (Multithread)**:
  - Utiliza `concurrent.futures.ThreadPoolExecutor` com número de threads configurável (10 a 500) e timeout ajustável por porta.
  - Execução 100% não bloqueante (a interface nunca trava durante o escaneamento).

---

## 📁 Estrutura dos Arquivos

| Arquivo | Descrição |
|---|---|
| `gui_port_scanner.py` | **Aplicação com Interface Gráfica (GUI)** completa em Tkinter. |
| `iniciar_gui.bat` | Arquivo executável (dois cliques) para abrir a interface gráfica no Windows. |
| `scanner_core.py` | Núcleo do motor de escaneamento, resolução DNS e mapeamento de serviços. |
| `threading_port_scan.py` | Versão em linha de comando (CLI) multithread otimizada e com suporte a argumentos. |
| `Portscan.py` | Versão básica corrigida e segura (socket individual e timeout). |

---

## 🚀 Como Executar

### 1. Interface Gráfica (Recomendado)

Você pode abrir a interface gráfica de duas formas simples:

1. **Dois cliques no arquivo**:
   ```text
   iniciar_gui.bat
   ```
2. **Ou via terminal**:
   ```bash
   python gui_port_scanner.py
   ```

### 2. Linha de Comando Multithread (CLI)

```bash
# Escaneamento padrão (localhost, portas 1-1000):
python threading_port_scan.py

# Especificando alvo, portas e threads:
python threading_port_scan.py -t 127.0.0.1 -p 1-1024 -w 60 --timeout 0.8
```

### 3. Linha de Comando Simples Corrigida

```bash
python Portscan.py 127.0.0.1
```
