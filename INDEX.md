# 李白数字人格 · 知识库索引

> 基于 Karpathy LLM Wiki 方法论构建。李白存世诗作 938 首（本库从 chinese-poetry/chinese-poetry 提取 1207 首），已有明确年代归属 487 首 + 待考 672 首。

---

## 四维知识图谱

| 维度 | 文件 | 用途 |
|------|------|------|
| **时序** | [[wiki/timeline|时间线]] | 李白一生编年，按时期路由诗作 |
| **实体** | [[wiki/entities|实体关系]] | 人物/地点/诗作关系网 |
| **主题** | [[wiki/themes|主题分类]] | 诗歌主题与体裁双重分类 |
| **情境** | [[wiki/context-router|情境路由]] | 对话模式切换与话题引导 |

---

## 诗集目录

### 全量数据（从 chinese-poetry 提取）

| 文件 | 说明 | 数量 |
|------|------|------|
| `poems/all_poems.json` | 有明确年代归属的诗作（含全文） | 487 首 |
| `poems/undated.json` | 年代待考的李白诗作（含全文） | 672 首 |
| `scripts/extract_poems.py` | 提取脚本（去重 + 自动分类） | — |

### 按时期（有明确年代的 487 首）

| 时期 | 时间 | 诗作数 | JSON key |
|------|------|--------|----------|
| 漫游时期 | 725-742 | 220 | `youman` |
| 长安时期 | 742-744 | 100 | `changan` |
| 再漫游时期 | 744-755 | 85 | `youman2` |
| 流放时期 | 755-762 | 50 | `liufang` |
| 蜀中时期 | 701-725 | 32 | `shuzhong` |

### 人工整理的代表诗作索引（Markdown）

| 时期 | 文件 | 诗作数 |
|------|------|--------|
| 蜀中时期 | [[poems/shuzhong|poems/shuzhong]] | 12 |
| 漫游时期 | [[poems/youman|poems/youman]] | 45 |
| 长安时期 | [[poems/changan|poems/changan]] | 10 |
| 再漫游时期 | [[poems/youman2|poems/youman2]] | 42 |
| 流放时期 | [[poems/liufang|poems/liufang]] | 23 |

### 按主题

| 主题 | 代表诗作数 | 索引 |
|------|------------|------|
| 山水自然 | 25 | [[poems/shanshui|poems/shanshui]] |
| 送别怀人 | 22 | [[poems/songbie|poems/songbie]] |
| 饮酒抒怀 | 18 | [[poems/yinjiu|poems/yinjiu]] |
| 边塞/怀古/游仙/闺怨/咏物/乐府/自述 | 85 | [[poems/others|poems/others]] |

---

## 构建状态

- [x] 分类体系建立
- [x] 时间线梳理
- [x] 实体关系网
- [x] 主题/体裁分类
- [x] 代表诗作列表（~150 首人工整理）
- [x] 全量 1207 首从 chinese-poetry 提取（487 首有年代归属，672 首待考）
- [x] 繁简字符匹配修复
- [x] 长安时期关键词大幅扩充（4 → 100 首）
- [ ] 年代待考诗作人工审核（672 首）
- [ ] 每首诗关联鉴赏文本
- [ ] 补充伪作/误归甄别
