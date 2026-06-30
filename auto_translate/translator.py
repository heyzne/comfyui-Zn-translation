"""
AI 翻译核心 - 使用 OpenAI API 翻译节点信息
"""

import json
import time
from typing import Dict, List, Optional
import logging
import os

logger = logging.getLogger(__name__)

class AITranslator:
    """AI 翻译器"""
    
    # 常用 ComfyUI 术语词典（预定义，确保翻译一致性）
    TERM_DICTIONARY = {
        # 数据类型
        "IMAGE": "图像",
        "MASK": "遮罩",
        "LATENT": "潜空间",
        "MODEL": "模型",
        "CLIP": "CLIP",
        "VAE": "VAE",
        "CONDITIONING": "条件",
        "INT": "整数",
        "FLOAT": "浮点数",
        "STRING": "字符串",
        "BOOLEAN": "布尔值",
        
        # 常用操作
        "Load": "加载",
        "Save": "保存",
        "Preview": "预览",
        "Sampler": "采样器",
        "Upscale": "放大",
        "Resize": "调整大小",
        "Crop": "裁剪",
        "Blur": "模糊",
        "Sharpen": "锐化",
        "Denoise": "降噪",
        "Encode": "编码",
        "Decode": "解码",
        "Convert": "转换",
        "Combine": "合并",
        "Split": "拆分",
        "Batch": "批量",
        "Empty": "空",
        "Random": "随机",
        "Seed": "种子",
        "Prompt": "提示词",
        "Positive": "正向",
        "Negative": "反向",
        "Strength": "强度",
        "Scale": "缩放",
        "Width": "宽度",
        "Height": "高度",
        "Steps": "步数",
        "CFG": "CFG",
        "Scheduler": "调度器",
        "Denoising": "降噪",
        "Mask": "遮罩",
        "Image": "图像",
        "Video": "视频",
        "Audio": "音频",
        "Text": "文本",
        "Number": "数字",
        "Color": "颜色",
        "Position": "位置",
        "Rotation": "旋转",
        "Flip": "翻转",
        "Rotate": "旋转",
        "Translate": "平移",
        "Transform": "变换",
        "Filter": "滤镜",
        "Effect": "效果",
        "Blend": "混合",
        "Composite": "合成",
        "Layer": "图层",
        "Mask": "蒙版",
        "Alpha": "透明",
        "Threshold": "阈值",
        "Invert": "反转",
        "Grow": "扩展",
        "Shrink": "收缩",
        "Feather": "羽化",
        "Smooth": "平滑",
        "Erode": "腐蚀",
        "Dilate": "膨胀",
        "Outline": "描边",
        "Fill": "填充",
        "Stroke": "描边",
        "Gradient": "渐变",
        "Pattern": "图案",
        "Texture": "纹理",
        "Noise": "噪点",
        "Pixel": "像素",
        "Vector": "矢量",
        "Curve": "曲线",
        "Path": "路径",
        "Shape": "形状",
        "Rectangle": "矩形",
        "Circle": "圆形",
        "Ellipse": "椭圆",
        "Polygon": "多边形",
        "Line": "线条",
        "Point": "点",
        "Area": "区域",
        "Region": "区域",
        "Selection": "选区",
        "Channel": "通道",
        "Histogram": "直方图",
        "Levels": "色阶",
        "Curves": "曲线",
        "Brightness": "亮度",
        "Contrast": "对比度",
        "Saturation": "饱和度",
        "Hue": "色相",
        "Color Balance": "色彩平衡",
        "Exposure": "曝光",
        "Highlights": "高光",
        "Shadows": "阴影",
        "Midtones": "中间调",
        "White Balance": "白平衡",
        "Temperature": "色温",
        "Tint": "色调",
        "Vibrance": "自然饱和度",
        "Clarity": "清晰度",
        "Dehaze": "去雾",
        "Vignette": "暗角",
        "Grain": "颗粒",
        "Fringe": "边缘",
        "Chromatic": "色差",
        "Aberration": "畸变",
        "Distortion": "畸变",
        "Perspective": "透视",
        "Lens": "镜头",
        "Camera": "相机",
        "Light": "灯光",
        "Shadow": "阴影",
        "Reflection": "反射",
        "Refraction": "折射",
        "Ambient": "环境",
        "Diffuse": "漫射",
        "Specular": "高光",
        "Glossy": "光泽",
        "Metallic": "金属",
        "Roughness": "粗糙度",
        "Normal": "法线",
        "Bump": "凹凸",
        "Displacement": "置换",
        "Occlusion": "遮挡",
        "Emission": "自发光",
        "Subsurface": "次表面",
        "Scattering": "散射",
        "Absorption": "吸收",
        "Transparency": "透明",
        "Refraction": "折射",
        "Caustics": "焦散",
        "Global Illumination": "全局光照",
        "Ambient Occlusion": "环境光遮蔽",
        "Ray Tracing": "光线追踪",
        "Path Tracing": "路径追踪",
        "Photon": "光子",
        "Radiosity": "辐射度",
        "Irradiance": "辐照度",
        "Luminance": "亮度",
        "Chromaticity": "色度",
        "Luma": "亮度",
        "Chroma": "色度",
        "Keying": "抠像",
        "Matting": "遮罩提取",
        "Rotoscoping": "逐帧抠像",
        "Tracking": "跟踪",
        "Stabilization": "稳定",
        "Motion": "运动",
        "Optical Flow": "光流",
        "Warp": "扭曲",
        "Morph": "变形",
        "Liquify": "液化",
        "Mesh": "网格",
        "Lattice": "晶格",
        "Bones": "骨骼",
        "Rigging": "绑定",
        "Skinning": "蒙皮",
        "Animation": "动画",
        "Keyframe": "关键帧",
        "Tweening": "补间",
        "Easing": "缓动",
        "Interpolation": "插值",
        "Extrapolation": "外推",
        "Loop": "循环",
        "Ping-pong": "往返",
        "Reverse": "反转",
        "Speed": "速度",
        "Time": "时间",
        "Frame": "帧",
        "Rate": "速率",
        "Duration": "时长",
        "Timeline": "时间轴",
        "Sequence": "序列",
        "Clip": "片段",
        "Track": "轨道",
        "Layer": "图层",
        "Composition": "合成",
        "Precompose": "预合成",
        "Nest": "嵌套",
        "Group": "编组",
        "Ungroup": "解组",
        "Merge": "合并",
        "Join": "连接",
        "Append": "追加",
        "Prepend": "前置",
        "Insert": "插入",
        "Delete": "删除",
        "Remove": "移除",
        "Clear": "清除",
        "Reset": "重置",
        "Default": "默认",
        "Custom": "自定义",
        "Preset": "预设",
        "Template": "模板",
        "Style": "样式",
        "Theme": "主题",
        "Mode": "模式",
        "Type": "类型",
        "Format": "格式",
        "Quality": "质量",
        "Resolution": "分辨率",
        "Size": "尺寸",
        "Aspect Ratio": "宽高比",
        "Orientation": "方向",
        "Portrait": "纵向",
        "Landscape": "横向",
        "Square": "正方形",
        "Panorama": "全景",
        "Fisheye": "鱼眼",
        "Wide Angle": "广角",
        "Telephoto": "长焦",
        "Macro": "微距",
        "Depth": "景深",
        "Focus": "焦点",
        "Aperture": "光圈",
        "Shutter": "快门",
        "ISO": "ISO",
        "Exposure": "曝光",
        "HDR": "HDR",
        "RAW": "RAW",
        "TIFF": "TIFF",
        "PNG": "PNG",
        "JPEG": "JPEG",
        "GIF": "GIF",
        "BMP": "BMP",
        "WEBP": "WEBP",
        "SVG": "SVG",
        "PDF": "PDF",
        "MP4": "MP4",
        "MOV": "MOV",
        "AVI": "AVI",
        "MKV": "MKV",
        "WMV": "WMV",
        "FLV": "FLV",
        "MP3": "MP3",
        "WAV": "WAV",
        "AAC": "AAC",
        "FLAC": "FLAC",
        "OGG": "OGG",
        "MIDI": "MIDI",
    }
    
    def __init__(self, api_key: str = None, api_base: str = None, model: str = None):
        from .config import Config
        self.config = Config()
        
        self.api_key = api_key or self.config.get('api_key')
        self.api_base = api_base or self.config.get('api_base')
        self.model = model or self.config.get('model')
        
        self.client = None
        self._init_client()
    
    def _init_client(self):
        """初始化 OpenAI 客户端"""
        if not self.api_key:
            logger.warning("No API key configured, translation will be skipped")
            return
        
        try:
            from openai import OpenAI
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.api_base
            )
        except ImportError:
            logger.error("openai package not installed. Run: pip install openai")
            raise
    
    def translate_nodes(self, nodes: Dict[str, Dict]) -> Dict[str, Dict]:
        """
        批量翻译节点信息
        返回翻译后的节点字典
        """
        if not self.client:
            logger.warning("AI translator not initialized, returning original names")
            return self._fallback_translate(nodes)
        
        translated = {}
        batch = []
        batch_names = []
        
        for node_name, node_info in nodes.items():
            # 先尝试术语词典翻译
            dict_result = self._translate_with_dictionary(node_name, node_info)
            if dict_result:
                translated[node_name] = dict_result
                continue
            
            batch.append((node_name, node_info))
            batch_names.append(node_name)
            
            # 批量处理
            if len(batch) >= self.config.get('batch_size', 10):
                results = self._translate_batch(batch)
                translated.update(results)
                batch = []
                batch_names = []
        
        # 处理剩余
        if batch:
            results = self._translate_batch(batch)
            translated.update(results)
        
        return translated
    
    def _translate_with_dictionary(self, node_name: str, node_info: Dict) -> Optional[Dict]:
        """使用术语词典翻译"""
        # 检查节点名是否完全匹配词典
        if node_name in self.TERM_DICTIONARY:
            return self._create_translation(node_name, self.TERM_DICTIONARY[node_name], node_info)
        
        # 尝试拆分翻译
        parts = self._split_node_name(node_name)
        translated_parts = []
        all_found = True
        
        for part in parts:
            if part in self.TERM_DICTIONARY:
                translated_parts.append(self.TERM_DICTIONARY[part])
            else:
                all_found = False
                break
        
        if all_found and translated_parts:
            translated_name = ''.join(translated_parts)
            return self._create_translation(node_name, translated_name, node_info)
        
        return None
    
    def _split_node_name(self, name: str) -> List[str]:
        """拆分节点名"""
        # 按空格、下划线、驼峰命名拆分
        import re
        # 处理驼峰命名
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\\1 \\2', name)
        s2 = re.sub('([a-z0-9])([A-Z])', r'\\1 \\2', s1)
        # 按空格和下划线拆分
        parts = re.split(r'[\\s_]+', s2)
        return [p for p in parts if p]
    
    def _create_translation(self, original: str, translated_title: str, node_info: Dict) -> Dict:
        """创建翻译条目"""
        result = {
            'title': translated_title,
            'inputs': {},
            'widgets': {},
            'outputs': {},
        }
        
        # 翻译输入
        for key, value in node_info.get('inputs', {}).items():
            trans_key = self.TERM_DICTIONARY.get(key, key)
            result['inputs'][key] = trans_key
        
        # 翻译参数
        for key, value in node_info.get('widgets', {}).items():
            trans_key = self.TERM_DICTIONARY.get(key, key)
            result['widgets'][key] = trans_key
        
        # 翻译输出
        for key, value in node_info.get('outputs', {}).items():
            if isinstance(value, str):
                trans_val = self.TERM_DICTIONARY.get(value, value)
                result['outputs'][key] = trans_val
            else:
                result['outputs'][key] = key
        
        # 描述
        if self.config.get('translate_descriptions') and node_info.get('description'):
            result['description'] = node_info['description']  # 描述可以后续翻译
        
        return result
    
    def _translate_batch(self, batch: List[tuple]) -> Dict[str, Dict]:
        """批量翻译"""
        if not batch:
            return {}
        
        # 构建提示
        nodes_desc = []
        for i, (name, info) in enumerate(batch):
            desc = f"{i+1}. {name}"
            if info.get('display_name'):
                desc += f" (display: {info['display_name']})"
            if info.get('description'):
                desc += f" - {info['description'][:100]}"
            nodes_desc.append(desc)
        
        prompt = f"""你是一个 ComfyUI 插件翻译专家。请将以下 ComfyUI 节点名称翻译成中文，保持简洁专业。

规则：
1. 节点名称翻译要准确、专业，符合图形图像/AI领域术语
2. 参数名(inputs/widgets)翻译要简洁
3. 输出类型(outputs)保持技术术语或适当翻译
4. 返回严格的JSON格式

待翻译节点：
{chr(10).join(nodes_desc)}

请返回JSON格式：
{{
  "节点原名1": {{
    "title": "中文标题",
    "inputs": {{"原参数名": "中文参数名"}},
    "widgets": {{"原参数名": "中文参数名"}},
    "outputs": {{"output_0": "中文输出名"}}
  }},
  ...
}}

注意：
- 只返回JSON，不要其他文字
- 如果某个节点无法翻译，保持原样
- 参数名翻译要简短，不超过6个汉字
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional ComfyUI plugin translator. Output only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=4000
            )
            
            content = response.choices[0].message.content
            
            # 清理JSON
            content = self._extract_json(content)
            result = json.loads(content)
            
            # 验证并补充
            validated = {}
            for name, info in batch:
                if name in result and isinstance(result[name], dict):
                    validated[name] = self._validate_translation(name, result[name], info)
                else:
                    # 使用回退翻译
                    validated[name] = self._fallback_single(name, info)
            
            return validated
            
        except Exception as e:
            logger.error(f"Batch translation failed: {e}")
            # 回退：逐个简单翻译
            return {name: self._fallback_single(name, info) for name, info in batch}
    
    def _extract_json(self, content: str) -> str:
        """从响应中提取JSON"""
        # 查找JSON块
        start = content.find('{')
        end = content.rfind('}')
        if start != -1 and end != -1:
            return content[start:end+1]
        return content
    
    def _validate_translation(self, name: str, trans: Dict, info: Dict) -> Dict:
        """验证翻译结果"""
        result = {
            'title': trans.get('title', name),
            'inputs': {},
            'widgets': {},
            'outputs': {},
        }
        
        # 确保所有原始参数都有对应
        for key in info.get('inputs', {}):
            result['inputs'][key] = trans.get('inputs', {}).get(key, key)
        
        for key in info.get('widgets', {}):
            result['widgets'][key] = trans.get('widgets', {}).get(key, key)
        
        for key in info.get('outputs', {}):
            result['outputs'][key] = trans.get('outputs', {}).get(key, key)
        
        return result
    
    def _fallback_single(self, name: str, info: Dict) -> Dict:
        """单个节点的回退翻译"""
        return self._create_translation(name, name, info)
    
    def _fallback_translate(self, nodes: Dict) -> Dict:
        """无API时的回退翻译（使用词典）"""
        result = {}
        for name, info in nodes.items():
            dict_result = self._translate_with_dictionary(name, info)
            if dict_result:
                result[name] = dict_result
            else:
                result[name] = self._fallback_single(name, info)
        return result
    
    def translate_text(self, text: str, source_lang: str = "en", target_lang: str = "zh") -> str:
        """翻译任意文本"""
        if not self.client or not text:
            return text
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": f"You are a translator. Translate from {source_lang} to {target_lang}. Keep technical terms accurate."},
                    {"role": "user", "content": text}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Text translation failed: {e}")
            return text
