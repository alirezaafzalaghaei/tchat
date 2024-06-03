from sanic import Sanic
import aiohttp
import asyncio
import os
import json
from sanic_redis import SanicRedis


app = Sanic("Notification-Server")


# Redis configuration
redis_host = os.getenv("REDIS_HOST", "redis")
redis_port = int(os.getenv("REDIS_PORT", 6379))
app.config["REDIS"] = f"redis://{redis_host}:{redis_port}"

redis = SanicRedis()
redis.init_app(app)


@app.websocket("/notifications")
async def feed(request, ws):
    try:
        data = await ws.recv()
        data = json.loads(data)

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://messenger-app:13247/api/user/is_session_valid", json=data
            ) as response:
                if response.status != 200:
                    return

                result = await response.json()
                if not result.get("success", False):
                    return

        async with redis.conn as redis_client:
            pubsub = redis_client.pubsub()
            await pubsub.subscribe("public_room", f'user-{data["user_id"]}')
            async for message in pubsub.listen():
                if message["type"] == "message":
                    msg = message["data"].decode("utf-8")
                    where = (
                        "public" if message["channel"] == b"public_room" else "private"
                    )
                    await ws.send(json.dumps({"where": where, "content": msg}))
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await ws.close()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=13246)
