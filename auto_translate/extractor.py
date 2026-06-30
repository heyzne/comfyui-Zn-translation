"""
从 Python 文件中提取节点信息
"""

import ast
import re
from pathlib import Path
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class NodeExtractor:
    """节点信息提取器"""
    
    def __init__(self):
        self.nodes = {}
    
    def extract_from_plugin(self, plugin_dir: Path) -> Dict[str, Dict]:
        """
        从插件目录提取所有节点信息
        返回: {node_name: {title, description, inputs, widgets, outputs, category}}
        """
        self.nodes = {}
        
        for py_file in plugin_dir.rglob("*.py"):
            try:
                self._extract_from_file(py_file)
            except Exception as e:
                logger.warning(f"Error extracting from {py_file}: {e}")
        
        return self.nodes
    
    def _extract_from_file(self, py_file: Path):
        """从单个文件提取"""
        content = py_file.read_text(encoding='utf-8')
        
        # 方法1: 提取 NODE_CLASS_MAPPINGS
        self._extract_node_class_mappings(content, py_file)
        
        # 方法2: 提取 NODE_DISPLAY_NAME_MAPPINGS  
        self._extract_display_names(content)
        
        # 方法3: 通过 AST 分析类定义
        self._extract_from_ast(content, py_file)
    
    def _extract_node_class_mappings(self, content: str, py_file: Path):
        """提取 NODE_CLASS_MAPPINGS"""
        # 正则匹配简单形式
        pattern = r'NODE_CLASS_MAPPINGS\s*=\s*\{([^}]+)\}'
        matches = re.findall(pattern, content, re.DOTALL)
        
        for match in matches:
            # 解析字典内容
            pairs = re.findall(r'["\\']([^"\\']+)["\\']\\s*:\\s*([^,\\n]+)', match)
            for name, class_ref in pairs:
                name = name.strip()
                if name and name not in self.nodes:
                    self.nodes[name] = {
                        'title': name,
                        'class_name': class_ref.strip().strip('"\\'').split('.')[-1],
                        'source_file': str(py_file.name),
                        'inputs': {},
                        'widgets': {},
                        'outputs': {},
                        'description': '',
                        'category': '',
                    }
    
    def _extract_display_names(self, content: str):
        """提取显示名称"""
        pattern = r'NODE_DISPLAY_NAME_MAPPINGS\s*=\s*\{([^}]+)\}'
        matches = re.findall(pattern, content, re.DOTALL)
        
        for match in matches:
            pairs = re.findall(r'["\\']([^"\\']+)["\\']\\s*:\\s*["\\']([^"\\']+)["\\']', match)
            for node_name, display_name in pairs:
                if node_name in self.nodes:
                    self.nodes[node_name]['display_name'] = display_name
    
    def _extract_from_ast(self, content: str, py_file: Path):
        """通过 AST 分析提取更详细的信息"""
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                self._analyze_class(node, py_file)
    
    def _analyze_class(self, class_node: ast.ClassDef, py_file: Path):
        """分析类定义"""
        # 检查是否是 ComfyUI 节点类
        is_node = False
        base_names = []
        
        for base in class_node.bases:
            if isinstance(base, ast.Name):
                base_names.append(base.id)
            elif isinstance(base, ast.Attribute):
                base_names.append(base.attr)
        
        # 查找 INPUT_TYPES 方法
        input_types = None
        for item in class_node.body:
            if isinstance(item, ast.FunctionDef) and item.name == 'INPUT_TYPES':
                input_types = item
                is_node = True
                break
            # 类变量形式的 INPUT_TYPES
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name) and target.id == 'INPUT_TYPES':
                        is_node = True
                        break
        
        if not is_node:
            return
        
        class_name = class_node.name
        
        # 找到对应的节点名
        node_name = None
        for name, info in self.nodes.items():
            if info.get('class_name') == class_name:
                node_name = name
                break
        
        if not node_name:
            # 尝试从文件名推断
            node_name = class_name
        
        if node_name not in self.nodes:
            self.nodes[node_name] = {
                'title': class_name,
                'class_name': class_name,
                'source_file': str(py_file.name),
                'inputs': {},
                'widgets': {},
                'outputs': {},
                'description': '',
                'category': '',
            }
        
        # 提取 docstring 作为描述
        if class_node.body and isinstance(class_node.body[0], ast.Expr):
            if isinstance(class_node.body[0].value, ast.Constant):
                self.nodes[node_name]['description'] = class_node.body[0].value.value
        
        # 提取 RETURN_TYPES
        self._extract_return_types(class_node, node_name)
        
        # 提取 INPUT_TYPES 中的参数
        if input_types:
            self._extract_input_types(input_types, node_name)
    
    def _extract_return_types(self, class_node: ast.ClassDef, node_name: str):
        """提取输出类型"""
        for item in class_node.body:
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name) and target.id == 'RETURN_TYPES':
                        if isinstance(item.value, (ast.Tuple, ast.List)):
                            types = []
                            for elt in item.value.elts:
                                if isinstance(elt, ast.Constant):
                                    types.append(elt.value)
                                elif isinstance(elt, ast.Name):
                                    types.append(elt.id)
                            self.nodes[node_name]['outputs'] = {
                                f'output_{i}': t for i, t in enumerate(types)
                            }
                        break
    
    def _extract_input_types(self, func_node: ast.FunctionDef, node_name: str):
        """提取输入参数类型"""
        # 简化处理，提取函数体中的返回字典
        for node in ast.walk(func_node):
            if isinstance(node, ast.Dict):
                for key, value in zip(node.keys, node.values):
                    if isinstance(key, ast.Constant) and key.value == 'required':
                        if isinstance(value, ast.Dict):
                            self._extract_params(value, node_name, 'required')
                    elif isinstance(key, ast.Constant) and key.value == 'optional':
                        if isinstance(value, ast.Dict):
                            self._extract_params(value, node_name, 'optional')
                    elif isinstance(key, ast.Constant) and key.value == 'hidden':
                        if isinstance(value, ast.Dict):
                            self._extract_params(value, node_name, 'hidden')
    
    def _extract_params(self, dict_node: ast.Dict, node_name: str, param_type: str):
        """提取参数字典"""
        for key, value in zip(dict_node.keys, dict_node.values):
            if isinstance(key, ast.Constant):
                param_name = key.value
                param_info = {'type': param_type}
                
                # 尝试解析参数类型
                if isinstance(value, (ast.Tuple, ast.List)):
                    if value.elts:
                        first = value.elts[0]
                        if isinstance(first, ast.Name):
                            param_info['data_type'] = first.id
                        elif isinstance(first, ast.Constant):
                            param_info['data_type'] = first.value
                
                # 判断是 input 还是 widget
                if param_type == 'required':
                    self.nodes[node_name]['inputs'][param_name] = param_info['data_type']
                else:
                    self.nodes[node_name]['widgets'][param_name] = param_info['data_type']
    
    def get_node_summary(self, node_name: str) -> Dict:
        """获取节点摘要"""
        return self.nodes.get(node_name, {})
    
    def get_all_node_names(self) -> List[str]:
        """获取所有节点名"""
        return list(self.nodes.keys())
