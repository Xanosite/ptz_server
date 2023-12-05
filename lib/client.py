import ast
import asyncio
import logging
from ptz_server import VERSION

MAGIC = 'pr7d68j1'
M_PORT = int(50201)

class Connection_manager:
    """
    con_man
    Manages client connections
    """
    host = None
    port = None
    serv = None

    def __init__(self, host: str, port: int=M_PORT) -> None:
        self.host = host
        self.port = port
    
    async def listen(self) -> None:
        """
        Listen for clients
        """
        self.serv = await asyncio.start_server(new_client, self.host, self.port)
        logging.info(f'Client server started on {self.host}:{self.port}')

    async def close(self) -> None:
        """
        Greaceful shutdown of client server
        """
        logging.info('Client server shutdown command received')
        self.serv.close()
        await self.serv.wait_closed()
        logging.info('Client server shutdown complete, offline')

    def get_clients(self) -> list:
        """
        Returns list of socket like objects currently connected
        """
        return [] if self.serv == None else self.serv.sockets

    def get_is_serving(self) -> bool:
        """
        Returns true if server is listening for connections
        """
        return False if self.serv is None else self.serv.is_serving()
    
    def get_loop(self) -> asyncio.BaseEventLoop:
        return None if self.serv is None else self.serv.get_loop()

## Client functions
async def client_handshake(reader: asyncio.StreamReader,
                           writer: asyncio.StreamWriter, addr: str) -> bool:
    """
    Performs initial connection checks on client connection
    Returns true if all checks pass
    """
    status = False
    # Check if magic and version response from client matches server
    init_data = {'version':VERSION,}
    await send(writer, init_data)
    client_response = await receive(reader, writer)
    keys = ('version', 'magic')
    if all(key in client_response.keys() for key in keys): status = (
        client_response['version'] == VERSION
        and client_response['magic'] == MAGIC
    )
    else: status = False
    logging.debug(f'Handshake attempt with {addr} success?: {status}')
    return status

async def close(writer: asyncio.StreamWriter) -> None:
    addr = writer.get_extra_info('peername')
    writer.close()
    await writer.wait_closed()
    logging.info(f'Closed client {addr}')

async def new_client(reader: asyncio.StreamReader,
                     writer: asyncio.StreamWriter) -> None:
    """
    Take new client connection and begin operations
    """
    addr = writer.get_extra_info('peername')
    logging.debug(f'New client connection atttempt from {addr}')
    # Perform initial client checks
    handshake = await client_handshake(reader, writer, addr)
    if handshake:
        logging.info(f'New client connected at {addr}')
    else:
        logging.warning(f'Connection attempt by {addr} failed handshake')
        await close(writer)
        return None
    # Close client connection
    await close(writer)

async def receive(reader: asyncio.StreamReader, writer: asyncio.StreamWriter=None) -> dict:
    paddr = None if writer == None else writer.get_extra_info('peername')
    saddr = None if writer == None else writer.get_extra_info('sockname')
    b_data = b''
    while True:
        chunk = await reader.read(1024)
        if chunk == b'': break
        else: b_data += chunk
    data = ast.literal_eval(b_data.decode('utf-8'))
    if writer == None: logging.debug(f'Received data: {data}')
    else: logging.debug(f'Server {saddr} received data from {paddr}: {data}')
    return data

async def send(writer: asyncio.StreamWriter , data: dict) -> None:
    paddr = writer.get_extra_info('peername')
    saddr = writer.get_extra_info('sockname')
    logging.debug(f'Server {saddr} sending data to {paddr}: {data}')
    b_data = bytes(str(data), 'utf-8')
    writer.write(b_data)
    await writer.drain()
    writer.write_eof()