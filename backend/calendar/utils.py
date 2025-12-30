#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片处理工具函数
包含拼图处理所需的公共工具函数
"""

import logging
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

logger = logging.getLogger(__name__)

# 常量定义
BACK_IMAGE = Path(__file__).parent / 'back.png'

# 输出图片配置
FINAL_PUZZLE_MIN_SIZE = 200 * 1024  # 200KB（最终拼图结果最小大小）
FINAL_PUZZLE_MAX_SIZE = 300 * 1024  # 300KB（最终拼图结果最大大小）


def add_rounded_corners_and_shadow(
    image: Image.Image,
    corner_radius: int = 25,
    shadow_offset: tuple = (5, 5),
    shadow_blur: int = 10,
    shadow_opacity: int = 100
) -> Image.Image:
    """
    为图片添加圆角和阴影效果
    
    Args:
        image: 原始图片
        corner_radius: 圆角半径（像素）
        shadow_offset: 阴影偏移量 (x, y)
        shadow_blur: 阴影模糊半径
        shadow_opacity: 阴影透明度（0-255）
    
    Returns:
        添加了圆角和阴影效果的图片（RGBA模式）
    """
    # 确保图片是RGBA模式
    if image.mode != 'RGBA':
        if image.mode == 'RGB':
            image = image.convert('RGBA')
        else:
            image = image.convert('RGBA')
    
    width, height = image.size
    
    # 创建圆角遮罩
    mask = Image.new('L', (width, height), 0)
    draw = ImageDraw.Draw(mask)
    
    # 绘制圆角矩形
    draw.rounded_rectangle(
        [(0, 0), (width, height)],
        radius=corner_radius,
        fill=255
    )
    
    # 应用圆角遮罩
    rounded_image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    rounded_image.paste(image, (0, 0), mask)
    
    # 创建阴影
    shadow_size = (
        width + abs(shadow_offset[0]) * 2 + shadow_blur * 2,
        height + abs(shadow_offset[1]) * 2 + shadow_blur * 2
    )
    shadow = Image.new('RGBA', shadow_size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    
    # 计算阴影位置（居中）
    shadow_x = abs(shadow_offset[0]) + shadow_blur
    shadow_y = abs(shadow_offset[1]) + shadow_blur
    
    # 绘制阴影（黑色半透明圆角矩形）
    shadow_draw.rounded_rectangle(
        [
            (shadow_x, shadow_y),
            (shadow_x + width, shadow_y + height)
        ],
        radius=corner_radius,
        fill=(0, 0, 0, shadow_opacity)
    )
    
    # 模糊阴影
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=shadow_blur))
    
    # 将阴影和图片合成
    result = Image.new('RGBA', shadow_size, (0, 0, 0, 0))
    result.paste(shadow, (0, 0), shadow)
    
    # 计算图片在结果中的位置（考虑阴影偏移）
    img_x = abs(shadow_offset[0]) + shadow_blur
    img_y = abs(shadow_offset[1]) + shadow_blur
    result.paste(rounded_image, (img_x, img_y), rounded_image)
    
    return result


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
