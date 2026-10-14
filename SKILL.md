---
name: course-lecture-notes
description: 把课堂转写（含嵌图 DOCX）、课件 PDF 和教材整合成可独立自学的桌面 HTML 讲义（高效讲义项目），每门课一个页面：分色荧光，右栏切换概念关系图/大纲/荧光地图，右下给 Mac 触控板手写小窗让位。用户说“做讲义/更新讲义/接着做某门课/资料齐了可以做了/改荧光/改概念关系/重建讲义”或提到 高效讲义、转写、课件、手写区 时使用。流程以脚本为主，按“省 token 规则”执行。
---

# 课程讲义制作

ROOT = 项目根目录：环境变量 `LECTURE_ROOT`，未设时为 `~/Library/Mobile Documents/com~apple~CloudDocs/Academic/高效讲义/`。课程材料在 ROOT 的上一级 `<课程>/`，教材在 `e-Textbook/`。S = 本 Skill 的 `scripts/`。

开工前只读 ROOT 的 `AGENTS.md`，以及它指向的**本课程**的那份记录。写正文前读 `references/standards.md`（约 3k token）；改阅读页面（荧光、概念关系、智慧区、面板）前读 `references/reader.md`。

项目目录：根目录只放 `开始阅读.html`、`00 阅读指南.md` 和每门课一个 `NN 课程.html`；图片字体在 `资源/`；源稿 `制作记录/正文/`，构建配置与底稿 `制作记录/构建/`，核验 `制作记录/核验/`，旧东西进 `制作记录/归档/`。不要在根目录新建别的版本文件。

## 省 token 规则（先于一切）

1. **脚本代替探索**：新材料用 `new_materials.py <材料目录>`，只打印没处理过的文件；不要 `ls`、`shasum`、翻记录去比对。处理完用 `--mark` 登记。
2. **每份材料只读一遍**：转写按 chunk 读完，边读边记要点；之后引用自己的笔记，不回头重读。
3. **图先看总览**：contact sheet 一张 20 图，只放大关键帧。
4. **写一次，查摘要**：正文每块一次 Write；构建、核验、QA 都看脚本打印的摘要和 json 中的计数，不重读成品 HTML。改错用 `grep -n` 定位后 Edit，不整文件重读。
5. **概念关系看骨架**：`reader/concept_map.py skeleton` 只列小节 id、标题、加粗词，起草概念图用它，不读整页。
   词语荧光同理：读一行一段的纯文本导出，`keywords.py` 只看匹配数和问题。
6. **验收看数字不看图**：桌面 QA 用 `desktop_qa.py` 的 PASS；浏览器里用 DOM 读数代替截图。用户说过“验收不用做”时，跳过可选的浏览器检查。
7. **不派子代理**做讲义正文、看图、自绘图（冷启动要重读上下文，且禁止用 Haiku 等小模型）。
8. 版面改动先给草图；不在读者正在用的文件上改，生成新文件。

## 流程（按顺序，每步都有脚本）

1. **盘点材料**：`python3 $S/new_materials.py <材料目录>`。课程是否每周只上一次、中间有没有缺课，要从转写的正文日期推断。
2. **抽取转写**：`python3 $S/extract_docx.py <scratchpad>/x <docx...>`。看输出里的 `head`，核对教师和正文日期。
3. **读文字**：逐个 Read `chunk_K.txt`（每块约 1 万 token），**必须读完**；课间闲聊和噪声段快速略过。记下讲解思路、例题、口误和错误、作业线索。
4. **看图**：`python3 $S/contact_sheet.py sheets <x>/<stem>/index.json <scratchpad>/s`。手写推导、作业页面要放大看清。
5. **教材**：扫描版 PDF 用 `pdftotext` 或 OCR **只做检索和定位**；题干、公式和图一律 `pdftoppm -r 100` 渲染成图后看。
6. **定范围、建覆盖表**：只写已授课的内容；作业需要的前置概念可少量补充，并在记录里说明。
7. **备份**：构建前把旧的页面、正文 md 和入口页复制到 `ROOT/制作记录/修订前备份/<课程>v<N>/`。
8. **裁图**：`contact_sheet.py grid` 叠坐标网格定裁切框，再 `contact_sheet.py crop spec.json ROOT/资源/<课程>原图`。正文里图片写 `资源/<课程>原图/xx.png`。
9. **写正文**：`ROOT/制作记录/正文/<课程>正文N.md`，每块不超过约 25k 字符、一次写入，语法见 standards。
10. **构建**：写 `ROOT/制作记录/构建/<课程>构建配置.json`（字段见 `build_lecture.py` 顶部；`output` 写 `底稿/NN 课程.html`，`root` 写 `../..`），`python3 $S/build_lecture.py <config>`，再 `python3 $S/reader/derive.py "<课程>"` 生成根目录页面。改了 Skill 脚本时用 `build_all.py` 全部重建，并按 standards“复现”在副本里比对。
11. **数学核验**：写 `ROOT/制作记录/核验/validate_<课程>.py`，用 fractions/sympy/枚举/模拟独立复核**每个数值结论和练习答案**，输出 json 报告。
12. **桌面验收**：`python3 $S/desktop_qa.py "ROOT/NN 课程.html" ROOT/制作记录/output/playwright/<课程> <锚点id...>`，要求 `PASS: true`（含阅读面板三种视图、原文、收起）；只抽看 3—4 张截图。
13. **阅读页面数据**：先 `python3 $S/reader/concept_map.py skeleton "<课程>"`，按骨架**手工写** `ROOT/制作记录/概念关系/<课程>.txt`（没有它页面就没有“概念”视图，derive.py 会打印 ⚠）；再写 `词语荧光/<课程>.txt`、需要时写 `智慧/<课程>.txt`（格式见 reader.md），然后 `python3 $S/reader/derive.py "<课程>"`（密集荧光自动补，不用写数据）。
14. **收尾**：更新 `开始阅读.html`、`00 阅读指南.md` 中该课程那一行；写 `制作记录/NN <课程>重构记录.md`（材料哈希前 12 位、范围、纠错、练习与教材题号对照、核验结果、新经验）；在 `03 决策与修订日志.md` 末尾追加一段；更新 `AGENTS.md` 的课程状态。新经验同时补进本 Skill 的 references。Skill 改完在 Skill 目录 commit 并 `git push`（一次推到个人仓库和 ZJUOC 两个远端）。

## 交付说明

用中文告诉用户：覆盖范围，练习数量，核验结果，发现的课件或课堂错误（最重要的两三条），缺失的材料（例如作业清单），下一次课的日期。文件链接用绝对路径，空格写成 `%20`。
