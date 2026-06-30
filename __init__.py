"""
ComfyUI Zn Translation Plugin
支持中英互译，API 密钥可在 ComfyUI 设置界面配置
"""

import os
import json
import sys
import shutil
import atexit
import server
import folder_paths
from pathlib import Path
from functools import lru_cache
from aiohttp import web

VERSION = "1.0.0"
ADDON_NAME = "comfyui-Zn-translation"
COMFY_PATH = Path(folder_paths.__file__).parent
CUR_PATH = Path(__file__).parent

# ============ 配置管理 ============
CONFIG_FILE = CUR_PATH / "config.json"

DEFAULT_CONFIG = {
    "translation_api": "libre",
    "api_key": "",
    "api_url": "",
    "source_lang": "en",
    "target_lang": "zh",
    "enable_auto_translate": False,
    "translate_on_load": True,
}

def load_config():
    """加载配置，支持 ComfyUI 设置界面修改"""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return {**DEFAULT_CONFIG, **json.load(f)}
        except Exception as e:
            print(f"[Zn-Translation] 配置加载失败: {e}")
    return DEFAULT_CONFIG.copy()

def save_config(config):
    """保存配置"""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[Zn-Translation] 配置保存失败: {e}")

CONFIG = load_config()

# ============ JSON 工具 ============
def try_get_json(path: Path):
    """尝试多种编码读取 JSON"""
    for coding in ["utf-8", "gbk"]:
        try:
            return json.loads(path.read_text(encoding=coding))
        except Exception:
            continue
    return {}

def get_nodes_translation(locale):
    """获取节点翻译"""
    path = CUR_PATH.joinpath(locale, "Nodes")
    if not path.exists():
        path = CUR_PATH.joinpath("zh-CN", "Nodes")
    if not path.exists():
        return {}
    translations = {}
    for jpath in path.glob("*.json"):
        translations.update(try_get_json(jpath))
    return translations

def get_category_translation(locale):
    """获取分类翻译"""
    cats = {}
    cat_dir = CUR_PATH.joinpath(locale, "Categories")
    if cat_dir.exists():
        for cat_json in cat_dir.glob("*.json"):
            cats.update(try_get_json(cat_json))
    return cats

def get_menu_translation(locale):
    """获取菜单翻译"""
    menus = {}
    menu_dir = CUR_PATH.joinpath(locale, "Menus")
    if menu_dir.exists():
        for menu_json in menu_dir.glob("*.json"):
            menus.update(try_get_json(menu_json))
    return menus

@lru_cache
def compile_translation(locale):
    """编译翻译数据"""
    nodes = get_nodes_translation(locale)
    categories = get_category_translation(locale)
    menus = get_menu_translation(locale)

    data = {
        "Nodes": nodes,
        "NodeCategory": categories,
        "Menu": menus,
        "locale": locale,
        "version": VERSION
    }
    return json.dumps(data, ensure_ascii=False)

@lru_cache
def compress_json(data, method="gzip"):
    """压缩 JSON 数据"""
    if method == "gzip":
        import gzip
        return gzip.compress(data.encode("utf-8"))
    return data

# ============ API 路由 ============

@server.PromptServer.instance.routes.post("/zn/get_translation")
async def get_translation(request: web.Request):
    """获取翻译数据"""
    post = await request.post()
    locale = post.get("locale", "zh-CN")
    accept_encoding = request.headers.get("Accept-Encoding", "")

    json_data = "{}"
    headers = {}
    try:
        json_data = compile_translation(locale)
        if "gzip" in accept_encoding:
            json_data = compress_json(json_data, method="gzip")
            headers["Content-Encoding"] = "gzip"
    except Exception as e:
        sys.stderr.write(f"[Zn/get_translation error]: {e}\n")
        sys.stderr.flush()

    return web.Response(status=200, body=json_data, headers=headers)

@server.PromptServer.instance.routes.get("/zn/get_config")
async def get_config(request: web.Request):
    """获取翻译配置（供前端使用）"""
    return web.json_response({
        "api_type": CONFIG.get("translation_api", "libre"),
        "source_lang": CONFIG.get("source_lang", "en"),
        "target_lang": CONFIG.get("target_lang", "zh"),
        "enable_auto": CONFIG.get("enable_auto_translate", False),
        "version": VERSION
    })

@server.PromptServer.instance.routes.post("/zn/save_config")
async def save_config_endpoint(request: web.Request):
    """保存配置（从 ComfyUI 设置界面调用）"""
    global CONFIG
    try:
        data = await request.json()
        for key in ["translation_api", "api_key", "api_url", "source_lang", "target_lang", "enable_auto_translate"]:
            if key in data:
                CONFIG[key] = data[key]
        save_config(CONFIG)
        return web.json_response({"status": "success", "config": CONFIG})
    except Exception as e:
        return web.json_response({"status": "error", "message": str(e)}, status=500)

