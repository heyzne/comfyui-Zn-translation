"""
ComfyUI-ZN-Translation
复刻 AIGODLIKE/AIGODLIKE-ComfyUI-Translation 架构
支持新版 ComfyUI (前端 > 1.2) 的 Vue 节点系统和 PrimeVue 弹窗
"""
import os
import json
import sys
import shutil
import atexit
from pathlib import Path
from functools import lru_cache

VERSION = "2.0.0"
ADDON_NAME = "ComfyUI-ZN-Translation"

# 尝试获取 ComfyUI 路径
try:
    import folder_paths
    COMFY_PATH = Path(folder_paths.__file__).parent
except ImportError:
    COMFY_PATH = Path(__file__).parent.parent.parent

CUR_PATH = Path(__file__).parent

# ============================================================
# 翻译数据加载
# ============================================================

def try_get_json(path):
    """尝试多种编码读取 JSON 文件"""
    if not path.exists():
        return {}
    for coding in ["utf-8", "gbk"]:
        try:
            return json.loads(path.read_text(encoding=coding))
        except Exception:
            continue
    return {}


def get_nodes_translation(locale="zh-CN"):
    """加载节点翻译: {locale}/Nodes/*.json"""
    path = CUR_PATH / "translations" / locale / "Nodes"
    if not path.exists():
        # 尝试旧格式: translations/Nodes/
        path = CUR_PATH / "translations" / "Nodes"
    if not path.exists():
        return {}
    translations = {}
    for jpath in path.glob("*.json"):
        translations.update(try_get_json(jpath))
    return translations


def get_category_translation(locale="zh-CN"):
    """加载分类翻译: {locale}/Categories/*.json"""
    cats = {}
    cat_dir = CUR_PATH / "translations" / locale / "Categories"
    if cat_dir.exists():
        for cat_json in cat_dir.glob("*.json"):
            cats.update(try_get_json(cat_json))

    # 也尝试旧格式
    if not cats:
        old_cat_dir = CUR_PATH / "translations" / "Categories"
        if old_cat_dir.exists():
            for cat_json in old_cat_dir.glob("*.json"):
                cats.update(try_get_json(cat_json))

    return cats


def get_menu_translation(locale="zh-CN"):
    """加载菜单翻译: {locale}/Menus/*.json"""
    menus = {}
    menu_dir = CUR_PATH / "translations" / locale / "Menus"
    if menu_dir.exists():
        for menu_json in menu_dir.glob("*.json"):
            menus.update(try_get_json(menu_json))

    # 也尝试旧格式
    if not menus:
        old_menu_dir = CUR_PATH / "translations" / "Menus"
        if old_menu_dir.exists():
            for menu_json in old_menu_dir.glob("*.json"):
                menus.update(try_get_json(menu_json))

    # 兼容最旧格式: translations/base.json
    base_path = CUR_PATH / "translations" / "base.json"
    if base_path.exists():
        menus.update(try_get_json(base_path))

    return menus


@lru_cache
def compile_translation(locale="zh-CN"):
    """编译所有翻译数据为统一 JSON"""
    nodes_translation = get_nodes_translation(locale)
    node_category_translation = get_category_translation(locale)
    menu_translation = get_menu_translation(locale)

    return json.dumps(
        obj={
            "Nodes": nodes_translation,
            "NodeCategory": node_category_translation,
            "Menu": menu_translation,
        },
        ensure_ascii=False,
    )


# ============================================================
# HTTP API
# ============================================================

try:
    import server
    from aiohttp import web

    @server.PromptServer.instance.routes.get("/zn_translation/get_data")
    async def get_translation_data(request):
        """返回编译后的翻译数据"""
        locale = request.query.get("locale", "zh-CN")
        try:
            json_data = compile_translation(locale)
            return web.Response(
                status=200,
                body=json_data,
                content_type="application/json",
                charset="utf-8",
            )
        except Exception as e:
            sys.stderr.write(f"[ZN-Translation] get_data error: {e}\n")
            sys.stderr.flush()
            return web.Response(status=500, body="{}")

    print("[ZN-Translation] 已注册翻译数据 API: GET /zn_translation/get_data")
except Exception as e:
    print(f"[ZN-Translation] 注册 API 失败: {e}")


# ============================================================
# 文件注入机制（复刻 AIGODLIKE register/unregister）
# ============================================================

def rmtree(path):
    """递归删除目录（安全版）"""
    path = Path(path)
    if not path.exists():
        return
    if path.is_symlink() or (path.resolve() != path and not path.is_dir()):
        path.unlink()
        return
    if path.is_file():
        path.unlink()
    elif path.is_dir():
        if path.name == ".git":
            # 跳过 .git 目录
            return
        for child in path.iterdir():
            rmtree(child)
        try:
            path.rmdir()
        except BaseException:
            pass


def register():
    """将插件文件复制到 ComfyUI web/extensions 目录"""
    import nodes

    target_path = COMFY_PATH / "web" / "extensions" / ADDON_NAME

    # 新版 ComfyUI 支持 EXTENSION_WEB_DIRS，无需复制
    if hasattr(nodes, "EXTENSION_WEB_DIRS"):
        rmtree(target_path)
        print("[ZN-Translation] 检测到新版 ComfyUI (EXTENSION_WEB_DIRS)，跳过文件复制")
        return

    try:
        if os.name == "nt":
            # Windows: 尝试创建符号连接
            try:
                import _winapi
                _winapi.CreateJunction(str(CUR_PATH), str(target_path))
                print(f"[ZN-Translation] 已创建符号连接: {target_path}")
            except (WindowsError, OSError, ImportError):
                # 回退到文件复制
                shutil.copytree(
                    str(CUR_PATH), str(target_path),
                    ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc", "cache")
                )
                print(f"[ZN-Translation] 已复制文件到: {target_path}")
        else:
            shutil.copytree(
                str(CUR_PATH), str(target_path),
                ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc", "cache")
            )
            print(f"[ZN-Translation] 已复制文件到: {target_path}")
    except Exception as e:
        sys.stderr.write(f"[ZN-Translation] register error: {e}\n")
        sys.stderr.flush()


def unregister():
    """退出时清理复制的文件"""
    target_path = COMFY_PATH / "web" / "extensions" / ADDON_NAME
    try:
        rmtree(target_path)
    except BaseException:
        pass


register()
atexit.register(unregister)

# ============================================================
# ComfyUI 注册
# ============================================================

NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}
WEB_DIRECTORY = "./js"

print(f"[ZN-Translation] 插件 v{VERSION} 加载完成 (复刻 AIGODLIKE 架构)")
