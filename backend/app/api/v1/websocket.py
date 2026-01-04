from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
from typing import List

router = APIRouter(prefix="/ws", tags=["websocket"])

# Store active WebSocket connections
active_connections: List[WebSocket] = []


@router.websocket("/ws/rides/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """
    WebSocket endpoint for real-time ride updates.
    Users (drivers/passengers) connect here to receive live notifications.
    """
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Broadcast to all connected clients
            # In production, filter by user role/location
            for connection in active_connections:
                try:
                    await connection.send_json({
                        "from": user_id,
                        "message": message,
                    })
                except:
                    pass
    except WebSocketDisconnect:
        active_connections.remove(websocket)
        print(f"User {user_id} disconnected")


async def broadcast_ride_available(ride_data: dict, driver_ids: List[str]):
    """
    Broadcast a new ride request to specific drivers.
    """
    notification = {
        "type": "new_ride",
        "data": ride_data,
    }
    
    for connection in active_connections:
        try:
            await connection.send_json(notification)
        except:
            pass
