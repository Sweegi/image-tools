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

logger = logging.getLogger(__name__)

# 常量定义
BACK_IMAGE = Path(__file__).parent / 'back.png'
BACK1_IMAGE = Path(__file__).parent / 'back1.png'

# 输出图片配置
FINAL_PUZZLE_MIN_SIZE = 200 * 1024  # 200KB（最终拼图结果最小大小）
FINAL_PUZZLE_MAX_SIZE = 300 * 1024  # 300KB（最终拼图结果最大大小）
BORDER_RADIUS = 25  # 圆角半径
SHADOW_OFFSET = (5, 5)
SHADOW_BLUR = 10


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


def save_final_puzzle_image(image: Image.Image, output_file: Path, target_size: int = 250 * 1024) -> None:
    """
    保存最终拼图结果图片，统一压缩到200-300KB之间
    
    Args:
        image: 图片对象
        output_file: 输出文件路径
        target_size: 目标文件大小（字节），默认250KB，会在200-300KB范围内调整
    """
    # 确保目标大小在合理范围内
    min_size = FINAL_PUZZLE_MIN_SIZE  # 200KB
    max_size = FINAL_PUZZLE_MAX_SIZE  # 300KB
    if target_size < min_size:
        target_size = min_size
    elif target_size > max_size:
        target_size = max_size
    
    # 确保图片是 RGB 模式（JPEG 不支持透明通道）
    if image.mode == 'RGBA':
        bg = Image.new('RGB', image.size, (255, 255, 255))
        bg.paste(image, mask=image.split()[3])
        image = bg
    elif image.mode != 'RGB':
        image = image.convert('RGB')
    
    # 如果输出文件是PNG，改为JPG
    if output_file.suffix.lower() == '.png':
        output_file = output_file.with_suffix('.jpg')
    
    # 先尝试高质量保存，检查文件大小
    current_quality = 95
    best_quality = current_quality
    best_size = 0
    
    # 从高质量开始逐步降低，找到最接近目标大小的质量
    while current_quality >= 30:
        image.save(output_file, 'JPEG', quality=current_quality, optimize=True)
        file_size = output_file.stat().st_size
        
        # 如果文件大小在目标范围内，直接返回
        if min_size <= file_size <= max_size:
            logger.info(f"  已保存最终拼图结果，质量: {current_quality}，大小: {file_size / 1024:.2f}KB")
            return
        
        # 记录最接近目标大小的质量
        if best_size == 0 or abs(file_size - target_size) < abs(best_size - target_size):
            best_quality = current_quality
            best_size = file_size
        
        # 如果文件太大，继续降低质量
        if file_size > max_size:
            current_quality -= 5
        # 如果文件太小，需要提高质量（但我们已经从高到低，所以这种情况不应该发生）
        else:
            break
    
    # 如果找到的质量对应的文件大小不在范围内，需要调整
    if best_size > max_size:
        # 文件太大，需要缩小尺寸
        # 计算缩放比例，使文件大小接近目标大小
        scale = (target_size / best_size) ** 0.5
        new_size = (int(image.width * scale), int(image.height * scale))
        resized_image = image.resize(new_size, Image.Resampling.LANCZOS)
        
        # 重新尝试保存，从较高质量开始
        current_quality = 85
        while current_quality >= 30:
            resized_image.save(output_file, 'JPEG', quality=current_quality, optimize=True)
            file_size = output_file.stat().st_size
            
            if min_size <= file_size <= max_size:
                logger.info(f"  已缩小尺寸并保存最终拼图结果，质量: {current_quality}，大小: {file_size / 1024:.2f}KB")
                return
            
            if file_size > max_size:
                current_quality -= 5
            else:
                # 文件太小，使用当前质量即可
                logger.info(f"  已缩小尺寸并保存最终拼图结果，质量: {current_quality}，大小: {file_size / 1024:.2f}KB")
                return
        
        # 如果还是太大，使用最低质量
        resized_image.save(output_file, 'JPEG', quality=30, optimize=True)
        file_size = output_file.stat().st_size
        logger.info(f"  已缩小尺寸并保存最终拼图结果（最低质量），大小: {file_size / 1024:.2f}KB")
    elif best_size < min_size:
        # 文件太小，使用最佳质量即可（这种情况很少见）
        image.save(output_file, 'JPEG', quality=best_quality, optimize=True)
        logger.info(f"  已保存最终拼图结果，质量: {best_quality}，大小: {best_size / 1024:.2f}KB")
    else:
        # 使用最佳质量
        image.save(output_file, 'JPEG', quality=best_quality, optimize=True)
        logger.info(f"  已保存最终拼图结果，质量: {best_quality}，大小: {best_size / 1024:.2f}KB")


