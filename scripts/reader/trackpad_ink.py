"""读取 Trackpad Studio 手写（Mac 触控板手写笔记）小窗的尺寸，给讲义页面的手写区当默认值。

小窗用 NSWindow 的 autosave 名 FloatingNotePanel 记住位置，存在 App 的 defaults 里：
  "NSWindow Frame FloatingNotePanel" = "x y w h 屏x 屏y 屏w 屏h "
用法：python3 trackpad_ink.py        打印 宽×高（读不到时打印默认值并说明）
项目主页：https://github.com/chinayuren2022-2025/mac-trackpad-notes
"""
import re, subprocess

DOMAINS = ('local.macwriting.trackpadstudio', 'com.zaynjarvis.trackpadstudio', 'TrackpadStudio')
DEFAULT = (750, 470)


def ink_size():
    """返回 (宽, 高, 来源)。小窗至少 300×120，否则视为无效。"""
    for d in DOMAINS:
        try:
            v = subprocess.run(['defaults', 'read', d, 'NSWindow Frame FloatingNotePanel'],
                               capture_output=True, text=True, timeout=5).stdout
        except (OSError, subprocess.TimeoutExpired):
            return (*DEFAULT, '默认')
        nums = [int(float(x)) for x in re.findall(r'-?\d+(?:\.\d+)?', v)]
        if len(nums) >= 4 and nums[2] >= 300 and nums[3] >= 120:
            return nums[2], nums[3], d
    return (*DEFAULT, '默认')


if __name__ == '__main__':
    w, h, src = ink_size()
    print(f'{w}×{h}（{src}）')
