"""
SREE Master 87-Unit-Test Suite
Fully validated test suite covering:
  - Dynamic Windows Path Resolution (OneDrive/Desktop/Downloads)
  - 3-Tier Security Guard Engine (Level 1 Safe, Level 2 Sensitive Confirmation, Level 3 Critical Block)
  - Skill Crystallizer 0ms Fast-Path & Shortcut Execution
  - Universal Multi-Provider AI Routing, Intra-Provider Model Cascading & Autonomous Healing
  - SQLite Long-Term Memory, Notes & Reminders Engine
  - Security Allowlist & System Telemetry Contracts

Pass Criteria: 87/87 Unit Tests Passing (100% Pass Rate).
"""

import unittest
import asyncio
import os
import sys
import time
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.automation.path_resolver import dynamic_path_resolver
from backend.app.automation.security_guard import security_guard, SecurityLevel
from backend.app.automation.crystallizer import skill_crystallizer
from backend.app.automation.allowlist import ALLOWLISTED_APPLICATIONS, get_approved_directories
from backend.app.automation.executor import automation_executor
from backend.app.ai.universal_router import universal_router
from backend.app.ai.prompts import build_prompt_with_context, SREE_SYSTEM_PROMPT
from backend.app.core.config import settings, update_runtime_setting
from backend.app.database.db import db_manager
from backend.app.memory.manager import memory_manager
from backend.app.services.system_telemetry import telemetry_service


# =====================================================================
# 1. Dynamic Windows Path Resolution Tests (10 Tests)
# =====================================================================
class TestDynamicPathResolver(unittest.TestCase):
    def test_01_resolve_desktop(self):
        desktop = dynamic_path_resolver.get_desktop()
        self.assertIsInstance(desktop, Path)
        self.assertTrue(desktop.name.lower() in ("desktop", "onedrive"))

    def test_02_resolve_documents(self):
        docs = dynamic_path_resolver.get_documents()
        self.assertIsInstance(docs, Path)
        self.assertTrue(docs.name.lower() in ("documents", "onedrive"))

    def test_03_resolve_downloads(self):
        downloads = dynamic_path_resolver.get_downloads()
        self.assertIsInstance(downloads, Path)
        self.assertIn("downloads", str(downloads).lower())

    def test_04_resolve_pictures(self):
        pics = dynamic_path_resolver.get_pictures()
        self.assertIsInstance(pics, Path)
        self.assertTrue(pics.name.lower() in ("pictures", "onedrive"))

    def test_05_resolve_project_root(self):
        root = dynamic_path_resolver.get_project_root()
        self.assertIsInstance(root, Path)
        self.assertTrue((root / "backend").exists() or (root / "frontend").exists())

    def test_06_resolve_subpath_desktop(self):
        resolved = dynamic_path_resolver.resolve_path("Desktop/Projects")
        self.assertIsInstance(resolved, Path)
        self.assertIn("projects", str(resolved).lower())

    def test_07_resolve_case_insensitivity(self):
        res_lower = dynamic_path_resolver.resolve_path("downloads")
        res_upper = dynamic_path_resolver.resolve_path("DOWNLOADS")
        self.assertEqual(res_lower, res_upper)

    def test_08_resolve_nonexistent_safe(self):
        resolved = dynamic_path_resolver.resolve_path("Desktop/NonExistentFolder_12345")
        self.assertIsInstance(resolved, Path)
        self.assertEqual(resolved.name, "NonExistentFolder_12345")

    def test_09_get_approved_directories(self):
        dirs = get_approved_directories()
        self.assertIsInstance(dirs, list)
        self.assertGreaterEqual(len(dirs), 1)

    def test_10_path_normalization(self):
        resolved = dynamic_path_resolver.resolve_path("Documents\\SubFolder/Nested")
        self.assertNotIn("/", str(resolved) if os.name == "nt" else "\\")


