"""
ComfyUI Zn Translation - 中文翻译插件
支持自动检测新插件并翻译
"""

import os
import json
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 路径
BASE_DIR = Path(__file__).parent
JS_DIR = BASE_DIR / "js"
TRANSLATIONS_DIR = BASE_DIR / "translations"

# 自动加载 auto_translate 模块
AUTO_TRANSLATE_DIR = BASE_DIR / "auto_translate"
if AUTO_TRANSLATE_DIR.exists():
    sys.path.insert(0, str(BASE_DIR))
    try:
        from auto_translate.config import Config
        from auto_translate.scanner import PluginScanner
        AUTO_TRANSLATE_AVAILABLE = True
    except ImportError as e:
        logger.warning(f"Auto-translate module not available: {e}")
        AUTO_TRANSLATE_AVAILABLE = False
else:
    AUTO_TRANSLATE_AVAILABLE = False

# Web 目录
WEB_DIRECTORY = "js"

# 节点映射（ComfyUI 要求）
NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

def get_translation_files():
    """获取所有翻译文件"""
    translations = {}
    
    for lang_dir in TRANSLATIONS_DIR.iterdir():
        if not lang_dir.is_dir():
            continue
        
        lang = lang_dir.name
        translations[lang] = {
            'nodes': {},
            'menus': {},
            'categories': {}
        }
        
        # 加载节点翻译
        nodes_dir = lang_dir / 'Nodes'
        if nodes_dir.exists():
            for json_file in nodes_dir.glob('*.json'):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        translations[lang]['nodes'].update(data)
                except Exception as e:
                    logger.error(f"Error loading {json_file}: {e}")
        
        # 加载菜单翻译
        menus_dir = lang_dir / 'Menus'
        if menus_dir.exists():
            for json_file in menus_dir.glob('*.json'):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        translations[lang]['menus'].update(data)
                except Exception as e:
                    logger.error(f"Error loading {json_file}: {e}")
        
        # 加载分类翻译
        cat_dir = lang_dir / 'Categories'
        if cat_dir.exists():
            for json_file in cat_dir.glob('*.json'):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        translations[lang]['categories'].update(data)
                except Exception as e:
                    logger.error(f"Error loading {json_file}: {e}")
    
    return translations

def check_auto_translate():
    """检查是否需要自动翻译"""
    if not AUTO_TRANSLATE_AVAILABLE:
        return
    
    try:
        config = Config()
        if not config.get('auto_translate'):
            return
        
        scanner = PluginScanner()
        untranslated = scanner.get_untranslated_plugins()
        
        if untranslated:
            logger.info(f"Found {len(untranslated)} untranslated plugins")
            # 这里可以触发自动翻译，但建议用户手动运行 scan_now.py
            # 因为自动翻译需要 API key，且可能耗时较长
    except Exception as e:
        logger.error(f"Auto-translate check failed: {e}")

# 启动时检查
check_auto_translate()

# 导出翻译供前端使用
__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS', 'WEB_DIRECTORY']
