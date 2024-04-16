import socket
import threading
import queue

IP = 'enter ip'
q = queue.Queue()

for i in range(1, 1001):
    q.put(i)

def Scan():
    while not q.empty():
        port = q.get()
        with  socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
              s.connect((IP, port))
              print(f'port {port} open ')
            except:
                pass
        q.task_done()


for i in range(30):
    t = threading.Thread(target=Scan, daemon=True)
    t.start()

q.join()
print('Finished')
