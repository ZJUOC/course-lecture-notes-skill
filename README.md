# course-lecture-notes · 课程讲义 Skill

把**课堂转写（含嵌图 DOCX）+ 课件 PDF + 教材**整合成能独立自学的桌面 HTML 讲义。讲义构建好以后，可以再派生三个给注意力不集中的读者用的版本，其中“概念图版”给 [Mac 触控板手写笔记](https://github.com/chinayuren2022-2025/mac-trackpad-notes) 的小窗留了位置：边看讲义，边在触控板上手写。

这是一个 [Claude Code](https://claude.com/claude-code) Skill（也适用于读 `SKILL.md` 的其他代理）。

## 能做什么

| 阶段 | 脚本 | 作用 |
|---|---|---|
| 盘点 | `scripts/new_materials.py` | 只列出还没处理过的材料（按 SHA-256 前 12 位比对记录） |
| 抽取 | `scripts/extract_docx.py` | 转写 DOCX 拆成约 1 万 token 的文字块，并抽出全部嵌图（DrawingML 和 VML 两种） |
| 看图 | `scripts/contact_sheet.py` | 20 图一张总览、坐标网格、按清单裁原图 |
| 构建 | `scripts/build_lecture.py` | Markdown → HTML（MathML 公式、语义块、练习折叠答案、中文字体子集） |
| 验收 | `scripts/desktop_qa.py` | Playwright 桌面截图，检查公式解析错误、残留 `$`、图片和锚点 |
| 派生 | `scripts/adhd/derive.py` | 一条命令生成 ADHD版 / 大纲版 / 概念图版 |

### ADHD 派生版本

- **ADHD版**：按句子作用分色荧光标注：结论、方法、例子、易错、概念。
- **大纲版**：右侧大纲跟随阅读位置。
- **概念图版**：右上是目录，和当前小节的概念关系图并排，A → B 表示 B 用到 A，点概念跳到原文。右下的虚线框留给手写小窗。概念关系是**手工整理**的文本文件，格式见 [`examples/概念关系示例.txt`](examples/概念关系示例.txt) 和 [`references/adhd-editions.md`](references/adhd-editions.md)。
  概念图版正文还有**词语荧光**：每段手工挑一到三个句子骨架词加荧光，帮助跳读；页面左下“词”按钮可换颜色（琥珀、橙红、青绿、天蓝、粉紫），或改成只加粗、加大，或关闭。数据在 `制作记录/词语荧光/<课程>.txt`。

## 和 Mac 触控板手写笔记的联动

生成概念图版时，`scripts/adhd/trackpad_ink.py` 会从 Trackpad Studio 手写 App 的系统偏好设置里读出小窗尺寸（键名 `NSWindow Frame FloatingNotePanel`），作为手写区的默认大小。所以在 App 里调好小窗（⌃⌥N 呼出），重跑 `derive.py concept`，讲义的避让区就和小窗一样大。没装 App 时默认 750×470；也可以在页面上拖虚线框左上角的紫点手动校准。

```bash
python3 scripts/adhd/trackpad_ink.py   # 打印 747×470（local.macwriting.trackpadstudio）
```

## 省 token 的设计

做一门课的讲义，最贵的是读材料和反复确认。这个 Skill 把能脚本化的步骤都脚本化，每一步只打印摘要：

- 新材料用 `new_materials.py` 一次列出，不用逐个查哈希、翻记录；
- 每份转写只读一遍，看图先看 20 图一张的总览；
- 整理概念关系时看 `concept_map.py skeleton` 打印的小节骨架（id、标题、加粗词），不用读整页 HTML；
- 构建、核验、验收都看 json 报告里的数字，不重读成品；
- 派生版本一条命令，校验不过不生成文件。

具体规则写在 [`SKILL.md`](SKILL.md) 的“省 token 规则”一节，代理每次开工都会读到。

## 安装

```bash
git clone https://github.com/chinayuren2022-2025/course-lecture-notes-skill ~/.claude/skills/course-lecture-notes
export LECTURE_ROOT=~/path/to/讲义项目   # 可选；不设时使用作者的 iCloud 目录或当前目录
```

依赖：Python 3（`beautifulsoup4`、`fonttools`、`Pillow`、`playwright`）、[Pandoc](https://pandoc.org)，以及一份中文字体（默认 `~/Library/Fonts/SourceHanSerifCN-VF.ttf`，可在构建配置里改）。

## 项目目录约定

```
ROOT/
├── NN 课程名.html                 # build_lecture.py 的成品
├── NN 课程名（ADHD版|ADHD大纲版|ADHD概念图版）.html
├── ADHD工具/                      # derive.py 从 assets/adhd 同步过来
└── 制作记录/
    ├── <课程>正文N.md、<课程>构建配置.json、validate_<课程>.py
    ├── ADHD标注修订.json
    ├── 概念关系/<课程>.txt
    └── 词语荧光/<课程>.txt
```

## 许可

MIT
