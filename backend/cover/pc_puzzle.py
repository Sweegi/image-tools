#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PC 拼图模块
处理 PC 相关的图片拼接任务
"""

import logging
from pathlib import Path
from typing import Optional
from PIL import Image

# 尝试相对导入，如果失败则使用绝对导入
try:
    from .utils import (
        PC_MAC_COVER,
        OUTPUT_RATIO,
        SPACING,
        SHADOW_OFFSET,
        SHADOW_BLUR,
        overlay_images,
        add_shadow_and_rounded_corners,
        resize_to_fit_ratio,
        create_background,
        get_image_file,
        save_optimized_image
    )
except ImportError:
    from utils import (
        PC_MAC_COVER,
        OUTPUT_RATIO,
        SPACING,
        SHADOW_OFFSET,
        SHADOW_BLUR,
        overlay_images,
        add_shadow_and_rounded_corners,
        resize_to_fit_ratio,
        create_background,
        get_image_file,
        save_optimized_image
    )

logger = logging.getLogger(__name__)


def prepare_pc_desktop_mac(work_dir: Path) -> bool:
    """
    准备 PC desktop mac 图片

    Args:
        work_dir: 工作目录

    Returns:
        是否成功
    """
    pc_desktop_mac = work_dir / 'pc-desktop-mac.png'
    if pc_desktop_mac.exists():
        logger.info(f"  pc-desktop-mac.png 已存在，跳过")
        return True

    pc = work_dir / 'pc.png'
    if not pc.exists():
        logger.error(f"  缺少 pc.png")
        return False

    if not PC_MAC_COVER.exists():
        logger.warning(f"  缺少覆盖图片: {PC_MAC_COVER}，跳过 pc-desktop-mac.png 生成")
        return False

    try:
        base_img = Image.open(pc)
        cover_img = Image.open(PC_MAC_COVER)

        # 确保两张图片都是 16:9 比例
        target_ratio = 16 / 9
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
        result.save(pc_desktop_mac, 'PNG')
        logger.info(f"  已生成 pc-desktop-mac.png")
        return True
    except Exception as e:
        logger.error(f"  生成 pc-desktop-mac.png 失败: {e}")
        return False

def create_pc_puzzle(work_dir: Path, output_dir: Path, main_color: Optional[str] = None) -> bool:
    """
    创建 PC 拼图
    要求：单个图片宽度占整体图片的80%，高度占40%，两张图片之间保留间隔

    Args:
        work_dir: 工作目录
        output_dir: 输出目录
        main_color: 主色调

    Returns:
        是否成功
    """
    pc_block_file = get_image_file(work_dir, 'pc-block')
    pc_desktop_mac_file = work_dir / 'pc-desktop-mac.png'
    
    # 特殊情况：如果只存在其中一张图片，则将该图居中显示
    if not pc_block_file and not pc_desktop_mac_file.exists():
        logger.error(f"  缺少 PC 拼图所需文件")
        return False

    try:
        # 先确定画布尺寸（1:1 比例）
        # 使用一个基准高度来计算画布尺寸
        base_height = 2000
        canvas_width = int(base_height * (OUTPUT_RATIO[0] / OUTPUT_RATIO[1]))
        canvas_height = base_height

        # 计算单张图片的目标尺寸
        # 单个图片宽度占整体图片的80%，高度占40%
        target_content_width = int(canvas_width * 0.8)
        target_content_height = int(canvas_height * 0.4)

        # 目标输入比例是 16:9
        target_input_ratio = 16 / 9

        # 准备原始图片文件路径和图片对象
        image_files = []
        source_img = None

        if pc_block_file:
            image_files.append(('block', pc_block_file))
            if source_img is None:
                source_img = Image.open(pc_block_file)

        if pc_desktop_mac_file.exists():
            image_files.append(('desktop', pc_desktop_mac_file))
            if source_img is None:
                source_img = Image.open(pc_desktop_mac_file)

        if not image_files:
            return False

        # 处理每张图片的函数
        def process_image(img_file_path: Path, target_w: int, target_h: int) -> Image.Image:
            """处理单张图片到目标尺寸"""
            img = Image.open(img_file_path)
            # 先调整图片到 16:9 比例
            img = resize_to_fit_ratio(img, target_input_ratio, (4000, 2000))

            # 计算缩放比例，确保图片能放入目标区域
            # 按宽度缩放
            scale_by_width = target_w / img.width
            scaled_height_by_width = img.height * scale_by_width

            # 按高度缩放
            scale_by_height = target_h / img.height
            scaled_width_by_height = img.width * scale_by_height

            # 选择较小的缩放比例，确保图片完全放入目标区域
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

        # 粘贴图片
        current_y = y_start
        for img in processed_images:
            # 水平居中
            x_pos = x_offset + (max(img.width for img in processed_images) - img.width) // 2
            bg.paste(img, (x_pos, current_y), img)
            current_y += img.height + SPACING

        # 保存并优化文件大小
        output_file = output_dir / 'pc-combined.png'
        save_optimized_image(bg, output_file)

        logger.info(f"  已生成 pc-combined.png")
        return True
    except Exception as e:
        logger.error(f"  生成 PC 拼图失败: {e}")
        return False
