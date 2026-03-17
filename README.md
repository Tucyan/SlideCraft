# PPPT - JSON to PPTX Converter

PPPT 是一个将结构化 JSON 数据转换为 PowerPoint (PPTX) 文件的工具。它支持多种元素类型，包括文本、形状、图片、表格、图表、动画和过渡效果。

## 项目结构

本项目包含两个版本：

### 1. agent-ppt/ - AI 智能体版本
专为 AI 智能体（如 Claude、GPT 等）设计的版本，提供完整的 JSON 到 PPTX 转换功能。

```
agent-ppt/
├── src/pppt/           # 核心源代码
├── SKILL.md            # Skill 定义文件
├── llm_prompt.md       # JSON 格式规范文档
├── pyproject.toml      # 项目配置
└── demo.py             # 演示入口
```

### 2. web-ppt/ - 网页端用户版本
为普通用户设计的图形界面版本，支持从网页 AI 助手获取 JSON 并生成 PPTX。

```
web-ppt/
├── src/pppt/           # 核心源代码
├── dist/WebPPT.exe     # 可执行文件（Windows）
├── llm_prompt.md       # JSON 格式规范文档
├── pyproject.toml      # 项目配置
└── build.spec          # PyInstaller 打包配置
```

## 功能特性

- **文本元素**：支持多种字体、大小、颜色、对齐方式
- **形状元素**：矩形、圆形等基础形状，支持填充和边框
- **图片/SVG**：支持嵌入图片和 SVG 矢量图
- **表格**：支持单元格合并、边框样式、背景色
- **图表**：柱状图、折线图、饼图
- **动画效果**：淡入、飞入、出现等入场动画
- **页面过渡**：淡入、推进、擦除等切换效果
- **高级特性**：旋转、透明度、渐变填充

## 快速开始

### 使用 Web 版本（推荐普通用户）

1. **下载程序**
   - 获取 `web-ppt/dist/WebPPT.exe`

2. **获取 JSON 格式规范**
   - 打开 `web-ppt/llm_prompt.md`
   - 复制其中的 JSON 格式规范

3. **使用网页 AI 生成 JSON**
   - 打开豆包、千问、元宝等网页 AI
   - 粘贴格式规范并描述你的 PPT 需求
   - AI 将生成符合规范的 JSON 数据

4. **生成 PPTX**
   - 运行 `WebPPT.exe`
   - 将 JSON 粘贴到文本框中
   - 点击"验证 JSON"确认格式正确
   - 设置文件名和保存位置
   - 点击"生成 PPTX"

### 使用 Agent 版本（开发者/AI 智能体）

#### 安装

```bash
cd agent-ppt
pip install -e .
```

#### 命令行使用

```bash
python -m pppt.cli input.json -o output.pptx
```

#### 编程使用

```python
from pppt import JsonToPptxExporter

# 从字典创建
doc = {
    "version": "2.0",
    "metadata": {...},
    "theme": {...},
    "slides": [...]
}
exporter = JsonToPptxExporter(doc, "output.pptx")
exporter.run()

# 从文件创建
JsonToPptxExporter.from_json_file("input.json", "output.pptx")
```

## JSON 格式示例

```json
{
  "version": "2.0",
  "metadata": {
    "presentation_id": "demo_001",
    "title": "示例演示",
    "author": "AI Assistant",
    "language": "zh-CN"
  },
  "theme": {
    "slide_size": "16:9",
    "font_scheme": {
      "heading_font": "Microsoft YaHei",
      "body_font": "Microsoft YaHei"
    },
    "color_scheme": {
      "primary": "#2196F3",
      "secondary": "#4CAF50"
    }
  },
  "slides": [
    {
      "slide_id": "slide_1",
      "background": {
        "type": "solid",
        "color": "#FFFFFF"
      },
      "elements": [
        {
          "type": "text",
          "text": "欢迎使用 PPPT",
          "x": 100,
          "y": 100,
          "w": 800,
          "h": 100,
          "style": {
            "font_size": 48,
            "bold": true,
            "color": "#2196F3"
          }
        }
      ]
    }
  ]
}
```

## 完整 JSON 规范

详见 `llm_prompt.md` 文件，包含：
- 元数据定义
- 主题配置
- 所有元素类型的详细参数
- 动画和过渡效果配置
- 图表数据结构

## 技术架构

### 三层架构设计

1. **CompileContext** (`context.py`)
   - 中央数据类，传递画布尺寸、主题、资源等信息
   - 控制坐标转换和资源加载

2. **XML Builders** (`xml_builders/`)
   - 纯函数生成 Open XML 片段
   - 每个模块负责特定元素类型的 XML 生成

3. **OOXML Package** (`ooxml/`)
   - 写入静态 OOXML 文件
   - 组装幻灯片并打包为 ZIP (PPTX)

### 支持的元素类型

| 类型 | 说明 |
|------|------|
| text | 文本框 |
| shape | 基本形状（矩形、圆形等）|
| image | 图片 |
| svg | SVG 矢量图（自动转为 PNG）|
| group | 元素组合 |
| table | 表格 |
| chart | 图表（柱状图、折线图、饼图）|

## 开发

### 运行测试

```bash
cd agent-ppt
PYTHONPATH=src python -m pytest tests/ -v
```

### 打包 EXE

```bash
cd web-ppt
pyinstaller build.spec --clean
```

## 依赖

- Python >= 3.9
- Pillow >= 9.0（图像处理）
- cairosvg >= 2.5（可选，SVG 转换）

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！
