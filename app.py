from http.server import HTTPServer, BaseHTTPRequestHandler

class HelloWorldHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b'<h1>Hello World!</h1>')

if __name__ == '__main__':
    server = HTTPServer(('localhost', 8000), HelloWorldHandler)
    print("Server running at http://localhost:8000/")
    server.serve_forever()