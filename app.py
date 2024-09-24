from container import Container
from bclib import edge
import asyncio
from methods import *
from decouple import config
import sys
import time
import os

try:
    
    if not os.path.isfile(".env"):
        raise
    HOST = str(config("HOST"))
    PORT = int(config("PORT"))
    DEBUG = bool(str(config("DEBUG")).lower() == "true")

except Exception as ex:
    print("[Error in .env file]", str(ex))
    for i in range(3, 1, -1):
        print(f"App will close in {i} sec")
        time.sleep(1)
    sys.exit(0)

if DEBUG:
    log_error = True
    log_request = True
else:
    log_error = False
    log_request = False

options = {
    "server": f"{HOST}:{PORT}",
    "router": "restful",
    "log_error": log_error,
    "log_request": log_request
}

loop = asyncio.new_event_loop()
app = edge.from_options(options, loop=loop)
container = Container()
container.config.from_json(filepath="./cnf.json")
container.config().update({
    "loop": loop
})
container.wire(
    modules=["methods"]
)

async def initialize_container_async():
    await container.init_resources()

@app.restful_action(
    app.url("import")
)
async def import_handler_async(context: edge.RESTfulContext):
    return await import_async(context)

app.listening()
