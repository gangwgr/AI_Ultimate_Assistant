from fastapi import APIRouter, HTTPException
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import logging
import os
import json
from typing import List, Optional
from pydantic import BaseModel

from app.core.config import settings

logger = logging.getLogger(__name__)

slack_router = APIRouter()

class SlackMessage(BaseModel):
    channel: str
    text: str
    thread_ts: Optional[str] = None

class SlackMessageResponse(BaseModel):
    ts: str
    user: str
    text: str
    channel: str
    thread_ts: Optional[str]
    reply_count: int
    is_bot: bool

class SlackChannel(BaseModel):
    id: str
    name: str
    is_channel: bool
    is_group: bool
    is_im: bool
    members: int

def get_slack_client():
    """Get Slack client with stored token"""
    try:
        slack_creds_file = os.path.join(settings.credentials_dir, "slack_credentials.json")
        if os.path.exists(slack_creds_file):
            with open(slack_creds_file, 'r') as f:
                creds = json.load(f)
            return WebClient(token=creds.get('access_token'))
        elif settings.slack_bot_token:
            return WebClient(token=settings.slack_bot_token)
        else:
            return None
    except Exception as e:
        logger.error(f"Error getting Slack client: {e}")
        return None

@slack_router.get("/channels", response_model=List[SlackChannel])
async def get_channels():
    """Get Slack channels"""
    try:
        client = get_slack_client()
        if not client:
            raise HTTPException(status_code=401, detail="Not authenticated with Slack")
        
        channels_list = []
        
        # Get public channels
        try:
            response = client.conversations_list(types="public_channel,private_channel")
            for channel in response["channels"]:
                channels_list.append(SlackChannel(
                    id=channel["id"],
                    name=channel["name"],
                    is_channel=True,
                    is_group=False,
                    is_im=False,
                    members=channel.get("num_members", 0)
                ))
        except SlackApiError as e:
            logger.error(f"Error fetching channels: {e}")
        
        # Get direct messages
        try:
            response = client.conversations_list(types="im")
            for dm in response["channels"]:
                user_info = client.users_info(user=dm["user"])
                channels_list.append(SlackChannel(
                    id=dm["id"],
                    name=f"DM with {user_info['user']['name']}",
                    is_channel=False,
                    is_group=False,
                    is_im=True,
                    members=2
                ))
        except SlackApiError as e:
            logger.error(f"Error fetching DMs: {e}")
        
        return channels_list
    
    except SlackApiError as e:
        logger.error(f"Slack API error: {e}")
        raise HTTPException(status_code=500, detail=f"Slack API error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@slack_router.get("/channels/{channel_id}/messages", response_model=List[SlackMessageResponse])
async def get_channel_messages(channel_id: str, limit: int = 50):
    """Get messages from a Slack channel"""
    try:
        client = get_slack_client()
        if not client:
            raise HTTPException(status_code=401, detail="Not authenticated with Slack")
        
        response = client.conversations_history(
            channel=channel_id,
            limit=limit
        )
        
        messages = []
        for message in response["messages"]:
            # Skip system messages and bot messages if needed
            if message.get("subtype") in ["channel_join", "channel_leave"]:
                continue
            
            user_name = "Unknown"
            if "user" in message:
                try:
                    user_info = client.users_info(user=message["user"])
                    user_name = user_info["user"]["name"]
                except:
                    user_name = message["user"]
            
            messages.append(SlackMessageResponse(
                ts=message["ts"],
                user=user_name,
                text=message.get("text", ""),
                channel=channel_id,
                thread_ts=message.get("thread_ts"),
                reply_count=message.get("reply_count", 0),
                is_bot=message.get("bot_id") is not None
            ))
        
        return messages
    
    except SlackApiError as e:
        logger.error(f"Slack API error: {e}")
        raise HTTPException(status_code=500, detail=f"Slack API error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@slack_router.post("/messages/send")
async def send_message(message_data: SlackMessage):
    """Send a message to Slack"""
    try:
        client = get_slack_client()
        if not client:
            raise HTTPException(status_code=401, detail="Not authenticated with Slack")
        
        kwargs = {
            "channel": message_data.channel,
            "text": message_data.text
        }
        
        if message_data.thread_ts:
            kwargs["thread_ts"] = message_data.thread_ts
        
        response = client.chat_postMessage(**kwargs)
        
        return {
            "message": "Message sent successfully",
            "ts": response["ts"],
            "channel": response["channel"]
        }
    
    except SlackApiError as e:
        logger.error(f"Slack API error: {e}")
        raise HTTPException(status_code=500, detail=f"Slack API error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@slack_router.get("/users")
async def get_users():
    """Get Slack users"""
    try:
        client = get_slack_client()
        if not client:
            raise HTTPException(status_code=401, detail="Not authenticated with Slack")
        
        response = client.users_list()
        users = []
        
        for user in response["members"]:
            if not user.get("deleted", False) and not user.get("is_bot", False):
                users.append({
                    "id": user["id"],
                    "name": user["name"],
                    "real_name": user.get("real_name", ""),
                    "email": user.get("profile", {}).get("email", ""),
                    "status": user.get("presence", "unknown")
                })
        
        return users
    
    except SlackApiError as e:
        logger.error(f"Slack API error: {e}")
        raise HTTPException(status_code=500, detail=f"Slack API error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@slack_router.get("/messages/search")
async def search_messages(query: str, count: int = 20):
    """Search messages in Slack"""
    try:
        client = get_slack_client()
        if not client:
            raise HTTPException(status_code=401, detail="Not authenticated with Slack")
        
        response = client.search_messages(
            query=query,
            count=count
        )
        
        messages = []
        if "messages" in response and "matches" in response["messages"]:
            for match in response["messages"]["matches"]:
                messages.append({
                    "text": match.get("text", ""),
                    "user": match.get("user", ""),
                    "ts": match.get("ts", ""),
                    "channel": match.get("channel", {}).get("name", ""),
                    "permalink": match.get("permalink", "")
                })
        
        return {
            "total": response.get("messages", {}).get("total", 0),
            "matches": messages
        }
    
    except SlackApiError as e:
        logger.error(f"Slack API error: {e}")
        raise HTTPException(status_code=500, detail=f"Slack API error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@slack_router.get("/status")
async def slack_status():
    """Check Slack connection status"""
    try:
        client = get_slack_client()
        if not client:
            return {"connected": False, "error": "No authentication"}
        
        response = client.auth_test()
        
        return {
            "connected": True,
            "team": response.get("team", ""),
            "user": response.get("user", ""),
            "team_id": response.get("team_id", ""),
            "user_id": response.get("user_id", "")
        }
    
    except SlackApiError as e:
        return {"connected": False, "error": str(e)}
    except Exception as e:
        return {"connected": False, "error": str(e)}

@slack_router.put("/messages/{ts}/update")
async def update_message(ts: str, channel: str, new_text: str):
    """Update a Slack message"""
    try:
        client = get_slack_client()
        if not client:
            raise HTTPException(status_code=401, detail="Not authenticated with Slack")
        
        response = client.chat_update(
            channel=channel,
            ts=ts,
            text=new_text
        )
        
        return {
            "message": "Message updated successfully",
            "ts": response["ts"]
        }
    
    except SlackApiError as e:
        logger.error(f"Slack API error: {e}")
        raise HTTPException(status_code=500, detail=f"Slack API error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@slack_router.delete("/messages/{ts}")
async def delete_message(ts: str, channel: str):
    """Delete a Slack message"""
    try:
        client = get_slack_client()
        if not client:
            raise HTTPException(status_code=401, detail="Not authenticated with Slack")
        
        client.chat_delete(
            channel=channel,
            ts=ts
        )
        
        return {"message": "Message deleted successfully"}
    
    except SlackApiError as e:
        logger.error(f"Slack API error: {e}")
        raise HTTPException(status_code=500, detail=f"Slack API error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 