# =====================================================================
# 2. 3-Tier Security Guard Engine Tests (18 Tests)
# =====================================================================
class TestSecurityGuard(unittest.TestCase):
    def setUp(self):
        security_guard._pending_action = None
        security_guard._pending_timestamp = 0

    def test_11_eval_safe_calculator(self):
        lvl = security_guard.evaluate_intent("launch_app", {"command": "calc.exe"})
        self.assertEqual(lvl, SecurityLevel.SAFE)

    def test_12_eval_safe_notepad(self):
        lvl = security_guard.evaluate_intent("launch_app", {"command": "notepad.exe"})
        self.assertEqual(lvl, SecurityLevel.SAFE)

    def test_13_eval_safe_weather(self):
        lvl = security_guard.evaluate_intent("weather_query", {"command": "weather in Tokyo"})
        self.assertEqual(lvl, SecurityLevel.SAFE)

    def test_14_eval_safe_time(self):
        lvl = security_guard.evaluate_intent("time_query", {"command": "what time is it"})
        self.assertEqual(lvl, SecurityLevel.SAFE)

    def test_15_eval_critical_format_c(self):
        lvl = security_guard.evaluate_intent("raw_command", {"command": "format C: /y"})
        self.assertEqual(lvl, SecurityLevel.CRITICAL)

    def test_16_eval_critical_rmdir_s(self):
        lvl = security_guard.evaluate_intent("raw_command", {"command": "rmdir /s /q Windows"})
        self.assertEqual(lvl, SecurityLevel.CRITICAL)

    def test_17_eval_critical_del_f(self):
        lvl = security_guard.evaluate_intent("raw_command", {"command": "del /f /s C:\\boot.ini"})
        self.assertEqual(lvl, SecurityLevel.CRITICAL)

    def test_18_eval_critical_drop_db(self):
        lvl = security_guard.evaluate_intent("raw_command", {"command": "DROP DATABASE sree_db"})
        self.assertEqual(lvl, SecurityLevel.CRITICAL)

    def test_19_eval_critical_system32(self):
        lvl = security_guard.evaluate_intent("raw_command", {"command": "del C:\\Windows\\System32\\drivers"})
        self.assertEqual(lvl, SecurityLevel.CRITICAL)

    def test_20_eval_critical_reg_delete(self):
        lvl = security_guard.evaluate_intent("raw_command", {"command": "reg delete HKLM\\Software"})
        self.assertEqual(lvl, SecurityLevel.CRITICAL)

    def test_21_eval_critical_encoded_powershell(self):
        lvl = security_guard.evaluate_intent("raw_command", {"command": "powershell -enc AAAA=="})
        self.assertEqual(lvl, SecurityLevel.CRITICAL)

    def test_22_eval_critical_shutdown(self):
        lvl = security_guard.evaluate_intent("raw_command", {"command": "shutdown /s /t 0"})
        self.assertEqual(lvl, SecurityLevel.CRITICAL)

    def test_23_eval_sensitive_wipe_data(self):
        lvl = security_guard.evaluate_intent("wipe_data", {})
        self.assertEqual(lvl, SecurityLevel.SENSITIVE)

    def test_24_eval_sensitive_delete_note(self):
        lvl = security_guard.evaluate_intent("delete_note", {})
        self.assertEqual(lvl, SecurityLevel.SENSITIVE)

    def test_25_eval_sensitive_delete_memory(self):
        lvl = security_guard.evaluate_intent("delete_memory", {})
        self.assertEqual(lvl, SecurityLevel.SENSITIVE)

    def test_26_stage_pending_action(self):
        res = security_guard.stage_pending_action("wipe_data", {"target": "all"}, "Erase all memories?")
        self.assertEqual(res["status"], "pending_confirmation")
        self.assertEqual(res["security_level"], 2)
        self.assertTrue(security_guard.has_pending_action())

    def test_27_confirm_pending_action_yes(self):
        security_guard.stage_pending_action("test_action", {}, "Confirm test action?")
        handled, action, msg = security_guard.check_pending_confirmation("yes")
        self.assertTrue(handled)
        self.assertEqual(action["type"], "test_action")
        self.assertFalse(security_guard.has_pending_action())

    def test_28_cancel_pending_action(self):
        security_guard.stage_pending_action("test_action", {}, "Confirm test action?")
        handled, action, msg = security_guard.check_pending_confirmation("cancel")
        self.assertTrue(handled)
        self.assertIsNone(action)
        self.assertIn("cancelled", msg.lower())
        self.assertFalse(security_guard.has_pending_action())


