"""讲义阅读器各脚本共用的路径与课程发现。

项目根目录（下称 ROOT）按顺序取：环境变量 LECTURE_ROOT → 当前目录或其上级中第一个含 制作记录/构建/ 的目录 → iCloud 默认位置。
  ROOT/NN 课程名.html                 读者打开的唯一成品（derive.py 生成）
  ROOT/制作记录/构建/底稿/NN 课程名.html  build_lecture.py 的输出（含 practice- 锚点的才算讲义）
  ROOT/制作记录/概念关系|词语荧光|智慧/   手工数据
  ROOT/资源/阅读器/                   页面用的 css/js，以本 Skill 的 assets/reader/ 为准，生成前同步
"""
import os, shutil
from pathlib import Path

SKILL = Path(__file__).resolve().parents[2]
ASSETS = SKILL / 'assets' / 'reader'
_default = Path('~/Library/Mobile Documents/com~apple~CloudDocs/Academic/高效讲义').expanduser()


def _find_root():
    if os.environ.get('LECTURE_ROOT'):
        return Path(os.environ['LECTURE_ROOT']).expanduser()
    for d in [Path.cwd(), *Path.cwd().parents]:
        if (d / '制作记录' / '构建').is_dir():
            return d
    if _default.exists():
        return _default
    raise SystemExit('找不到讲义项目：在项目目录里运行，或设 LECTURE_ROOT；新项目用 new_project.py 创建')


ROOT = _find_root().resolve()
REC = ROOT / '制作记录'
BASE = REC / '构建' / '底稿'
TOOLS = ROOT / '资源' / '阅读器'


def base(course):
    return BASE / f'{course}.html'


def courses():
    return [p.stem for p in sorted(BASE.glob('[0-9][0-9] *.html')) if 'practice-' in p.read_text()]


COURSES = courses()


def sync_assets():
    """把 Skill 里的 css/js 复制到 ROOT/资源/阅读器/（内容相同则不动）。"""
    TOOLS.mkdir(parents=True, exist_ok=True)
    for f in ASSETS.iterdir():
        dst = TOOLS / f.name
        if not dst.exists() or dst.read_bytes() != f.read_bytes():
            shutil.copy2(f, dst)
            print('同步', dst.relative_to(ROOT))
