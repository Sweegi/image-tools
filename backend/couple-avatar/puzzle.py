#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
情侣头像拼图工具
用于批量处理情侣头像拼图任务，自动遍历指定目录下的图片文件夹，将成对的图片按照特定规则拼接成新的图片。
"""

import sys
import logging
from pathlib import Path
from typing import List, Tuple, Optional
from PIL import Image

# 尝试相对导入，如果失败则使用绝对导入
try:
    from .utils import (
        BACK_IMAGE, BACK1_IMAGE, add_shadow_and_rounded_corners, 
        save_final_puzzle_image, create_circular_image, create_rounded_square_image,
        create_couple_background, add_border
    )
except ImportError:
    from utils import (
        BACK_IMAGE, BACK1_IMAGE, add_shadow_and_rounded_corners, 
        save_final_puzzle_image, create_circular_image, create_rounded_square_image,
        create_couple_background, add_border
    )

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# 常量定义
IMGS_DIR = Path(__file__).parent / 'imgs'
RESULT_DIR_NAME_SINGLE = 'single-result'  # 单个头像处理结果目录


def find_image_pairs(work_dir: Path) -> List[Tuple[Path, Path]]:
    """
    查找目录下的图片配对（*-a.png 和 *-b.png）
    
    Args:
        work_dir: 工作目录
    
    Returns:
        配对列表，每个元素是 (a图片路径, b图片路径) 的元组
    """
    pairs = []
    
    # 查找所有 -a.png 文件
    a_files = sorted(work_dir.glob('*-a.png'))
    
    for a_file in a_files:
        # 构造对应的 b 文件路径
        b_file_name = a_file.name.replace('-a.png', '-b.png')
        b_file = work_dir / b_file_name
        
        if b_file.exists():
            pairs.append((a_file, b_file))
        else:
            logger.warning(f"  未找到配对文件: {b_file_name}")
    
    return pairs


def create_couple_puzzle(
    back_img: Image.Image,
    img_a: Image.Image,
    img_b: Image.Image,
    horizontal_spacing_ratio: float = 0.15,
    vertical_offset_ratio: float = 0.25
) -> Image.Image:
    """
    创建情侣头像拼图
    
    Args:
        back_img: 原始back.png底图
        img_a: 第一张图片（左侧）
        img_b: 第二张图片（右侧）
        horizontal_spacing_ratio: 水平间距比例（相对于图片宽度）
        vertical_offset_ratio: 垂直错位比例（相对于图片高度）
    
    Returns:
        拼图结果（保持底图比例）
    """
    # 先创建背景底图：将a、b图片无缝平接，从中间按3:4比例裁剪，添加磨玻璃效果，然后覆盖back.png
    back_width, back_height = back_img.size
    target_size = (back_width, back_height)
    
    # 创建背景底图
    final_back_img = create_couple_background(img_a, img_b, back_img, target_size)
    
    # 计算图片的最大尺寸（使用底图的较小尺寸的45%，放大图片）
    max_size = int(min(back_width, back_height) * 0.45)
    
    # 调整图片尺寸（保持1:1比例）
    if img_a.width != img_a.height:
        # 如果不是正方形，裁剪为正方形（居中裁剪）
        size = min(img_a.width, img_a.height)
        left = (img_a.width - size) // 2
        top = (img_a.height - size) // 2
        img_a = img_a.crop((left, top, left + size, top + size))
    
    if img_b.width != img_b.height:
        size = min(img_b.width, img_b.height)
        left = (img_b.width - size) // 2
        top = (img_b.height - size) // 2
        img_b = img_b.crop((left, top, left + size, top + size))
    
    # 缩放图片到最大尺寸
    if img_a.width > max_size:
        img_a = img_a.resize((max_size, max_size), Image.Resampling.LANCZOS)
    if img_b.width > max_size:
        img_b = img_b.resize((max_size, max_size), Image.Resampling.LANCZOS)
    
    # 添加圆角和阴影效果
    img_a_with_effects = add_shadow_and_rounded_corners(img_a)
    img_b_with_effects = add_shadow_and_rounded_corners(img_b)
    
    # 使用处理后的背景底图
    result_img = final_back_img.copy()
    
    # 确保result_img是RGB模式
    if result_img.mode != 'RGB':
        result_img = result_img.convert('RGB')
    
    # 计算水平间距（相对于图片宽度）
    horizontal_spacing = int(max(img_a_with_effects.width, img_b_with_effects.width) * horizontal_spacing_ratio)
    
    # 计算两张图片的总宽度（包括间距）
    total_width = img_a_with_effects.width + horizontal_spacing + img_b_with_effects.width
    
    # 计算垂直错位量（相对于图片高度）
    vertical_offset = int(max(img_a_with_effects.height, img_b_with_effects.height) * vertical_offset_ratio)
    
    # 计算整体居中位置（水平居中）
    center_x = back_width // 2
    start_x = center_x - total_width // 2
    
    # 计算垂直居中位置
    center_y = back_height // 2
    
    # 计算左侧图片位置（整体居中，左侧图片向上错位）
    left_x = start_x
    left_y = center_y - img_a_with_effects.height // 2 - vertical_offset
    
    # 计算右侧图片位置（整体居中，右侧图片向下错位）
    right_x = start_x + img_a_with_effects.width + horizontal_spacing
    right_y = center_y - img_b_with_effects.height // 2 + vertical_offset
    
    # 确保图片不超出边界
    left_x = max(0, min(left_x, back_width - img_a_with_effects.width))
    left_y = max(0, min(left_y, back_height - img_a_with_effects.height))
    right_x = max(0, min(right_x, back_width - img_b_with_effects.width))
    right_y = max(0, min(right_y, back_height - img_b_with_effects.height))
    
    # 粘贴图片（自动处理透明通道）
    result_img.paste(img_a_with_effects, (left_x, left_y), img_a_with_effects)
    result_img.paste(img_b_with_effects, (right_x, right_y), img_b_with_effects)
    
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
    
    # 检查结果目录是否已存在（目录名-a-result）
    result_dir_name = f"{work_dir.name}-a-result"
    result_dir = work_dir.parent / result_dir_name
    if result_dir.exists() and result_dir.is_dir():
        logger.info(f"  结果目录已存在，跳过: {result_dir_name}")
        return True
    
    # 查找图片配对
    pairs = find_image_pairs(work_dir)
    
    if not pairs:
        logger.warning(f"  未找到任何图片配对")
        return False
    
    logger.info(f"  找到 {len(pairs)} 对图片")
    
    # 创建结果目录
    result_dir.mkdir(parents=True, exist_ok=True)
    
    success_count = 0
    for a_file, b_file in pairs:
        try:
            # 打开图片
            img_a = Image.open(a_file)
            img_b = Image.open(b_file)
            
            # 确保图片是 RGB 或 RGBA 模式
            if img_a.mode not in ('RGB', 'RGBA'):
                img_a = img_a.convert('RGBA')
            if img_b.mode not in ('RGB', 'RGBA'):
                img_b = img_b.convert('RGBA')
            
            # 创建拼图
            puzzle_img = create_couple_puzzle(back_img, img_a, img_b)
            
            # 生成输出文件名（使用 a 文件的名称，去掉 -a.png，添加 .jpg）
            output_name = a_file.stem.replace('-a', '') + '.jpg'
            output_file = result_dir / output_name
            
            # 保存结果（压缩到300KB以下）
            save_final_puzzle_image(puzzle_img, output_file)
            
            logger.info(f"  已处理: {a_file.name} + {b_file.name} -> {output_name}")
            success_count += 1
            
        except Exception as e:
            logger.error(f"  处理图片配对失败 {a_file.name} + {b_file.name}: {e}")
    
    logger.info(f"  处理完成: {success_count}/{len(pairs)} 对图片成功")
    return success_count > 0


def create_single_avatar_display(
    avatar_img: Image.Image, 
    back_img: Image.Image,
    circle_img: Optional[Image.Image] = None,
    circle_position: str = 'right'  # 'right' 右下角, 'left' 左下角
) -> Image.Image:
    """
    创建单个头像的3:4展示页面
    
    Args:
        avatar_img: 方形头像图片
        back_img: 底图
        circle_img: 圆形头像图片（如果为None，则使用avatar_img）
        circle_position: 圆形图片位置，'right'为右下角，'left'为左下角
    
    Returns:
        3:4比例的展示图片
    """
    # 计算3:4比例的尺寸（基于底图宽度）
    target_width = back_img.width
    target_height = int(target_width * 4 / 3)
    
    # 如果底图高度不够，以高度为准
    if target_height > back_img.height:
        target_height = back_img.height
        target_width = int(target_height * 3 / 4)
    
    # 创建3:4比例的画布
    canvas = Image.new('RGB', (target_width, target_height), (255, 255, 255))
    
    # 缩放底图以适应画布
    back_resized = back_img.resize((target_width, target_height), Image.Resampling.LANCZOS)
    
    # 将底图粘贴到画布
    canvas.paste(back_resized, (0, 0))
    
    # 计算方形头像的尺寸（使用画布宽度的70%）
    square_size = int(target_width * 0.7)
    
    # 创建圆角方形头像
    square_img = create_rounded_square_image(avatar_img, radius=30)
    if square_img.width != square_size:
        square_img = square_img.resize((square_size, square_size), Image.Resampling.LANCZOS)
    
    # 添加阴影效果
    square_img_with_effects = add_shadow_and_rounded_corners(square_img, radius=30)
    
    # 计算圆形头像的尺寸（方形图片的1/3，然后进一步放大）
    base_circle_diameter = square_size // 3
    circle_diameter = int(base_circle_diameter * 1.5)  # 放大50%
    
    # 创建圆形头像（带白色边框和白灰色外边框，外边框加粗到24px）
    # 如果指定了circle_img，使用指定的图片；否则使用avatar_img
    circle_source_img = circle_img if circle_img is not None else avatar_img
    circle_img_processed = create_circular_image(circle_source_img, border_width=8, outer_border_width=24)
    if circle_img_processed.width != circle_diameter:
        circle_img_processed = circle_img_processed.resize((circle_diameter, circle_diameter), Image.Resampling.LANCZOS)
    
    # 计算方形图片的位置（居中上方）
    square_x = (target_width - square_img_with_effects.width) // 2
    square_y = int(target_height * 0.15)  # 距离顶部15%
    
    # 计算圆形图片的位置
    # 注意：需要考虑方形图片添加阴影后的实际尺寸
    square_actual_width = square_img_with_effects.width
    square_actual_height = square_img_with_effects.height
    overlap = circle_diameter // 3  # 重叠部分
    
    if circle_position == 'left':
        # 左下角位置：计算右下角圆形图片距离右边缘的间隔，让左下角圆形图片距离左边缘的间隔与之相同
        # 右下角圆形图片的右边缘位置
        right_circle_right_edge = square_x + square_actual_width + overlap
        # 右下角圆形图片距离右边缘的间隔
        right_margin = target_width - right_circle_right_edge
        # 左下角圆形图片的左边缘应该距离左边缘相同的间隔
        circle_x = right_margin
        circle_y = square_y + square_actual_height - circle_diameter + overlap
    else:
        # 右下角位置（默认）
        circle_x = square_x + square_actual_width - circle_diameter + overlap
        circle_y = square_y + square_actual_height - circle_diameter + overlap
    
    # 确保圆形图片不超出边界
    circle_x = max(0, min(circle_x, target_width - circle_diameter))
    circle_y = max(0, min(circle_y, target_height - circle_diameter))
    
    # 粘贴方形图片
    canvas.paste(square_img_with_effects, (square_x, square_y), square_img_with_effects)
    
    # 粘贴圆形图片（在方形图片之上，因为有重叠）
    canvas.paste(circle_img_processed, (circle_x, circle_y), circle_img_processed)
    
    return canvas


def process_single_avatars(work_dir: Path, back1_img: Image.Image) -> bool:
    """
    处理目录下的单个头像文件
    
    Args:
        work_dir: 工作目录
        back1_img: back1底图
    
    Returns:
        是否成功
    """
    logger.info(f"处理单个头像: {work_dir.name}")
    
    # 检查结果目录是否已存在
    result_dir_name = f"{work_dir.name}-{RESULT_DIR_NAME_SINGLE}"
    result_dir = work_dir.parent / result_dir_name
    if result_dir.exists() and result_dir.is_dir():
        logger.info(f"  结果目录已存在，跳过: {result_dir_name}")
        return True
    
    # 查找所有头像文件
    a_files = sorted(work_dir.glob('*-a.png'))
    b_files = sorted(work_dir.glob('*-b.png'))
    other_files = []
    
    # 查找其他非成对的图片文件
    all_png_files = sorted(work_dir.glob('*.png'))
    for png_file in all_png_files:
        if not png_file.name.endswith('-a.png') and not png_file.name.endswith('-b.png'):
            other_files.append(png_file)
    
    if not a_files and not b_files and not other_files:
        logger.warning(f"  未找到任何头像文件")
        return False
    
    logger.info(f"  找到 {len(a_files)} 个a图, {len(b_files)} 个b图, {len(other_files)} 个其他图片")
    
    # 创建结果目录
    result_dir.mkdir(parents=True, exist_ok=True)
    
    success_count = 0
    processed_pairs = set()  # 记录已处理的配对
    
    # 处理成对的a-b图片
    for a_file in a_files:
        # 查找对应的b文件
        b_file_name = a_file.name.replace('-a.png', '-b.png')
        b_file = work_dir / b_file_name
        
        if b_file.exists() and b_file in b_files:
            # 成对处理
            processed_pairs.add(a_file.name)
            processed_pairs.add(b_file.name)
            
            try:
                # 处理a图：方形用a图，圆形用b图，位置在右下角
                a_img = Image.open(a_file)
                b_img = Image.open(b_file)
                
                if a_img.mode not in ('RGB', 'RGBA'):
                    a_img = a_img.convert('RGBA')
                if b_img.mode not in ('RGB', 'RGBA'):
                    b_img = b_img.convert('RGBA')
                
                # 创建a图的展示页面
                display_img_a = create_single_avatar_display(
                    a_img, back1_img, circle_img=b_img, circle_position='right'
                )
                output_name_a = a_file.stem + '.jpg'
                output_file_a = result_dir / output_name_a
                save_final_puzzle_image(display_img_a, output_file_a)
                logger.info(f"  已处理: {a_file.name} -> {output_name_a} (方形:a, 圆形:b, 右下角)")
                success_count += 1
                
                # 处理b图：方形用b图，圆形用a图，位置在左下角
                display_img_b = create_single_avatar_display(
                    b_img, back1_img, circle_img=a_img, circle_position='left'
                )
                output_name_b = b_file.stem + '.jpg'
                output_file_b = result_dir / output_name_b
                save_final_puzzle_image(display_img_b, output_file_b)
                logger.info(f"  已处理: {b_file.name} -> {output_name_b} (方形:b, 圆形:a, 左下角)")
                success_count += 1
                
            except Exception as e:
                logger.error(f"  处理头像配对失败 {a_file.name} + {b_file.name}: {e}")
    
    # 处理单独的b文件（没有对应a文件的）
    for b_file in b_files:
        if b_file.name not in processed_pairs:
            try:
                b_img = Image.open(b_file)
                if b_img.mode not in ('RGB', 'RGBA'):
                    b_img = b_img.convert('RGBA')
                
                # 保持原有逻辑：方形和圆形都用b图
                display_img = create_single_avatar_display(b_img, back1_img)
                output_name = b_file.stem + '.jpg'
                output_file = result_dir / output_name
                save_final_puzzle_image(display_img, output_file)
                logger.info(f"  已处理: {b_file.name} -> {output_name} (单独文件)")
                success_count += 1
                
            except Exception as e:
                logger.error(f"  处理头像文件失败 {b_file.name}: {e}")
    
    # 处理其他非成对的图片文件
    for other_file in other_files:
        try:
            other_img = Image.open(other_file)
            if other_img.mode not in ('RGB', 'RGBA'):
                other_img = other_img.convert('RGBA')
            
            # 保持原有逻辑：方形和圆形都用同一张图
            display_img = create_single_avatar_display(other_img, back1_img)
            output_name = other_file.stem + '.jpg'
            output_file = result_dir / output_name
            save_final_puzzle_image(display_img, output_file)
            logger.info(f"  已处理: {other_file.name} -> {output_name} (单独文件)")
            success_count += 1
            
        except Exception as e:
            logger.error(f"  处理头像文件失败 {other_file.name}: {e}")
    
    total_files = len(a_files) + len(b_files) + len(other_files)
    logger.info(f"  处理完成: {success_count}/{total_files} 个头像成功")
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
        # 保持底图的原始模式（RGBA或RGB），不进行转换
        # 因为back.png是透明图片，需要在create_couple_background中正确处理
        logger.info(f"底图尺寸: {back_img.size[0]}x{back_img.size[1]}, 模式: {back_img.mode}")
    except Exception as e:
        logger.error(f"打开底图失败: {e}")
        sys.exit(1)
    
    # 检查back1底图是否存在（用于单个头像处理）
    back1_img = None
    if BACK1_IMAGE.exists():
        try:
            back1_img = Image.open(BACK1_IMAGE)
            if back1_img.mode != 'RGB':
                back1_img = back1_img.convert('RGB')
            logger.info(f"back1底图尺寸: {back1_img.size[0]}x{back1_img.size[1]}")
        except Exception as e:
            logger.warning(f"打开back1底图失败: {e}，将跳过单个头像处理")
    else:
        logger.warning(f"back1底图不存在: {BACK1_IMAGE}，将跳过单个头像处理")
    
    # 检查 imgs 目录
    if not IMGS_DIR.exists():
        logger.error(f"图片目录不存在: {IMGS_DIR}")
        sys.exit(1)
    
    # 遍历所有子目录（排除结果目录）
    subdirs = [d for d in IMGS_DIR.iterdir() if d.is_dir() and not d.name.endswith('-a-result') and not d.name.endswith(f'-{RESULT_DIR_NAME_SINGLE}')]
    
    if not subdirs:
        logger.warning("未找到任何子目录")
        return
    
    logger.info(f"找到 {len(subdirs)} 个子目录")
    
    # 处理情侣头像拼图
    logger.info("=" * 50)
    logger.info("处理情侣头像拼图")
    logger.info("=" * 50)
    success_count = 0
    for subdir in subdirs:
        try:
            if process_directory(subdir, back_img):
                success_count += 1
        except Exception as e:
            logger.error(f"处理目录 {subdir.name} 时发生错误: {e}")
    
    logger.info(f"情侣头像拼图处理完成: {success_count}/{len(subdirs)} 个目录成功")
    
    # 处理单个头像展示
    if back1_img:
        logger.info("=" * 50)
        logger.info("处理单个头像展示")
        logger.info("=" * 50)
        single_success_count = 0
        for subdir in subdirs:
            try:
                if process_single_avatars(subdir, back1_img):
                    single_success_count += 1
            except Exception as e:
                logger.error(f"处理单个头像 {subdir.name} 时发生错误: {e}")
        
        logger.info(f"单个头像展示处理完成: {single_success_count}/{len(subdirs)} 个目录成功")


if __name__ == '__main__':
    main()