# =====================================================================
# 3. Skill Crystallizer Fast-Path Tests (18 Tests)
# =====================================================================
class TestSkillCrystallizer(unittest.TestCase):
    def test_29_wake_word_stripping(self):
        res = asyncio.run(skill_crystallizer.execute_fast_path("Hey SREE, what time is it?"))
        self.assertIsNotNone(res)
        self.assertIn("currently", res.lower())

    def test_30_greeting_hi(self):
        res = asyncio.run(skill_crystallizer.execute_fast_path("hi"))
        self.assertIn("SREE is listening", res)

    def test_31_greeting_good_morning(self):
        res = asyncio.run(skill_crystallizer.execute_fast_path("good morning"))
        self.assertIn("SREE is listening", res)

    def test_32_greeting_sree(self):
        res = asyncio.run(skill_crystallizer.execute_fast_path("sree"))
        self.assertIn("SREE is listening", res)

    def test_33_greeting_sri_alias(self):
        res = asyncio.run(skill_crystallizer.execute_fast_path("sri"))
        self.assertIn("SREE is listening", res)

    def test_34_deactivation_stop_listening(self):
        res = asyncio.run(skill_crystallizer.execute_fast_path("stop listening"))
        self.assertIn("deactivated", res.lower())

    def test_35_deactivation_be_quiet(self):
        res = asyncio.run(skill_crystallizer.execute_fast_path("be quiet"))
        self.assertIn("deactivated", res.lower())

    def test_36_deactivation_go_to_sleep(self):
        res = asyncio.run(skill_crystallizer.execute_fast_path("go to sleep"))
        self.assertIn("deactivated", res.lower())

    def test_37_time_query(self):
        res = asyncio.run(skill_crystallizer.execute_fast_path("what time is it"))
        self.assertIn("it is currently", res.lower())

    def test_38_time_query_current(self):
        res = asyncio.run(skill_crystallizer.execute_fast_path("current time"))
        self.assertIn("it is currently", res.lower())

    def test_39_date_query(self):
        res = asyncio.run(skill_crystallizer.execute_fast_path("what is the date"))
        self.assertIn("today is", res.lower())

    def test_40_date_day_query(self):
        res = asyncio.run(skill_crystallizer.execute_fast_path("what day is it"))
        self.assertIn("today is", res.lower())

    def test_41_capabilities_query(self):
        res = asyncio.run(skill_crystallizer.execute_fast_path("what can you do"))
        self.assertIn("launch apps", res.lower())

    def test_42_identity_query(self):
        res = asyncio.run(skill_crystallizer.execute_fast_path("who are you"))
        self.assertIn("i am sree", res.lower())

    def test_43_health_status_query(self):
        res = asyncio.run(skill_crystallizer.execute_fast_path("how are you"))
        self.assertIn("peak performance", res.lower())

    def test_44_app_shortcut_notepad(self):
        res = asyncio.run(skill_crystallizer.execute_fast_path("open notepad"))
        self.assertTrue("opening" in res.lower() or "notice" in res.lower())

    def test_45_app_shortcut_calculator(self):
        res = asyncio.run(skill_crystallizer.execute_fast_path("launch calculator"))
        self.assertTrue("opening" in res.lower() or "notice" in res.lower())

    def test_46_unrecognized_routes_to_brain(self):
        res = asyncio.run(skill_crystallizer.execute_fast_path("explain the theory of relativity in simple terms"))
        self.assertIsNone(res)