def create_circular_image(image: Image.Image, border_width: int = 8, outer_border_width: int = 3) -> Image.Image:
    """
    创建圆形图片，带白色边框和白灰色外边框
    
    Args:
        image: 原始图片（应该是正方形）
        border_width: 内边框宽度（像素，白色）
        outer_border_width: 外边框宽度（像素，白灰色）
    
    Returns:
        带白色边框和白灰色外边框的圆形图片
    """
    # 确保图片是正方形
    size = min(image.width, image.height)
    if image.width != image.height:
        # 居中裁剪为正方形
        left = (image.width - size) // 2
        top = (image.height - size) // 2
        image = image.crop((left, top, left + size, top + size))
    
    # 创建圆形遮罩
    mask = Image.new('L', (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse([(0, 0), (size, size)], fill=255)
    
    # 应用圆形遮罩
    if image.mode == 'RGBA':
        image = image.copy()
        image.putalpha(mask)
    else:
        image = image.convert('RGBA')
        image.putalpha(mask)
    
    # 创建带边框的画布（增加内边框和外边框宽度）
    canvas_size = size + border_width * 2 + outer_border_width * 2
    canvas = Image.new('RGBA', (canvas_size, canvas_size), (255, 255, 255, 0))
    
    # 绘制白灰色外边框（浅灰色，RGB: 220, 220, 220）
    border_draw = ImageDraw.Draw(canvas)
    border_draw.ellipse(
        [(outer_border_width, outer_border_width), 
         (canvas_size - outer_border_width, canvas_size - outer_border_width)],
        fill=(220, 220, 220, 255)
    )
    
    # 绘制白色内边框
    inner_border_start = outer_border_width + border_width
    inner_border_end = canvas_size - outer_border_width - border_width
    border_draw.ellipse(
        [(inner_border_start, inner_border_start), 
         (inner_border_end, inner_border_end)],
        fill=(255, 255, 255, 255)
    )
    
    # 创建内部圆形遮罩（用于裁剪图片）
    inner_mask = Image.new('L', (size, size), 0)
    inner_draw = ImageDraw.Draw(inner_mask)
    inner_draw.ellipse([(0, 0), (size, size)], fill=255)
    
    # 应用内部遮罩到图片
    inner_image = image.copy()
    inner_image.putalpha(inner_mask)
    
    # 将图片粘贴到画布中心（考虑外边框和内边框）
    paste_x = outer_border_width + border_width
    paste_y = outer_border_width + border_width
    canvas.paste(inner_image, (paste_x, paste_y), inner_image)
    
    return canvas


def create_rounded_square_image(image: Image.Image, radius: int = 30) -> Image.Image:
    """
    创建圆角方形图片
    
    Args:
        image: 原始图片（应该是正方形）
        radius: 圆角半径
    
    Returns:
        圆角方形图片
    """
    # 确保图片是正方形
    size = min(image.width, image.height)
    if image.width != image.height:
        # 居中裁剪为正方形
        left = (image.width - size) // 2
        top = (image.height - size) // 2
        image = image.crop((left, top, left + size, top + size))
    
    # 创建圆角遮罩
    mask = create_rounded_rectangle_mask((size, size), radius)
    
    # 应用圆角遮罩
    if image.mode == 'RGBA':
        image = image.copy()
        image.putalpha(mask)
    else:
        image = image.convert('RGBA')
        image.putalpha(mask)
    
    return image
