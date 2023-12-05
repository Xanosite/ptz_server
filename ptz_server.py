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
    con_man = client_lib.Connection_manager('fc0')
    async with asyncio.TaskGroup() as tg:
        tg.create_task(con_man.listen())

def init_logger(mdir):
    fname = datetime.now().strftime('%Y-%m-%d') + '.log'
    logging.basicConfig(
        filename = pathlib.Path(mdir/'logs'/fname),
        level = logging.INFO,
        format = '%(levelname)s %(asctime)s %(message)s',
        datefmt = '%H:%M:%S'
    )

if __name__ == '__main__':
    asyncio.run(main())