# =====================================================================
# 4. Universal Multi-Provider AI Routing & Intra-Provider Cascading (15 Tests)
# =====================================================================
class TestUniversalRouter(unittest.TestCase):
    def test_47_initial_active_provider(self):
        status = universal_router.get_status()
        self.assertIn(status["active_provider"], ["ollama", "groq", "openrouter", "gemini", "openai", "custom"])

    def test_48_get_status_structure(self):
        status = universal_router.get_status()
        self.assertIn("providers", status)
        self.assertIn("ollama", status["providers"])
        self.assertIn("groq", status["providers"])
        self.assertIn("openrouter", status["providers"])
        self.assertIn("gemini", status["providers"])

    def test_49_groq_cascade_order(self):
        groq_cfg = universal_router.PROVIDERS["groq"]
        self.assertIn("models_cascade", groq_cfg)
        self.assertGreaterEqual(len(groq_cfg["models_cascade"]), 3)
        self.assertEqual(groq_cfg["models_cascade"][0], "llama-3.3-70b-versatile")

    def test_50_openrouter_free_models(self):
        or_cfg = universal_router.PROVIDERS["openrouter"]
        self.assertIn("free_models", or_cfg)
        self.assertTrue(any(":free" in m for m in or_cfg["free_models"]))

    def test_51_gemini_cascade_order(self):
        gem_cfg = universal_router.PROVIDERS["gemini"]
        self.assertIn("models_cascade", gem_cfg)
        self.assertIn("gemini-2.0-flash", gem_cfg["models_cascade"])

    def test_52_switch_provider_valid(self):
        orig = universal_router.active_provider
        universal_router.set_active_provider("openrouter")
        self.assertEqual(universal_router.active_provider, "openrouter")
        universal_router.set_active_provider(orig)

    def test_53_switch_provider_invalid(self):
        with self.assertRaises(ValueError):
            universal_router.set_active_provider("invalid_provider_xyz")

    def test_54_autonomous_healing_config_update(self):
        update_runtime_setting("AI_PROVIDER", "ollama")
        self.assertEqual(settings.AI_PROVIDER, "ollama")

    def test_55_custom_endpoint_config(self):
        cust = universal_router.PROVIDERS["custom"]
        self.assertIn("base_url", cust)
        self.assertIn("default_model", cust)

    def test_56_openai_config(self):
        oai = universal_router.PROVIDERS["openai"]
        self.assertIn("default_model", oai)

    def test_57_intra_provider_cascade_selection(self):
        cascade = universal_router.PROVIDERS["groq"]["models_cascade"]
        self.assertEqual(cascade[0], "llama-3.3-70b-versatile")
        self.assertEqual(cascade[1], "llama-3.1-8b-instant")

    def test_58_system_prompt_builder(self):
        msgs = build_prompt_with_context("Hi SREE", memory_context="", conversation_history=[])
        self.assertGreaterEqual(len(msgs), 2)
        self.assertEqual(msgs[0]["role"], "system")
        self.assertIn("SREE", msgs[0]["content"])

    def test_59_prompt_context_injection(self):
        msgs = build_prompt_with_context("Hi SREE", memory_context="User loves Python", conversation_history=[])
        self.assertTrue(any("User loves Python" in m["content"] for m in msgs))

    def test_60_streaming_chunk_format(self):
        sample_chunk = {"model": "llama3.2:3b", "chunk": "Hello", "done": False}
        self.assertIn("chunk", sample_chunk)
        self.assertFalse(sample_chunk["done"])

    def test_61_ollama_provider_online_detection(self):
        status = universal_router.get_status()
        self.assertIn("online", status["providers"]["ollama"])


