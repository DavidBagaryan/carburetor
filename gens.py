import socket
from select import select

from views import index, blog

URLS = {
    '/': index,
    '/blog': blog
}

tasks = []
to_read = {}
to_write = {}


def server():
    server_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('localhost', 5000))
    server_socket.listen(1)

    while True:
        yield ('read', server_socket)
        client_socket, address = server_socket.accept()

        print(f'connection from {address}')
        tasks.append(client(client_socket))


def client(client_socket):
    while True:
        yield ('read', client_socket)
        request = client_socket.recv(4096)

        if not request:
            break
        else:
            response = Response(request)
            output = response.generate_response()

            yield ('write', client_socket)
            client_socket.send(output)

    client_socket.close()


def event_loop():
    while any([tasks, to_read, to_write]):
        while not tasks:
            ready_to_read, ready_to_write, _ = select(to_read, to_write, [])

            for sock in ready_to_read:
                tasks.append(to_read.pop(sock))

            for sock in ready_to_write:
                tasks.append(to_write.pop(sock))

        try:
            task = tasks.pop(0)

            reason, sock = next(task)

            if reason == 'read':
                to_read[sock] = task
            if reason == 'write':
                to_write[sock] = task

        except StopIteration:
            print('DONE!')


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
        if self.url not in URLS:
            return Response.PAGE_NOT_FOUND

        return Response.STATUS_OK

    def add_mask(self, code) -> str:
        bad_request = '<h1>{}</h1><p>{}</p>'

        if code == 404:
            result = bad_request.format(code, 'page not found')
        elif code == 405:
            result = bad_request.format(code, 'method not allowed')
        else:
            result = URLS[self.url]()

        return result


if __name__ == '__main__':
    tasks.append(server())
    event_loop()
