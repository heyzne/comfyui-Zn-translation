"""
ComfyUI Zn Translation - Auto Translate Module
自动检测新插件并翻译节点
"""

from .scanner import PluginScanner
from .extractor import NodeExtractor
from .translator import AITranslator
from .generator import TranslationGenerator
from .config import Config

__version__ = "2.0.0"
__all__ = ['PluginScanner', 'NodeExtractor', 'AITranslator', 'TranslationGenerator', 'Config']
