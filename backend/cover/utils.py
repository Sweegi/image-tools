#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片处理工具函数
包含拼图处理所需的公共工具函数
"""

import logging
from pathlib import Path
from typing import Optional, Tuple
from PIL import Image, ImageFilter, ImageDraw
import numpy as np
from sklearn.cluster import KMeans

logger = logging.getLogger(__name__)

# 常量定义
BACK_IMAGE = Path(__file__).parent / 'back.jpg'
MOBILE_BLOCK_COVER = Path(__file__).parent / 'mobile-block-cover.png'
PAD_BLOCK_COVER = Path(__file__).parent / 'pad-block-cover.png'
PAD_LOCK_COVER = Path(__file__).parent / 'pad-lock-cover.png'
PC_MAC_COVER = Path(__file__).parent / 'pc-mac-cover.png'

# 输出图片配置
OUTPUT_RATIO = (1, 1)  # 1:1 比例
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB
BORDER_RADIUS = 25  # 圆角半径（从20增加到25）
SHADOW_OFFSET = (5, 5)
SHADOW_BLUR = 10
SPACING = 60  # 图片之间的间隔（从30增加到60，增大一倍）


def extract_main_color(image: Image.Image, k: int = 3) -> Tuple[int, int, int]:
    """
    提取图片的主色调

    Args:
        image: PIL Image 对象
        k: K-means 聚类数量

    Returns:
        RGB 颜色元组
    """
    # 将图片转换为 numpy 数组
    img_array = np.array(image)

    # 如果是 RGBA，只取 RGB
    if img_array.shape[2] == 4:
        img_array = img_array[:, :, :3]

    # 重塑为二维数组 (像素数, RGB)
    pixels = img_array.reshape(-1, 3)

    # 使用 K-means 聚类
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    kmeans.fit(pixels)

    # 获取最大的聚类中心（主色调）
    labels = kmeans.labels_
    cluster_sizes = np.bincount(labels)
    main_cluster_idx = np.argmax(cluster_sizes)
    main_color = kmeans.cluster_centers_[main_cluster_idx]

    return tuple(map(int, main_color))


def create_rounded_rectangle_mask(size: Tuple[int, int], radius: int) -> Image.Image:
    """
    创建圆角矩形遮罩

    Args:
        size: 图片尺寸 (width, height)
        radius: 圆角半径

    Returns:
        遮罩图片
    """
    mask = Image.new('L', size, 0)
    draw = ImageDraw.Draw(mask)

    # 绘制圆角矩形
    draw.rounded_rectangle(
        [(0, 0), size],
        radius=radius,
        fill=255
    )

    return mask


def add_shadow_and_rounded_corners(image: Image.Image, radius: int = BORDER_RADIUS) -> Image.Image:
    """
    为图片添加阴影和圆角效果

    Args:
        image: 原始图片
        radius: 圆角半径

    Returns:
        处理后的图片
    """
    # 创建带阴影的画布（增加边距以容纳阴影）
    shadow_margin = max(SHADOW_OFFSET) + SHADOW_BLUR
    canvas_size = (
        image.width + shadow_margin * 2,
        image.height + shadow_margin * 2
    )

    # 创建阴影层
    shadow = Image.new('RGBA', canvas_size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)

    # 绘制阴影（使用半透明黑色）
    shadow_rect = [
        (shadow_margin + SHADOW_OFFSET[0], shadow_margin + SHADOW_OFFSET[1]),
        (shadow_margin + image.width + SHADOW_OFFSET[0], shadow_margin + image.height + SHADOW_OFFSET[1])
    ]
    shadow_draw.rounded_rectangle(
        shadow_rect,
        radius=radius,
        fill=(0, 0, 0, 100)
    )

    # 模糊阴影
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=SHADOW_BLUR))

    # 创建圆角遮罩
    mask = create_rounded_rectangle_mask(image.size, radius)

    # 如果原图有透明通道，应用遮罩
    if image.mode == 'RGBA':
        image = image.copy()
        image.putalpha(mask)
    else:
        image = image.convert('RGBA')
        image.putalpha(mask)

    # 将图片粘贴到阴影层上
    shadow.paste(image, (shadow_margin, shadow_margin), image)

    return shadow


def overlay_images(base: Image.Image, overlay: Image.Image) -> Image.Image:
    """
    将覆盖图片叠加到底图上

    Args:
        base: 底图
        overlay: 覆盖图

    Returns:
        叠加后的图片
    """
    # 确保两张图片尺寸一致
    if base.size != overlay.size:
        overlay = overlay.resize(base.size, Image.Resampling.LANCZOS)

    # 如果底图没有透明通道，转换为 RGBA
    if base.mode != 'RGBA':
        base = base.convert('RGBA')

    # 如果覆盖图没有透明通道，转换为 RGBA
    if overlay.mode != 'RGBA':
        overlay = overlay.convert('RGBA')

    # 创建新图片并叠加
    result = Image.alpha_composite(base, overlay)

    return result


def get_image_file(work_dir: Path, base_name: str) -> Optional[Path]:
    """
    获取图片文件（支持多种格式）

    Args:
        work_dir: 工作目录
        base_name: 基础文件名（不含扩展名）

    Returns:
        图片文件路径，如果不存在则返回 None
    """
    for ext in ['.png', '.jpg', '.jpeg', '.webp']:
        file_path = work_dir / f"{base_name}{ext}"
        if file_path.exists():
            return file_path
    return None


def create_background(size: Tuple[int, int], main_color: Optional[str] = None, source_image: Optional[Image.Image] = None) -> Image.Image:
    """
    创建背景图片

    背景逻辑：
    - main_color = None: 使用默认背景（back.jpg）
    - main_color = "": 自动提取主色调（如果提供了 source_image）
    - main_color = "#ffffff": 使用指定的纯色背景

    Args:
        size: 背景尺寸
        main_color: 主色调（16进制颜色代码，如 #ffffff）。如果为空字符串，则自动提取主色调；如果为 None，则使用默认背景
        source_image: 用于提取主色调的源图片（仅在 main_color="" 时使用）

    Returns:
        背景图片
    """
    # 如果 main_color 是 None，始终使用默认背景（back.jpg）
    if main_color is None:
        bg = Image.open(BACK_IMAGE)
        return bg.resize(size, Image.Resampling.LANCZOS)

    # 如果 main_color 是空字符串，表示自动提取主色调
    if main_color == '':
        if source_image:
            # 从源图片提取主色调
            bg_color = extract_main_color(source_image)
            return Image.new('RGB', size, bg_color)
        else:
            # 没有源图片，使用默认背景
            bg = Image.open(BACK_IMAGE)
            return bg.resize(size, Image.Resampling.LANCZOS)

    # 如果 main_color 有值，使用纯色背景
    # 解析颜色代码
    color_str = main_color
    if color_str.startswith('#'):
        color_str = color_str[1:]

    if len(color_str) == 3:
        # 短格式 #fff -> #ffffff
        color_str = ''.join([c * 2 for c in color_str])

    try:
        r = int(color_str[0:2], 16)
        g = int(color_str[2:4], 16)
        b = int(color_str[4:6], 16)
        bg_color = (r, g, b)
        return Image.new('RGB', size, bg_color)
    except (ValueError, IndexError):
        logger.warning(f"  无效的颜色代码: {main_color}，使用默认背景")
        bg = Image.open(BACK_IMAGE)
        return bg.resize(size, Image.Resampling.LANCZOS)


def resize_to_fit_ratio(image: Image.Image, target_ratio: float, max_size: Tuple[int, int]) -> Image.Image:
    """
    调整图片尺寸以适应目标比例，同时不超过最大尺寸

    Args:
        image: 原始图片
        target_ratio: 目标宽高比
        max_size: 最大尺寸 (width, height)

    Returns:
        调整后的图片
    """
    current_ratio = image.width / image.height

    if abs(current_ratio - target_ratio) < 0.01:
        # 比例已经匹配，只需缩放
        scale = min(max_size[0] / image.width, max_size[1] / image.height)
        new_size = (int(image.width * scale), int(image.height * scale))
        return image.resize(new_size, Image.Resampling.LANCZOS)

    # 需要调整比例
    # 计算在目标比例下的最大尺寸
    if current_ratio > target_ratio:
        # 图片更宽，以高度为准
        max_height = min(max_size[1], int(max_size[0] / target_ratio))
        max_width = int(max_height * target_ratio)
    else:
        # 图片更高，以宽度为准
        max_width = min(max_size[0], int(max_size[1] * target_ratio))
        max_height = int(max_width / target_ratio)
    
    # 计算缩放比例
    scale = min(max_width / image.width, max_height / image.height)
    new_size = (int(image.width * scale), int(image.height * scale))

    # 调整到目标比例
    if new_size[0] / new_size[1] > target_ratio:
        # 需要裁剪宽度
        new_width = int(new_size[1] * target_ratio)
        crop_left = (new_size[0] - new_width) // 2
        resized = image.resize(new_size, Image.Resampling.LANCZOS)
        return resized.crop((crop_left, 0, crop_left + new_width, new_size[1]))
    else:
        # 需要裁剪高度
        new_height = int(new_size[0] / target_ratio)
        crop_top = (new_size[1] - new_height) // 2
        resized = image.resize(new_size, Image.Resampling.LANCZOS)
        return resized.crop((0, crop_top, new_size[0], crop_top + new_height))


def save_optimized_image(image: Image.Image, output_file: Path, quality: int = 95) -> None:
    """
    保存图片并优化文件大小

    Args:
        image: 图片对象
        output_file: 输出文件路径
        quality: 初始质量（用于 JPEG）
    """
    # 先尝试保存为 PNG
    image.save(output_file, 'PNG', optimize=True)

    # 检查文件大小
    file_size = output_file.stat().st_size

    if file_size > MAX_FILE_SIZE:
        # 如果超过 2MB，转换为 JPEG 并降低质量
        logger.info(f"  文件大小 {file_size / 1024 / 1024:.2f}MB 超过限制，转换为 JPEG")

        # 如果原图有透明通道，需要添加白色背景
        if image.mode == 'RGBA':
            bg = Image.new('RGB', image.size, (255, 255, 255))
            bg.paste(image, mask=image.split()[3])
            image = bg
        else:
            image = image.convert('RGB')

        # 删除 PNG 文件
        output_file.unlink()

        # 生成 JPG 文件路径
        output_file_jpg = output_file.with_suffix('.jpg')

        # 逐步降低质量直到文件大小符合要求
        current_quality = quality
        while current_quality > 50:
            image.save(output_file_jpg, 'JPEG', quality=current_quality, optimize=True)
            file_size = output_file_jpg.stat().st_size

            if file_size <= MAX_FILE_SIZE:
                logger.info(f"  已优化为 JPEG，质量: {current_quality}，大小: {file_size / 1024 / 1024:.2f}MB")
                return

            current_quality -= 5

        # 如果质量降到 50 还是太大，需要缩小尺寸
        if file_size > MAX_FILE_SIZE:
            scale = (MAX_FILE_SIZE / file_size) ** 0.5
            new_size = (int(image.width * scale), int(image.height * scale))
            image = image.resize(new_size, Image.Resampling.LANCZOS)
            image.save(output_file_jpg, 'JPEG', quality=75, optimize=True)
            file_size = output_file_jpg.stat().st_size
            logger.info(f"  已缩小尺寸并保存为 JPEG，大小: {file_size / 1024 / 1024:.2f}MB")
