"""Test matchmaking flow: creates two users, matches them, verifies interaction."""
import asyncio
import json
import httpx
import websockets
import sys

API = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws"

async def main():
    # 1. Register two test users
    async with httpx.AsyncClient() as client:
        for u in ["test_player_a", "test_player_b"]:
            r = await client.post(f"{API}/auth/register", json={
                "username": u, "password": "test123", "nickname": u
            })
            print(f"Register {u}: {r.status_code}", r.json() if r.status_code != 200 else "OK")

        # 2. Login both
        ra = await client.post(f"{API}/auth/login", json={"username": "test_player_a", "password": "test123"})
        rb = await client.post(f"{API}/auth/login", json={"username": "test_player_b", "password": "test123"})
        token_a = ra.json()["access_token"]
        token_b = rb.json()["access_token"]
        print(f"Login A: {ra.status_code}, B: {rb.status_code}")

    # 3. Connect two WebSockets
    async def connect_ws(token, name):
        ws = await websockets.connect(WS_URL)
        # Send auth
        await ws.send(json.dumps({"type": "auth", "token": token}))
        resp = await ws.recv()
        msg = json.loads(resp)
        print(f"{name} auth response: {msg['type']}")
        assert msg["type"] == "auth_ok", f"Auth failed for {name}: {msg}"
        return ws

    ws_a = await connect_ws(token_a, "A")
    ws_b = await connect_ws(token_b, "B")

    async def recv_until(ws, expected_type, timeout=10):
        """Keep receiving until we get expected_type, return that message."""
        deadline = asyncio.get_event_loop().time() + timeout
        while asyncio.get_event_loop().time() < deadline:
            resp = await asyncio.wait_for(ws.recv(), timeout=5)
            msg = json.loads(resp)
            print(f"  [{expected_type}] got: {msg['type']}")
            if msg["type"] == expected_type:
                return msg
            if msg["type"] == "error":
                print(f"  ERROR: {msg['message']}")
        raise TimeoutError(f"Did not receive {expected_type} within {timeout}s")

    # 4. Both send start_match
    print("\n--- Sending start_match from A ---")
    await ws_a.send(json.dumps({"type": "start_match"}))
    # A might get match_queued first, or match_found depending on timing

    await asyncio.sleep(1)

    print("\n--- Sending start_match from B ---")
    await ws_b.send(json.dumps({"type": "start_match"}))

    # 5. Collect match_found and game_state from both
    print("\n--- Awaiting responses ---")
    tasks = []
    for label, ws in [("A", ws_a), ("B", ws_b)]:
        tasks.append(recv_until(ws, "match_found"))
        tasks.append(recv_until(ws, "game_state"))

    results = await asyncio.gather(*tasks, return_exceptions=True)
    for i, r in enumerate(results):
        if isinstance(r, Exception):
            print(f"  Task {i} exception: {r}")
        else:
            print(f"  Task {i}: {r['type']} - your_turn={r.get('your_turn', 'N/A')}, color={r.get('your_color', 'N/A')}")

    # 6. Black player sends place_stone
    print("\n--- Testing place_stone ---")
    # Find which player is black
    black_ws = None
    for label, ws in [("A", ws_a), ("B", ws_b)]:
        # Try to get game_state for each
        pass

    # Based on the results, determine black player
    # match_found tells us your_color
    match_a = results[0] if not isinstance(results[0], Exception) else None
    match_b = results[2] if not isinstance(results[2], Exception) else None
    
    if match_a and match_a.get("your_color") == "black":
        black_ws = ws_a
        print("Player A is black")
    elif match_b and match_b.get("your_color") == "black":
        black_ws = ws_b
        print("Player B is black")
    else:
        print("Could not determine black player from match_found")
        # Check game_state
        gs_a = results[1] if not isinstance(results[1], Exception) else None
        if gs_a and gs_a.get("your_turn") is True:
            black_ws = ws_a
            print("Player A is black (from game_state)" )
        
    if black_ws:
        # Black places a stone
        print("Black placing stone at (7,7)...")
        await black_ws.send(json.dumps({"type": "place_stone", "row": 7, "col": 7}))
        resp = await asyncio.wait_for(black_ws.recv(), timeout=5)
        rmsg = json.loads(resp)
        print(f"  Response: {rmsg}")
        
        if rmsg["type"] == "stone_placed":
            print("  Stone placed successfully!")
        elif rmsg["type"] == "error":
            print(f"  FAILED: {rmsg['message']}")

    # 7. Test chat
    print("\n--- Testing chat ---")
    await ws_a.send(json.dumps({"type": "chat", "message": "你好", "room_id": "test"}))
    resp = await asyncio.wait_for(ws_a.recv(), timeout=5)
    rmsg = json.loads(resp)
    print(f"  Chat response: {rmsg}")
    if rmsg["type"] == "error" and "不在房间" in rmsg.get("message", ""):
        print("  FAILED: chat rejected - not in room")
    elif rmsg["type"] == "chat":
        print("  Chat works!")
    else:
        print(f"  Unexpected response: {rmsg}")

    # Cleanup
    await ws_a.close()
    await ws_b.close()
    print("\n--- Done ---")

if __name__ == "__main__":
    asyncio.run(main())
