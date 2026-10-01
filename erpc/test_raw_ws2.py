import requests, urllib3, json, time, re
import socketio

urllib3.disable_warnings()

token = open("/mnt/c/Users/Administrator/Desktop/JySecAI/erpc/data/femet_jwt.txt").read().strip()

# EIO=4 with tpesig Host offers websocket upgrade
# Let's use python-socketio with custom headers
class TpeSigManager(socketio.Client):
    def __init__(self):
        super().__init__(ssl_verify=False)
        
# Actually, let's try a different approach - use the raw websocket
# with proper EIO=4 websocket upgrade
from websockets.asyncio.client import connect
import ssl, asyncio

async def test():
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    
    # EIO=4 websocket with tpesig Host
    ws_url = "wss://tpertc.tfd.gov.tw:8787/socket.io/?EIO=4&transport=websocket"
    
    # Use a raw socket approach instead
    import socket, struct
    
    # Actually let's try with the websockets library and set Host header
    # But websockets doesn't let us override Host...
    # Let me use a raw TCP approach
    
    # First get the SID via polling with tpesig Host
    r = requests.get(
        "https://tpertc.tfd.gov.tw:8787/socket.io/?EIO=4&transport=polling",
        headers={"Host": "tpesig.femet.com.tw"},
        verify=False, timeout=10
    )
    print(f"Polling: {r.status_code} {r.text[:200]}")
    
    m = re.search(r'"sid":"([^"]+)"', r.text)
    if m:
        sid = m.group(1)
        print(f"SID: {sid}")
        
        # Now connect via websocket using raw socket with tpesig Host header
        host = "tpertc.tfd.gov.tw"
        port = 8787
        
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ssock = ctx.wrap_socket(sock, server_hostname="tpertc.tfd.gov.tw")
        ssock.connect((host, port))
        
        # Build websocket upgrade request with tpesig Host
        ws_key = "dGhlIHNhbXBsZSBub25jZQ=="
        request = (
            f"GET /socket.io/?EIO=4&transport=websocket&sid={sid} HTTP/1.1\r\n"
            f"Host: tpesig.femet.com.tw\r\n"
            f"Upgrade: websocket\r\n"
            f"Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {ws_key}\r\n"
            f"Sec-WebSocket-Version: 13\r\n"
            f"Origin: https://tpesig.femet.com.tw\r\n"
            f"\r\n"
        )
        ssock.send(request.encode())
        
        # Read response
        resp = ssock.recv(4096)
        print(f"WS upgrade response: {resp[:500]}")
        
        if b"101" in resp:
            print("WebSocket upgrade SUCCESS!")
            
            # Read handshake
            time.sleep(0.5)
            data = ssock.recv(4096)
            print(f"Handshake: {data[:300]}")
            
            # Send auth (CONNECT packet with token)
            auth_data = f'0{{"token":"{token}"}}'
            ssock.send(auth_data.encode())
            time.sleep(1)
            
            try:
                resp1 = ssock.recv(4096)
                print(f"Auth response: {resp1[:300]}")
            except:
                print("No auth response")
            
            # Send join
            join_data = '42["join",{"name":"femet","room":"myRoom123"}]'
            ssock.send(join_data.encode())
            time.sleep(2)
            
            try:
                resp2 = ssock.recv(4096)
                print(f"After join: {resp2[:500]}")
            except:
                print("No join response")
            
            # Listen for events
            print("Listening for 25 seconds...")
            for i in range(13):
                time.sleep(2)
                try:
                    ssock.settimeout(1)
                    resp3 = ssock.recv(4096)
                    if resp3:
                        print(f"  [{i*2}s] {resp3[:500]}")
                    else:
                        print(f"  [{i*2}s] connection closed")
                        break
                except socket.timeout:
                    # Send pong to keep alive
                    ssock.send(b"3")
                    pass
                except Exception as e:
                    print(f"  [{i*2}s] error: {e}")
                    break
            
            ssock.close()
        else:
            print("WebSocket upgrade failed")
            ssock.close()

asyncio.run(test())
