#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日历拼图工具
用于批量处理日历拼图任务，自动遍历指定目录下的图片文件夹，将12张日历图片按照特定规则拼接。
"""

import sys
import logging
from pathlib import Path
from typing import List, Optional
from PIL import Image

# 尝试相对导入，如果失败则使用绝对导入
try:
    from .utils import BACK_IMAGE, save_final_puzzle_image, add_rounded_corners_and_shadow
except ImportError:
    from utils import BACK_IMAGE, save_final_puzzle_image, add_rounded_corners_and_shadow

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# 常量定义
IMGS_DIR = Path(__file__).parent / 'imgs'
RESULT_DIR_SUFFIX = '-result'  # 结果目录后缀


def find_calendar_images(work_dir: Path) -> List[Path]:
    """
    查找目录下的日历图片（1.png 到 12.png）
    
    Args:
        work_dir: 工作目录
    
    Returns:
        排序后的图片路径列表
    """
    images = []
    
    # 查找1-12的图片文件
    for i in range(1, 13):
        # 尝试多种可能的文件扩展名
        for ext in ['.png', '.jpg', '.jpeg', '.PNG', '.JPG', '.JPEG']:
            img_file = work_dir / f"{i}{ext}"
            if img_file.exists():
                images.append(img_file)
                break
    
    return sorted(images, key=lambda x: int(x.stem))


def create_overview_puzzle(
    back_img: Image.Image,
    calendar_images: List[Image.Image]
) -> Image.Image:
    """
    创建概览拼图：将12张日历图片按每行3张，共4行拼成一张概览图
    
    Args:
        back_img: 背景图片（back.png）
        calendar_images: 12张日历图片列表
    
    Returns:
        拼图结果（保持背景图尺寸）
    """
    back_width, back_height = back_img.size
    
    # 确保back.png是RGB模式
    if back_img.mode == 'RGBA':
        bg = Image.new('RGB', back_img.size, (255, 255, 255))
        bg.paste(back_img, mask=back_img.split()[3])
        result_img = bg
    elif back_img.mode != 'RGB':
        result_img = back_img.convert('RGB')
    else:
        result_img = back_img.copy()
    
    # 计算每张图片的尺寸
    # 每行3张，共4行，需要留出间距
    # 上半部分预留10%的空白
    rows = 4
    cols = 3
    top_margin_ratio = 0.1  # 上半部分预留10%空白
    padding_ratio = 0.05  # 边距比例（相对于背景图宽度）
    spacing_ratio = 0.02  # 图片间距比例（相对于背景图宽度）
    
    top_margin = int(back_height * top_margin_ratio)
    padding = int(back_width * padding_ratio)
    spacing = int(back_width * spacing_ratio)
    
    # 计算每张图片的可用宽度和高度（从20%位置开始）
    available_width = back_width - padding * 2 - spacing * (cols - 1)
    available_height = back_height - top_margin - padding * 2 - spacing * (rows - 1)
    
    img_width = available_width // cols
    img_height = available_height // rows
    
    # 处理每张日历图片
    processed_images = []
    for img in calendar_images:
        # 确保图片是RGB或RGBA模式
        if img.mode not in ('RGB', 'RGBA'):
            img = img.convert('RGBA')
        
        # 调整图片尺寸，保持宽高比
        img_ratio = img.width / img.height
        target_ratio = img_width / img_height
        
        if img_ratio > target_ratio:
            # 图片更宽，以高度为准
            new_height = img_height
            new_width = int(new_height * img_ratio)
        else:
            # 图片更高，以宽度为准
            new_width = img_width
            new_height = int(new_width / img_ratio)
        
        # 如果调整后的尺寸超出，需要进一步缩放
        if new_width > img_width:
            new_width = img_width
            new_height = int(new_width / img_ratio)
        if new_height > img_height:
            new_height = img_height
            new_width = int(new_height * img_ratio)
        
        resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # 创建居中放置的画布
        canvas = Image.new('RGBA', (img_width, img_height), (255, 255, 255, 0))
        paste_x = (img_width - new_width) // 2
        paste_y = (img_height - new_height) // 2
        canvas.paste(resized_img, (paste_x, paste_y), resized_img if resized_img.mode == 'RGBA' else None)
        
        # 添加圆角和阴影效果
        canvas_with_effect = add_rounded_corners_and_shadow(
            canvas,
            corner_radius=25,
            shadow_offset=(5, 5),
            shadow_blur=10,
            shadow_opacity=100
        )
        
        processed_images.append(canvas_with_effect)
    
    # 将处理后的图片拼接到背景图上
    # 计算阴影和偏移后的实际尺寸
    shadow_offset_x = 5
    shadow_offset_y = 5
    shadow_blur = 10
    shadow_padding_x = abs(shadow_offset_x) + shadow_blur
    shadow_padding_y = abs(shadow_offset_y) + shadow_blur
    
    for row in range(rows):
        for col in range(cols):
            idx = row * cols + col
            if idx < len(processed_images):
                # 计算基础位置（考虑阴影偏移）
                base_x = padding + col * (img_width + spacing)
                base_y = top_margin + padding + row * (img_height + spacing)
                
                # 调整位置以居中阴影效果
                x = base_x - shadow_padding_x
                y = base_y - shadow_padding_y
                
                result_img.paste(processed_images[idx], (x, y), processed_images[idx])
    
    return result_img


def create_single_calendar_puzzle(
    back_img: Image.Image,
    calendar_img: Image.Image
) -> Image.Image:
    """
    创建单张日历拼图：日历图片居中，宽度占底图宽度的60%
    
    Args:
        back_img: 背景图片（back.png）
        calendar_img: 日历图片
    
    Returns:
        拼图结果（保持背景图尺寸）
    """
    back_width, back_height = back_img.size
    
    # 确保back.png是RGB模式
    if back_img.mode == 'RGBA':
        bg = Image.new('RGB', back_img.size, (255, 255, 255))
        bg.paste(back_img, mask=back_img.split()[3])
        result_img = bg
    elif back_img.mode != 'RGB':
        result_img = back_img.convert('RGB')
    else:
        result_img = back_img.copy()
    
    # 计算日历图片的目标宽度（底图宽度的65%）
    target_width = int(back_width * 0.65)
    
    # 确保图片是RGB或RGBA模式
    if calendar_img.mode not in ('RGB', 'RGBA'):
        calendar_img = calendar_img.convert('RGBA')
    
    # 调整图片尺寸，保持宽高比
    img_ratio = calendar_img.width / calendar_img.height
    new_width = target_width
    new_height = int(new_width / img_ratio)
    
    # 如果高度超出背景图，以高度为准重新计算
    if new_height > back_height * 0.9:  # 留10%的边距
        new_height = int(back_height * 0.9)
        new_width = int(new_height * img_ratio)
    
    resized_img = calendar_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    # 添加圆角和阴影效果
    img_with_effect = add_rounded_corners_and_shadow(
        resized_img,
        corner_radius=25,
        shadow_offset=(5, 5),
        shadow_blur=10,
        shadow_opacity=100
    )
    
    # 计算居中位置（考虑阴影偏移）
    shadow_offset_x = 5
    shadow_offset_y = 5
    shadow_blur = 10
    shadow_padding_x = abs(shadow_offset_x) + shadow_blur
    shadow_padding_y = abs(shadow_offset_y) + shadow_blur
    
    effect_width, effect_height = img_with_effect.size
    paste_x = (back_width - effect_width) // 2
    paste_y = (back_height - effect_height) // 2
    
    # 粘贴到背景图上
    result_img.paste(img_with_effect, (paste_x, paste_y), img_with_effect)
    
    return result_img


def process_directory(work_dir: Path, back_img: Image.Image) -> bool:
    """
    处理单个目录
    
    Args:
        work_dir: 工作目录
        back_img: 底图
    
    Returns:
        是否成功
    """
    logger.info(f"处理目录: {work_dir.name}")
    
    # 检查结果目录是否已存在
    result_dir_name = f"{work_dir.name}{RESULT_DIR_SUFFIX}"
    result_dir = work_dir.parent / result_dir_name
    if result_dir.exists() and result_dir.is_dir():
        logger.info(f"  结果目录已存在，跳过: {result_dir_name}")
        return True
    
    # 查找日历图片
    image_files = find_calendar_images(work_dir)
    
    if len(image_files) != 12:
        logger.warning(f"  找到 {len(image_files)} 张图片，期望12张")
        if len(image_files) == 0:
            return False
    
    logger.info(f"  找到 {len(image_files)} 张日历图片")
    
    # 创建结果目录
    result_dir.mkdir(parents=True, exist_ok=True)
    
    # 打开所有日历图片
    calendar_images = []
    for img_file in image_files:
        try:
            img = Image.open(img_file)
            calendar_images.append(img)
        except Exception as e:
            logger.error(f"  打开图片失败 {img_file.name}: {e}")
            return False
    
    success_count = 0
    
    # 拼图逻辑1：创建概览图
    try:
        overview_img = create_overview_puzzle(back_img, calendar_images)
        overview_file = result_dir / 'overview.jpg'
        save_final_puzzle_image(overview_img, overview_file)
        logger.info(f"  已创建概览图: overview.jpg")
        success_count += 1
    except Exception as e:
        logger.error(f"  创建概览图失败: {e}")
    
    # 拼图逻辑2：为每张图片创建独立拼图
    for idx, (img_file, calendar_img) in enumerate(zip(image_files, calendar_images), 1):
        try:
            single_img = create_single_calendar_puzzle(back_img, calendar_img)
            output_name = f"{idx}.jpg"
            output_file = result_dir / output_name
            save_final_puzzle_image(single_img, output_file)
            logger.info(f"  已处理: {img_file.name} -> {output_name}")
            success_count += 1
        except Exception as e:
            logger.error(f"  处理图片失败 {img_file.name}: {e}")
    
    logger.info(f"  处理完成: {success_count}/{len(image_files) + 1} 个文件成功")
    return success_count > 0


def main():
    """
    主函数
    """
    # 检查底图是否存在
    if not BACK_IMAGE.exists():
        logger.error(f"底图不存在: {BACK_IMAGE}")
        sys.exit(1)
    
    # 打开底图
    try:
        back_img = Image.open(BACK_IMAGE)
        logger.info(f"底图尺寸: {back_img.size[0]}x{back_img.size[1]}, 模式: {back_img.mode}")
    except Exception as e:
        logger.error(f"打开底图失败: {e}")
        sys.exit(1)
    
    # 检查 imgs 目录
    if not IMGS_DIR.exists():
        logger.error(f"图片目录不存在: {IMGS_DIR}")
        sys.exit(1)
    
    # 遍历所有子目录（排除结果目录）
    subdirs = [d for d in IMGS_DIR.iterdir() if d.is_dir() and not d.name.endswith(RESULT_DIR_SUFFIX)]
    
    if not subdirs:
        logger.warning("未找到任何子目录")
        return
    
    logger.info(f"找到 {len(subdirs)} 个子目录")
    
    # 处理每个目录
    logger.info("=" * 50)
    logger.info("处理日历拼图")
    logger.info("=" * 50)
    success_count = 0
    for subdir in subdirs:
        try:
            if process_directory(subdir, back_img):
                success_count += 1
        except Exception as e:
            logger.error(f"处理目录 {subdir.name} 时发生错误: {e}")
    
    logger.info(f"日历拼图处理完成: {success_count}/{len(subdirs)} 个目录成功")


if __name__ == '__main__':
    main()
