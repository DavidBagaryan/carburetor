import socket
import selectors

from views import index, blog


class Engine:
    URLS = {
        '/': index,
        '/blog': blog
    }

    selector: selectors.DefaultSelector = None

    def __init__(self, tcp_ip: tuple):
        self.ip_and_port = tcp_ip

    def run_server(self):
        # socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
        server_socket = socket.socket()
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(self.ip_and_port)
        server_socket.listen(1)

        self.set_selector(server_socket)

    def set_selector(self, server_socket):
        self.selector = selectors.DefaultSelector()
        self.selector.register(fileobj=server_socket, events=selectors.EVENT_READ, data=self.accept_connection)

    def accept_connection(self, server_socket):
        client_socket, address = server_socket.accept()
        print(f'connection from {address}')
        self.selector.register(fileobj=client_socket, events=selectors.EVENT_READ, data=self.send_message)

    def send_message(self, client_socket):
        request = client_socket.recv(4096)
        if request:
            response = Response(request)
            output = response.generate_response()
            client_socket.send(output)
        else:
            self.selector.unregister(client_socket)
            client_socket.close()

    def event_loop(self):
        while True:
            event = self.selector.select()  # (key, event)
            for key, _ in event:
                print(key.data)
                key.data(key.fileobj)

    def run(self):
        self.run_server()
        self.event_loop()


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
    engine.run()