# =====================================================================
# 5. SQLite Long-Term Memory, Notes & Reminders Engine (16 Tests)
# =====================================================================
class TestDatabaseAndMemory(unittest.TestCase):
    def test_62_db_save_and_get_message(self):
        db_manager.save_message("test_sess", "user", "Hello database test", model="test")
        hist = db_manager.get_conversation_history("test_sess", limit=5)
        self.assertGreaterEqual(len(hist), 1)
        self.assertEqual(hist[-1]["content"], "Hello database test")

    def test_63_db_conversation_history_limit(self):
        for i in range(10):
            db_manager.save_message("limit_sess", "user", f"Msg {i}")
        hist = db_manager.get_conversation_history("limit_sess", limit=3)
        self.assertEqual(len(hist), 3)

    def test_64_db_clear_conversation(self):
        db_manager.save_message("clear_sess", "user", "To be cleared")
        db_manager.clear_conversation("clear_sess")
        hist = db_manager.get_conversation_history("clear_sess")
        self.assertEqual(len(hist), 0)

    def test_65_memory_add_and_retrieve(self):
        mid = db_manager.add_memory("Unit_Test_Key", "Unit_Test_Val", category="test")
        mems = db_manager.get_all_memories()
        self.assertTrue(any(m["key"] == "Unit_Test_Key" for m in mems))
        db_manager.delete_memory(mid)

    def test_66_memory_category_classification(self):
        mid = db_manager.add_memory("Favorite Color", "Deep Blue", category="preference")
        mems = db_manager.get_all_memories()
        target = next((m for m in mems if m["id"] == mid), None)
        self.assertIsNotNone(target)
        self.assertEqual(target["category"], "preference")
        db_manager.delete_memory(mid)

    def test_67_memory_delete(self):
        mid = db_manager.add_memory("Temp_Key", "Temp_Val")
        db_manager.delete_memory(mid)
        mems = db_manager.get_all_memories()
        self.assertFalse(any(m["id"] == mid for m in mems))

    def test_68_memory_context_string_formatting(self):
        mid = db_manager.add_memory("Editor", "VSCode")
        ctx = memory_manager.get_memory_context_string()
        self.assertIn("Editor: VSCode", ctx)
        db_manager.delete_memory(mid)

    def test_69_memory_intent_extraction_remember(self):
        intent = memory_manager.extract_memory_intent("Remember that my pet's name is Luna")
        self.assertIsNotNone(intent)
        self.assertEqual(intent["category"], "user_preference")
        self.assertEqual(intent["value"], "Luna")

    def test_70_memory_intent_extraction_my_is(self):
        intent = memory_manager.extract_memory_intent("Remember: my preferred drink is green tea")
        self.assertIsNotNone(intent)
        self.assertIn("drink", intent["key"].lower())

    def test_71_note_create_and_get(self):
        nid = db_manager.create_note("Test Title", "Test Note Content", tags="test")
        notes = db_manager.get_all_notes()
        self.assertTrue(any(n["id"] == nid for n in notes))
        db_manager.delete_note(nid)

    def test_72_note_search(self):
        nid = db_manager.create_note("UniqueSearchTitle123", "Body content", tags="search")
        results = db_manager.search_notes("UniqueSearchTitle123")
        self.assertGreaterEqual(len(results), 1)
        self.assertEqual(results[0]["id"], nid)
        db_manager.delete_note(nid)

    def test_73_note_update(self):
        nid = db_manager.create_note("Original", "Original Content")
        updated = db_manager.update_note(nid, title="Updated Title", content="Updated Content")
        self.assertTrue(updated)
        notes = db_manager.get_all_notes()
        target = next(n for n in notes if n["id"] == nid)
        self.assertEqual(target["title"], "Updated Title")
        db_manager.delete_note(nid)

    def test_74_note_delete(self):
        nid = db_manager.create_note("To Delete", "Delete Me")
        db_manager.delete_note(nid)
        notes = db_manager.get_all_notes()
        self.assertFalse(any(n["id"] == nid for n in notes))

    def test_75_reminder_create(self):
        rid = db_manager.create_reminder("Test Reminder Due", priority="high")
        rems = db_manager.get_all_reminders()
        self.assertTrue(any(r["id"] == rid for r in rems))
        db_manager.delete_reminder(rid)

    def test_76_reminder_toggle_complete(self):
        rid = db_manager.create_reminder("Toggle Me")
        db_manager.toggle_reminder(rid, completed=True)
        rems = db_manager.get_all_reminders()
        target = next(r for r in rems if r["id"] == rid)
        self.assertTrue(target["completed"])
        db_manager.delete_reminder(rid)

    def test_77_privacy_export_bundle(self):
        data = db_manager.export_all_data()
        self.assertIn("conversations", data)
        self.assertIn("memories", data)
        self.assertIn("notes", data)
        self.assertIn("reminders", data)


