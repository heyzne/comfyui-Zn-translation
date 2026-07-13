import os, sys, threading, traceback
from pathlib import Path

# ComfyUI 要求必须有 NODE_CLASS_MAPPINGS
NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

EXTENSION_DIR = Path(__file__).parent.resolve()
(EXTENSION_DIR / "locales").mkdir(exist_ok=True)
(EXTENSION_DIR / "cache").mkdir(exist_ok=True)

print("[AutoTranslator] Loading modules...")

try:
    from .translator_core import AutoTranslator
    print("[AutoTranslator] translator_core loaded")
except Exception as e:
    print(f"[AutoTranslator] FAILED to load translator_core: {e}")
    traceback.print_exc()
    raise

try:
    from .node_scanner import NodeScanner
    print("[AutoTranslator] node_scanner loaded")
except Exception as e:
    print(f"[AutoTranslator] FAILED to load node_scanner: {e}")
    traceback.print_exc()
    raise

translator = None
scanner = None

def _init_async():
    global translator, scanner
    try:
        print("[AutoTranslator] Starting async init...")
        scanner = NodeScanner()
        print("[AutoTranslator] NodeScanner created")
        translator = AutoTranslator()
        print("[AutoTranslator] AutoTranslator created")
        scanner.scan_and_translate(translator)
        scanner.start_monitor(translator)
        print("[AutoTranslator] Async init complete")
    except Exception as e:
        print(f"[AutoTranslator] Async init FAILED: {e}")
        traceback.print_exc()

print("[AutoTranslator] Starting background thread...")
threading.Thread(target=_init_async, daemon=True, name="AutoTranslator").start()
print("[AutoTranslator] Background thread started")

WEB_DIRECTORY = "./web"
