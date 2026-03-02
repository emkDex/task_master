"""
WebSocket API routes for TaskMaster Pro.
"""

import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.core.security import decode_access_token
from app.services.websocket_service import websocket_manager

router = APIRouter()


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: str,
    token: str = Query(..., description="JWT access token"),
    db: AsyncSession = Depends(get_db)
):
    """
    WebSocket endpoint for real-time notifications.
    
    - **user_id**: User ID (must match token)
    - **token**: JWT access token (query parameter)
    
    The connection requires a valid JWT token and the user_id in the path
    must match the user ID in the token.
    
    Messages:
    - Client -> Server: `{"type": "ping"}` for heartbeat
    - Server -> Client: `{"type": "notification", "data": {...}}` for notifications
    - Server -> Client: `{"type": "pong"}` heartbeat response
    """
    try:
        # Validate token
        payload = decode_access_token(token)
        token_user_id = payload.get("sub")
        
        if not token_user_id or token_user_id != user_id:
            await websocket.close(code=4001, reason="Invalid token or user ID mismatch")
            return
        
        # Connect
        await websocket_manager.connect(websocket, user_id)
        
        try:
            while True:
                # Wait for messages from client
                data = await websocket.receive_json()
                
                # Handle ping messages
                if data.get("type") == "ping":
                    await websocket_manager.handle_ping(user_id)
                
        except WebSocketDisconnect:
            websocket_manager.disconnect(user_id)
    
    except Exception as e:
        # Close connection on error
        try:
            await websocket.close(code=4001, reason="Authentication failed")
        except Exception:
            pass
