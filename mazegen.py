import asyncio
import aiohttp
from aiohttp.web import RouteTableDef, run_app, Application, Request, Response, json_response

from mazelib import generate_maze # optional

routes = RouteTableDef()

@routes.get('/')
async def index(request : Request) -> Response:
    """Done for you.
    Works with __main__ to display an informative front-end"""
    return Response(text=index_file, content_type="text/html")

@routes.post('/notify')
async def alert(request : Request) -> Response:
    """Done for you.
    If you POST a URL to /notify, this function POSTs this app's URL to the URL it is sent."""
    url = await request.text()
    print('POSTing',whoami,'to',url)
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=whoami) as resp:
            return Response(status=resp.status, headers=resp.headers, body=await resp.read())


@routes.get('/static')
async def static_maze(request : Request) -> Response:
    """Returns the same 7×7 maze with 4 exits every time it is called"""
    maze = [ 
        "988088c"
    , "1220224"
    , "5ba49c5"
    , "49c1041"
    , "5361045"
    , "1880004"
    , "3220226"
    ]
    return json_response(maze)


@routes.get('/dynamic/{h}')
async def dynamic_maze(request : Request) -> Response:
    """Returns a different 7×7 maze each time it is called,
    with between 0 and 4 exits as specified by the hex digit in the URL:
    /dynamic/0 has 4 exits, /dynamic/1 has 3 (left is closed),
    and so on up to /dynamic/F which has no exits at all."""
    kind = int(request.match_info['h'], 16) # get the kind from the path
    maze = None

    kindGates = {
        0: [((0, 3), 1), ((3,6),2), ((6, 3), 4), ((3, 0), 8)],
        1: [((3,6),2), ((6, 3), 4), ((3, 0), 8)],
        2: [((0, 3), 1), ((6, 3), 4), ((3, 0), 8)],
        3: [((6, 3), 4), ((3, 0), 8)],
        4: [((0, 3), 1), ((3,6),2), ((3, 0), 8)],
        5: [((3,6),2), ((3, 0), 8)],
        6: [((0, 3), 1), ((3, 0), 8)],
        7: [((3, 0), 8)],
        8: [((0, 3), 1), ((3,6),2), ((6, 3), 4)],
        9: [((3,6),2), ((6, 3), 4)],
        10: [((0, 3), 1), ((6, 3), 4)],
        11: [((6, 3), 4)],
        12: [((0, 3), 1), ((3,6),2)],
        13: [((3,6),2)],
        14: [((0, 3), 1)],
        15: []
    }

    # .append((x,y), wall)
    print(kindGates[kind])
    maze = generate_maze(kindGates[kind])
    print("HERES THE Mze")
    print(maze)

#     if kind == 0:
#         maze = ["DFD3ACD", "1A0A824", "5D5D5F5", "4757592", "1A0A02C", "5D7D3E5", "32A0AA6"]
#     if kind == 1:
#         maze = ["DFD3ACD", "1A0A824", "5D5D5F5", "5757592", "1A0A02C", "5D7D3E5", "32A0AA6"]
#     if kind == 2:
#         maze = ["DFD3ACD", "1A0A824", "5D5D5F5", "4757592", "1A0A02C", "5D7D3E5", "32A2AA6"]
#     if kind == 3:
#         maze = [
#     "DDD5BCF",
#     "5553C3C",
#     "553C3C7",
#     "53C3C3A",
#     "3C3C3AE",
#     "D3C3AAE",
#     "3E3AAAE"
#   ]
#     if kind == 4:
#         maze = ["DFD3ACD", "1A0A824", "5D5D5F5", "4757596", "1A0A02C", "5D7D3E5", "32A0AA6"]
#     if kind == 5:
#         maze = [     "9AA0AAC",     "59E5BC5",     "57F5F75",     "1A808A4",     "5D326D5",     "53AAA65",     "3AA8AA6"   ]
#     if kind == 6:
#         maze = ["DFD3ACD", "1A0A824", "5D5D5F5", "4757596", "1A0A02C", "5D7D3E5", "32A2AA6"]
#     if kind == 7:
#         maze = [     "9AA0AAC",     "59E5BC5",     "57F5F75",     "1A808A4",     "5D326D5",     "53AAA65",     "3AAAAA6"   ]
#     if kind == 8:
#         maze = ["DFDBACD", "1A0A824", "5D5D5F5", "4757592", "1A0A02C", "5D7D3E5", "32A0AA6"]
#     if kind == 9:
#         maze = ["DFDBACD", "1A0A824", "5D5D5F5", "5757592", "1A0A02C", "5D7D3E5", "32A0AA6"]
#     if kind == 10:
#         maze = ["988A8AC", "555D5B4", "55777B4", "00A8A80", "14F5B04", "14F5904", "32A2226"]
#     if kind == 11:
#         maze = ["988A8AC", "555D5B4", "55777B4", "10A8A80", "14F5B04", "14F5904", "32A2226"]
#     if kind == 12:
#         maze = ["DFDBACD", "1A0A824", "5D5D5F5", "4757596", "1A0A02C", "5D7D3E5", "32A0AA6"]
#     if kind == 13:
#         maze = [ "9aaaaac" , "59888c5" , "5100045" , "5100045" , "5100045" , "5322265" , "3AA8AA6" ]
#     if kind == 14:
#         maze = [     "9AA8AAC",     "59E5BC5",     "57F5F75",     "0A808A4",     "5D326D5",     "53AAA65",     "3AAAAA6"   ]
#     if kind == 15:
#         maze = [     "DDDDBCF",     "5553C3C",     "553C3C7",     "53C3C3E",     "3C3C3AE",     "D3C3AAE",     "3E3AAAE"   ]
        
    return json_response(maze)


if __name__ == '__main__':
    # done for you
    
    # run the app with custom host and port
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', type=str, default="0.0.0.0")
    parser.add_argument('-p','--port', type=int, default=5340)
    args = parser.parse_args()

    # figure out our URL (a "fully qualified domain name" or fqdn), and put it into index.html
    import socket
    whoami = socket.getfqdn()
    if '.' not in whoami: whoami = 'localhost'
    whoami += ':'+str(args.port)
    whoami = 'http://' + whoami
    index_file = open('index.html').read().replace('UNKNOWN', whoami)

    print('running as', whoami)
    
    app = Application()
    app.add_routes(routes)
    run_app(app, host=args.host, port=args.port)
