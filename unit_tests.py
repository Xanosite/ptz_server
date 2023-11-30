import asyncio
import logging
import pathlib
import lib.client as client_lib
from datetime import datetime

async def main() -> None:
    mdir = pathlib.Path(__file__).parent.resolve()
    init_logger(mdir)
    logging.info('#### Unit tests started. ####')
    print(('#'*25) +'  Pautzke Server: Unit tests  ' + ('#'*25))
    await test_tester()
    await test_handler()

def make_test_display(test_name: str, status: int) -> str:
    match status:
        case 0: state = 'Running'
        case 1: state = 'Passed'
        case 2: state = 'Failed'
        case 3: state = 'Unknown'
        case 4: pass
        case 5: pass
    space = 80 - len(test_name) - len(state)
    return test_name + (' . ' * int(space/3)) + (' ' * (space % 3)) + state

def print_test(test_name, status: int, end: bool) -> None:
    if end: print(make_test_display(test_name, status))
    else: print(make_test_display(test_name,0), end='\r')
    

def init_logger(mdir):
    fname = datetime.now().strftime('%Y-%m-%d') + '.log'
    logging.basicConfig(
        filename = pathlib.Path(mdir/'logs'/fname),
        level = logging.DEBUG,
        format = '%(levelname)s %(asctime)s %(message)s',
        datefmt = '%H:%M:%S'
    )

# Tests
async def test_tester():
    print_test('Test Tester', 0, False)
    print_test('Test Tester', 1, True)

async def test_handler():
    status = 0
    print_test('Client Server', status, False)
    handler = None
    try:
        handler = client_lib.Handler('172.233.157.205')
        await handler.listen_clients()
    except Exception as err:
        logging.error(err)
        status = 2
    else: status = 1
    print_test('Client Server', status, True)
    status = 3 if status == 2 else 0
    print_test('Client connection', status, status == 3)
    if status == 3: return None
    try:
        reader, writer = await asyncio.open_connection('172.233.157.205', 50201)
        data = await reader.read(1000)
        data = data.decode('utf-8')
        writer.close()
        await writer.wait_closed()
        reader2, writer2 = await asyncio.open_connection('172.233.157.205', 50201)
        data2 = await reader2.read(1000)
        writer2.close()
        await writer2.wait_closed()
        await handler.close()
    except Exception as err:
        logging.error(err)
        status = 2
    else: status = 1
    print_test('Client Connection', status, True)

if __name__ == '__main__':
    asyncio.run(main())

