# ComfyUI Zn Translation - 中文翻译插件

## 新功能：自动检测 & AI 翻译

### 功能特点
- 🔍 **自动扫描**：一键扫描 `custom_nodes` 目录，检测所有未翻译插件
- 🤖 **AI 翻译**：使用 OpenAI API 自动翻译节点名称、参数、输出
- 📚 **术语词典**：内置 200+ 专业术语，确保翻译一致性
- 🔄 **实时监控**：可选后台监控，新插件安装后自动翻译
- 🛡️ **安全合并**：不会覆盖用户手动修改的翻译

### 安装
```bash
cd ComfyUI/custom_nodes
git clone https://github.com/heyzne/comfyui-Zn-translation.git
cd comfyui-Zn-translation
pip install -r requirements.txt  # 安装依赖