@server.PromptServer.instance.routes.post("/zn/translate_text")
async def translate_text(request: web.Request):
    """
    文本翻译接口
    支持国内免费翻译 API
    """
    try:
        data = await request.json()
        text = data.get("text", "")
        source = data.get("source", CONFIG.get("source_lang", "en"))
        target = data.get("target", CONFIG.get("target_lang", "zh"))
        api_type = data.get("api_type", CONFIG.get("translation_api", "libre"))

        if not text:
            return web.json_response({"status": "error", "message": "文本不能为空"})

        result = await do_translate(text, source, target, api_type)
        return web.json_response({"status": "success", "result": result})
    except Exception as e:
        return web.json_response({"status": "error", "message": str(e)})

async def do_translate(text, source, target, api_type):
    """执行翻译"""
    import aiohttp

    if api_type == "libre":
        url = CONFIG.get("api_url") or "https://libretranslate.de/translate"
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json={
                "q": text,
                "source": source,
                "target": target,
                "format": "text"
            }) as resp:
                data = await resp.json()
                return data.get("translatedText", text)

    elif api_type == "baidu":
        import hashlib
        import random
        appid = CONFIG.get("api_key", "").split(":")[0] if ":" in CONFIG.get("api_key", "") else CONFIG.get("api_key", "")
        secret = CONFIG.get("api_key", "").split(":")[1] if ":" in CONFIG.get("api_key", "") else ""
        salt = random.randint(32768, 65536)
        sign = hashlib.md5(f"{appid}{text}{salt}{secret}".encode()).hexdigest()
        url = "https://fanyi-api.baidu.com/api/trans/vip/translate"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params={
                "q": text,
                "from": source,
                "to": target,
                "appid": appid,
                "salt": salt,
                "sign": sign
            }) as resp:
                data = await resp.json()
                if "trans_result" in data:
                    return "".join([r["dst"] for r in data["trans_result"]])
                return text

    elif api_type == "youdao":
        import hashlib
        import random
        import time
        app_key = CONFIG.get("api_key", "").split(":")[0] if ":" in CONFIG.get("api_key", "") else CONFIG.get("api_key", "")
        app_secret = CONFIG.get("api_key", "").split(":")[1] if ":" in CONFIG.get("api_key", "") else ""
        salt = str(random.randint(1, 65536))
        curtime = str(int(time.time()))
        sign_str = app_key + truncate(text) + salt + curtime + app_secret
        sign = hashlib.sha256(sign_str.encode("utf-8")).hexdigest()

        url = "https://openapi.youdao.com/api"
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data={
                "q": text,
                "from": source,
                "to": target,
                "appKey": app_key,
                "salt": salt,
                "sign": sign,
                "signType": "v3",
                "curtime": curtime
            }) as resp:
                data = await resp.json()
                if "translation" in data:
                    return data["translation"][0]
                return text

    elif api_type == "custom":
        url = CONFIG.get("api_url", "")
        if not url:
            return text
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json={
                "text": text,
                "source": source,
                "target": target,
                "key": CONFIG.get("api_key", "")
            }) as resp:
                data = await resp.json()
                return data.get("result", text)

    return text

def truncate(q):
    """有道 API 签名辅助"""
    if q is None:
        return None
    size = len(q)
    return q if size <= 20 else q[0:10] + str(size) + q[size - 10:size]

# ============ 注册 ComfyUI 扩展 ============
def rmtree(path: Path):
    """安全删除目录"""
    if not path.exists():
        return
    if path.is_file():
        path.unlink()
    elif path.is_dir():
        for child in path.iterdir():
            rmtree(child)
        try:
            path.rmdir()
        except:
            pass

def register():
    """注册插件到 ComfyUI web 扩展"""
    ext_path = COMFY_PATH.joinpath("web", "extensions", ADDON_NAME)

    try:
        if ext_path.exists():
            rmtree(ext_path)
        shutil.copytree(
            CUR_PATH.as_posix(), 
            ext_path.as_posix(),
            ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc")
        )
        print(f"[Zn-Translation] 插件已注册: {ext_path}")
    except Exception as e:
        sys.stderr.write(f"[Zn/register error]: {e}\n")
        sys.stderr.flush()

def unregister():
    """卸载插件"""
    ext_path = COMFY_PATH.joinpath("web", "extensions", ADDON_NAME)
    try:
        rmtree(ext_path)
    except:
        pass

register()
atexit.register(unregister)

# ComfyUI 节点注册
NODE_CLASS_MAPPINGS = {}
WEB_DIRECTORY = "./"

print(f"[Zn-Translation] v{VERSION} 加载完成")
