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
    # 上半部分预留9.5%的空白（缩小5%）
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

    # 整体缩小5%
    img_width = int(available_width // cols * 0.95)
    img_height = int(available_height // rows * 0.95)

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

        # 确保图片是RGBA模式
        if resized_img.mode != 'RGBA':
            resized_img = resized_img.convert('RGBA')

        # 直接在原图上添加圆角和阴影效果，不要有白边
        img_with_effect = add_rounded_corners_and_shadow(
            resized_img,
            corner_radius=25,
            shadow_offset=(5, 5),
            shadow_blur=10,
            shadow_opacity=100
        )

        processed_images.append(img_with_effect)

    # 将处理后的图片拼接到背景图上
    # 计算整个拼图区域的尺寸（用于整体居中）
    total_width = cols * img_width + (cols - 1) * spacing
    total_height = rows * img_height + (rows - 1) * spacing

    # 计算整体拼图区域的起始位置（居中）
    start_x = (back_width - total_width) // 2
    start_y = (back_height - total_height) // 2

    for row in range(rows):
        for col in range(cols):
            idx = row * cols + col
            if idx < len(processed_images):
                # 计算单元格的中心位置（基于整体居中后的起始位置）
                cell_x = start_x + col * (img_width + spacing) + img_width // 2
                cell_y = start_y + row * (img_height + spacing) + img_height // 2

                # 获取处理后的图片尺寸（包括阴影边距）
                img_with_effect = processed_images[idx]
                effect_width, effect_height = img_with_effect.size

                # 计算粘贴位置，使图片在单元格内居中
                x = cell_x - effect_width // 2
                y = cell_y - effect_height // 2

                result_img.paste(img_with_effect, (x, y), img_with_effect)

    return result_img


def create_overview_puzzle_2x2(
    back_img: Image.Image,
    calendar_images: List[Image.Image]
) -> Image.Image:
    """
    创建2x2概览拼图：将4张日历图片按每行2张，共2行拼成一张概览图

    Args:
        back_img: 背景图片（back.png）
        calendar_images: 4张日历图片列表

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
    # 每行2张，共2行，需要留出间距
    rows = 2
    cols = 2
    top_margin_ratio = 0.1  # 上半部分预留10%空白
    padding_ratio = 0.05  # 边距比例（相对于背景图宽度）
    spacing_ratio = 0.02  # 图片间距比例（相对于背景图宽度）

    top_margin = int(back_height * top_margin_ratio)
    padding = int(back_width * padding_ratio)
    spacing = int(back_width * spacing_ratio)

    # 计算每张图片的可用宽度和高度
    available_width = back_width - padding * 2 - spacing * (cols - 1)
    available_height = back_height - top_margin - padding * 2 - spacing * (rows - 1)

    # 整体缩小5%
    img_width = int(available_width // cols * 0.95)
    img_height = int(available_height // rows * 0.95)

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

        # 确保图片是RGBA模式
        if resized_img.mode != 'RGBA':
            resized_img = resized_img.convert('RGBA')

        # 直接在原图上添加圆角和阴影效果，不要有白边
        img_with_effect = add_rounded_corners_and_shadow(
            resized_img,
            corner_radius=25,
            shadow_offset=(5, 5),
            shadow_blur=10,
            shadow_opacity=100
        )

        processed_images.append(img_with_effect)

    # 将处理后的图片拼接到背景图上
    # 计算整个拼图区域的尺寸（用于整体居中）
    total_width = cols * img_width + (cols - 1) * spacing
    total_height = rows * img_height + (rows - 1) * spacing

    # 计算整体拼图区域的起始位置（居中）
    start_x = (back_width - total_width) // 2
    start_y = (back_height - total_height) // 2

    for row in range(rows):
        for col in range(cols):
            idx = row * cols + col
            if idx < len(processed_images):
                # 计算单元格的中心位置（基于整体居中后的起始位置）
                cell_x = start_x + col * (img_width + spacing) + img_width // 2
                cell_y = start_y + row * (img_height + spacing) + img_height // 2

                # 获取处理后的图片尺寸（包括阴影边距）
                img_with_effect = processed_images[idx]
                effect_width, effect_height = img_with_effect.size

                # 计算粘贴位置，使图片在单元格内居中
                x = cell_x - effect_width // 2
                y = cell_y - effect_height // 2

                result_img.paste(img_with_effect, (x, y), img_with_effect)

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

    # 计算日历图片的目标宽度（底图宽度的68.25%，即65% * 1.05）
    target_width = int(back_width * 0.6825)

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

    # 计算居中位置（考虑阴影边距，新实现会在图片周围添加shadow_margin边距）
    shadow_offset = (5, 5)
    shadow_blur = 10
    shadow_margin = max(shadow_offset) + shadow_blur

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

    # 检测back.png的比例
    back_width, back_height = back_img.size
    back_ratio = back_width / back_height
    is_square = abs(back_ratio - 1.0) < 0.01  # 允许0.01的误差

    # 拼图逻辑1：创建概览图
    if is_square:
        # 当back.png是1:1时，按每行2列共4张图作为一张拼图结果，共产生3张overview拼图结果
        try:
            # 将12张图片分成3组，每组4张
            for group_idx in range(3):
                start_idx = group_idx * 4
                end_idx = start_idx + 4
                group_images = calendar_images[start_idx:end_idx]
                
                if len(group_images) == 4:
                    overview_img = create_overview_puzzle_2x2(back_img, group_images)
                    overview_file = result_dir / f'overview{group_idx + 1}.jpg'
                    save_final_puzzle_image(overview_img, overview_file)
                    logger.info(f"  已创建概览图: overview{group_idx + 1}.jpg")
                    success_count += 1
        except Exception as e:
            logger.error(f"  创建概览图失败: {e}")
    else:
        # 原有逻辑：将12张日历图片按每行3张，共4行拼成一张概览图
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
