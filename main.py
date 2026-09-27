import asyncio
import json
import requests
import websockets

with open("config.json") as f:
    cfg = json.load(f)

TOKEN = cfg["token"]
STATUS = cfg["status"]
ACT = cfg["activity"]

TYPE_IDS = {
    "playing": 0,
    "streaming": 1,
    "listening": 2,
    "watching": 3,
    "custom": 4,
    "competing": 5,
}


def build_activity():
    kind = ACT["type"].lower()

    if kind == "custom":
        a = {"name": "Custom Status", "type": 4,
             "state": ACT["custom_status"], "id": "custom"}
        if ACT["use_emoji"]:
            a["emoji"] = {"name": ACT["emoji"], "id": None, "animated": False}
        return a

    a = {"name": ACT["name"], "type": TYPE_IDS.get(kind, 0)}
    if ACT.get("details"):
        a["details"] = ACT["details"]
    if ACT.get("state"):
        a["state"] = ACT["state"]
    if kind == "streaming":
        a["url"] = ACT["stream_url"]
    return a


def check_token():
    r = requests.get("https://discord.com/api/v10/users/@me",
                     headers={"Authorization": TOKEN})
    if r.status_code != 200:
        print("Invalid token!")
        exit()
    u = r.json()
    print(f"Logged in as {u['username']} ({u['id']})!")


async def gateway():
    uri = "wss://gateway.discord.gg/?v=10&encoding=json"
    activity = build_activity()

    async with websockets.connect(uri) as ws:
        hello = json.loads(await ws.recv())
        interval = hello["d"]["heartbeat_interval"] / 1000

        async def heartbeat():
            while True:
                await asyncio.sleep(interval)
                await ws.send(json.dumps({"op": 1, "d": None}))

        asyncio.create_task(heartbeat())

        await ws.send(json.dumps({
            "op": 2,
            "d": {
                "token": TOKEN,
                "properties": {"$os": "windows", "$browser": "chrome", "$device": "pc"},
                "presence": {"status": STATUS, "afk": False, "activities": [activity]},
            },
        }))

        while True:
            await ws.recv()


check_token()

while True:
    try:
        asyncio.run(gateway())
    except Exception as e:
        print("Reconnecting...", e)
        asyncio.sleep(5)
