import ast
import asyncio
import logging

MAGIC = 'pr7d68j1'
M_PORT = int(50201)

class Handler:
    """
    Client connection manager
    """
    active = False
    hostname = None
    host = None
    port = None
    serversock = None
    status_mon = {}
    clients = {}

    def __init__(self, host: str, port: int=M_PORT) -> None:
        """
        host: ipv4 address of host system
        """
        self.clients = []
        self.host = host
        self.port = port
        self.serv = None

    async def listen_clients(self) -> None:
        """
        Listens for connections, spawns new clients on connect
        """
        async def new_client(reader: asyncio.StreamReader,
                             writer: asyncio.StreamWriter) -> None:
            """
            Manage new client connections
            """
            client = Client(reader, writer, self)
            self.clients.append(client)
            await client.start()
        # Start up server socket for listening
        self.serv = await asyncio.start_server(new_client, self.host, self.port)
        logging.info(
            f'Client listening server started at {self.host}:{self.port}'
        )
        
    async def close(self) -> None:
        """
        Graceful shutdown of client manager
        """
        logging.info("Client connection server stop command received")
        logging.debug(f'Clients connected: {len(self.clients)}')
        if len(self.clients) > 0:
            for client in self.clients:
                await client.close()
        logging.debug(f'Clients connected: {len(self.clients)}')
        self.serv.close()
        await self.serv.wait_closed()
        logging.info("Client connection server stopped")

class Client:
    """
    Client manager
    """
    def __init__(self, reader: asyncio.StreamReader,
                 writer: asyncio.StreamWriter,
                 handler: Handler) -> None:
        self.reader = reader
        self.writer = writer
        self.status = {}
        self.handler = handler

    async def start(self) -> None:
        await self.send_to_client(self.status)

    async def close(self) -> None:
        if self.writer.is_closing():
            return None
        else:
            self.writer.close()
            await self.writer.wait_closed()

    async def send_to_client(self, data: dict) -> None:
        b_data = bytes(str(data), 'utf-8')
        self.writer.write(b_data)
        await self.writer.drain()

    async def receive_from_client(self) -> dict:
        data = b''
        while True:
            chunk = await self.reader.read(100)
            if chunk == b'': break
            data += chunk
        return ast.literal_eval(data.decode('utf-8'))
        
    async def parse_client_data(self, data: dict) -> None:
        # Commands
        if 'command' in data.keys():
            match data['command']:
                case 'dev_kit': await self.cmd_dev_kit(data)

    async def com_shutdown(self, target: str) -> None:
        match target:
            case 'handler': self.handler.close()
            case 'client': self.close()
    
    async def cmd_dev_kit(self, data: dict) -> None:
        match data['command']:
            case 'disconnect_client': self.close()
            case 'stop_client_server': self.handler.close()
