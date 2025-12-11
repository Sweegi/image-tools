#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mobile 拼图模块
处理 Mobile 相关的图片拼接任务
"""

import logging
from pathlib import Path
from typing import Optional
from PIL import Image, ImageFilter

# 尝试相对导入，如果失败则使用绝对导入
try:
    from .utils import (
        MOBILE_BLOCK_COVER,
        OUTPUT_RATIO,
        SPACING,
        overlay_images,
        add_shadow_and_rounded_corners,
        resize_to_fit_ratio,
        create_background,
        get_image_file,
        save_optimized_image,
        save_optimized_jpeg,
        add_size_watermark
    )
except ImportError:
    from utils import (
        MOBILE_BLOCK_COVER,
        OUTPUT_RATIO,
        SPACING,
        overlay_images,
        add_shadow_and_rounded_corners,
        resize_to_fit_ratio,
        create_background,
        get_image_file,
        save_optimized_image,
        save_optimized_jpeg,
        add_size_watermark
    )

logger = logging.getLogger(__name__)


def crop_to_ratio_center_height(image: Image.Image, target_ratio: float) -> Image.Image:
    """
    以中心和高度为基础，裁剪图片宽度将其调整为目标比例
    
    Args:
        image: 原始图片
        target_ratio: 目标宽高比（宽度/高度）
    
    Returns:
        裁剪后的图片
    """
    current_ratio = image.width / image.height
    
    # 如果比例已经匹配，直接返回
    if abs(current_ratio - target_ratio) < 0.01:
        return image
    
    # 保持高度不变，计算目标宽度
    target_width = int(image.height * target_ratio)
    
    # 如果目标宽度大于原图宽度，需要先放大（这种情况很少见，但处理一下）
    if target_width > image.width:
        # 先放大到目标宽度，保持高度不变
        resized = image.resize((target_width, image.height), Image.Resampling.LANCZOS)
        return resized
    
    # 从中心裁剪宽度
    crop_left = (image.width - target_width) // 2
    crop_right = crop_left + target_width
    
    return image.crop((crop_left, 0, crop_right, image.height))


def prepare_mobile_desktop(work_dir: Path) -> bool:
    """
    准备 Mobile desktop 图片

    Args:
        work_dir: 工作目录

    Returns:
        是否成功
    """
    mobile_desktop = work_dir / 'mobile-desktop.png'
    if mobile_desktop.exists():
        logger.info(f"  mobile-desktop.png 已存在，跳过")
        return True

    mobile = work_dir / 'mobile.png'
    if not mobile.exists():
        logger.error(f"  缺少 mobile.png")
        return False

    if not MOBILE_BLOCK_COVER.exists():
        logger.error(f"  缺少覆盖图片: {MOBILE_BLOCK_COVER}")
        return False

    try:
        base_img = Image.open(mobile)
        cover_img = Image.open(MOBILE_BLOCK_COVER)
        
        # 确保两张图片都是 9:19 比例
        base_ratio = base_img.width / base_img.height
        cover_ratio = cover_img.width / cover_img.height
        target_ratio = 9 / 19

        # 调整底图尺寸：如果原图不是 9:19，则以中心和高度为基础，裁剪宽度将其调整为 9:19
        if abs(base_ratio - target_ratio) > 0.01:
            base_img = crop_to_ratio_center_height(base_img, target_ratio)

        # 调整覆盖图尺寸
        if abs(cover_ratio - target_ratio) > 0.01:
            new_height = cover_img.height
            new_width = int(new_height * target_ratio)
            cover_img = cover_img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # 确保两张图片尺寸一致
        if base_img.size != cover_img.size:
            cover_img = cover_img.resize(base_img.size, Image.Resampling.LANCZOS)

        result = overlay_images(base_img, cover_img)
        result.save(mobile_desktop, 'PNG')
        logger.info(f"  已生成 mobile-desktop.png")
        return True
    except Exception as e:
        logger.error(f"  生成 mobile-desktop.png 失败: {e}")
        return False

def create_mobile_puzzle(work_dir: Path, output_dir: Path, main_color: Optional[str] = None) -> bool:
    """
    创建 Mobile 拼图
    两张图片居中水平排列，单个图片占总页面高度的70%

    Args:
        work_dir: 工作目录
        output_dir: 输出目录
        main_color: 主色调
    
    Returns:
        是否成功
    """
    mobile_lock_file = get_image_file(work_dir, 'mobile-lock')
    mobile_desktop_file = work_dir / 'mobile-desktop.png'

    if not mobile_lock_file or not mobile_desktop_file.exists():
        logger.error(f"  缺少 Mobile 拼图所需文件")
        return False

    try:
        mobile_lock = Image.open(mobile_lock_file)
        mobile_desktop = Image.open(mobile_desktop_file)

        # 确保两张图片都是 9:19 比例
        target_input_ratio = 9 / 19
        mobile_lock = resize_to_fit_ratio(mobile_lock, target_input_ratio, (2000, 4000))
        mobile_desktop = resize_to_fit_ratio(mobile_desktop, target_input_ratio, (2000, 4000))

        # 先确定画布尺寸（1:1 比例）
        # 使用一个基准高度来计算画布尺寸
        base_height = 2000
        canvas_width = int(base_height * (OUTPUT_RATIO[0] / OUTPUT_RATIO[1]))
        canvas_height = base_height

        # 计算目标图片内容高度：每张图片占画布高度的70%
        # 注意：这是图片内容部分的高度，不包括阴影
        target_content_height = int(canvas_height * 0.7)
        # 根据 9:19 比例计算目标宽度
        target_content_width = int(target_content_height * target_input_ratio)

        # 调整两张图片到目标尺寸
        mobile_lock = mobile_lock.resize((target_content_width, target_content_height), Image.Resampling.LANCZOS)
        mobile_desktop = mobile_desktop.resize((target_content_width, target_content_height), Image.Resampling.LANCZOS)

        # 添加阴影和圆角（这会使图片尺寸变大，因为增加了边距）
        mobile_lock = add_shadow_and_rounded_corners(mobile_lock)
        mobile_desktop = add_shadow_and_rounded_corners(mobile_desktop)

        # 计算两张图片（带阴影）的总宽度和间距
        total_content_width = mobile_lock.width + mobile_desktop.width + SPACING

        # 如果总宽度超过画布，需要按比例缩小，但保持图片内容高度占70%的比例
        # 计算缩放比例，确保两张图片内容宽度之和 + 间距不超过画布
        max_total_width = canvas_width
        if total_content_width > max_total_width:
            # 计算需要缩小的比例
            # 目标：2 * target_content_width * scale + SPACING <= max_total_width
            # 所以：scale <= (max_total_width - SPACING) / (2 * target_content_width)
            max_scale = (max_total_width - SPACING) / (2 * target_content_width)
            if max_scale < 1.0:
                # 需要缩小（保持高度占70%的比例）
                new_target_content_width = int(target_content_width * max_scale)
                new_target_content_height = int(target_content_height * max_scale)

                # 重新调整图片尺寸
                mobile_lock = Image.open(mobile_lock_file)
                mobile_desktop = Image.open(mobile_desktop_file)
                mobile_lock = resize_to_fit_ratio(mobile_lock, target_input_ratio, (2000, 4000))
                mobile_desktop = resize_to_fit_ratio(mobile_desktop, target_input_ratio, (2000, 4000))
                mobile_lock = mobile_lock.resize((new_target_content_width, new_target_content_height), Image.Resampling.LANCZOS)
                mobile_desktop = mobile_desktop.resize((new_target_content_width, new_target_content_height), Image.Resampling.LANCZOS)

                # 重新添加阴影和圆角
                mobile_lock = add_shadow_and_rounded_corners(mobile_lock)
                mobile_desktop = add_shadow_and_rounded_corners(mobile_desktop)
                total_content_width = mobile_lock.width + mobile_desktop.width + SPACING

        # 创建背景
        # main_color = None: 使用默认背景（back.jpg）
        # main_color = "": 自动提取主色调
        # main_color = "#ffffff": 使用纯色背景
        original_mobile_lock = Image.open(mobile_lock_file)
        bg = create_background((canvas_width, canvas_height), main_color, original_mobile_lock)

        # 获取原始 mobile.png 图片尺寸
        mobile_file = get_image_file(work_dir, 'mobile')
        if mobile_file:
            original_mobile = Image.open(mobile_file)
            original_width, original_height = original_mobile.size
        else:
            # 如果没有找到 mobile.png，使用 mobile-lock 的尺寸
            original_width, original_height = original_mobile_lock.size

        # 计算居中位置（水平居中，垂直居中）
        x_offset = (canvas_width - total_content_width) // 2
        y_offset = (canvas_height - max(mobile_lock.height, mobile_desktop.height)) // 2

        # 粘贴图片
        bg.paste(mobile_lock, (x_offset, y_offset), mobile_lock)
        bg.paste(mobile_desktop, (x_offset + mobile_lock.width + SPACING, y_offset), mobile_desktop)

        # 添加尺寸水印（使用原始 mobile.png 的尺寸）
        bg = add_size_watermark(bg, original_width, original_height)
        
        # 保存并优化文件大小
        output_file = output_dir / 'mobile-combined.png'
        save_optimized_image(bg, output_file)

        logger.info(f"  已生成 mobile-combined.png")
        return True
    except Exception as e:
        logger.error(f"  生成 Mobile 拼图失败: {e}")
        return False


def prepare_mobile_desktop_2(work_dir: Path) -> bool:
    """
    准备 Mobile desktop-2 图片
    将 mobile.png 整张图做磨玻璃模糊效果，再使用 mobile-block-cover.png 图片生成 mobile-desktop-2.png

    Args:
        work_dir: 工作目录

    Returns:
        是否成功
    """
    mobile_desktop_2 = work_dir / 'mobile-desktop-2.png'
    if mobile_desktop_2.exists():
        logger.info(f"  mobile-desktop-2.png 已存在，跳过")
        return True

    mobile = work_dir / 'mobile.png'
    if not mobile.exists():
        logger.error(f"  缺少 mobile.png")
        return False

    if not MOBILE_BLOCK_COVER.exists():
        logger.error(f"  缺少覆盖图片: {MOBILE_BLOCK_COVER}")
        return False

    try:
        base_img = Image.open(mobile)
        cover_img = Image.open(MOBILE_BLOCK_COVER)
        
        # 确保两张图片都是 9:19 比例
        base_ratio = base_img.width / base_img.height
        cover_ratio = cover_img.width / cover_img.height
        target_ratio = 9 / 19

        # 调整底图尺寸：如果原图不是 9:19，则以中心和高度为基础，裁剪宽度将其调整为 9:19
        if abs(base_ratio - target_ratio) > 0.01:
            base_img = crop_to_ratio_center_height(base_img, target_ratio)

        # 调整覆盖图尺寸
        if abs(cover_ratio - target_ratio) > 0.01:
            new_height = cover_img.height
            new_width = int(new_height * target_ratio)
            cover_img = cover_img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # 确保两张图片尺寸一致
        if base_img.size != cover_img.size:
            cover_img = cover_img.resize(base_img.size, Image.Resampling.LANCZOS)

        # 对底图进行磨玻璃模糊效果（高斯模糊，加大模糊半径以增强效果）
        blurred_img = base_img.filter(ImageFilter.GaussianBlur(radius=140))

        # 叠加覆盖图
        result = overlay_images(blurred_img, cover_img)
        result.save(mobile_desktop_2, 'PNG')
        logger.info(f"  已生成 mobile-desktop-2.png")
        return True
    except Exception as e:
        logger.error(f"  生成 mobile-desktop-2.png 失败: {e}")
        return False


def create_mobile_puzzle_2(work_dir: Path, output_dir: Path, main_color: Optional[str] = None) -> bool:
    """
    创建 Mobile 拼图-2
    两张图片居中水平排列，单个图片占总页面高度的70%
    使用 mobile-lock.jpg 和 mobile-desktop-2.png 拼接生成 mobile-combined-2.jpg

    Args:
        work_dir: 工作目录
        output_dir: 输出目录
        main_color: 主色调
    
    Returns:
        是否成功
    """
    mobile_lock_file = get_image_file(work_dir, 'mobile-lock')
    mobile_desktop_2_file = work_dir / 'mobile-desktop-2.png'

    if not mobile_lock_file or not mobile_desktop_2_file.exists():
        logger.error(f"  缺少 Mobile 拼图-2 所需文件")
        return False

    try:
        mobile_lock = Image.open(mobile_lock_file)
        mobile_desktop_2 = Image.open(mobile_desktop_2_file)

        # 确保两张图片都是 9:19 比例
        target_input_ratio = 9 / 19
        mobile_lock = resize_to_fit_ratio(mobile_lock, target_input_ratio, (2000, 4000))
        mobile_desktop_2 = resize_to_fit_ratio(mobile_desktop_2, target_input_ratio, (2000, 4000))

        # 先确定画布尺寸（1:1 比例）
        # 使用一个基准高度来计算画布尺寸
        base_height = 2000
        canvas_width = int(base_height * (OUTPUT_RATIO[0] / OUTPUT_RATIO[1]))
        canvas_height = base_height

        # 计算目标图片内容高度：每张图片占画布高度的70%
        # 注意：这是图片内容部分的高度，不包括阴影
        target_content_height = int(canvas_height * 0.7)
        # 根据 9:19 比例计算目标宽度
        target_content_width = int(target_content_height * target_input_ratio)

        # 调整两张图片到目标尺寸
        mobile_lock = mobile_lock.resize((target_content_width, target_content_height), Image.Resampling.LANCZOS)
        mobile_desktop_2 = mobile_desktop_2.resize((target_content_width, target_content_height), Image.Resampling.LANCZOS)

        # 添加阴影和圆角（这会使图片尺寸变大，因为增加了边距）
        mobile_lock = add_shadow_and_rounded_corners(mobile_lock)
        mobile_desktop_2 = add_shadow_and_rounded_corners(mobile_desktop_2)

        # 计算两张图片（带阴影）的总宽度和间距
        total_content_width = mobile_lock.width + mobile_desktop_2.width + SPACING

        # 如果总宽度超过画布，需要按比例缩小，但保持图片内容高度占70%的比例
        # 计算缩放比例，确保两张图片内容宽度之和 + 间距不超过画布
        max_total_width = canvas_width
        if total_content_width > max_total_width:
            # 计算需要缩小的比例
            # 目标：2 * target_content_width * scale + SPACING <= max_total_width
            # 所以：scale <= (max_total_width - SPACING) / (2 * target_content_width)
            max_scale = (max_total_width - SPACING) / (2 * target_content_width)
            if max_scale < 1.0:
                # 需要缩小（保持高度占70%的比例）
                new_target_content_width = int(target_content_width * max_scale)
                new_target_content_height = int(target_content_height * max_scale)

                # 重新调整图片尺寸
                mobile_lock = Image.open(mobile_lock_file)
                mobile_desktop_2 = Image.open(mobile_desktop_2_file)
                mobile_lock = resize_to_fit_ratio(mobile_lock, target_input_ratio, (2000, 4000))
                mobile_desktop_2 = resize_to_fit_ratio(mobile_desktop_2, target_input_ratio, (2000, 4000))
                mobile_lock = mobile_lock.resize((new_target_content_width, new_target_content_height), Image.Resampling.LANCZOS)
                mobile_desktop_2 = mobile_desktop_2.resize((new_target_content_width, new_target_content_height), Image.Resampling.LANCZOS)

                # 重新添加阴影和圆角
                mobile_lock = add_shadow_and_rounded_corners(mobile_lock)
                mobile_desktop_2 = add_shadow_and_rounded_corners(mobile_desktop_2)
                total_content_width = mobile_lock.width + mobile_desktop_2.width + SPACING

        # 创建背景
        # main_color = None: 使用默认背景（back.jpg）
        # main_color = "": 自动提取主色调
        # main_color = "#ffffff": 使用纯色背景
        original_mobile_lock = Image.open(mobile_lock_file)
        bg = create_background((canvas_width, canvas_height), main_color, original_mobile_lock)

        # 获取原始 mobile.png 图片尺寸
        mobile_file = get_image_file(work_dir, 'mobile')
        if mobile_file:
            original_mobile = Image.open(mobile_file)
            original_width, original_height = original_mobile.size
        else:
            # 如果没有找到 mobile.png，使用 mobile-lock 的尺寸
            original_width, original_height = original_mobile_lock.size

        # 计算居中位置（水平居中，垂直居中）
        x_offset = (canvas_width - total_content_width) // 2
        y_offset = (canvas_height - max(mobile_lock.height, mobile_desktop_2.height)) // 2

        # 粘贴图片
        bg.paste(mobile_lock, (x_offset, y_offset), mobile_lock)
        bg.paste(mobile_desktop_2, (x_offset + mobile_lock.width + SPACING, y_offset), mobile_desktop_2)

        # 添加尺寸水印（使用原始 mobile.png 的尺寸）
        bg = add_size_watermark(bg, original_width, original_height)
        
        # 保存为 JPG 格式（压缩到 500KB 以内）
        output_file = output_dir / 'mobile-combined-2.jpg'
        save_optimized_jpeg(bg, output_file)
        logger.info(f"  已生成 mobile-combined-2.jpg")
        return True
    except Exception as e:
        logger.error(f"  生成 Mobile 拼图-2 失败: {e}")
        return False


def prepare_mobile_desktop_3(work_dir: Path) -> bool:
    """
    准备 Mobile desktop-3 图片
    如果存在 mobile-2.png，则参照 mobile.png 的磨玻璃处理效果进行处理
    将 mobile-2.png 整张图做磨玻璃模糊效果，再使用 mobile-block-cover.png 图片生成 mobile-desktop-3.png

    Args:
        work_dir: 工作目录

    Returns:
        是否成功
    """
    mobile_desktop_3 = work_dir / 'mobile-desktop-3.png'
    if mobile_desktop_3.exists():
        logger.info(f"  mobile-desktop-3.png 已存在，跳过")
        return True

    mobile_2 = get_image_file(work_dir, 'mobile-2')
    if not mobile_2:
        logger.info(f"  未找到 mobile-2.png，跳过 mobile-desktop-3.png 生成")
        return True

    if not MOBILE_BLOCK_COVER.exists():
        logger.error(f"  缺少覆盖图片: {MOBILE_BLOCK_COVER}")
        return False

    try:
        base_img = Image.open(mobile_2)
        cover_img = Image.open(MOBILE_BLOCK_COVER)
        
        # 确保两张图片都是 9:19 比例
        base_ratio = base_img.width / base_img.height
        cover_ratio = cover_img.width / cover_img.height
        target_ratio = 9 / 19

        # 调整底图尺寸
        if abs(base_ratio - target_ratio) > 0.01:
            new_height = base_img.height
            new_width = int(new_height * target_ratio)
            base_img = base_img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # 调整覆盖图尺寸
        if abs(cover_ratio - target_ratio) > 0.01:
            new_height = cover_img.height
            new_width = int(new_height * target_ratio)
            cover_img = cover_img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # 确保两张图片尺寸一致
        if base_img.size != cover_img.size:
            cover_img = cover_img.resize(base_img.size, Image.Resampling.LANCZOS)

        # 对底图进行磨玻璃模糊效果（高斯模糊，参照 mobile.png 的处理效果，radius=140）
        blurred_img = base_img.filter(ImageFilter.GaussianBlur(radius=140))

        # 叠加覆盖图
        result = overlay_images(blurred_img, cover_img)
        result.save(mobile_desktop_3, 'PNG')
        logger.info(f"  已生成 mobile-desktop-3.png")
        return True
    except Exception as e:
        logger.error(f"  生成 mobile-desktop-3.png 失败: {e}")
        return False


def create_mobile_puzzle_3(work_dir: Path, output_dir: Path, main_color: Optional[str] = None) -> bool:
    """
    创建 Mobile 拼图-3
    两张图片居中水平排列，单个图片占总页面高度的70%
    使用 mobile-lock.jpg 和 mobile-desktop-3.png 拼接生成 mobile-combined-3.jpg

    Args:
        work_dir: 工作目录
        output_dir: 输出目录
        main_color: 主色调
    
    Returns:
        是否成功
    """
    mobile_lock_file = get_image_file(work_dir, 'mobile-lock')
    mobile_desktop_3_file = work_dir / 'mobile-desktop-3.png'

    if not mobile_lock_file or not mobile_desktop_3_file.exists():
        logger.info(f"  缺少 Mobile 拼图-3 所需文件，跳过")
        return True

    try:
        mobile_lock = Image.open(mobile_lock_file)
        mobile_desktop_3 = Image.open(mobile_desktop_3_file)

        # 确保两张图片都是 9:19 比例
        target_input_ratio = 9 / 19
        mobile_lock = resize_to_fit_ratio(mobile_lock, target_input_ratio, (2000, 4000))
        mobile_desktop_3 = resize_to_fit_ratio(mobile_desktop_3, target_input_ratio, (2000, 4000))

        # 先确定画布尺寸（1:1 比例）
        # 使用一个基准高度来计算画布尺寸
        base_height = 2000
        canvas_width = int(base_height * (OUTPUT_RATIO[0] / OUTPUT_RATIO[1]))
        canvas_height = base_height

        # 计算目标图片内容高度：每张图片占画布高度的70%
        # 注意：这是图片内容部分的高度，不包括阴影
        target_content_height = int(canvas_height * 0.7)
        # 根据 9:19 比例计算目标宽度
        target_content_width = int(target_content_height * target_input_ratio)

        # 调整两张图片到目标尺寸
        mobile_lock = mobile_lock.resize((target_content_width, target_content_height), Image.Resampling.LANCZOS)
        mobile_desktop_3 = mobile_desktop_3.resize((target_content_width, target_content_height), Image.Resampling.LANCZOS)

        # 添加阴影和圆角（这会使图片尺寸变大，因为增加了边距）
        mobile_lock = add_shadow_and_rounded_corners(mobile_lock)
        mobile_desktop_3 = add_shadow_and_rounded_corners(mobile_desktop_3)

        # 计算两张图片（带阴影）的总宽度和间距
        total_content_width = mobile_lock.width + mobile_desktop_3.width + SPACING

        # 如果总宽度超过画布，需要按比例缩小，但保持图片内容高度占70%的比例
        # 计算缩放比例，确保两张图片内容宽度之和 + 间距不超过画布
        max_total_width = canvas_width
        if total_content_width > max_total_width:
            # 计算需要缩小的比例
            # 目标：2 * target_content_width * scale + SPACING <= max_total_width
            # 所以：scale <= (max_total_width - SPACING) / (2 * target_content_width)
            max_scale = (max_total_width - SPACING) / (2 * target_content_width)
            if max_scale < 1.0:
                # 需要缩小（保持高度占70%的比例）
                new_target_content_width = int(target_content_width * max_scale)
                new_target_content_height = int(target_content_height * max_scale)

                # 重新调整图片尺寸
                mobile_lock = Image.open(mobile_lock_file)
                mobile_desktop_3 = Image.open(mobile_desktop_3_file)
                mobile_lock = resize_to_fit_ratio(mobile_lock, target_input_ratio, (2000, 4000))
                mobile_desktop_3 = resize_to_fit_ratio(mobile_desktop_3, target_input_ratio, (2000, 4000))
                mobile_lock = mobile_lock.resize((new_target_content_width, new_target_content_height), Image.Resampling.LANCZOS)
                mobile_desktop_3 = mobile_desktop_3.resize((new_target_content_width, new_target_content_height), Image.Resampling.LANCZOS)

                # 重新添加阴影和圆角
                mobile_lock = add_shadow_and_rounded_corners(mobile_lock)
                mobile_desktop_3 = add_shadow_and_rounded_corners(mobile_desktop_3)
                total_content_width = mobile_lock.width + mobile_desktop_3.width + SPACING

        # 创建背景
        # main_color = None: 使用默认背景（back.jpg）
        # main_color = "": 自动提取主色调
        # main_color = "#ffffff": 使用纯色背景
        original_mobile_lock = Image.open(mobile_lock_file)
        bg = create_background((canvas_width, canvas_height), main_color, original_mobile_lock)

        # 获取原始 mobile.png 图片尺寸
        mobile_file = get_image_file(work_dir, 'mobile')
        if mobile_file:
            original_mobile = Image.open(mobile_file)
            original_width, original_height = original_mobile.size
        else:
            # 如果没有找到 mobile.png，使用 mobile-lock 的尺寸
            original_width, original_height = original_mobile_lock.size

        # 计算居中位置（水平居中，垂直居中）
        x_offset = (canvas_width - total_content_width) // 2
        y_offset = (canvas_height - max(mobile_lock.height, mobile_desktop_3.height)) // 2

        # 粘贴图片
        bg.paste(mobile_lock, (x_offset, y_offset), mobile_lock)
        bg.paste(mobile_desktop_3, (x_offset + mobile_lock.width + SPACING, y_offset), mobile_desktop_3)

        # 添加尺寸水印（使用原始 mobile.png 的尺寸）
        bg = add_size_watermark(bg, original_width, original_height)
        
        # 保存为 JPG 格式（压缩到 500KB 以内）
        output_file = output_dir / 'mobile-combined-3.jpg'
        save_optimized_jpeg(bg, output_file)
        logger.info(f"  已生成 mobile-combined-3.jpg")
        return True
    except Exception as e:
        logger.error(f"  生成 Mobile 拼图-3 失败: {e}")
        return False

