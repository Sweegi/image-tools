#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片处理工具函数
包含拼图处理所需的公共工具函数
"""

import logging
from pathlib import Path
from typing import Optional, Tuple
from PIL import Image, ImageFilter, ImageDraw, ImageEnhance
import numpy as np

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


def add_border(image: Image.Image, border_width: int = 12, border_color: Tuple[int, int, int] = (220, 220, 220), radius: int = 25) -> Image.Image:
    """
    为图片添加带圆角的边框

    Args:
        image: 原始图片（应该已经添加了圆角和阴影效果）
        border_width: 边框宽度（像素）
        border_color: 边框颜色（RGB），默认白灰色 (220, 220, 220)
        radius: 圆角半径（像素），应该与图片的圆角半径一致

    Returns:
        带边框的图片
    """
    # 创建带边框的画布
    canvas_size = (
        image.width + border_width * 2,
        image.height + border_width * 2
    )

    # 创建画布，填充边框颜色
    canvas = Image.new('RGBA', canvas_size, (*border_color, 255))
    draw = ImageDraw.Draw(canvas)

    # 边框的圆角半径（外圆角，比图片圆角稍大）
    border_radius = radius + border_width

    # 绘制圆角矩形边框（外框）
    draw.rounded_rectangle(
        [(0, 0), canvas_size],
        radius=border_radius,
        fill=(*border_color, 255)
    )

    # 创建内部遮罩（用于挖空内部区域，显示原图）
    inner_mask = Image.new('L', canvas_size, 255)  # 先全部填充
    inner_draw = ImageDraw.Draw(inner_mask)
    # 绘制内部圆角矩形（挖空区域）
    inner_rect = [
        (border_width, border_width),
        (canvas_size[0] - border_width, canvas_size[1] - border_width)
    ]
    inner_draw.rounded_rectangle(
        inner_rect,
        radius=radius,
        fill=0  # 挖空
    )

    # 应用遮罩到canvas的alpha通道，使内部区域透明
    canvas_alpha = canvas.split()[3]
    # 将遮罩应用到alpha通道（反转，使内部透明）
    new_alpha = Image.new('L', canvas_size, 255)
    # 内部区域（遮罩为0的地方）设为透明
    alpha_array = np.array(canvas_alpha)
    mask_array = np.array(inner_mask)
    alpha_array[mask_array == 0] = 0
    new_alpha = Image.fromarray(alpha_array)
    canvas.putalpha(new_alpha)

    # 将原图粘贴到画布中心
    canvas.paste(image, (border_width, border_width), image)

    return canvas


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


def create_couple_background(img_a: Image.Image, img_b: Image.Image, back_img: Image.Image, target_size: Tuple[int, int]) -> Image.Image:
    """
    创建情侣头像拼图的背景底图

    Args:
        img_a: 第一张图片（左侧）
        img_b: 第二张图片（右侧）
        back_img: 原始back.png底图
        target_size: 目标尺寸 (width, height)

    Returns:
        处理后的背景底图
    """
    # 确保两张图片是RGB模式（去除透明通道）
    if img_a.mode == 'RGBA':
        # 如果有透明通道，先转换为RGB（使用白色背景）
        bg_a = Image.new('RGB', img_a.size, (255, 255, 255))
        bg_a.paste(img_a, mask=img_a.split()[3])
        img_a = bg_a
    elif img_a.mode != 'RGB':
        img_a = img_a.convert('RGB')

    if img_b.mode == 'RGBA':
        # 如果有透明通道，先转换为RGB（使用白色背景）
        bg_b = Image.new('RGB', img_b.size, (255, 255, 255))
        bg_b.paste(img_b, mask=img_b.split()[3])
        img_b = bg_b
    elif img_b.mode != 'RGB':
        img_b = img_b.convert('RGB')

    # 确保两张图片高度一致（以较小的为准）
    min_height = min(img_a.height, img_b.height)
    if img_a.height != min_height:
        img_a = img_a.resize((int(img_a.width * min_height / img_a.height), min_height), Image.Resampling.LANCZOS)
    if img_b.height != min_height:
        img_b = img_b.resize((int(img_b.width * min_height / img_b.height), min_height), Image.Resampling.LANCZOS)

    # 无缝平接两张图片（左右拼接）
    stitched_width = img_a.width + img_b.width
    stitched_img = Image.new('RGB', (stitched_width, min_height), (255, 255, 255))
    stitched_img.paste(img_a, (0, 0))
    stitched_img.paste(img_b, (img_a.width, 0))

    # 计算3:4比例的裁剪尺寸
    target_width, target_height = target_size
    target_ratio = target_width / target_height  # 3:4 = 0.75

    # 从中间位置按3:4比例裁剪
    if stitched_img.width / stitched_img.height > target_ratio:
        # 图片更宽，需要裁剪宽度
        crop_width = int(stitched_img.height * target_ratio)
        crop_left = (stitched_img.width - crop_width) // 2
        cropped_img = stitched_img.crop((crop_left, 0, crop_left + crop_width, stitched_img.height))
    else:
        # 图片更高，需要裁剪高度
        crop_height = int(stitched_img.width / target_ratio)
        crop_top = (stitched_img.height - crop_height) // 2
        cropped_img = stitched_img.crop((0, crop_top, stitched_img.width, crop_top + crop_height))

    # 调整到目标尺寸
    cropped_img = cropped_img.resize(target_size, Image.Resampling.LANCZOS)

    # 添加磨玻璃效果（高斯模糊，radius=20，减弱效果）
    blurred_img = cropped_img.filter(ImageFilter.GaussianBlur(radius=20))

    # 确保磨玻璃图片是RGB模式
    if blurred_img.mode != 'RGB':
        blurred_img = blurred_img.convert('RGB')

    # 将back.png覆盖在磨玻璃效果图片之上
    # 确保back.png尺寸与目标尺寸一致
    back_resized = back_img.resize(target_size, Image.Resampling.LANCZOS)

    # 由于back.png是透明图片，需要正确处理alpha通道
    # 先将磨玻璃图片转换为RGBA模式作为底图
    blurred_rgba = blurred_img.convert('RGBA')

    # 如果back.png有透明通道，使用alpha_composite进行叠加
    # 这样透明区域会显示磨玻璃图片，不透明区域会显示back.png
    if back_resized.mode == 'RGBA':
        result = Image.alpha_composite(blurred_rgba, back_resized)
    else:
        # 如果back.png没有透明通道，直接叠加
        back_rgba = back_resized.convert('RGBA')
        result = Image.alpha_composite(blurred_rgba, back_rgba)

    # 确保返回RGB模式
    if result.mode != 'RGB':
        result = result.convert('RGB')

    return result


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
