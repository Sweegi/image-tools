#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
手机屏幕替换工具

将手机模板图片（白色空白屏幕）中的屏幕区域替换为指定的壁纸图片。
- 自动检测屏幕白色区域，边缘使用亮度渐变 alpha 混合，无白边
- 壁纸以 cover 模式填充，不留白边
- 输出保持原图分辨率，无损 PNG

用法:
    python phone_screen_replace.py <壁纸图片> [-p 手机模板] [-o 输出路径]

示例:
    python phone_screen_replace.py wallpaper.jpg
    python phone_screen_replace.py wallpaper.jpg -p my_phone.png -o result.png
"""

import argparse
import numpy as np
from pathlib import Path
from PIL import Image
from scipy import ndimage
from scipy.ndimage import binary_dilation

DEFAULT_PHONE_TEMPLATE = Path(__file__).parent / 'phone_template.png'


def find_screen_mask(phone_img: Image.Image) -> tuple[np.ndarray, tuple[int, int, int, int]]:
    """
    自动检测手机图片中的屏幕区域，返回精确掩码和边界框。

    算法：
    1. 定位手机边框（深色像素），确定手机在图中的中心坐标
    2. 对亮白像素做连通域标记，从中心找到屏幕所在连通域
    3. 返回布尔掩码（全图尺寸）及其边界框 (left, top, right, bottom)
    """
    arr = np.array(phone_img.convert('RGB'))
    h, w = arr.shape[:2]

    is_dark = (arr[:, :, 0] < 80) & (arr[:, :, 1] < 80) & (arr[:, :, 2] < 80)
    dark_rows = np.where(is_dark.any(axis=1))[0]
    dark_cols = np.where(is_dark.any(axis=0))[0]

    if len(dark_rows) == 0 or len(dark_cols) == 0:
        raise ValueError("未检测到手机边框，请确认输入图片包含深色手机边框")

    center_y = (int(dark_rows.min()) + int(dark_rows.max())) // 2
    center_x = (int(dark_cols.min()) + int(dark_cols.max())) // 2

    is_bright = (arr[:, :, 0] > 240) & (arr[:, :, 1] > 240) & (arr[:, :, 2] > 240)
    labeled, _ = ndimage.label(is_bright)

    screen_label = int(labeled[center_y, center_x])

    if screen_label == 0:
        found = False
        for offset in range(1, 100):
            for dy, dx in [(0, offset), (0, -offset), (offset, 0), (-offset, 0),
                           (offset, offset), (-offset, -offset), (offset, -offset), (-offset, offset)]:
                ny, nx = center_y + dy, center_x + dx
                if 0 <= ny < h and 0 <= nx < w and labeled[ny, nx] != 0:
                    screen_label = int(labeled[ny, nx])
                    found = True
                    break
            if found:
                break

    if screen_label == 0:
        raise ValueError("未能在图片中心附近找到白色屏幕区域，请检查输入图片")

    screen_mask = labeled == screen_label
    rows = np.where(screen_mask.any(axis=1))[0]
    cols = np.where(screen_mask.any(axis=0))[0]

    bounds = (int(cols.min()), int(rows.min()), int(cols.max()), int(rows.max()))
    return screen_mask, bounds


def crop_wallpaper_to_ratio(wallpaper: Image.Image, ratio: float = 9 / 19) -> Image.Image:
    """
    将壁纸裁剪为指定宽高比（默认 9:19）。

    保持原图高度不变，按高度计算目标宽度后居中裁剪。
    若目标宽度超过原图宽度（原图太窄），则直接返回原图，不做拉伸。
    """
    target_w = int(wallpaper.height * ratio)

    if target_w >= wallpaper.width:
        return wallpaper

    crop_x = (wallpaper.width - target_w) // 2
    return wallpaper.crop((crop_x, 0, crop_x + target_w, wallpaper.height))


def fit_wallpaper_to_screen(wallpaper: Image.Image, screen_w: int, screen_h: int) -> Image.Image:
    """
    将壁纸以 cover 模式缩放并居中裁剪，使其完整填充屏幕区域，不留白边。
    """
    wp_ratio = wallpaper.width / wallpaper.height
    screen_ratio = screen_w / screen_h

    if wp_ratio > screen_ratio:
        new_h = screen_h
        new_w = int(new_h * wp_ratio)
    else:
        new_w = screen_w
        new_h = int(new_w / wp_ratio)

    resized = wallpaper.resize((new_w, new_h), Image.Resampling.LANCZOS)

    crop_x = (new_w - screen_w) // 2
    crop_y = (new_h - screen_h) // 2
    return resized.crop((crop_x, crop_y, crop_x + screen_w, crop_y + screen_h))


def replace_screen(phone_path: str, wallpaper_path: str, output_path: str) -> None:
    """
    将手机模板中的白色屏幕区域替换为壁纸图片。

    合成策略（边缘无白边）：
    - 在屏幕边界框内，以像素最小通道值（min R/G/B）计算亮度
    - 将亮度映射为 alpha：暗色边框→0（保留原图），纯白屏幕→1（显示壁纸）
    - 边缘抗锯齿像素自动平滑混合，消除白边
    - 全程使用 float32 计算，最终无损保存为 PNG
    """
    print(f"加载手机模板: {phone_path}")
    phone = Image.open(phone_path).convert('RGBA')

    print(f"加载壁纸: {wallpaper_path}")
    wallpaper = Image.open(wallpaper_path).convert('RGBA')
    wallpaper = crop_wallpaper_to_ratio(wallpaper)
    print(f"  壁纸已裁剪为 9:19 → {wallpaper.width} × {wallpaper.height} px")

    print("检测屏幕区域...")
    screen_mask, (left, top, right, bottom) = find_screen_mask(phone)
    screen_w = right - left + 1
    screen_h = bottom - top + 1
    print(f"  屏幕坐标: ({left}, {top}) → ({right}, {bottom})，尺寸: {screen_w} × {screen_h} px")

    wp_fitted = fit_wallpaper_to_screen(wallpaper, screen_w, screen_h)

    # float32 全程计算，避免截断误差
    phone_arr = np.array(phone, dtype=np.float32)
    wp_arr = np.array(wp_fitted, dtype=np.float32)

    # 将屏幕核心掩码向外膨胀若干像素，覆盖边缘抗锯齿过渡区
    dilated_mask = binary_dilation(screen_mask, iterations=6)

    region = phone_arr[top:bottom + 1, left:right + 1]          # (H, W, 4)
    local_dilated = dilated_mask[top:bottom + 1, left:right + 1] # (H, W)

    # 用最小通道值衡量"亮白程度"：纯白=255，深色边框≈0，抗锯齿像素介于其间
    # alpha 映射：[dark_thresh, white_thresh] → [0, 1]
    dark_thresh, white_thresh = 60.0, 230.0
    min_channel = region[:, :, :3].min(axis=2)  # (H, W)
    alpha = np.clip((min_channel - dark_thresh) / (white_thresh - dark_thresh), 0.0, 1.0)

    # 膨胀区域外强制 alpha=0，避免影响屏幕范围之外的像素
    alpha[~local_dilated] = 0.0

    alpha_4ch = alpha[:, :, np.newaxis]  # broadcast 到 4 通道
    blended = wp_arr * alpha_4ch + region * (1.0 - alpha_4ch)

    phone_arr[top:bottom + 1, left:right + 1] = blended

    result = Image.fromarray(phone_arr.clip(0, 255).astype(np.uint8))

    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # compress_level=1：PNG 无损但编码更快；若追求最小体积可改为 9
    result.save(str(out_path), format='PNG', compress_level=1)
    print(f"已保存结果: {out_path}  ({result.width} × {result.height} px)")


def main():
    parser = argparse.ArgumentParser(
        description='将手机模板中的白色屏幕替换为指定壁纸（边缘无白边，输出高清 PNG）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            '示例:\n'
            '  python phone_screen_replace.py wallpaper.jpg\n'
            '  python phone_screen_replace.py wallpaper.jpg -p custom_phone.png -o result.png'
        )
    )
    parser.add_argument('wallpaper', help='壁纸图片路径')
    parser.add_argument(
        '-p', '--phone',
        default=str(DEFAULT_PHONE_TEMPLATE),
        help=f'手机模板图片路径（默认: {DEFAULT_PHONE_TEMPLATE.name}）'
    )
    parser.add_argument('-o', '--output', default='output.png', help='输出路径（默认: output.png）')

    args = parser.parse_args()
    replace_screen(args.phone, args.wallpaper, args.output)


if __name__ == '__main__':
    main()
