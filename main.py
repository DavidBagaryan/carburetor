import socket
from select import select

from views import index, blog


class Engine:
    URLS = {
        '/': index,
        '/blog': blog
    }

    server_socket: socket.socket = None
    ip_and_port: tuple = None
    to_monitor = []

    def __init__(self, tcp_ip: tuple):
        self.ip_and_port = tcp_ip
        self.set_server_socket()

        self.to_monitor.append(self.server_socket)

    def set_server_socket(self):
        # socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
        sock = socket.socket()
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(self.ip_and_port)
        sock.listen(1)
        self.server_socket = sock

    def event_loop(self):
        while True:
            ready_to_read, _, _ = select(self.to_monitor, [], [])  # read, write, errors

            for sock in ready_to_read:
                if sock is self.server_socket:
                    self.accept_connection(sock)
                else:
                    self.send_message(sock)

    def accept_connection(self, server_socket):
        client_socket, address = server_socket.accept()
        print(f'connection from {address}')
        self.to_monitor.append(client_socket)

    @staticmethod
    def send_message(client_socket):
        request = client_socket.recv(4096)
        print(request)

        if request:
            response = Response(request)
            output = response.generate_response()

            client_socket.send(output)
        else:
            # client_socket.sendall(output)
            client_socket.close()


class Response:
    request = None
    method = None
    url = None

    METHOD_NOT_ALLOWED = ('HTTP/1.1 405 Method not allowed\n\n', 405)
    PAGE_NOT_FOUND = ('HTTP/1.1 404 not found\n\n', 404)
    STATUS_OK = ('HTTP/1.1 200 OK\n\n', 200)

    def __init__(self, request):
        self.request = request

    def generate_response(self) -> bytes:
        """:returns: encoded bytes"""

        self.parse_request()
        headers, code = self.validate_request()
        body = self.add_mask(code)

        return f'{headers} {body}'.encode('utf-8')

    def parse_request(self):
        """parse decoded user request"""

        parsed = self.request.decode('utf-8').split(' ')

        if len(parsed) > 1:
            self.method = parsed[0]
            self.url = parsed[1]

    def validate_request(self) -> tuple:
        """
        some toggle validation
        :returns: tuple with response
        """

        if not self.method == 'GET':
            return Response.METHOD_NOT_ALLOWED
        if self.url not in Engine.URLS:
            return Response.PAGE_NOT_FOUND

        return Response.STATUS_OK

    def add_mask(self, code) -> str:
        bad_request = '<h1>{}</h1><p>{}</p>'

        if code == 404:
            result = bad_request.format(code, 'page not found')
        elif code == 405:
            result = bad_request.format(code, 'method not allowed')
        else:
            result = Engine.URLS[self.url]()

        return result


if __name__ == '__main__':
    engine = Engine(('localhost', 5000))
    engine.event_loop()
