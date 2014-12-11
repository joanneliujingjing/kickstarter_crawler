#server test
import kickstarter_server_port as KSP
import socket

def test(url,identifier):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host = socket.gethostname()
    client.connect((host, KSP.PROJECT_PROBE_PORT))
    client.send(repr((url,identifier,)))
    client.shutdown(socket.SHUT_RDWR)
    client.close()
