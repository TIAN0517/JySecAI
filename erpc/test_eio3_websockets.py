import asyncio
import ssl
import json
from websockets.asyncio.client import connect, ClientConnection

token = open("/mnt/c/Users/Administrator/Desktop/JySecAI/erpc/data/femet_jwt.txt").read().strip()

async def test():
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    
    # EIO=3 with token in URL query, tpesig Host
    uri = f"wss://tpertc.tfd.gov.tw:8787/socket.io/?EIO=3&transport=websocket&token={token}"
    
    try:
        async with connect(
            uri,
            ssl=ssl_ctx,
            open_timeout=5,
            close_timeout=2,
            additional_headers={
                "Host": "tpesig.femet.com.tw",
                "Origin": "https://tpesig.femet.com.tw"
            }
        ) as ws:
            print("Connected! Reading handshake...")
            
            # Read handshake
            msg = await asyncio.wait_for(ws.recv(), timeout=5)
            print(f"Handshake: {msg[:200]}")
            
            # The server might send 40 (CONNECT_ERROR) or wait for our CONNECT
            # In EUI=3, we need to send the CONNECT packet ourselves
            # Socket.IO v3 CONNECT: 0{auth}
            
            # Send CONNECT with auth
            auth = f'0{{"token":"{token}"}}'
            await ws.send(auth)
            print(f"Sent auth: {auth}")
            
            try:
                resp = await asyncio.wait_for(ws.recv(), timeout=5)
                print(f"Auth response: {resp[:300]}")
            except asyncio.TimeoutError:
                print("No auth response (timeout)")
            
            # Send join
            join = '42["join",{"name":"femet","room":"myRoom123"}]'
            await ws.send(join)
            print(f"Sent join: {join}")
            
            try:
                resp = await asyncio.wait_for(ws.recv(), timeout=5)
                print(f"Join response: {resp[:500]}")
            except asyncio.TimeoutError:
                print("No join response (timeout)")
            
            # Listen
            print("Listening for 20 seconds...")
            for i in range(10):
                try:
                    resp = await asyncio.wait_for(ws.recv(), timeout=2)
                    print(f"  [{i*2}s] {resp[:300]}")
                except asyncio.TimeoutError:
                    # Send ping
                    await ws.send("2")
                    try:
                        pong = await asyncio.wait_for(ws.recv(), timeout=2)
                        print(f"  [{i*2}s] Pong: {pong[:100]}")
                    except:
                        pass
                except Exception as e:
                    print(f"  [{i*2}s] Error: {e}")
                    break
                await asyncio.sleep(1)
            
    except Exception as e:
        print(f"Connection error: {e}")

asyncio.run(test())
