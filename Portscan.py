import socket

IP_ADDRESS = 'enter ip'


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    for PORT in range(100, 151):
        try:
            s.connect((IP_ADDRESS,PORT))
            print(f'Port {PORT} is linening and open')
        except:
            print(f'failed to connect {PORT}')

