import os, sys, json, time, re, threading, traceback
from pathlib import Path
from typing import Dict, List

print("[AutoTranslator] node_scanner module loading...")

class NodeScanner:
    def __init__(self):
        print("[AutoTranslator] NodeScanner.__init__ starting...")
        self.comfyui_dir = self._find_comfyui_dir()
        print(f"[AutoTranslator] ComfyUI dir: {self.comfyui_dir}")
        self.custom_nodes_dir = self.comfyui_dir / "custom_nodes" if self.comfyui_dir else None
        print(f"[AutoTranslator] Custom nodes dir: {self.custom_nodes_dir}")
        self.locales_dir = Path(__file__).parent / "locales"
        self.locales_dir.mkdir(exist_ok=True)
        self._known_plugins = set()
        self._monitor_thread = None
        print("[AutoTranslator] NodeScanner.__init__ complete")

    def _find_comfyui_dir(self) -> Path:
        possible_paths = [
            Path.cwd().parent.parent,
            Path.cwd().parent,
            Path.home() / "ComfyUI",
            Path.home() / "Documents" / "ComfyUI",
            Path("/opt/ComfyUI"),
            Path("C:/ComfyUI"),
        ]
        for path in possible_paths:
            if (path / "comfy").exists() or (path / "main.py").exists():
                return path
        for p in sys.path:
            p = Path(p)
            if (p / "comfy").exists():
                return p
        return Path.cwd()

    def scan_all_nodes(self) -> Dict[str, dict]:
        print("[AutoTranslator] scan_all_nodes starting...")
        nodes_info = {}

        if not self.custom_nodes_dir or not self.custom_nodes_dir.exists():
            print("[AutoTranslator] custom_nodes dir not found, skipping scan")
            return nodes_info

        plugin_count = 0
        for plugin_dir in self.custom_nodes_dir.iterdir():
            if not plugin_dir.is_dir() or plugin_dir.name.startswith('.') or plugin_dir.name.startswith('__'):
                continue
            if 'auto-translator' in plugin_dir.name.lower():
                continue

            try:
                plugin_nodes = self._scan_plugin(plugin_dir)
                if plugin_nodes:
                    nodes_info[plugin_dir.name] = plugin_nodes
                    plugin_count += 1
            except Exception as e:
                print(f"[AutoTranslator] Failed to scan {plugin_dir.name}: {e}")
                traceback.print_exc()
                continue

        print(f"[AutoTranslator] scan_all_nodes complete: {plugin_count} plugins, {sum(len(n) for n in nodes_info.values())} nodes")
        return nodes_info

    def _scan_plugin(self, plugin_dir: Path) -> Dict[str, dict]:
        nodes = {}
        for py_file in plugin_dir.rglob("*.py"):
            if py_file.name.startswith('__'):
                continue
            try:
                file_nodes = self._extract_nodes_from_file(py_file)
                nodes.update(file_nodes)
            except Exception as e:
                print(f"[AutoTranslator] Failed to parse {py_file}: {e}")
                continue
        return nodes

    def _extract_nodes_from_file(self, py_file: Path) -> Dict[str, dict]:
        nodes = {}
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"[AutoTranslator] Failed to read {py_file}: {e}")
            return nodes

        try:
            class_pattern = r'class\s+(\w+)\s*[:\(]'
            classes = re.findall(class_pattern, content)
        except Exception as e:
            print(f"[AutoTranslator] Regex failed on {py_file}: {e}")
            return nodes

        for class_name in classes:
            if 'INPUT_TYPES' in content or 'RETURN_TYPES' in content:
                try:
                    node_info = self._parse_node_class(content, class_name)
                    if node_info:
                        nodes[class_name] = node_info
                except Exception as e:
                    print(f"[AutoTranslator] Failed to parse class {class_name}: {e}")
                    continue
        return nodes

    def _parse_node_class(self, content: str, class_name: str) -> dict:
        node_info = {
            'class_name': class_name,
            'display_name': class_name,
            'category': '',
            'inputs': {},
            'outputs': {},
        }

        try:
            name_match = re.search(r'RETURN_NAMES\s*=\s*\[(.*?)\]', content)
            if name_match:
                raw = name_match.group(1).strip()
                raw = raw.strip(chr(34))
                raw = raw.strip(chr(39))
                node_info['display_name'] = raw.strip()
        except Exception as e:
            print(f"[AutoTranslator] RETURN_NAMES parse failed: {e}")

        try:
            cat_pattern = r'CATEGORY\s*=\s*' + chr(34) + r'(.+?)' + chr(34)
            cat_match = re.search(cat_pattern, content)
            if not cat_match:
                cat_pattern = r"CATEGORY\s*=\s*" + chr(39) + r"(.+?)" + chr(39)
                cat_match = re.search(cat_pattern, content)
            if cat_match:
                node_info['category'] = cat_match.group(1)
        except Exception as e:
            print(f"[AutoTranslator] CATEGORY parse failed: {e}")

        try:
            input_match = re.search(r'INPUT_TYPES\s*\(.*\)\s*return\s*\{(.*?)\}', content, re.DOTALL)
            if input_match:
                inputs_str = input_match.group(1)
                param_pattern = chr(34) + r'(\w+)' + chr(34) + r'\s*:'
                param_matches = re.findall(param_pattern, inputs_str)
                if not param_matches:
                    param_pattern = chr(39) + r'(\w+)' + chr(39) + r'\s*:'
                    param_matches = re.findall(param_pattern, inputs_str)
                for param in param_matches:
                    node_info['inputs'][param] = param
        except Exception as e:
            print(f"[AutoTranslator] INPUT_TYPES parse failed: {e}")

        try:
            return_match = re.search(r'RETURN_TYPES\s*=\s*\((.*?)\)', content)
            if return_match:
                types = return_match.group(1).split(',')
                for i, t in enumerate(types):
                    t = t.strip()
                    t = t.strip(chr(34))
                    t = t.strip(chr(39))
                    if t:
                        node_info['outputs'][f'output_{i}'] = t
        except Exception as e:
            print(f"[AutoTranslator] RETURN_TYPES parse failed: {e}")

        return node_info

    def scan_and_translate(self, translator):
        print("[AutoTranslator] scan_and_translate starting...")
        nodes_info = self.scan_all_nodes()

        if not nodes_info:
            print("[AutoTranslator] No nodes found to translate")
            return

        texts_to_translate = set()
        for plugin_name, nodes in nodes_info.items():
            for node_name, node_data in nodes.items():
                if node_data.get('display_name') and not self._is_chinese(node_data['display_name']):
                    texts_to_translate.add(node_data['display_name'])
                if node_data.get('category') and not self._is_chinese(node_data['category']):
                    texts_to_translate.add(node_data['category'])
                for param_name in node_data.get('inputs', {}).values():
                    if param_name and not self._is_chinese(param_name):
                        texts_to_translate.add(param_name)
                for output_name in node_data.get('outputs', {}).values():
                    if output_name and not self._is_chinese(output_name):
                        texts_to_translate.add(output_name)

        print(f"[AutoTranslator] Found {len(texts_to_translate)} texts to translate")

        if not texts_to_translate:
            print("[AutoTranslator] No texts need translation")
            return

        try:
            translations = translator.translate_batch(list(texts_to_translate))
            self._generate_translation_files(nodes_info, translations)
        except Exception as e:
            print(f"[AutoTranslator] Translation failed: {e}")
            traceback.print_exc()
            return

        total = sum(len(n) for n in nodes_info.values())
        print(f"[AutoTranslator] done: {total} nodes, {len(texts_to_translate)} texts translated")

    def _generate_translation_files(self, nodes_info: Dict, translations: Dict[str, str]):
        for plugin_name, nodes in nodes_info.items():
            translation_dict = {}
            for node_name, node_data in nodes.items():
                display_name = node_data.get('display_name', node_name)
                if display_name in translations:
                    translation_dict[f"node.{node_name}.title"] = translations[display_name]

                category = node_data.get('category', '')
                if category in translations:
                    translation_dict[f"node.{node_name}.category"] = translations[category]

                for param_key, param_name in node_data.get('inputs', {}).items():
                    if param_name in translations:
                        translation_dict[f"node.{node_name}.input.{param_key}"] = translations[param_name]

                for output_key, output_name in node_data.get('outputs', {}).items():
                    if output_name in translations:
                        translation_dict[f"node.{node_name}.output.{output_key}"] = translations[output_name]

            if translation_dict:
                try:
                    safe_name = plugin_name.replace(' ', '_').replace('-', '_')
                    output_file = self.locales_dir / f"{safe_name}.zh.json"
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(translation_dict, f, ensure_ascii=False, indent=2)
                    print(f"[AutoTranslator] Written {output_file} ({len(translation_dict)} entries)")
                except Exception as e:
                    print(f"[AutoTranslator] Failed to write {plugin_name}: {e}")

        try:
            master_translation = {}
            for f in self.locales_dir.glob("*.zh.json"):
                with open(f, 'r', encoding='utf-8') as fp:
                    master_translation.update(json.load(fp))

            master_file = self.locales_dir / "master.zh.json"
            with open(master_file, 'w', encoding='utf-8') as f:
                json.dump(master_translation, f, ensure_ascii=False, indent=2)
            print(f"[AutoTranslator] Master file written: {len(master_translation)} entries")
        except Exception as e:
            print(f"[AutoTranslator] Master file failed: {e}")

    def _is_chinese(self, text: str) -> bool:
        if not text:
            return False
        return any('\u4e00' <= char <= '\u9fff' for char in text)

    def start_monitor(self, translator):
        if not self.custom_nodes_dir:
            print("[AutoTranslator] Cannot start monitor: no custom_nodes dir")
            return

        try:
            self._known_plugins = {d.name for d in self.custom_nodes_dir.iterdir() if d.is_dir()}
            print(f"[AutoTranslator] Monitor: watching {len(self._known_plugins)} plugins")
        except Exception as e:
            print(f"[AutoTranslator] Monitor init failed: {e}")
            return

        def _monitor():
            while True:
                time.sleep(60)
                if not self.custom_nodes_dir.exists():
                    continue
                try:
                    current = {d.name for d in self.custom_nodes_dir.iterdir() if d.is_dir()}
                    new_plugins = current - self._known_plugins
                    if new_plugins:
                        print(f"[AutoTranslator] New plugins detected: {new_plugins}")
                        self.scan_and_translate(translator)
                        self._known_plugins = current
                except Exception as e:
                    print(f"[AutoTranslator] Monitor error: {e}")

        self._monitor_thread = threading.Thread(target=_monitor, daemon=True, name="AutoTranslator-Monitor")
        self._monitor_thread.start()
        print("[AutoTranslator] Monitor thread started")

print("[AutoTranslator] node_scanner module loaded")
