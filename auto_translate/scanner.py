"""
扫描 custom_nodes 目录，检测新插件
"""

import os
import json
import ast
from pathlib import Path
from typing import List, Dict, Set
import logging

logger = logging.getLogger(__name__)

class PluginScanner:
    """插件扫描器"""
    
    # 忽略的目录
    IGNORE_DIRS = {
        '__pycache__', '.git', '.idea', '.vscode', 
        'comfyui-Zn-translation',  # 自己
        'ComfyUI-Manager',  # 管理器本身
        'AIGODLIKE-COMFYUI-TRANSLATION',  # 其他翻译插件
    }
    
    # 忽略的文件模式
    IGNORE_PATTERNS = ('test_', '_test', 'example', 'demo')
    
    def __init__(self, custom_nodes_path: Path = None):
        from .config import Config
        self.config = Config()
        self.custom_nodes_path = custom_nodes_path or self.config.custom_nodes_path
        self.scanned_plugins = set()
    
    def scan_plugins(self) -> List[Dict]:
        """
        扫描所有插件，返回未翻译或需要更新的插件列表
        """
        plugins = []
        
        if not self.custom_nodes_path.exists():
            logger.error(f"Custom nodes path not found: {self.custom_nodes_path}")
            return plugins
        
        for item in self.custom_nodes_path.iterdir():
            if not item.is_dir():
                continue
            
            # 忽略不需要的目录
            if item.name in self.IGNORE_DIRS:
                continue
            
            # 检查是否已有翻译
            plugin_info = self._analyze_plugin(item)
            if plugin_info:
                plugins.append(plugin_info)
        
        return sorted(plugins, key=lambda x: x['name'])
    
    def _analyze_plugin(self, plugin_dir: Path) -> Dict:
        """分析单个插件"""
        info = {
            'name': plugin_dir.name,
            'path': str(plugin_dir),
            'has_node_mappings': False,
            'node_files': [],
            'translated': False,
            'translation_file': None,
            'node_count': 0,
        }
        
        # 查找包含 NODE_CLASS_MAPPINGS 的 Python 文件
        for py_file in plugin_dir.rglob("*.py"):
            if any(p in py_file.name for p in self.IGNORE_PATTERNS):
                continue
            
            try:
                content = py_file.read_text(encoding='utf-8')
                if 'NODE_CLASS_MAPPINGS' in content or 'NODE_DISPLAY_NAME_MAPPINGS' in content:
                    info['has_node_mappings'] = True
                    info['node_files'].append(str(py_file.relative_to(plugin_dir)))
            except Exception as e:
                logger.warning(f"Cannot read {py_file}: {e}")
        
        # 检查是否已有翻译文件
        trans_file = self.config.translation_nodes_path / f"{plugin_dir.name}.json"
        if trans_file.exists():
            info['translated'] = True
            info['translation_file'] = str(trans_file)
            try:
                with open(trans_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    info['node_count'] = len(data)
            except:
                pass
        
        return info if info['has_node_mappings'] else None
    
    def get_untranslated_plugins(self) -> List[Dict]:
        """获取未翻译的插件"""
        all_plugins = self.scan_plugins()
        return [p for p in all_plugins if not p['translated']]
    
    def get_outdated_plugins(self) -> List[Dict]:
        """获取可能需要更新的插件（有翻译但节点数量不匹配）"""
        # 这里可以添加更复杂的逻辑，比如比较节点数量
        outdated = []
        for plugin in self.scan_plugins():
            if plugin['translated']:
                # 重新扫描实际节点数
                actual_count = self._count_actual_nodes(Path(plugin['path']))
                if actual_count > plugin['node_count']:
                    plugin['actual_nodes'] = actual_count
                    outdated.append(plugin)
        return outdated
    
    def _count_actual_nodes(self, plugin_dir: Path) -> int:
        """统计插件实际节点数量"""
        count = 0
        for py_file in plugin_dir.rglob("*.py"):
            try:
                content = py_file.read_text(encoding='utf-8')
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Assign):
                        for target in node.targets:
                            if isinstance(target, ast.Name) and target.id == 'NODE_CLASS_MAPPINGS':
                                if isinstance(node.value, ast.Dict):
                                    count += len(node.value.keys)
            except:
                pass
        return count
