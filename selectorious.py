import socket
import selectors

from views import index, blog


class Engine:
    URLS = {
        '/': index,
        '/blog': blog
    }

    selector: selectors.DefaultSelector = None
    server_socket: socket.socket = None
    client_socket: socket.socket = None
    ip_and_port: tuple = None

    def __init__(self, tcp_ip: tuple):
        self.ip_and_port = tcp_ip

    def init_server_socket(self):
        # socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
        self.server_socket = socket.socket()
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(self.ip_and_port)
        self.server_socket.listen(1)

    def set_selector(self):
        self.selector = selectors.DefaultSelector()
        self.selector.register(fileobj=self.server_socket, events=selectors.EVENT_READ, data=self.accept_connection)

    def accept_connection(self):
        self.client_socket, address = self.server_socket.accept()
        print(f'connection from {address}')
        self.selector.register(fileobj=self.client_socket, events=selectors.EVENT_READ, data=self.send_message)

    def send_message(self):
        request = self.client_socket.recv(4096)
        if request:
            response = Response(request)
            output = response.generate_response()
            self.client_socket.send(output)
        else:
            self.selector.unregister(self.client_socket)
            self.client_socket.close()

    def event_loop(self):
        while True:
            event = self.selector.select()  # (key, event)
            for key, _ in event:
                key.data()

                # callback = key.data
                # callback(key.fileobj)

    def run_server(self):
        if self.server_socket is None:
            self.init_server_socket()
            self.set_selector()

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
    engine.run_server()