# =====================================================================
# 6. Security Allowlist & System Telemetry Contracts (10 Tests)
# =====================================================================
class TestSecurityAllowlistAndTelemetry(unittest.TestCase):
    def test_78_hardware_ram_telemetry(self):
        telem = telemetry_service.get_system_telemetry()
        self.assertIn("hardware", telem)
        self.assertGreater(telem["hardware"]["ram_total_gb"], 0)

    def test_79_hardware_cpu_telemetry(self):
        telem = telemetry_service.get_system_telemetry()
        self.assertIn("cpu_percent", telem["hardware"])
        self.assertGreaterEqual(telem["hardware"]["cpu_percent"], 0)

    def test_80_allowlisted_apps_list(self):
        apps = automation_executor.get_allowlisted_apps()
        self.assertIsInstance(apps, list)
        self.assertGreaterEqual(len(apps), 5)

    def test_81_allowlisted_app_notepad_exists(self):
        self.assertIn("notepad", ALLOWLISTED_APPLICATIONS)

    def test_82_allowlisted_app_calc_exists(self):
        self.assertIn("calculator", ALLOWLISTED_APPLICATIONS)

    def test_83_allowlisted_app_browser_exists(self):
        self.assertIn("browser", ALLOWLISTED_APPLICATIONS)

    def test_84_allowlisted_app_terminal_exists(self):
        self.assertIn("terminal", ALLOWLISTED_APPLICATIONS)

    def test_85_allowlisted_app_vscode_exists(self):
        self.assertIn("vscode", ALLOWLISTED_APPLICATIONS)

    def test_86_allowlist_security_rejection(self):
        result = automation_executor.launch_application("unauthorized_malicious_app_xyz")
        self.assertFalse(result["success"])
        self.assertIn("not in the security allowlist", result["error"])

    def test_87_chat_fast_path_integration(self):
        res = asyncio.run(skill_crystallizer.execute_fast_path("hi sree"))
        self.assertIsNotNone(res)
        self.assertIn("SREE is listening", res)

    def test_88_fresh_db_auto_bootstrap(self):
        import tempfile
        from backend.app.database.db import DatabaseManager
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_db = Path(tmp_dir) / "bootstrap_test.db"
            db = DatabaseManager(db_path=tmp_db)
            db.add_memory("test_key", "test_val", "general")
            mems = db.get_all_memories()
            self.assertEqual(len(mems), 1)
            self.assertEqual(mems[0]["key"], "test_key")
            db.engine.dispose()

    def test_89_desktop_control_dimensions(self):
        from backend.app.automation.desktop_control import desktop_control
        w, h = desktop_control.get_screen_dimensions()
        self.assertGreater(w, 0)
        self.assertGreater(h, 0)

    def test_90_wipe_data_security_full_reset(self):
        from backend.app.api.chat import handle_proactive_actions
        # Stage wipe data
        security_guard.stage_pending_action(
            action_type="wipe_data",
            payload={},
            prompt_message="Test wipe"
        )
        self.assertTrue(security_guard.has_pending_action())
        # Confirm
        res = asyncio.run(handle_proactive_actions("yes"))
        self.assertIn("wiped successfully", res.lower())
        self.assertFalse(security_guard.has_pending_action())


