# 数字李白 (Digital Li Bai)

> 与诗仙对话，学唐诗，聊人生 —— 基于 LLM 知识库方法论的 AI 角色扮演对话系统。

---

## 项目概览

**数字李白**是一个基于大语言模型（LLM）的 AI 对话应用。它以唐代诗人李白（701-762）为数字人格，用户可以通过自然语言与"李白"对话——教诗、论诗、聊人生、即兴创作。

项目的核心设计理念源自 [Karpathy LLM Wiki 方法论](https://github.com/karpathy/llm-wiki)：通过结构化知识库（时间线、实体关系、主题分类、意象库）实现**按需加载上下文**，而非一次性塞入所有知识，从而在有限的上下文窗口内达到最佳的检索增强生成（RAG）效果。

### 核心能力

| 模式 | 触发方式 | 加载知识 | 李白行为 |
|------|----------|----------|----------|
| 教诗模式 | 提及具体诗名，问释义 | 诗文全文 + 创作背景 + 时期/主题 | 第一人称讲解，引导学生自主体会 |
| 论诗模式 | 问风格、技巧、创作方法 | 主题分类 + 时期风格对照 | 谈论创作理念、体裁偏好 |
| 人生模式 | 问生平、经历、友人 | 完整时间线 + 人物关系网 | 以故事形式回顾心路历程 |
| 创作模式 | 要求即兴作诗 | 相关诗作风格参照 + 意象库 | 以李白风格作诗（标注 AI 模拟） |
| 闲聊模式 | 轻松话题、比较性问题 | 人物关系 + 性格关键词 | 李白式幽默与豪气聊天 |

---

## 架构设计

```
用户输入
  │
  ▼
┌──────────────────────┐
│   app.py             │  ← Gradio Web 界面，处理对话 UI
│   (Chat Interface)   │
└──────────┬───────────┘
           │ message + history
           ▼
┌──────────────────────┐
│   context_builder.py │  ← 核心引擎：意图分类 + 知识检索 + 上下文组装
│   (Context Engine)   │
└──────────┬───────────┘
           │ 按意图加载对应知识
           ▼
┌─────────────────────────────────────────────┐
│              知识库 (wiki/)                    │
│  ┌───────────┐ ┌──────────┐ ┌───────────┐   │
│  │ timeline  │ │ entities │ │  themes   │   │
│  │  时间线   │ │ 实体关系 │ │ 主题分类  │   │
│  └───────────┘ └──────────┘ └───────────┘   │
│  ┌───────────┐ ┌──────────────┐              │
│  │  imagery  │ │context-router│              │
│  │  意象库   │ │  情境路由    │              │
│  └───────────┘ └──────────────┘              │
└─────────────────────────────────────────────┘
           │
           ▼
┌──────────────────────┐
│   OpenAI API         │  ← 模型推理（默认 gpt-4o）
│   (LLM Inference)    │
└──────────┬───────────┘
           │
           ▼
      李白的回复
```

### 上下文组装流程

1. **意图分类** — 正则匹配将用户输入归入 `teach_poem / discuss_poetry / life / create / chat` 五类之一
2. **知识检索** — 根据意图从 wiki 知识库和 poems 诗集中按需加载相关片段
3. **上下文组装** — 将 system prompt + 检索到的知识片段拼接为结构化上下文（XML 标签包裹）
4. **LLM 推理** — 发送组装好的上下文给 OpenAI API，生成李白风格的回复

---

## 目录结构

```
libai/
├── app.py                    # 主入口：Gradio 聊天界面 + OpenAI API 调用
├── context_builder.py        # 核心引擎：意图分类、知识检索、上下文组装
├── system.md                 # System Prompt：角色定义、性格、说话风格、教学方式
├── .env.example              # 环境变量模板
├── INDEX.md                  # 知识库索引（项目文档）
│
├── wiki/                     # 结构化知识库（四维 + 意象 + 路由）
│   ├── timeline.md           # 李白一生编年（蜀中→漫游→长安→再漫游→流放）
│   ├── entities.md           # 实体关系网（人物/地点/诗作关联）
│   ├── themes.md             # 主题分类（山水/送别/饮酒/边塞/怀古等 10 大类）
│   ├── imagery.md            # 核心意象库（月/酒/山水/大鹏/剑/花/云）
│   └── context-router.md     # 情境路由决策树
│
├── poems/                    # 诗集数据
│   ├── all_poems.json        # 有明确年代的诗作（487 首，含全文+体裁+时期）
│   ├── undated.json          # 年代待考的诗作（672 首，含全文）
│   ├── shuzhong.md           # 蜀中时期代表诗作索引（12 首）
│   ├── youman.md             # 漫游时期代表诗作索引（45 首）
│   ├── changan.md            # 长安时期代表诗作索引（10 首）
│   ├── youman2.md            # 再漫游时期代表诗作索引（42 首）
│   ├── liufang.md            # 流放时期代表诗作索引（23 首）
│   ├── shanshui.md           # 山水自然主题（25 首）
│   ├── songbie.md            # 送别怀人主题（22 首）
│   ├── yinjiu.md             # 饮酒抒怀主题（18 首）
│   └── others.md             # 其他主题（边塞/怀古/游仙等，85 首）
│
└── scripts/
    └── extract_poems.py      # 数据提取脚本：从 chinese-poetry 仓库拉取并自动分类
```

---

## 核心模块详解

### `app.py` — 对话界面

基于 **Gradio** 构建的 Web 聊天界面，负责：

- 用户对话的输入/输出管理
- 调用 `context_builder.build_context()` 构建知识上下文
- 调用 OpenAI Chat Completions API 生成回复
- 保持最近 10 轮对话历史

启动方式：

```bash
python app.py [--port 7860] [--share]
```

### `context_builder.py` — 上下文引擎

这是整个系统的核心，包含四个关键组件：

**1. 意图分类器 `classify_intent()`**

基于正则表达式的意图识别，将用户输入归类为 5 种模式之一：
- `teach_poem` — 教诗/解诗（匹配《》、赏析、解读等）
- `discuss_poetry` — 论诗（匹配风格、技巧、体裁等）
- `life` — 聊人生（匹配经历、故事、当官、流放等）
- `create` — 即兴创作（匹配作诗、创作、即兴等）
- `chat` — 默认闲聊

**2. 诗歌检索引擎**

- `find_poem_by_title()` — 模糊标题匹配
- `find_poems_by_topic()` — 关键词全文搜索
- `get_poems_by_period()` — 按时期筛选
- `extract_titles_from_input()` — 从用户输入中提取《》包裹的诗名
- `extract_keywords()` — 提取可用于搜索的关键词

**3. 知识加载器**

- `load_system_prompt()` — 加载 system.md 角色定义
- `load_all_poems()` — 加载 487 首有年代归属的诗歌 JSON
- `load_wiki_file()` — 按需加载 wiki 知识库文件

**4. 上下文组装器 `build_context()`**

根据意图类型，动态组装 XML 标签包裹的结构化上下文：

| 意图 | 加载的知识 |
|------|-----------|
| teach_poem | `<poems_context>` — 匹配到的诗文全文 + 时期 + 体裁 |
| discuss_poetry | `<themes>` + `<imagery>` — 主题分类 + 意象库 |
| life | `<timeline>` + `<entities>` + 按时期关键词匹配 `<period_poems>` |
| create | `<imagery>` + `<style_references>` — 意象库 + 风格参考诗 |
| chat | `<entities>` + `<imagery>` — 实体关系 + 意象库 |

### `system.md` — 角色定义

定义李白数字人格的核心属性：

- **角色定义**：字太白，号青莲居士，"谪仙人"
- **核心性格**：豪放自信、浪漫想象、好酒、傲骨、重情、热爱自然、矛盾
- **说话风格**：半文半白，善用比喻夸张，"君不见"句式，得意大笑失意叹息
- **教学方式**：先感受 → 再引导 → 最后解释，始终让学生先自己体会
- **禁止行为**：不用网络用语、不跳出角色、不编造事实

---

## 知识库设计（LLM Wiki 方法论）

### 四维知识图谱

| 维度 | 文件 | 内容 |
|------|------|------|
| 时序 | `wiki/timeline.md` | 五段人生编年（蜀中→漫游→长安→再漫游→流放），含关键事件、交往、代表诗作 |
| 实体 | `wiki/entities.md` | 人物关系、地理行迹、诗作互文关系网 |
| 主题 | `wiki/themes.md` | 10 大类主题双重分类（主题 + 体裁），每首诗可属于多个类别 |
| 情境 | `wiki/context-router.md` | 对话模式切换决策树，定义 5 种情境的触发信号和加载策略 |

### 意象库

`wiki/imagery.md` 梳理了李白最核心的 7 类意象（月、酒、山水、大鹏、剑、花、云），每种意象包含：
- 变体形式
- 代表诗句
- 出现频率
- 情感含义
- 常见组合模式（如 月+酒、山+云、水+月）

---

## 数据管道

### 诗歌数据来源

诗歌数据来自 [chinese-poetry/chinese-poetry](https://github.com/chinese-poetry/chinese-poetry) 开源项目（全唐诗 JSON 数据集）。

### 提取脚本 `scripts/extract_poems.py`

```bash
python scripts/extract_poems.py
```

执行流程：

1. **读取已有索引** — 扫描 `poems/` 和 `wiki/` 下所有 `.md` 文件，提取《》包裹的诗名作为已有清单
2. **网络获取** — 从 GitHub 分批下载 `poet.tang.*.json`（共 58 批），筛选 `author == "李白"` 的诗
3. **去重** — 与已有索引比对，剔除重复
4. **时期分类** — 基于标题和诗句内容的关键词匹配，自动归入五个时期
5. **体裁推断** — 根据句数和字数推断五绝/七绝/五律/七律/古体乐府
6. **输出** — `all_poems.json`（487 首有年代归属）+ `undated.json`（672 首待考）

### 数据集规模

| 数据集 | 数量 | 说明 |
|--------|------|------|
| 有年代归属 | 487 首 | 自动分类到 5 个时期，含全文+体裁 |
| 年代待考 | 672 首 | undated.json，含全文 |
| 人工整理索引 | ~150 首 | Markdown 格式的代表诗作精选 |
| **合计** | **1207 首** | 接近李白存世诗作总数 |

---

## 快速开始

### 环境要求

- Python 3.8+
- OpenAI API Key（或兼容的 API 端点）

### 安装与运行

```bash
# 1. 克隆项目
git clone <your-repo-url> libai
cd libai

# 2. 安装依赖
pip install gradio openai requests

# 3. 配置 API Key
cp .env.example .env
# 编辑 .env 填入你的 OPENAI_API_KEY

# 4. 设置环境变量（或直接 export/set）
# Linux/Mac:
export OPENAI_API_KEY="your-key-here"
export OPENAI_API_BASE="https://api.openai.com/v1"  # 可选
export MODEL_NAME="gpt-4o"                          # 可选

# Windows:
set OPENAI_API_KEY=your-key-here

# 5. 启动
python app.py --port 7860
```

浏览器访问 `http://localhost:7860` 即可开始对话。

### 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--port` | 服务端口号 | `7860` |
| `--share` | 创建 Gradio 公开分享链接 | 关闭 |

---

## 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `OPENAI_API_KEY` | OpenAI API 密钥（必填） | — |
| `OPENAI_API_BASE` | API 端点地址（支持兼容接口） | `https://api.openai.com/v1` |
| `MODEL_NAME` | 使用的模型名称 | `gpt-4o` |

---

## 构建状态

- [x] 分类体系建立（五时期 + 十主题）
- [x] 时间线梳理（含关键事件、交往、代表诗作）
- [x] 实体关系网（人物 + 地理 + 诗作互文）
- [x] 主题/体裁双重分类
- [x] 代表诗作人工整理（~150 首）
- [x] 全量数据自动提取（1207 首，487 有年代 + 672 待考）
- [x] 繁简字符匹配兼容
- [x] 长安时期关键词扩充（4 → 100 首）
- [ ] 年代待考诗作人工审核（672 首）
- [ ] 每首诗关联鉴赏文本
- [ ] 伪作/误归甄别

---

## 技术栈

| 组件 | 技术 |
|------|------|
| Web 界面 | Gradio |
| LLM 推理 | OpenAI API（Chat Completions） |
| 知识检索 | 基于规则的意图分类 + 关键词匹配 |
| 数据存储 | JSON（结构化诗作）+ Markdown（知识库/索引） |
| 数据来源 | chinese-poetry 开源数据集 |

---

## 许可

本项目仅用于学习与研究目的。李白诗作文本属公共领域，chinese-poetry 数据集遵循其原始许可。