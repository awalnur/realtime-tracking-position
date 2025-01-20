import websockets
from fastapi import FastAPI
from fastapi.params import Header
from starlette.websockets import WebSocket

app = FastAPI()

@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, ws_authorization: str = Header(None, convert_underscores=True), room_id: str=None):
    print(ws_authorization)
    print(room_id)
    websockets.basic_auth(websocket, ["user", "password"])
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"{ws_authorization}: Message text was: {data}")
        print(f"Message text was: {data}")




@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}
