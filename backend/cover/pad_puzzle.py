#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pad 拼图模块
处理 Pad 相关的图片拼接任务
"""

import logging
from pathlib import Path
from typing import Optional
from PIL import Image

# 尝试相对导入，如果失败则使用绝对导入
try:
    from .utils import (
        PAD_BLOCK_COVER,
        PAD_LOCK_COVER,
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
        PAD_BLOCK_COVER,
        PAD_LOCK_COVER,
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


def prepare_pad_images(work_dir: Path) -> bool:
    """
    准备 Pad desktop 和 lock 图片
    
    Args:
        work_dir: 工作目录
    
    Returns:
        是否成功
    """
    pad = get_image_file(work_dir, 'pad')
    if not pad:
        logger.info(f"  未找到 pad.png，跳过 Pad 图片预处理")
        return True
    
    success = True
    
    # 处理 pad-desktop.png
    pad_desktop = work_dir / 'pad-desktop.png'
    if not pad_desktop.exists():
        # 根据 README，pad-desktop.png 使用 pad-block-cover.png
        if not PAD_BLOCK_COVER.exists():
            logger.warning(f"  缺少覆盖图片: {PAD_BLOCK_COVER}，跳过 pad-desktop.png 生成")
        else:
            try:
                base_img = Image.open(pad)
                cover_img = Image.open(PAD_BLOCK_COVER)
                
                # 确保两张图片都是 4:3 比例
                target_ratio = 4 / 3
                base_ratio = base_img.width / base_img.height
                cover_ratio = cover_img.width / cover_img.height
                
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
                result.save(pad_desktop, 'PNG')
                logger.info(f"  已生成 pad-desktop.png")
            except Exception as e:
                logger.error(f"  生成 pad-desktop.png 失败: {e}")
                success = False
    else:
        logger.info(f"  pad-desktop.png 已存在，跳过")
    
    # 处理 pad-lock.png
    pad_lock = work_dir / 'pad-lock.png'
    if not pad_lock.exists():
        if not PAD_LOCK_COVER.exists():
            logger.warning(f"  缺少覆盖图片: {PAD_LOCK_COVER}，跳过 pad-lock.png 生成")
        else:
            try:
                base_img = Image.open(pad)
                cover_img = Image.open(PAD_LOCK_COVER)
                
                # 确保两张图片都是 4:3 比例
                target_ratio = 4 / 3
                base_ratio = base_img.width / base_img.height
                cover_ratio = cover_img.width / cover_img.height
                
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
                result.save(pad_lock, 'PNG')
                logger.info(f"  已生成 pad-lock.png")
            except Exception as e:
                logger.error(f"  生成 pad-lock.png 失败: {e}")
                success = False
    else:
        logger.info(f"  pad-lock.png 已存在，跳过")
    
    return success


def create_pad_puzzle(work_dir: Path, output_dir: Path, main_color: Optional[str] = None) -> bool:
    """
    创建 Pad 拼图
    要求：单个图片宽度占整体图片的70%，高度不超过40%，两张图片纵向拼接，图片间有间隙
    
    Args:
        work_dir: 工作目录
        output_dir: 输出目录
        main_color: 主色调
    
    Returns:
        是否成功
    """
    pad_file = get_image_file(work_dir, 'pad')

    # 如果不存在 pad.png，跳过 Pad 壁纸拼接
    if not pad_file:
        logger.info(f"  未找到 pad.png，跳过 Pad 壁纸拼接")
        return True

    pad_lock_file = get_image_file(work_dir, 'pad-lock')
    pad_desktop_file = work_dir / 'pad-desktop.png'
    
    # 优先使用 pad-lock.png，如果不存在则使用 pad-lock.jpg 等
    if not pad_lock_file:
        pad_lock_file = work_dir / 'pad-lock.png'
    
    if not pad_lock_file.exists() or not pad_desktop_file.exists():
        logger.error(f"  缺少 Pad 拼图所需文件")
        return False
    
    try:
        # 先确定画布尺寸（1:1 比例）
        # 使用一个基准高度来计算画布尺寸
        base_height = 2000
        canvas_width = int(base_height * (OUTPUT_RATIO[0] / OUTPUT_RATIO[1]))
        canvas_height = base_height
        
        # 计算单张图片的目标尺寸
        # 单个图片宽度占整体图片的70%，高度不超过40%
        target_content_width = int(canvas_width * 0.7)
        target_content_height = int(canvas_height * 0.4)

        # 目标输入比例是 4:3
        target_input_ratio = 4 / 3

        # 准备原始图片文件路径和图片对象
        image_files = []
        source_img = None

        if pad_lock_file.exists():
            image_files.append(('lock', pad_lock_file))
            if source_img is None:
                source_img = Image.open(pad_lock_file)

        if pad_desktop_file.exists():
            image_files.append(('desktop', pad_desktop_file))
            if source_img is None:
                source_img = Image.open(pad_desktop_file)

        if not image_files:
            return False

        # 处理每张图片的函数
        def process_image(img_file_path: Path, target_w: int, target_h: int) -> Image.Image:
            """处理单张图片到目标尺寸"""
            img = Image.open(img_file_path)
            # 先调整图片到 4:3 比例
            img = resize_to_fit_ratio(img, target_input_ratio, (3000, 2250))

            # 计算缩放比例，确保图片能放入目标区域
            # 按宽度缩放
            scale_by_width = target_w / img.width
            scaled_height_by_width = img.height * scale_by_width

            # 按高度缩放（高度不超过40%）
            scale_by_height = target_h / img.height
            scaled_width_by_height = img.width * scale_by_height

            # 选择较小的缩放比例，确保图片完全放入目标区域，且高度不超过40%
            if scaled_height_by_width <= target_h:
                # 按宽度缩放，高度不会超出
                final_width = target_w
                final_height = int(scaled_height_by_width)
            else:
                # 按高度缩放，宽度不会超出
                final_width = int(scaled_width_by_height)
                final_height = target_h

            # 调整图片尺寸
            img = img.resize((final_width, final_height), Image.Resampling.LANCZOS)

            # 添加阴影和圆角（这会使图片尺寸变大，因为增加了边距）
            img = add_shadow_and_rounded_corners(img)
            return img

        # 第一次处理图片
        processed_images = []
        for name, img_file in image_files:
            img = process_image(img_file, target_content_width, target_content_height)
            processed_images.append(img)

        # 计算两张图片的总高度（包括阴影边距）和间隔
        total_content_height = sum(img.height for img in processed_images) + SPACING * (len(processed_images) - 1)

        # 如果总高度超过画布，需要按比例缩小
        if total_content_height > canvas_height:
            # 计算缩放比例（基于总高度，包括阴影和间隔）
            max_available_height = canvas_height
            spacing_total = SPACING * (len(processed_images) - 1)
            images_total_height = total_content_height - spacing_total
            if images_total_height > 0:
                scale = (max_available_height - spacing_total) / images_total_height
            else:
                scale = 1.0

            # 重新处理图片，按比例缩小目标尺寸
            new_target_content_width = int(target_content_width * scale)
            new_target_content_height = int(target_content_height * scale)

            processed_images = []
            for name, img_file in image_files:
                img = process_image(img_file, new_target_content_width, new_target_content_height)
                processed_images.append(img)

            total_content_height = sum(img.height for img in processed_images) + SPACING * (len(processed_images) - 1)

        # 创建背景
        # main_color = None: 使用默认背景（back.jpg）
        # main_color = "": 自动提取主色调
        # main_color = "#ffffff": 使用纯色背景
        bg = create_background((canvas_width, canvas_height), main_color, source_img)

        # 计算居中位置（水平居中，垂直居中）
        x_offset = (canvas_width - max(img.width for img in processed_images)) // 2
        y_start = (canvas_height - total_content_height) // 2

        # 粘贴图片（纵向排列）
        current_y = y_start
        for img in processed_images:
            # 水平居中
            x_pos = x_offset + (max(img.width for img in processed_images) - img.width) // 2
            bg.paste(img, (x_pos, current_y), img)
            current_y += img.height + SPACING

        # 保存并优化文件大小
        output_file = output_dir / 'pad-combined.png'
        save_optimized_image(bg, output_file)

        logger.info(f"  已生成 pad-combined.png")
        return True
    except Exception as e:
        logger.error(f"  生成 Pad 拼图失败: {e}")
        return False

