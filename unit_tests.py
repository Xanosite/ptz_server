import asyncio
#import client_lib

async def main() -> None:
    await run_test('Test Tester', test_tester)

def make_test_display(test_name: str, status: int) -> str:
    match status:
        case 0: state = 'Running'
        case 1: state = 'Passed'
        case 2: pass
        case 3: pass
        case 4: pass
        case 5: pass
    space = 80 - len(test_name) - len(state)
    return test_name + (' . ' * int(space/3)) + (' ' * (space % 3)) + state

async def run_test(test_name, test) -> None:
    print(make_test_display(test_name,0), end='\r')
    print(make_test_display(test_name, await test()))

async def test_tester() -> int:
    return 1

if __name__ == '__main__':
    asyncio.run(main())