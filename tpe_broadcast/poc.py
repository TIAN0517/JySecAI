import asyncio
from aioice.turn import create_turn_endpoint, TurnClientUdpProtocol

class UserProtocol(asyncio.DatagramProtocol):
    def datagram_received(self, data, addr): pass
    def connection_made(self, transport): self.transport = transport

async def main():
    loop = asyncio.get_event_loop()
    turn_transport, user_protocol = await create_turn_endpoint(
        UserProtocol,
        server_addr=("turnserver.tfd.gov.tw", 3478),
        username="jarstar", password="12345678",
        lifetime=600, channel_refresh_time=120,
        transport="udp",
    )
    relayed = turn_transport.get_extra_info('sockname')
    print(f"Allocated: {relayed}")  # ('210.69.42.27', 57496)

asyncio.run(main())
