import json

from fastapi import FastAPI
from fastapi.params import Header
from starlette.websockets import WebSocket, WebSocketDisconnect

app = FastAPI()


class ConnectionManager:
    def __init__(self):
        self.room_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, room: str, websocket: WebSocket):
        await websocket.accept()
        if room not in self.room_connections:
            self.room_connections[room] = []
        self.room_connections[room].append(websocket)

    def disconnect(self, room: str, websocket: WebSocket, reason: str = None):
        if room in self.room_connections and websocket in self.room_connections[room]:
            self.room_connections[room].remove(websocket)
            if not self.room_connections[room]:
                del self.room_connections[room]
            if reason:
                print(f"WebSocket disconnected for room {room} due to: {reason}")
                websocket.close(code=1007)


    async def send_personal_message(self, message: str, websocket: WebSocket):
        print(self.room_connections)
        try:
            await websocket.send_text(message)
        except RuntimeError:
            # Handle scenario where message cannot be sent due to WebSocket closure
            print("Attempted to send to a closed WebSocket.")


    async def broadcast(self, room: str, message: str):
        print(self.room_connections)

        if room in self.room_connections:
            for connection in self.room_connections[room]:
                try:
                    await connection.send_text(message)
                except RuntimeError:
                    # Handle scenario where message cannot be sent due to WebSocket closure
                    print("Attempted to send to a closed WebSocket.")
                    self.disconnect(room, connection)


manager = ConnectionManager()


@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, Sec_WebSocket_Protocol: str = Header(None, convert_underscores=True),  room_id: str=None):
    print(Sec_WebSocket_Protocol)
    # if Sec_WebSocket_Protocol !="yourAccessTokenOrSimilar":
    #     await manager.send_personal_message("Please provide a valid ws_authorization", websocket)
    #     print(f"Unauthorized connection attempt to room {room_id} using ws_authorization: {ws_authorization}")
    #     await websocket.close(code=403)  # Close WebSocket connection with 403 status
    #
    #     return
    # You can validate or handle the subprotocol here:
    # if Sec_WebSocket_Protocol and Sec_WebSocket_Protocol != "yourExpectedProtocol":
    #     await websocket.close(code=4000)  # Close with an appropriate error code
    #     print(f"Invalid subprotocol {Sec_WebSocket_Protocol}. Connection closed.")
    #     return
    # await websocket.accept(subprotocol=Sec_WebSocket_Protocol)  # Accept with subprotocol if needed

    await manager.connect(room_id, websocket)
    try:
        while True:
            if room_id is None:
                await manager.send_personal_message("Please provide a room_id", websocket)
                break

            # if ws_authorization is None:
            #
            #     await manager.send_personal_message("Please provide a ws_authorization", websocket)
            #     # print(f"Unauthorized connection attempt to room {room_id} using ws_authorization: {ws_authorization}")
            #     continue

            try:
                data = await websocket.receive_json()
                await manager.broadcast(room_id, json.dumps(data))

            except WebSocketDisconnect:  # Gracefully handle disconnections
                print(f"WebSocket disconnected for room {room_id}")
                await manager.broadcast(room_id, f"Client #{room_id} left the chat")

                break
            except Exception as e:
                print(e)
                try:
                    data = await websocket.receive_text()

                    broadcast_message = {
                        "status": "success",
                        "action": "broadcast_message",
                        "content": data,
                        "room_id": room_id,
                    }
                    await manager.broadcast(room_id, f"'{broadcast_message}")
                    await manager.send_personal_message("Please send Valid Data", websocket)
                except RuntimeError:
                    print("WebSocket already disconnected. Aborting.")
                    break


            # try:
            #     # Validate GeoJSON format
            #     import json
            #     geospatial_data = json.loads(data)
            #     if "type" not in geospatial_data or "coordinates" not in geospatial_data:
            #         raise ValueError("Invalid GeoJSON format")
            #
            #     # Log valid GeoJSON details
            #     print(f"Received GeoJSON: {geospatial_data}")
            #
            #     await manager.send_personal_message(f"Valid GeoJSON received: {geospatial_data}", websocket)
            #     await manager.broadcast(room_id, f"Client #{room_id} sent: {geospatial_data}")
            # except (json.JSONDecodeError, ValueError) as e:
            #     # Handle invalid GeoJSON format and send an error message
            #     error_message = f"Error: Invalid GeoJSON data - {e}"
            #     print(error_message)
            #     await manager.send_personal_message(error_message, websocket)
    except WebSocketDisconnect:
        manager.disconnect(room_id, websocket)
        await manager.broadcast(room_id, f"Client #{room_id} left the chat")



@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}
