"""
WebSocket service for TaskMaster Pro.
Manages WebSocket connections and message broadcasting.
"""

import json
import asyncio
from typing import Dict, List, Optional
from fastapi import WebSocket, WebSocketDisconnect


class ConnectionManager:
    """
    WebSocket connection manager.
    Handles user connections, disconnections, and message routing.
    """
    
    def __init__(self):
        # Map of user_id to WebSocket connection
        self.active_connections: Dict[str, WebSocket] = {}
        # Map of user_id to last ping time
        self.last_ping: Dict[str, float] = {}
        # Heartbeat interval in seconds
        self.heartbeat_interval = 30
    
    async def connect(self, websocket: WebSocket, user_id: str) -> None:
        """
        Accept a WebSocket connection and register it.
        
        Args:
            websocket: WebSocket connection
            user_id: User ID for the connection
        """
        await websocket.accept()
        
        # Close existing connection for this user if any
        if user_id in self.active_connections:
            old_ws = self.active_connections[user_id]
            try:
                await old_ws.close()
            except Exception:
                pass
        
        self.active_connections[user_id] = websocket
        self.last_ping[user_id] = asyncio.get_event_loop().time()
        
        # Send connection confirmation
        await self.send_personal_message({
            "type": "connection",
            "status": "connected",
            "user_id": user_id
        }, user_id)
        
        print(f"WebSocket connected: {user_id}")
    
    def disconnect(self, user_id: str) -> None:
        """
        Disconnect a user and remove their connection.
        
        Args:
            user_id: User ID to disconnect
        """
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        if user_id in self.last_ping:
            del self.last_ping[user_id]
        
        print(f"WebSocket disconnected: {user_id}")
    
    async def send_personal_message(
        self,
        message: dict,
        user_id: str
    ) -> bool:
        """
        Send a message to a specific user.
        
        Args:
            message: Message to send (will be JSON serialized)
            user_id: Target user ID
        
        Returns:
            True if message was sent, False otherwise
        """
        if user_id not in self.active_connections:
            return False
        
        websocket = self.active_connections[user_id]
        
        try:
            await websocket.send_json(message)
            return True
        except Exception as e:
            print(f"Error sending message to {user_id}: {e}")
            self.disconnect(user_id)
            return False
    
    async def broadcast(self, message: dict) -> None:
        """
        Broadcast a message to all connected users.
        
        Args:
            message: Message to broadcast
        """
        disconnected = []
        
        for user_id, websocket in self.active_connections.items():
            try:
                await websocket.send_json(message)
            except Exception as e:
                print(f"Error broadcasting to {user_id}: {e}")
                disconnected.append(user_id)
        
        # Clean up disconnected users
        for user_id in disconnected:
            self.disconnect(user_id)
    
    async def send_to_multiple(
        self,
        message: dict,
        user_ids: List[str]
    ) -> None:
        """
        Send a message to multiple users.
        
        Args:
            message: Message to send
            user_ids: List of target user IDs
        """
        for user_id in user_ids:
            await self.send_personal_message(message, user_id)
    
    async def handle_ping(self, user_id: str) -> None:
        """
        Handle ping from client.
        
        Args:
            user_id: User ID that sent ping
        """
        self.last_ping[user_id] = asyncio.get_event_loop().time()
        
        # Send pong response
        await self.send_personal_message({
            "type": "pong",
            "timestamp": asyncio.get_event_loop().time()
        }, user_id)
    
    async def heartbeat_checker(self) -> None:
        """
        Background task to check for stale connections.
        Disconnects users that haven't sent a ping in a while.
        """
        while True:
            await asyncio.sleep(self.heartbeat_interval)
            
            current_time = asyncio.get_event_loop().time()
            stale_threshold = self.heartbeat_interval * 3  # 90 seconds
            
            stale_users = [
                user_id for user_id, last_ping in self.last_ping.items()
                if current_time - last_ping > stale_threshold
            ]
            
            for user_id in stale_users:
                print(f"Disconnecting stale connection: {user_id}")
                if user_id in self.active_connections:
                    try:
                        await self.active_connections[user_id].close()
                    except Exception:
                        pass
                self.disconnect(user_id)
    
    def is_connected(self, user_id: str) -> bool:
        """
        Check if a user is currently connected.
        
        Args:
            user_id: User ID to check
        
        Returns:
            True if user is connected, False otherwise
        """
        return user_id in self.active_connections
    
    def get_connected_users(self) -> List[str]:
        """
        Get list of all connected user IDs.
        
        Returns:
            List of connected user IDs
        """
        return list(self.active_connections.keys())
    
    async def send_notification_count(
        self,
        user_id: str,
        count: int
    ) -> bool:
        """
        Send notification count update to a user.
        
        Args:
            user_id: User ID
            count: Number of unread notifications
        
        Returns:
            True if sent successfully
        """
        return await self.send_personal_message({
            "type": "notification_count",
            "count": count
        }, user_id)


# Global connection manager instance
websocket_manager = ConnectionManager()
