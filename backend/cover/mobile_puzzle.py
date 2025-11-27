#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mobile 拼图模块
处理 Mobile 相关的图片拼接任务
"""

import logging
from pathlib import Path
from typing import Optional
from PIL import Image

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
        save_optimized_image
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
        save_optimized_image
    )

logger = logging.getLogger(__name__)


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

        # 计算居中位置（水平居中，垂直居中）
        x_offset = (canvas_width - total_content_width) // 2
        y_offset = (canvas_height - max(mobile_lock.height, mobile_desktop.height)) // 2

        # 粘贴图片
        bg.paste(mobile_lock, (x_offset, y_offset), mobile_lock)
        bg.paste(mobile_desktop, (x_offset + mobile_lock.width + SPACING, y_offset), mobile_desktop)

        # 保存并优化文件大小
        output_file = output_dir / 'mobile-combined.png'
        save_optimized_image(bg, output_file)

        logger.info(f"  已生成 mobile-combined.png")
        return True
    except Exception as e:
        logger.error(f"  生成 Mobile 拼图失败: {e}")
        return False

