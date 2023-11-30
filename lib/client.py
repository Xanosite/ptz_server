import asyncio
import logging
import socket

MAGIC = 'pr7d68j1'
S_PORT = 50201

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

    def __init__(self, host: str) -> None:
        """
        host: ipv4 address of host system
        """
        self.active = True
        self.clients = []
        self.host = host
        self.hostname = socket.getfqdn()
        self.port = None
        self.serversock = None

    async def announce_self(self) -> None:
        """
        Broadcast actual server port via UDP
        """
        logging.info('Server port announcement service stared')
        udp_serversocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_serversocket.bind(self.host, S_PORT)
        udp_serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        data = (MAGIC, self.hostname, self.port)
        while self.active:
            self.status_mon['announce_self'] = 'Active'
            await send_udp(
                udp_serversocket, (MAGIC, self.hostname, self.port), S_PORT
            )
            logging.debug(
                f'Service port announcement broadcasted from {self.hostname}:'
                f'{S_PORT}\n    Data: {data}'
            )
            await asyncio.sleep(5)
        udp_serversocket.shutdown(socket.SHUT_RDWR)
        udp_serversocket.close()
        self.status_mon['announce_self'] = 'Inactive'
        logging.info('Server port announcement service stopped')

    async def listen_clients(self) -> None:
        """
        Listens for connections, spawns new clients on connect
        """
        # Start up server socket for listening
        self.serversock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serversock.bind((self.host, 0))
        self.port = self.serversock.getsockname()[1]
        self.serversock.listen(10)
        logging.info(f'Listening on {self.host}:{self.port}')
        # Listen for new connections, spawn new clients
        while self.active:
            self.status_mon['listen_clients'] = 'Active'
            connection, address = self.serversock.accept()
            logging.debug(f'Accepted connection to {address[0]}')
            self.clients.append(Client(connection, address[0]))
            await asyncio.sleep()
        # Shut down listening socket if handler becomes inactive
        self.status_mon['listen_clients'] = 'Inactive'
        self.serversock.shutdown(socket.SHUT_RDWR)
        self.serversock.close()
        self.serversock = None
        logging.info('Listening service stopped')

    def close_client(self, client) -> None:
        """
        Close client and remove from tracked clients
        client: client to be closed
        """
        client.close()
        del self.clients[client.get_address()]

    async def close(self) -> None:
        """
        Graceful shutdown of client manager
        """
        self.active = False
        for client in self.clients:
            client.close()
        timer = 0
        waiting = True
        while waiting:
            if 'Active' in self.status_mon.values(): waiting = True
            elif len(self.clients) > 0: waiting = True
            else: waiting = False
            if timer > 9:
                logging.warning('Client handler did not shut down properly')
                waiting = False
            if waiting:
                display = '  Status monitor:\n'
                for activity in self.status_mon:
                    display += f'    {activity}:{self.status_mon[activity]}\n'
                display += '  Clients:\n'
                for client in self.clients:
                    logging.debug(f'{len(self.clients)} clients still connected')
                logging.debug(f'Client handler waiting:\n{display}')
                await asyncio.sleep(2)
                timer += 2
        logging.info('Client handler service stopped')

class Client:
    """
    Client manager
    """
    address = None
    connection = None
    def __init__(self, connection: socket.socket, address: str) -> None:
        self.address = address
        self.connection = connection

    def get_address(self) -> str:
        return self.address

    def close(self) -> None:
        self.connection.shutdown(socket.SHUT_RDWR)
        self.connection.close()
        logging.debug(f'Connection closed to {self.address}')

async def send_to_sock(socket: socket.socket, data: dict) -> None:
    """
    Send data to active socket
    Data sent as bytes string of dictionary
    """
    b_data = bytes(str(data), 'utf-8')
    total_sent = len(b_data)
    sent = 0
    while sent < total_sent:
        sent = socket.send(b_data[total_sent:])
        if sent == 0:
            raise RuntimeError('Socket connection broken')
        total_sent += sent
        if sent < total_sent: await asyncio.sleep()

async def send_udp(socket: socket.socket, data: dict, port: int) -> None:
    """
    Broadcast data via UDP socket
    Data sent as bytes string of dictionary
    """
    b_data = bytes(str(data), 'utf-8')
    total_sent = len(b_data)
    sent = 0
    while sent < total_sent:
        sent = socket.sendto(b_data[total_sent:], ('<broadcast>', port))
        if sent == 0:
            raise RuntimeError('Socket error')
        total_sent += sent
        if sent < total_sent: await asyncio.sleep()