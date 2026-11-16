# 熊AI走（deai-walk）

去除文本中的 AI 生成痕迹，让文字更自然、更有人味。这是一个 prompt 型 Skill：主入口 `SKILL.md`，规则与词表放在 `references/`，检测脚本放在 `scripts/`。

- 作者：走跑飞
- 版本：v1.3.0
- 许可证：CC BY 4.0，全文见 [LICENSE](LICENSE)；复制、修改、分发须保留原作者署名
- 仓库：<https://github.com/tomy1314/deai-walk>

## 它能做什么

以「文字编辑」身份识别并改写 AI 写作痕迹，覆盖 22 种模式（夸大象征意义、宣传性语言、三段式法则、AI 高频词、否定式排比、解释癖、光滑叙事、匀质句式等）。改写只调整表达方式，不添加原文没有的事实，不改变原文立场。

**不承诺通过任何 AIGC 检测。** 本工具只让统计特征更接近人类写作的自然区间。

## 怎么用

放到 WorkBuddy 的 skills 目录即可被识别：

```
~/.workbuddy/skills/熊AI走/
```

说出「去 AI 味」「润色一下」「帮我改得像人写的」「过一下 AIGC 检测」等触发词即可唤起；也可以直接给文件路径或目录，要求批量处理。

执行流程六步：判断输入形态 → 判断篇幅与分块 → 检测 → 改写 → 自检 → 交付。小说/叙事文本在第二步与第三步之间多一层「叙述者定位」（谁在说／对谁说／为什么说，不占步号），并走六层检查表（字/词/句/段/场景/篇）；学术、法律、公关、文案走通用分支，改写尺度最小。

可选的机械扫描（失败时降级为人工扫描，结果不替代人工判断）：

```bash
python {SKILL_DIR}/scripts/ai_taste_scanner.py <目标文件绝对路径>
```

完整规则、触发条件、边界情况与质量自检清单见 [SKILL.md](SKILL.md)。

## 目录结构

| 路径 | 用途 |
|---|---|
| `SKILL.md` | 主入口：铁律、文件分区、六步流程、交付前自检 |
| `LICENSE` | CC BY 4.0 全文 |
| `VERSION_HASH.md` | 逐文件 SHA-256 指纹，用于版本比对 |
| `persona_overlay.md` | 可选人格覆盖层（默认不加载，仅显式要求时启用） |
| `references/` | 禁词表、22 种模式、改写规则、冲突裁决、自检清单、叙事六层检查表、真感原则与质感方案 |
| `references/novel_optional/` | 小说/叙事分支专用：叙述者定位、DNA、情感引擎 |
| `scripts/ai_taste_scanner.py` | 字/词/句层机械扫描脚本 |

> 生成期参考（动笔前读）与改稿期工具（写完用）不要混读，详见 `SKILL.md` 的「文件分区」与「边界」两节。
> `SKILL.md` 中提到的 `de-ai-flavor` 是本机镜像副本，不在本仓库内；本仓库目录为唯一权威。

## 版本校验

`VERSION_HASH.md` 记录技能内容文件的 SHA-256，任何与表中哈希不符的修改版本均非官方版。表内不含该文件自身（自引用排除），也不含 `.gitignore`、`.gitattributes`——这两个是上传时新增的仓库配置文件，不属于技能内容。

```bash
python - <<'HASHCHECK'
import hashlib, pathlib
print(hashlib.sha256(pathlib.Path("SKILL.md").read_bytes()).hexdigest())
HASHCHECK
```

## 变更记录

- 2026-11-16：公开上传（提交 `9f2158f`，18 个技能内容文件，当时未含 README）；同日补入本 README，并在 `VERSION_HASH.md` 中登记其哈希。技能规则与版本号均未改动，仍为 v1.3.0。
- 技能本身的版本沿革见 `SKILL.md` frontmatter 的 `changelog`（v1.1.0 → v1.1.1 → v1.2.0 → v1.2.1 → v1.3.0）。
