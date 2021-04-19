import socket

host = "192.168.0.101"
port = 3333

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((host, port))
response = client.recv(4096)

print('response: ')
print(response.decode())