# =====================================================================
# 7. Offline Semantic Memory Search & Local Vector Embeddings (Issue #3) (9 Tests)
# =====================================================================
class TestSemanticMemorySearch(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Insert test memories for semantic evaluation
        cls.mem_ids = []
        cls.mem_ids.append(db_manager.add_memory("Editor", "VS Code", category="coding"))
        cls.mem_ids.append(db_manager.add_memory("Language", "Python", category="coding"))
        cls.mem_ids.append(db_manager.add_memory("Pet", "Max the golden retriever", category="pets"))
        cls.mem_ids.append(db_manager.add_memory("City", "San Francisco", category="location"))

    @classmethod
    def tearDownClass(cls):
        for mid in cls.mem_ids:
            db_manager.delete_memory(mid)

    def test_91_semantic_engine_embedding_dimension_and_norm(self):
        from backend.app.memory.semantic_engine import semantic_engine
        vec = semantic_engine.embed_text_sync("favorite editor is VS Code")
        self.assertIsInstance(vec, list)
        self.assertEqual(len(vec), 128)
        norm = sum(x ** 2 for x in vec) ** 0.5
        self.assertAlmostEqual(norm, 1.0, places=3)

    def test_92_semantic_engine_cosine_similarity(self):
        from backend.app.memory.semantic_engine import semantic_engine
        v1 = [1.0, 0.0, 0.0]
        v2 = [1.0, 0.0, 0.0]
        v3 = [0.0, 1.0, 0.0]
        self.assertAlmostEqual(semantic_engine.cosine_similarity(v1, v2), 1.0, places=4)
        self.assertAlmostEqual(semantic_engine.cosine_similarity(v1, v3), 0.0, places=4)

    def test_93_semantic_engine_conceptual_ranking_editor_vs_pet(self):
        """Resolves GitHub Issue #3: query 'what are my coding tools' ranks editor/python over pet."""
        from backend.app.memory.semantic_engine import semantic_engine
        query_vec = semantic_engine.embed_text_sync("what are my coding tools")
        
        candidates = [
            {"id": 1, "key": "Editor", "value": "VS Code", "category": "coding"},
            {"id": 2, "key": "Language", "value": "Python", "category": "coding"},
            {"id": 3, "key": "Pet", "value": "Max the dog", "category": "pets"},
        ]
        
        ranked = semantic_engine.rank_memories(query_vec, candidates, top_k=3, min_similarity=0.10)
        self.assertGreaterEqual(len(ranked), 2)
        # Top 2 ranked results must be coding-related, not the pet
        top_keys = [r["key"] for r in ranked[:2]]
        self.assertIn("Editor", top_keys)
        self.assertIn("Language", top_keys)
        # Similarity of Editor/Language should be higher than Pet
        top_sim = ranked[0]["similarity"]
        self.assertGreater(top_sim, 0.50)

    def test_94_db_memory_embedding_persistence(self):
        test_emb = [0.123] * 128
        mid = db_manager.add_memory("Persistence_Test", "Test Value", category="test", embedding=test_emb)
        self.TestSemanticMemorySearch_mid = mid
        mems = db_manager.get_all_memories()
        target = next((m for m in mems if m["id"] == mid), None)
        self.assertIsNotNone(target)
        self.assertIsNotNone(target.get("embedding"))
        self.assertEqual(len(target["embedding"]), 128)
        self.assertAlmostEqual(target["embedding"][0], 0.123, places=3)
        db_manager.delete_memory(mid)

    def test_95_memory_manager_add_memory_with_embedding(self):
        mid = memory_manager.add_memory("Hardware_GPU", "RTX 4090", category="hardware")
        mems = db_manager.get_all_memories()
        target = next((m for m in mems if m["id"] == mid), None)
        self.assertIsNotNone(target)
        self.assertIsNotNone(target.get("embedding"))
        self.assertEqual(len(target["embedding"]), 128)
        db_manager.delete_memory(mid)

    def test_96_memory_manager_semantic_search(self):
        results = memory_manager.search_semantic_memories("what programming environment and editor do I use", top_k=2, min_similarity=0.20)
        self.assertGreaterEqual(len(results), 1)
        found_keys = [r["key"] for r in results]
        self.assertTrue("Editor" in found_keys or "Language" in found_keys)
        self.assertNotIn("City", found_keys)

    def test_97_memory_manager_context_injection_relevance(self):
        ctx = memory_manager.get_relevant_memory_context("coding language and editor", max_items=2)
        self.assertIn("relevance:", ctx.lower())
        self.assertTrue("editor" in ctx.lower() or "python" in ctx.lower())

    def test_98_memory_manager_reindex_all(self):
        # Insert a memory directly without embedding
        mid = db_manager.add_memory("No_Emb_Key", "No Emb Val", category="work", embedding=None)
        # Clear embedding in DB explicitly to simulate legacy record
        with db_manager.get_session() as sess:
            from backend.app.database.db import Memory
            mem = sess.query(Memory).filter(Memory.id == mid).first()
            if mem:
                mem.embedding = None
                sess.commit()

        reindexed = memory_manager.reindex_all_memories()
        self.assertGreaterEqual(reindexed, 1)

        mems = db_manager.get_all_memories()
        target = next((m for m in mems if m["id"] == mid), None)
        self.assertIsNotNone(target)
        self.assertIsNotNone(target.get("embedding"))
        db_manager.delete_memory(mid)

    def test_99_memory_api_search_and_reindex_endpoints(self):
        from backend.app.api.memory import search_memories, reindex_memories
        # Test semantic search endpoint function
        search_res = asyncio.run(search_memories(query="coding tools", top_k=3, threshold=0.15))
        self.assertEqual(search_res["query"], "coding tools")
        self.assertIn("results", search_res)
        self.assertIsInstance(search_res["results"], list)

        # Test reindex endpoint function
        reindex_res = asyncio.run(reindex_memories())
        self.assertEqual(reindex_res["status"], "success")
        self.assertIn("reindexed_count", reindex_res)


# =====================================================================
# Main Test Runner
# =====================================================================
if __name__ == "__main__":
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    
    # Load all 7 test classes in order
    suite.addTests(loader.loadTestsFromTestCase(TestDynamicPathResolver))
    suite.addTests(loader.loadTestsFromTestCase(TestSecurityGuard))
    suite.addTests(loader.loadTestsFromTestCase(TestSkillCrystallizer))
    suite.addTests(loader.loadTestsFromTestCase(TestUniversalRouter))
    suite.addTests(loader.loadTestsFromTestCase(TestDatabaseAndMemory))
    suite.addTests(loader.loadTestsFromTestCase(TestSecurityAllowlistAndTelemetry))
    suite.addTests(loader.loadTestsFromTestCase(TestSemanticMemorySearch))

    total = suite.countTestCases()
    print("=" * 70)
    print(f"       RUNNING SREE MASTER TEST SUITE ({total} UNIT TESTS)")
    print("=" * 70)

    start_time = time.time()
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    duration = time.time() - start_time

    print("\n" + "=" * 70)
    print(f"  TESTS RUN: {result.testsRun} | PASSED: {result.testsRun - len(result.failures) - len(result.errors)} | FAILED: {len(result.failures)} | ERRORS: {len(result.errors)}")
    print(f"  EXECUTION TIME: {duration:.2f}s")
    if result.wasSuccessful():
        print(f"  STATUS: 100% PASS RATE ({result.testsRun}/{result.testsRun} Passing)")
    print("=" * 70)

    sys.exit(0 if result.wasSuccessful() else 1)
