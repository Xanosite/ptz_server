import asyncio
import lib.client as client_lib
import logging
import pathlib
from datetime import datetime

VERSION = 0.3

async def main() -> None:
    mdir = pathlib.Path(__file__).parent.resolve()
    init_logger(mdir)
    logging.info(f'ptz_server v{VERSION} started')
    client_man = client_lib.Handler()
    async with asyncio.TaskGroup() as tg:
        announce_port = tg.create_task(client_man.announce_self())
        listen_ports = tg.create_task(client_man.listen_clients())
        close = tg.create_task(client_man.close())
    gentle_exit()

def gentle_exit() -> None:
    logging.info('Shutdown command received')

def init_logger(mdir):
    fname = datetime.now().strftime('%Y-%m-%d') + '.log.'
    logging.basicConfig(
        filename = pathlib.Path(mdir/'logs'/fname),
        level = logging.INFO,
        format = '%(levelname)s %(asctime)s %(message)s',
        datefmt = '%H:%M:%S'
    )

if __name__ == '__main__':
    asyncio.run(main())