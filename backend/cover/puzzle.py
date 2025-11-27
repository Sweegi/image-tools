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

# 尝试相对导入，如果失败则使用绝对导入
try:
    from .mobile_puzzle import prepare_mobile_desktop, create_mobile_puzzle
    from .pad_puzzle import prepare_pad_images, create_pad_puzzle
    from .pc_puzzle import prepare_pc_desktop_mac, create_pc_puzzle
    from .utils import get_image_file
except ImportError:
    from mobile_puzzle import prepare_mobile_desktop, create_mobile_puzzle
    from pad_puzzle import prepare_pad_images, create_pad_puzzle
    from pc_puzzle import prepare_pc_desktop_mac, create_pc_puzzle
    from utils import get_image_file

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# 常量定义
IMGS_DIR = Path(__file__).parent / 'imgs'

# 临时文件列表（在拼图完成后需要清理）
TEMP_FILES = [
    'mobile-desktop.png',
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
        'pc-block.png',
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
    
    # 图片预处理
    logger.info(f"  开始图片预处理...")
    prepare_mobile_desktop(work_dir)
    prepare_pad_images(work_dir)
    prepare_pc_desktop_mac(work_dir)
    
    # 执行拼图
    logger.info(f"  开始拼图处理...")
    success = True
    
    success &= create_mobile_puzzle(work_dir, intr_dir, main_color)
    success &= create_pc_puzzle(work_dir, intr_dir, main_color)
    success &= create_pad_puzzle(work_dir, intr_dir, main_color)
    
    # 清理临时文件
    logger.info(f"  清理临时文件...")
    cleanup_temp_files(work_dir)
    
    if success:
        logger.info(f"  目录处理完成: {work_dir}")
    else:
        logger.warning(f"  目录处理部分失败: {work_dir}")
    
    return success


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
