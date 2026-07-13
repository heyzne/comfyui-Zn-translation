import json, time, hashlib, ssl, urllib.request, urllib.parse, traceback
from pathlib import Path
from typing import Dict, List
import random

print("[AutoTranslator] translator_core module loading...")

try:
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    print("[AutoTranslator] SSL context created")
except Exception as e:
    print(f"[AutoTranslator] SSL context FAILED: {e}")
    traceback.print_exc()
    ssl_context = None

class AutoTranslator:
    def __init__(self, cache_dir=None):
        print("[AutoTranslator] AutoTranslator.__init__ starting...")
        self.cache_dir = Path(cache_dir) if cache_dir else Path(__file__).parent / "cache"
        self.cache_dir.mkdir(exist_ok=True)
        self.translation_cache = {}
        self.load_cache()

        self.builtin_terms = {}
        terms_file = Path(__file__).parent / "builtin_terms.json"
        print(f"[AutoTranslator] Looking for terms file: {terms_file}")
        if terms_file.exists():
            try:
                with open(terms_file, 'r', encoding='utf-8') as f:
                    self.builtin_terms = json.load(f)
                print(f"[AutoTranslator] Loaded {len(self.builtin_terms)} builtin terms")
            except Exception as e:
                print(f"[AutoTranslator] Failed to load terms: {e}")
                traceback.print_exc()
        else:
            print("[AutoTranslator] No builtin_terms.json found")

        self.apis = {
            'google_free': self._translate_google_free,
            'libretranslate': self._translate_libre,
        }
        self.current_api = 'google_free'
        print("[AutoTranslator] AutoTranslator.__init__ complete")

    def load_cache(self):
        cache_file = self.cache_dir / "translation_cache.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    self.translation_cache = json.load(f)
            except Exception as e:
                print(f"[AutoTranslator] Cache load failed: {e}")
                self.translation_cache = {}

    def save_cache(self):
        cache_file = self.cache_dir / "translation_cache.json"
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.translation_cache, f, ensure_ascii=False, indent=2)

    def get_cache_key(self, text: str, target_lang: str = 'zh') -> str:
        return hashlib.md5(f"{text}:{target_lang}".encode()).hexdigest()

    def translate(self, text: str, target_lang: str = 'zh', source_lang: str = 'en') -> str:
        if not text or not isinstance(text, str):
            return text

        text_lower = text.lower().strip()

        if text_lower in self.builtin_terms:
            return self.builtin_terms[text_lower]

        cache_key = self.get_cache_key(text, target_lang)
        if cache_key in self.translation_cache:
            return self.translation_cache[cache_key]

        if self._is_chinese(text):
            self.translation_cache[cache_key] = text
            return text

        translated = self._try_translate(text, target_lang, source_lang)
        self.translation_cache[cache_key] = translated
        return translated

    def _is_chinese(self, text: str) -> bool:
        chinese_chars = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
        return chinese_chars > len(text) * 0.3

    def _try_translate(self, text: str, target: str, source: str) -> str:
        apis = list(self.apis.keys())
        random.shuffle(apis)

        for api_name in apis:
            for attempt in range(2):
                try:
                    result = self.apis[api_name](text, target, source)
                    if result and result != text:
                        self.current_api = api_name
                        return result
                except Exception:
                    if attempt < 1:
                        time.sleep(0.5)
                    continue

        return text

    def _translate_google_free(self, text: str, target: str, source: str) -> str:
        encoded_text = urllib.parse.quote(text)
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl={source}&tl={target}&dt=t&q={encoded_text}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=8, context=ssl_context) as response:
            data = json.loads(response.read().decode('utf-8'))
        return ''.join([item[0] for item in data[0] if item[0]])

    def _translate_libre(self, text: str, target: str, source: str) -> str:
        instances = [
            "https://libretranslate.de/translate",
            "https://translate.argosopentech.com/translate",
            "https://libretranslate.pussthecat.org/translate",
        ]
        for instance in instances:
            try:
                data = {'q': text, 'source': source, 'target': target, 'format': 'text'}
                req = urllib.request.Request(
                    instance,
                    data=json.dumps(data).encode('utf-8'),
                    headers={'Content-Type': 'application/json'},
                    method='POST'
                )
                with urllib.request.urlopen(req, timeout=8, context=ssl_context) as response:
                    result = json.loads(response.read().decode('utf-8'))
                    return result.get('translatedText', text)
            except:
                continue
        raise Exception("All failed")

    def translate_batch(self, texts: List[str], target: str = 'zh', source: str = 'en') -> Dict[str, str]:
        results = {}
        total = len(texts)

        for i, text in enumerate(texts):
            if not text:
                continue
            results[text] = self.translate(text, target, source)

            if (i + 1) % 100 == 0 or i == total - 1:
                print(f"[AutoTranslator] progress: {i+1}/{total} ({(i+1)*100//total}%)")

            if (i + 1) % 50 == 0:
                self.save_cache()

            time.sleep(0.2)

        self.save_cache()
        return results

print("[AutoTranslator] translator_core module loaded")
