# ADHD 派生版本（讲义构建后再做）

原讲义 `NN 课程.html` 不动，脚本派生三套新文件。读者正在用的版本不要直接改：要改版面时先出草图，确认后生成新的一套。

| 文件 | 内容 | 脚本 |
|---|---|---|
| `NN 课程（ADHD版）.html` | 按句子作用分色荧光标注（结论/方法/例子/易错/概念），右侧阅读地图 | `make_adhd.py` |
| `NN 课程（ADHD大纲版）.html` | 标注相同，右侧换成跟随阅读位置的概念大纲 | `make_outline.py` |
| `NN 课程（ADHD概念图版）.html` | 右上：目录 和 当前小节的概念关系图并排（1:2）；右下：留给手写小窗 | `make_concept.py` |

一条命令：`python3 $S/adhd/derive.py`（改了概念关系只跑 `derive.py concept`）。脚本先把 `assets/adhd/*.css|js` 同步到 `ROOT/ADHD工具/`，页面里的链接带内容哈希，不会读到缓存。

## 标注修订
`ROOT/制作记录/ADHD标注修订.json`：`{"句子开头若干字": "none|thesis|claim|evidence|counter|term"}`。报告在 `ADHD标注报告.json`，每类有抽样句，只看抽样就能判断规则是否跑偏。

## 概念关系（手工整理，不能自动抽取）
文件：`ROOT/制作记录/概念关系/<课程>.txt`，每节一块：

```
@小节id
概念名 | 依赖1:边标签, 依赖2 | 原文定位词
用到: 概念A, 概念B          # 练习、例题小节只写这一行
```

- 只收最基本的概念：读者要的是“有哪些概念、谁用到谁”，不要定理细节、易错点。每节 1—4 个概念为宜。
- 箭头 A → B 表示 B 用到 A。依赖必须在本节或前面的小节已经定义；跨节依赖页面上显示为“← A”。
- 依赖之间用“逗号+空格”分隔，所以 `u(x,y)` 这类名字安全；边标签里不要写“, ”。
- 定位词要在该小节原文中出现（忽略空白），点概念时跳到这里；找不到就退回小节标题（只是警告）。
- 起草流程（省 token）：
  1. `python3 $S/adhd/concept_map.py skeleton "<课程>"`：每节只列 id、标题、加粗词、语义块标题，✓ 表示已整理。看这个起草，不读整页 HTML。
  2. 一门课的 txt 一次写完。
  3. `python3 $S/adhd/concept_map.py`：校验全部课程，只打印统计和问题。
  4. `python3 $S/adhd/derive.py concept`。

## 词语荧光（手工挑选，可选）
概念图版正文里，每段给一到三个撑起句子的词（主题、转折对比、结论）加一道窄荧光，帮助跳读；不解释含义。

- 数据：`ROOT/制作记录/词语荧光/<课程>.txt`，每行 `段落前缀 || 词1 | 词2 | 词3`，按页面顺序。前缀可取段内任意一段原文（忽略空白，公式写成 `$tex$`），从上一行匹配到的段落往后找。没有这个文件的课程不加。讲义中间插入新单元时，新条目要插在 txt 里对应的位置，追加在末尾会因为顺序而全部匹配不上；行间公式会把一段切成两段，公式后的文字要用它自己的开头作前缀。
- 词不能跨公式或行内标签；已在 `<strong>` 里的词计为“原本已加粗”跳过。纯公式段、短答案段不标。
- 起草（省 token）：先把段落导出成“一行一段”的纯文本（`keywords.plain()`），一次读完，一门课写一个 txt；`python3 $S/adhd/keywords.py [课程]` 只打印匹配数和问题，按问题改词（多半是词里含公式或跨了加粗），不读页面。
- 生成：`make_concept.py` 自动调用 `keywords.apply`，输出里显示“词语荧光 N 处”。
- 样式：`concept.css` 的 `mark.kw` 与 `html[data-kw=amber|coral|green|blue|pink|bold|big|off]`；`concept.js` 在左下圆点前加“词”按钮和弹出菜单，选择记在页面状态 `st.kw`。

### 密集荧光（自动，默认开）
用户反馈：只有每段一到三个词仍然读不下去，要“每句话隔几个词就有标记”，而且不必有严格的意义。所以在手工词语荧光之后，`dense.py` 按分句自动补浅一档的荧光 `mark.kw2`：

- 按中文标点切分句，公式、加粗、已有荧光不动；jieba 分词，名词、动名词、实义动词、成语优先，相邻名词合并；加粗术语、概念关系里的概念名、手工荧光词作为词典并加分。
- 密度：分句约每 6 个汉字一处，最多 4 处；紧挨已有标记的短分句少标一个。复变约每 14 字一处（加上手工词更密）。
- 不需要数据文件，没写词语荧光 txt 的课程也会有；`LECTURE_DENSE=0` 时不生成。试跑：`python3 $S/adhd/dense.py <课程>` 只打印统计和样例。
- 页面：左下“词”按钮旁的“密”按钮开关密集荧光（`st.kwd`，`html[data-kwd=sparse]` 时 kw2 不显示）；“词”菜单的颜色、加粗、加大、关闭对两档都生效。

## 手写区与 Mac 触控板手写笔记
概念图版右下的虚线框给 [Mac 触控板手写笔记（Trackpad Studio 手写）](https://github.com/chinayuren2022-2025/mac-trackpad-notes) 的小窗（⌃⌥N 呼出）让位。

- `make_concept.py` 生成时调用 `trackpad_ink.py`，从 App 的 defaults（`NSWindow Frame FloatingNotePanel`）读出小窗宽高，写进页面 `data-ink="宽x高"` 作为默认值。没装 App 或读不到时用 750×470。
- 读者在页面上拖虚线框左上角的紫点会覆盖默认值（按页面记在 localStorage）；双击紫点回到小窗尺寸。
- 改了小窗大小后，重跑 `derive.py concept` 即可同步。

## 已知的坑
1. 内置浏览器窗格隐藏时不派发 scroll 事件、暂停 requestAnimationFrame，截图是空白。滚动跟随用 setTimeout 节流，并在 scrollend、load 时再同步一次；测试时 `dispatchEvent(new Event('scroll'))`，用 DOM 读数（getBoundingClientRect、类名）代替截图。
2. 本地预览端口 8765 可能被别的程序占用，换端口自己起 `python3 -m http.server`，测完关掉。
3. 测完清掉 localStorage 里 `adhd-` 开头的键，免得测试状态留给读者。
