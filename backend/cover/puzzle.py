#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片拼图工具
遍历 imgs 目录下的项目目录，对每个子目录中的图片进行处理，结果输出到对应的 *-result 目录。
"""

import sys
import argparse
import logging
from pathlib import Path
from typing import Optional
from PIL import Image

try:
    from .mobile_puzzle import (
        prepare_mobile_desktop, create_mobile_puzzle,
        prepare_mobile_desktop_2, create_mobile_puzzle_2,
        prepare_mobile_desktop_3, create_mobile_puzzle_3,
    )
    from .pad_puzzle import prepare_pad_images, create_pad_puzzle
    from .pc_puzzle import prepare_pc_desktop_mac, create_pc_puzzle
    from .utils import get_image_file, BACK_IMAGE, save_final_puzzle_image, add_shadow_and_rounded_corners, add_size_watermark
    from .phone_screen_replace import replace_screen
except ImportError:
    from mobile_puzzle import (
        prepare_mobile_desktop, create_mobile_puzzle,
        prepare_mobile_desktop_2, create_mobile_puzzle_2,
        prepare_mobile_desktop_3, create_mobile_puzzle_3,
    )
    from pad_puzzle import prepare_pad_images, create_pad_puzzle
    from pc_puzzle import prepare_pc_desktop_mac, create_pc_puzzle
    from utils import get_image_file, BACK_IMAGE, save_final_puzzle_image, add_shadow_and_rounded_corners, add_size_watermark
    from phone_screen_replace import replace_screen

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

IMGS_DIR = Path(__file__).parent / 'imgs'
MOBILE_IMGS_DIR = Path(__file__).parent / 'mobile-imgs'
PHONE_TEMPLATE = Path(__file__).parent / 'phone_template.png'


def process_subfolder(source_dir: Path, result_dir: Path, main_color: Optional[str] = None) -> bool:
    """
    处理单个子目录（如 imgs/projectA/1/），将结果输出到 result_dir

    - 若存在 mobile-lock.*：使用 phone_screen_replace 生成 mobile-cover.png
    - 若存在 mobile.png（+ mobile-lock.*）：执行 Mobile 图片预处理和拼图
    - 若存在 pc.png：执行 PC 图片预处理和拼图
    - 若存在 pad.png：执行 Pad 图片预处理和拼图

    Args:
        source_dir: 源图片目录
        result_dir: 结果输出目录
        main_color: 背景主色调

    Returns:
        是否成功
    """
    result_dir.mkdir(parents=True, exist_ok=True)
    success = True

    mobile_lock_file = get_image_file(source_dir, 'mobile-lock')

    # 1. mobile-lock.* → phone mockup → mobile-cover.png
    if mobile_lock_file:
        cover_output = result_dir / 'mobile-cover.png'
        if not cover_output.exists():
            if PHONE_TEMPLATE.exists():
                try:
                    replace_screen(str(PHONE_TEMPLATE), str(mobile_lock_file), str(cover_output))
                    logger.info(f"  已生成 mobile-cover.png")
                except Exception as e:
                    logger.error(f"  生成 mobile-cover.png 失败: {e}")
                    success = False
            else:
                logger.warning(f"  缺少手机模板 phone_template.png，跳过 mobile-cover.png 生成")

    # 2. mobile.png + mobile-lock.* → Mobile 预处理 + 拼图
    mobile_file = get_image_file(source_dir, 'mobile')
    if mobile_file:
        prepare_mobile_desktop(result_dir, source_dir=source_dir)
        prepare_mobile_desktop_2(result_dir, source_dir=source_dir)
        prepare_mobile_desktop_3(result_dir, source_dir=source_dir)

        if mobile_lock_file:
            success &= create_mobile_puzzle(result_dir, result_dir, main_color, source_dir=source_dir)
            success &= create_mobile_puzzle_2(result_dir, result_dir, main_color, source_dir=source_dir)
            success &= create_mobile_puzzle_3(result_dir, result_dir, main_color, source_dir=source_dir)

    # 3. pc.png → PC 预处理 + 拼图
    pc_file = get_image_file(source_dir, 'pc')
    if pc_file:
        prepare_pc_desktop_mac(result_dir, source_dir=source_dir)
        success &= create_pc_puzzle(result_dir, result_dir, main_color, source_dir=source_dir)

    # 4. pad.png → Pad 预处理 + 拼图
    pad_file = get_image_file(source_dir, 'pad')
    if pad_file:
        prepare_pad_images(result_dir, source_dir=source_dir)
        success &= create_pad_puzzle(result_dir, result_dir, main_color, source_dir=source_dir)

    return success


def process_plain_images(source_dir: Path, result_dir: Path) -> bool:
    """
    处理 source_dir 下直接存放的图片文件（1.png、2.png 等），
    以 back.png 为底图，将每张图片缩放后居中贴合，结果输出到 result_dir。
    处理逻辑与 mobile-imgs 目录相同：添加阴影圆角、尺寸水印，保存为压缩 JPG。

    Args:
        source_dir: 源图片目录
        result_dir: 结果输出目录

    Returns:
        是否成功（未找到图片时返回 True）
    """
    if not BACK_IMAGE.exists():
        logger.error(f"  缺少底图: {BACK_IMAGE}")
        return False

    image_extensions = ['.png', '.jpg', '.jpeg', '.webp']
    image_files = []
    for ext in image_extensions:
        image_files.extend(source_dir.glob(f'*{ext}'))
        image_files.extend(source_dir.glob(f'*{ext.upper()}'))

    if not image_files:
        return True

    result_dir.mkdir(parents=True, exist_ok=True)

    try:
        back_img = Image.open(BACK_IMAGE)
        if back_img.mode != 'RGB':
            back_img = back_img.convert('RGB')
        back_w, back_h = back_img.size
    except Exception as e:
        logger.error(f"  打开底图失败: {e}")
        return False

    max_w = int(back_w * 0.7)
    max_h = int(back_h * 0.7)
    success_count = 0

    for img_file in sorted(image_files):
        output_file = result_dir / img_file.name
        if output_file.exists():
            logger.info(f"  {img_file.name} 已存在，跳过")
            success_count += 1
            continue
        try:
            img = Image.open(img_file)
            orig_w, orig_h = img.size

            scale = min(max_w / orig_w, max_h / orig_h, 1.0)
            if scale < 1.0:
                img = img.resize((int(orig_w * scale), int(orig_h * scale)), Image.Resampling.LANCZOS)

            img = add_shadow_and_rounded_corners(img)

            result_img = back_img.copy()
            result_img.paste(img, ((back_w - img.width) // 2, (back_h - img.height) // 2), img)
            result_img = add_size_watermark(result_img, orig_w, orig_h)

            save_final_puzzle_image(result_img, output_file)
            logger.info(f"  已处理: {img_file.name}")
            success_count += 1
        except Exception as e:
            logger.error(f"  处理图片 {img_file.name} 失败: {e}")

    logger.info(f"  处理完成: {success_count}/{len(image_files)} 张图片成功")
    return success_count > 0


def process_project(project_dir: Path, main_color: Optional[str] = None) -> bool:
    """
    处理单个项目目录（如 imgs/projectA/）

    - 若 imgs/projectA-result/ 已存在，则跳过整个项目
    - 处理 projectA/ 下的子目录（文件夹），每个子目录独立调用 process_subfolder
    - 处理 projectA/ 下的成对图片文件（{name}.* + {name}-lock.*），调用 process_image_pairs
    - 所有结果保存至 imgs/projectA-result/ 对应路径下

    Args:
        project_dir: 项目目录
        main_color: 背景主色调

    Returns:
        是否成功
    """
    result_dir = project_dir.parent / f"{project_dir.name}-result"

    if result_dir.exists():
        logger.info(f"结果目录已存在，跳过: {project_dir.name}")
        return True

    logger.info(f"处理项目: {project_dir.name}")

    image_extensions = ['.png', '.jpg', '.jpeg', '.webp']
    subfolders = sorted([d for d in project_dir.iterdir() if d.is_dir()])
    plain_images = [
        f for ext in image_extensions
        for f in list(project_dir.glob(f'*{ext}')) + list(project_dir.glob(f'*{ext.upper()}'))
    ]

    if not subfolders and not plain_images:
        logger.warning(f"项目 {project_dir.name} 下没有可处理的内容，跳过")
        return False

    success = True

    # 1. 处理子目录（文件夹类型）
    if subfolders:
        logger.info(f"  子目录共 {len(subfolders)} 个")
        for subfolder in subfolders:
            logger.info(f"  处理子目录: {subfolder.name}")
            result_subfolder = result_dir / subfolder.name
            try:
                if not process_subfolder(subfolder, result_subfolder, main_color):
                    success = False
            except Exception as e:
                logger.error(f"  处理子目录 {subfolder.name} 失败: {e}")
                success = False

    # 2. 处理直接存放的图片文件（1.png、2.png 等），居中拼到 back.png 上
    if plain_images:
        if not process_plain_images(project_dir, result_dir):
            success = False

    if success:
        logger.info(f"项目处理完成: {project_dir.name}")
    else:
        logger.warning(f"项目处理部分失败: {project_dir.name}")

    return success


def process_mobile_imgs_directory(source_dir: Path, result_dir: Path) -> bool:
    """
    处理 mobile-imgs 下的目录，将图片拼接到 back.png 上

    Args:
        source_dir: 源目录
        result_dir: 结果目录

    Returns:
        是否成功
    """
    logger.info(f"处理 mobile-imgs 目录: {source_dir}")

    if result_dir.exists() and result_dir.is_dir():
        logger.info(f"  结果目录已存在，跳过: {result_dir.name}")
        return True

    if not BACK_IMAGE.exists():
        logger.error(f"  缺少底图: {BACK_IMAGE}")
        return False

    if not source_dir.exists() or not source_dir.is_dir():
        logger.error(f"  源目录不存在: {source_dir}")
        return False

    result_dir.mkdir(parents=True, exist_ok=True)

    try:
        back_img = Image.open(BACK_IMAGE)
        if back_img.mode != 'RGB':
            back_img = back_img.convert('RGB')
        back_width, back_height = back_img.size
        logger.info(f"  底图尺寸: {back_width}x{back_height}")
    except Exception as e:
        logger.error(f"  打开底图失败: {e}")
        return False

    max_width = int(back_width * 0.7)
    max_height = int(back_height * 0.7)

    image_extensions = ['.png', '.jpg', '.jpeg', '.webp']

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
            img = Image.open(img_file)
            img_width, img_height = img.size

            width_ratio = max_width / img_width if img_width > 0 else 1
            height_ratio = max_height / img_height if img_height > 0 else 1
            scale = min(width_ratio, height_ratio, 1.0)

            new_width = int(img_width * scale)
            new_height = int(img_height * scale)

            if scale < 1.0:
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

            img_with_effects = add_shadow_and_rounded_corners(img)

            result_img = back_img.copy()

            x_offset = (back_width - img_with_effects.width) // 2
            y_offset = (back_height - img_with_effects.height) // 2

            result_img.paste(img_with_effects, (x_offset, y_offset), img_with_effects)

            result_img = add_size_watermark(result_img, img_width, img_height)

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

    subdirs = [d for d in MOBILE_IMGS_DIR.iterdir() if d.is_dir() and not d.name.endswith('-result')]

    if not subdirs:
        logger.info(f"mobile-imgs 目录下没有找到子目录，跳过")
        return

    logger.info(f"找到 {len(subdirs)} 个子目录需要处理")

    success_count = 0
    for source_dir in subdirs:
        try:
            result_dir_name = f"{source_dir.name}-result"
            result_dir = MOBILE_IMGS_DIR / result_dir_name
            if process_mobile_imgs_directory(source_dir, result_dir):
                success_count += 1
        except Exception as e:
            logger.error(f"处理目录 {source_dir.name} 时发生错误: {e}")

    logger.info(f"mobile-imgs 处理完成: {success_count}/{len(subdirs)} 个目录成功")


def main():
    parser = argparse.ArgumentParser(description='图片拼图工具')
    parser.add_argument(
        '--main-color',
        type=str,
        nargs='?',
        const='',
        help='主色调（16进制颜色代码，如 #fff 或 #ffffff）。如果不提供值，则自动提取图片主色调'
    )

    args = parser.parse_args()

    main_color = None
    if args.main_color is not None:
        main_color = args.main_color  # '' 表示自动提取，非空字符串表示指定颜色

    logger.info("=" * 50)
    logger.info("处理 mobile-imgs 目录")
    logger.info("=" * 50)
    process_mobile_imgs()

    logger.info("=" * 50)
    logger.info("处理 imgs 目录（项目级别）")
    logger.info("=" * 50)

    if not IMGS_DIR.exists():
        logger.error(f"图片目录不存在: {IMGS_DIR}")
        sys.exit(1)

    project_dirs = sorted([
        d for d in IMGS_DIR.iterdir()
        if d.is_dir() and not d.name.endswith('-result')
    ])

    if not project_dirs:
        logger.warning("未找到任何项目目录")
        return

    logger.info(f"找到 {len(project_dirs)} 个项目")

    success_count = 0
    for project_dir in project_dirs:
        try:
            if process_project(project_dir, main_color):
                success_count += 1
        except Exception as e:
            logger.error(f"处理项目 {project_dir.name} 时发生错误: {e}")

    logger.info(f"处理完成: {success_count}/{len(project_dirs)} 个项目成功")


if __name__ == '__main__':
    main()
