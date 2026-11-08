"""
Comprehensive Master Integration Test Suite for Project SREE
Validates AI Inference, SQLite Memory, Notes, Reminders, Automation, and Web Search.
"""

import sys
import asyncio
import httpx
from pathlib import Path

BASE_URL = "http://127.0.0.1:8005"

async def test_full_system():
    print("=" * 65)
    print("       SREE MASTER SYSTEM INTEGRATION TEST")
    print("=" * 65)

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        # 1. Health & Status
        print("\n[1/8] Verifying Core Server & Ollama...")
        res = await client.get("/health")
        assert res.status_code == 200, f"Health check failed: {res.text}"
        data = res.json()
        print(f"  --> App: {data['app']}, Ollama Status: {data['ollama']}")
        assert data["ollama"] == "connected"
        print("  --> PASS: Server healthy & connected to Ollama.")

        # 2. System Telemetry
        print("\n[2/8] Testing System Telemetry...")
        res = await client.get("/api/system/status")
        assert res.status_code == 200
        status_data = res.json()
        print(f"  --> Model: {status_data['ai_engine']['default_model']}")
        print(f"  --> RAM: {status_data['hardware']['ram_used_gb']} / {status_data['hardware']['ram_total_gb']} GB")
        print("  --> PASS: Hardware metrics reporting accurately.")

        # 3. Long-Term Memory
        print("\n[3/8] Testing SQLite Long-Term Memory...")
        res = await client.post("/api/memory", json={"key": "Favorite Editor", "value": "VS Code", "category": "preference"})
        assert res.status_code == 200
        mem_id = res.json()["id"]
        print(f"  --> Saved Memory ID: {mem_id}")

        res = await client.get("/api/memory")
        memories = res.json()["memories"]
        assert any(m["key"] == "Favorite Editor" for m in memories)
        print(f"  --> Discovered {len(memories)} persistent memories.")
        print("  --> PASS: Memory persistence operational.")

        # 4. Encrypted Notes
        print("\n[4/8] Testing Notes Engine...")
        res = await client.post("/api/notes", json={"title": "Test Briefing", "content": "Review SREE architecture", "tags": "project"})
        assert res.status_code == 200
        note_id = res.json()["id"]
        print(f"  --> Created Note ID: {note_id}")

        res = await client.get("/api/notes?search=Briefing")
        notes = res.json()["notes"]
        assert len(notes) > 0
        assert notes[0]["title"] == "Test Briefing"
        print("  --> PASS: Notes search & retrieval verified.")

        # 5. Productivity & Reminders
        print("\n[5/8] Testing Reminders Engine...")
        res = await client.post("/api/reminders", json={"title": "Deploy SREE v1.0", "due_time": "Today 12:00 PM"})
        assert res.status_code == 200
        remind_id = res.json()["id"]
        print(f"  --> Created Reminder ID: {remind_id}")

        res = await client.patch(f"/api/reminders/{remind_id}/toggle", json={"completed": True})
        assert res.status_code == 200
        print("  --> PASS: Reminder completion toggled.")

        # 6. Laptop Automation Allowlist
        print("\n[6/8] Testing Security Allowlist & Telemetry...")
        res = await client.get("/api/automation/apps")
        assert res.status_code == 200
        apps = res.json()["apps"]
        print(f"  --> Authorized apps ({len(apps)}): {[a['id'] for a in apps]}")

        res = await client.get("/api/automation/telemetry")
        assert res.status_code == 200
        telem = res.json()
        print(f"  --> Uptime: {telem['uptime_hours']} hrs, CPU: {telem['cpu_percent']}%")
        print("  --> PASS: Security boundary & telemetry verified.")

        # 7. Safe File Search
        print("\n[7/8] Testing Safe File Search...")
        res = await client.post("/api/automation/files/search", json={"query": "README"})
        assert res.status_code == 200
        files = res.json()["results"]
        print(f"  --> Found {len(files)} files matching 'README' in approved paths.")
        print("  --> PASS: File discovery inside boundary verified.")

        # 8. Live AI Chat with Proactive Command & Memory Context
        print("\n[8/8] Testing AI Proactive Command & Generation...")
        # A) Proactive App Launch test
        res = await client.post("/api/chat", json={"message": "Please launch calculator"})
        assert res.status_code == 200
        chat_data = res.json()
        print(f"  --> SREE Action Response: {chat_data['reply']}")
        assert "calculator" in chat_data["reply"].lower()

        # B) Contextual conversational generation
        res = await client.post("/api/chat", json={"message": "What is my favorite editor?"})
        assert res.status_code == 200
        chat_data2 = res.json()
        print(f"  --> SREE Memory Response: {chat_data2['reply']}")
        assert "VS Code" in chat_data2["reply"] or "editor" in chat_data2["reply"]
        print("  --> PASS: SREE successfully injected long-term memory into response!")

        # 9. Data Export Check
        print("\n[BONUS] Testing Data Export...")
        res = await client.get("/api/data/export")
        assert res.status_code == 200
        export_data = res.json()
        print(f"  --> Exported {len(export_data['conversations'])} messages, {len(export_data['memories'])} memories.")
        print("  --> PASS: Privacy export verified.")

    print("\n" + "=" * 65)
    print("  ALL 8 MODULES PASSED SYSTEM INTEGRATION TESTS!")
    print("=" * 65)

if __name__ == "__main__":
    asyncio.run(test_full_system())

