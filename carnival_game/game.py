from aiohttp import web
import uuid 

def error_page(msg: str):
    with open("error.html") as f:
        page = f.read()

    page = page.replace("__ERROR_MSG__", msg)

    return web.Response(
        text=page,
        content_type="text/html",
        status=400
    )


routes = web.RouteTableDef()

# Add aiohttp endpoints here, including at least @routes.get("/")
# Send tickets using `async with request.app['client'].post('/transfer', data=...) as resp:`

@routes.get("/")
async def home(request: web.Request) -> web.Response:
    print("Someone visited page: ", request.headers.get("User-Agent", "unknown"))
    memo = f'67-{uuid.uuid4().hex[:6]}'
    with open("home.html") as f:
        home_page = f.read()
    home_page = home_page.replace("__MEMO__", memo)
    resp = web.Response(text=home_page, content_type="text/html")
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    resp.headers["Pragma"] = "no-cache"
    resp.headers["Expires"] = "0"
    return resp

@routes.post("/end")
async def end(request: web.Request) -> web.Response:
    data = await request.post()
    memo = data["memo"]
    tickets = int(data["tickets"])
    player = request.app["sessions"].get(memo)
    if not player:
        return error_page("Unknown memo/session. Did you verify payment in /play first?")
    async with request.app["client"].post('/transfer', 
        json={'dst': player, 'n':tickets, 'memo':memo}
    ) as resp:
        data = await resp.json()
        if 'error' in data:
            print("The transfer failed; is bc_agent.py running and the USER/PASS correct?")
        else: 
            request.app["sessions"].pop(memo, None)
    
    with open("payout.html") as f:
        payout_page = f.read()
    payout_page = payout_page.replace("__TICKETS__", str(tickets))
    payout_page = payout_page.replace("__MEMO__", memo)
    payout_page = payout_page.replace("__PLAYER__", player)
    return web.Response(text=payout_page, content_type="text/html")
        
@routes.post("/play")
async def play(request: web.Request) -> web.Response:
    data = await request.post()
    memo = data["memo"].strip()
    block_id = data["block_id"].strip()
    async with request.app["client"].post("/getlive",
        data = block_id
    ) as resp:
        if resp.status != 200:
            return error_page("Blockchain ID seriously wrong.")
        block = await resp.json()
        if 'error' in block:
            return error_page(f"Could not locate block. Error: {block['error']}")

    change = block["change"]
        
    if change["dst"] != USER:
        return error_page("Payment was not received by this booth.")
    if change["memo"] != memo:
        return error_page("Incorrect memo.")

    if change["n"] < 2:
        return error_page("Insufficient number of tickets.")

    request.app["sessions"][memo] = change["src"]
    # no errors, payment complete, direct to play
    with open("play.html") as f:
        play_page = f.read()
    play_page = play_page.replace("__MEMO__", memo)
    return web.Response(text=play_page, content_type="text/html")

# The code below should connect your code to bc_agent correctly without needing student edits

async def asyncstartup(app: web.Application) -> None:
    """Run after the app exists and the asyncio system is functional"""
    import aiohttp
    auth = aiohttp.BasicAuth(login=USER, password=PASS)
    app['client'] = aiohttp.ClientSession(f'http://localhost:{PORT}', auth=auth)
    app['sessions'] = {}

async def asyncshutdown(app):
    """Cleanup and prepare to exit."""
    await app['client'].close()


if __name__ == '__main__': 
    # parse command-line arguments
    import argparse, pathlib, json
    parser = argparse.ArgumentParser()
    parser.add_argument('config', type=pathlib.Path, help="the private config file used by bc_agent.py on the same server")
    args = parser.parse_args()
    
    # load the blockchain contact info
    try:
        with open(args.config) as src:
            pconf = json.load(src)
        PORT = pconf['port']
        USER = None
        for u,p in pconf['passcodes'].items():
            if u.endswith('_b'):
                if USER is None:
                    USER, PASS = u, p
                else:
                    raise LookupError('Config file ambiguous with multiple booths')
    except BaseException as ex:
        print('ERROR: Invalid config file')
        print(ex)
        quit(1)
        
    # create the app
    app = web.Application()
    app.on_startup.append(asyncstartup)
    app.on_shutdown.append(asyncshutdown)
    app.add_routes(routes)
    
    web.run_app(app, host="0.0.0.0", port=20258) # this function never returns

