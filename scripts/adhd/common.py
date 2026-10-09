"""ADHD 派生版本共用的路径与课程发现。

项目根目录（下称 ROOT）按顺序取：环境变量 LECTURE_ROOT → iCloud 默认位置 → 当前目录。
讲义成品：ROOT/NN 课程名.html（含 practice- 锚点的才算讲义）；手工数据在 ROOT/制作记录/。
样式脚本以本 Skill 的 assets/adhd/ 为准，生成前同步到 ROOT/ADHD工具/。
"""
import os, shutil
from pathlib import Path

SKILL = Path(__file__).resolve().parents[2]
ASSETS = SKILL / 'assets' / 'adhd'
_default = Path('~/Library/Mobile Documents/com~apple~CloudDocs/Academic/高效讲义').expanduser()
ROOT = Path(os.environ.get('LECTURE_ROOT') or (_default if _default.exists() else Path.cwd())).resolve()
REC = ROOT / '制作记录'
TOOLS = ROOT / 'ADHD工具'


def courses():
    out = []
    for p in sorted(ROOT.glob('[0-9][0-9] *.html')):
        if '（' not in p.stem and 'practice-' in p.read_text():
            out.append(p.stem)
    return out


COURSES = courses()


def sync_assets():
    """把 Skill 里的 css/js 复制到 ROOT/ADHD工具/（内容相同则不动）。"""
    TOOLS.mkdir(exist_ok=True)
    for f in ASSETS.iterdir():
        dst = TOOLS / f.name
        if not dst.exists() or dst.read_bytes() != f.read_bytes():
            shutil.copy2(f, dst)
            print('同步', dst.name)
