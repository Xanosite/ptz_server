import ast
import asyncio
import logging
import pathlib
import lib.client as client_lib
from datetime import datetime

async def main() -> None:
    mdir = pathlib.Path(__file__).parent.resolve()
    init_logger(mdir)
    logging.debug('# Unit tests: Starting unit test sequence')
    print(('#'*25) +'  Pautzke Server: Unit tests  ' + ('#'*25))
    con_man_test = await test_client_connection_manager()
    clients_test = await test_client_connections(con_man_test)
    logging.debug('# Unit tests: Test sequence complete')

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

def print_test(test_name, status: int, end: bool=False) -> None:
    if end:
        print(make_test_display(test_name, status))
        logging.debug(f'# Unit test: {test_name} test complete')
    else:
        print(make_test_display(test_name,0), end='\r')
        logging.debug(f'# Unit test: {test_name} test starting')
    
def init_logger(mdir):
    fname = datetime.now().strftime('%Y-%m-%d') + '.log'
    logging.basicConfig(
        filename = pathlib.Path(mdir/'logs'/fname),
        level = logging.DEBUG,
        format = '%(levelname)s %(asctime)s %(message)s',
        datefmt = '%H:%M:%S'
    )

async def test_client_connection_manager() -> int:
    name = 'Client connection manager'
    print_test(name, 0)
    try:
        con_man = client_lib.Connection_manager('fc0')
        await con_man.listen()
        await con_man.close()
    except Exception as err:
        logging.error(err)
        state = 2
    else: state = 1
    print_test(name, state, True)
    return state

async def test_client_connections(con_man_state: int) -> int:
    
    async def client() -> int:
        try:
            reader, writer = await asyncio.open_connection(
                'fc0', 50201
            )
            # Read data from server
            b_data = b''
            saddr = writer.get_extra_info('sockname')
            paddr = writer.get_extra_info('peername')
            while True:
                chunk = await reader.read(1024)
                if chunk == b'': break
                else:
                    b_data += chunk
            data = ast.literal_eval(b_data.decode('utf-8'))
            logging.debug(
                f'Client {saddr} received data from server {paddr}: {data}'
            )
            if data['version'] != client_lib.VERSION: return 2
            data = {'version':client_lib.VERSION, 'magic':client_lib.MAGIC}
            logging.debug(
                f'Client {saddr} sending data to server {paddr}: {data}'
            )
            b_data = bytes(str(data), 'utf-8')
            writer.write(b_data)
            await writer.drain()
            writer.write_eof()
            writer.close()
            await writer.wait_closed()
        except Exception as err:
            logging.error(err)
            state = 2
        else: state = 1
        return state
    
    name = 'Client connections'
    print_test(name, 0)
    if con_man_state != 1:
        state = 3
    else:
        con_man = client_lib.Connection_manager('fc0')
        await con_man.listen()
        client_1 = await client()
        client_2 = await client()
        await asyncio.sleep(1)
        await con_man.close()
        if client_1 == 1 and client_2 ==1: state = 1
        else: state = 2
    print_test(name, state, True)
    return state

if __name__ == '__main__': asyncio.run(main())