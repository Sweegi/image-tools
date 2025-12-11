#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片拼图工具
用于批量处理图片拼图任务，自动遍历指定目录下的图片文件夹，将成对的图片按照特定规则拼接成新的图片。
"""

import sys
import argparse
import logging
from pathlib import Path
from typing import Optional, Tuple, List
from PIL import Image

# 尝试相对导入，如果失败则使用绝对导入
try:
    from .mobile_puzzle import prepare_mobile_desktop, create_mobile_puzzle, prepare_mobile_desktop_2, create_mobile_puzzle_2, prepare_mobile_desktop_3, create_mobile_puzzle_3
    from .pad_puzzle import prepare_pad_images, create_pad_puzzle
    from .pc_puzzle import prepare_pc_desktop_mac, create_pc_puzzle
    from .utils import get_image_file, BACK_IMAGE, save_optimized_image, save_final_puzzle_image, add_shadow_and_rounded_corners, add_size_watermark
except ImportError:
    from mobile_puzzle import prepare_mobile_desktop, create_mobile_puzzle, prepare_mobile_desktop_2, create_mobile_puzzle_2, prepare_mobile_desktop_3, create_mobile_puzzle_3
    from pad_puzzle import prepare_pad_images, create_pad_puzzle
    from pc_puzzle import prepare_pc_desktop_mac, create_pc_puzzle
    from utils import get_image_file, BACK_IMAGE, save_optimized_image, save_final_puzzle_image, add_shadow_and_rounded_corners, add_size_watermark

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# 常量定义
IMGS_DIR = Path(__file__).parent / 'imgs'
MOBILE_IMGS_DIR = Path(__file__).parent / 'mobile-imgs'

# 临时文件列表（在拼图完成后需要清理）
# 注意：mobile-desktop.png、mobile-desktop-2.png 和 mobile-desktop-3.png 已移除，保留这些文件
TEMP_FILES = [
    'pad-desktop.png',
    'pad-lock.png',
    'pc-desktop-mac.png'
]


def cleanup_temp_files(work_dir: Path) -> None:
    """
    清理临时文件
    
    Args:
        work_dir: 工作目录
    """
    cleaned_count = 0
    for temp_file in TEMP_FILES:
        temp_path = work_dir / temp_file
        if temp_path.exists():
            try:
                temp_path.unlink()
                cleaned_count += 1
                logger.debug(f"  已删除临时文件: {temp_file}")
            except Exception as e:
                logger.warning(f"  删除临时文件失败 {temp_file}: {e}")
    
    if cleaned_count > 0:
        logger.info(f"  已清理 {cleaned_count} 个临时文件")


def check_files_completeness(work_dir: Path) -> Tuple[bool, List[str]]:
    """
    检查文件完整性
    
    Args:
        work_dir: 工作目录
    
    Returns:
        (是否完整, 缺失文件列表)
    """
    required_files = [
        'mobile.png',
        'mobile-lock.png',
        'pc.png',
        'pad.png'
    ]
    
    missing_files = []
    for file in required_files:
        # 支持多种格式
        found = False
        for ext in ['.png', '.jpg', '.jpeg', '.webp']:
            if (work_dir / f"{file.rsplit('.', 1)[0]}{ext}").exists():
                found = True
                break
        if not found:
            missing_files.append(file)
    
    return len(missing_files) == 0, missing_files




def generate_image_info_file(work_dir: Path) -> None:
    """
    生成图片信息txt文件
    
    Args:
        work_dir: 工作目录
    """
    # 支持的图片格式
    image_extensions = ['.png', '.jpg', '.jpeg', '.webp']
    
    # 统计手机壁纸数量（mobile*.png，不包含mobile-lock.png）
    mobile_count = 0
    for ext in image_extensions:
        for file in work_dir.glob(f'mobile*{ext}'):
            file_name_lower = file.name.lower()
            # 排除 mobile-lock.png 和 mobile-lock.* 格式的文件
            if not file_name_lower.startswith('mobile-lock.'):
                mobile_count += 1
    
    # 统计平板壁纸数量（pad*.png）
    pad_count = 0
    for ext in image_extensions:
        pad_count += len(list(work_dir.glob(f'pad*{ext}')))
    
    # 统计电脑壁纸数量（pc*.png）
    pc_count = 0
    for ext in image_extensions:
        pc_count += len(list(work_dir.glob(f'pc*{ext}')))
    
    # 统计合集目录下的图片数量
    collection_count = 0
    collection_dir = work_dir / '合集'
    if collection_dir.exists() and collection_dir.is_dir():
        # 使用集合去重，避免重复计算
        collection_files = set()
        for ext in image_extensions:
            # 匹配所有大小写变体
            collection_files.update(collection_dir.glob(f'*{ext}'))
            collection_files.update(collection_dir.glob(f'*{ext.upper()}'))
        collection_count = len(collection_files)
    
    # 生成txt文件内容
    lines = []
    if mobile_count > 0:
        lines.append(f"手机壁纸 x {mobile_count}张")
    if pad_count > 0:
        lines.append(f"平板壁纸 x {pad_count}张")
    if pc_count > 0:
        lines.append(f"电脑壁纸 x {pc_count}张")
    if collection_count > 0:
        lines.append(f"赠送{collection_count}张合集9:16手机壁纸")
    
    # 如果有内容，写入文件
    if lines:
        txt_file = work_dir / '图片信息.txt'
        try:
            with open(txt_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))
            logger.info(f"  已生成图片信息文件: {txt_file.name}")
        except Exception as e:
            logger.warning(f"  生成图片信息文件失败: {e}")


def process_directory(work_dir: Path, main_color: Optional[str] = None) -> bool:
    """
    处理单个目录
    
    Args:
        work_dir: 工作目录
        main_color: 主色调
    
    Returns:
        是否成功
    """
    logger.info(f"处理目录: {work_dir}")
    
    # 检查是否已处理
    intr_dir = work_dir / 'intr'
    if intr_dir.exists():
        logger.info(f"  目录已处理（存在 intr 文件夹），跳过")
        return True
    
    # 检查文件完整性
    is_complete, missing_files = check_files_completeness(work_dir)
    if not is_complete:
        logger.error(f"  文件不完整，缺少: {', '.join(missing_files)}")
        return False
    
    # 创建输出目录
    intr_dir.mkdir(exist_ok=True)
    
    # 在图片合并之前统计并生成图片信息txt文件
    generate_image_info_file(work_dir)
    
    # 图片预处理
    logger.info(f"  开始图片预处理...")
    prepare_mobile_desktop(work_dir)
    prepare_mobile_desktop_2(work_dir)
    prepare_mobile_desktop_3(work_dir)
    prepare_pad_images(work_dir)
    prepare_pc_desktop_mac(work_dir)
    
    # 执行拼图
    logger.info(f"  开始拼图处理...")
    success = True
    
    success &= create_mobile_puzzle(work_dir, intr_dir, main_color)
    success &= create_mobile_puzzle_2(work_dir, intr_dir, main_color)
    success &= create_mobile_puzzle_3(work_dir, intr_dir, main_color)
    success &= create_pc_puzzle(work_dir, intr_dir, main_color)
    success &= create_pad_puzzle(work_dir, intr_dir, main_color)
    
    # 清理临时文件（暂时注释）
    # logger.info(f"  清理临时文件...")
    # cleanup_temp_files(work_dir)
    
    if success:
        logger.info(f"  目录处理完成: {work_dir}")
    else:
        logger.warning(f"  目录处理部分失败: {work_dir}")
    
    return success


def process_mobile_imgs_directory(source_dir: Path, result_dir: Path) -> bool:
    """
    处理 mobile-imgs 下的目录，将图片拼接到 back.jpg 上
    
    Args:
        source_dir: 源目录（如 "aaa"）
        result_dir: 结果目录（如 "aaa-result"）
    
    Returns:
        是否成功
    """
    logger.info(f"处理 mobile-imgs 目录: {source_dir}")
    
    # 检查结果目录是否已存在，如果存在则跳过
    if result_dir.exists() and result_dir.is_dir():
        logger.info(f"  结果目录已存在，跳过: {result_dir.name}")
        return True
    
    # 检查 back.jpg 是否存在
    if not BACK_IMAGE.exists():
        logger.error(f"  缺少底图: {BACK_IMAGE}")
        return False
    
    # 检查源目录是否存在
    if not source_dir.exists() or not source_dir.is_dir():
        logger.error(f"  源目录不存在: {source_dir}")
        return False
    
    # 创建结果目录
    result_dir.mkdir(parents=True, exist_ok=True)
    
    # 打开底图
    try:
        back_img = Image.open(BACK_IMAGE)
        # 确保底图是 RGB 模式
        if back_img.mode != 'RGB':
            back_img = back_img.convert('RGB')
        back_width, back_height = back_img.size
        logger.info(f"  底图尺寸: {back_width}x{back_height}")
    except Exception as e:
        logger.error(f"  打开底图失败: {e}")
        return False
    
    # 计算最大尺寸（70%）
    max_width = int(back_width * 0.7)
    max_height = int(back_height * 0.7)
    
    # 支持的图片格式
    image_extensions = ['.png', '.jpg', '.jpeg', '.webp']
    
    # 获取所有图片文件
    image_files = []
    for ext in image_extensions:
        image_files.extend(source_dir.glob(f'*{ext}'))
        image_files.extend(source_dir.glob(f'*{ext.upper()}'))
    
    if not image_files:
        logger.warning(f"  未找到任何图片文件")
        return False
    
    logger.info(f"  找到 {len(image_files)} 张图片")
    
    success_count = 0
    for img_file in image_files:
        try:
            # 打开图片
            img = Image.open(img_file)
            img_width, img_height = img.size
            
            # 计算缩放比例，保持宽高比，不超过最大尺寸
            width_ratio = max_width / img_width if img_width > 0 else 1
            height_ratio = max_height / img_height if img_height > 0 else 1
            scale = min(width_ratio, height_ratio, 1.0)  # 不超过 1.0，不放大
            
            # 计算新尺寸
            new_width = int(img_width * scale)
            new_height = int(img_height * scale)
            
            # 调整图片尺寸（保持比例）
            if scale < 1.0:
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # 添加圆角和阴影效果（使图片看起来更自然，不会那么突兀）
            img_with_effects = add_shadow_and_rounded_corners(img)
            
            # 创建底图副本
            result_img = back_img.copy()
            
            # 计算居中位置（需要考虑阴影增加的边距）
            x_offset = (back_width - img_with_effects.width) // 2
            y_offset = (back_height - img_with_effects.height) // 2
            
            # 粘贴带效果的图片（自动处理透明通道）
            result_img.paste(img_with_effects, (x_offset, y_offset), img_with_effects)
            
            # 添加尺寸水印（使用原始图片尺寸）
            result_img = add_size_watermark(result_img, img_width, img_height)
            
            # 保存结果（统一压缩到200-300KB）
            output_file = result_dir / img_file.name
            save_final_puzzle_image(result_img, output_file)
            
            logger.info(f"  已处理: {img_file.name} -> {output_file.name}")
            success_count += 1
            
        except Exception as e:
            logger.error(f"  处理图片 {img_file.name} 失败: {e}")
    
    logger.info(f"  处理完成: {success_count}/{len(image_files)} 张图片成功")
    return success_count > 0


def process_mobile_imgs() -> None:
    """
    处理 mobile-imgs 目录下的所有子目录
    遍历所有子目录，对每个目录进行拼图处理，结果保存到对应的 "目录名-result" 目录
    """
    if not MOBILE_IMGS_DIR.exists():
        logger.info(f"mobile-imgs 目录不存在，跳过")
        return
    
    # 获取所有子目录
    subdirs = [d for d in MOBILE_IMGS_DIR.iterdir() if d.is_dir() and not d.name.endswith('-result')]
    
    if not subdirs:
        logger.info(f"mobile-imgs 目录下没有找到子目录，跳过")
        return
    
    logger.info(f"找到 {len(subdirs)} 个子目录需要处理")
    
    success_count = 0
    for source_dir in subdirs:
        try:
            # 结果目录名称：源目录名 + "-result"
            result_dir_name = f"{source_dir.name}-result"
            result_dir = MOBILE_IMGS_DIR / result_dir_name
            
            # 处理目录
            if process_mobile_imgs_directory(source_dir, result_dir):
                success_count += 1
        except Exception as e:
            logger.error(f"处理目录 {source_dir.name} 时发生错误: {e}")
    
    logger.info(f"mobile-imgs 处理完成: {success_count}/{len(subdirs)} 个目录成功")


def main():
    """
    主函数
    """
    parser = argparse.ArgumentParser(description='图片拼图工具')
    parser.add_argument(
        '--main-color',
        type=str,
        nargs='?',
        const='',
        help='主色调（16进制颜色代码，如 #fff 或 #ffffff）。如果不提供值，则自动提取图片主色调'
    )
    
    args = parser.parse_args()
    
    # 处理主色调参数
    main_color = None
    if args.main_color is not None:
        if args.main_color == '':
            # 只提供了 --main-color 但没有值，自动提取
            main_color = ''
        else:
            # 提供了具体的颜色值
            main_color = args.main_color
    
    # 处理 mobile-imgs 目录
    logger.info("=" * 50)
    logger.info("处理 mobile-imgs 目录")
    logger.info("=" * 50)
    process_mobile_imgs()
    
    # 检查 imgs 目录
    if not IMGS_DIR.exists():
        logger.error(f"图片目录不存在: {IMGS_DIR}")
        sys.exit(1)
    
    # 遍历所有子目录
    subdirs = [d for d in IMGS_DIR.iterdir() if d.is_dir()]
    
    if not subdirs:
        logger.warning("未找到任何子目录")
        return
    
    logger.info(f"找到 {len(subdirs)} 个子目录")
    
    success_count = 0
    for subdir in subdirs:
        try:
            if process_directory(subdir, main_color):
                success_count += 1
        except Exception as e:
            logger.error(f"处理目录 {subdir} 时发生错误: {e}")
    
    logger.info(f"处理完成: {success_count}/{len(subdirs)} 个目录成功")


if __name__ == '__main__':
    main()
