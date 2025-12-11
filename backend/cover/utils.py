#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片处理工具函数
包含拼图处理所需的公共工具函数
"""

import logging
from pathlib import Path
from typing import Optional, Tuple
from PIL import Image, ImageFilter, ImageDraw, ImageFont
import numpy as np
from sklearn.cluster import KMeans
import platform

logger = logging.getLogger(__name__)

# 常量定义
BACK_IMAGE = Path(__file__).parent / 'back.jpg'
MOBILE_BLOCK_COVER = Path(__file__).parent / 'mobile-block-cover.png'
PAD_BLOCK_COVER = Path(__file__).parent / 'pad-block-cover.png'
PAD_LOCK_COVER = Path(__file__).parent / 'pad-lock-cover.png'
PC_MAC_COVER = Path(__file__).parent / 'pc-mac-cover.png'

# 输出图片配置
OUTPUT_RATIO = (1, 1)  # 1:1 比例
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB
MAX_JPEG_SIZE = 500 * 1024  # 500KB（用于最终输出的 JPG 文件）
FINAL_PUZZLE_MIN_SIZE = 200 * 1024  # 200KB（最终拼图结果最小大小）
FINAL_PUZZLE_MAX_SIZE = 300 * 1024  # 300KB（最终拼图结果最大大小）
BORDER_RADIUS = 25  # 圆角半径（从20增加到25）
SHADOW_OFFSET = (5, 5)
SHADOW_BLUR = 10
SPACING = 60  # 图片之间的间隔（从30增加到60，增大一倍）


def extract_main_color(image: Image.Image, k: int = 3) -> Tuple[int, int, int]:
    """
    提取图片的主色调

    Args:
        image: PIL Image 对象
        k: K-means 聚类数量

    Returns:
        RGB 颜色元组
    """
    # 将图片转换为 numpy 数组
    img_array = np.array(image)

    # 如果是 RGBA，只取 RGB
    if img_array.shape[2] == 4:
        img_array = img_array[:, :, :3]

    # 重塑为二维数组 (像素数, RGB)
    pixels = img_array.reshape(-1, 3)

    # 使用 K-means 聚类
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    kmeans.fit(pixels)

    # 获取最大的聚类中心（主色调）
    labels = kmeans.labels_
    cluster_sizes = np.bincount(labels)
    main_cluster_idx = np.argmax(cluster_sizes)
    main_color = kmeans.cluster_centers_[main_cluster_idx]

    return tuple(map(int, main_color))


def create_rounded_rectangle_mask(size: Tuple[int, int], radius: int) -> Image.Image:
    """
    创建圆角矩形遮罩

    Args:
        size: 图片尺寸 (width, height)
        radius: 圆角半径

    Returns:
        遮罩图片
    """
    mask = Image.new('L', size, 0)
    draw = ImageDraw.Draw(mask)

    # 绘制圆角矩形
    draw.rounded_rectangle(
        [(0, 0), size],
        radius=radius,
        fill=255
    )

    return mask


def add_shadow_and_rounded_corners(image: Image.Image, radius: int = BORDER_RADIUS) -> Image.Image:
    """
    为图片添加阴影和圆角效果

    Args:
        image: 原始图片
        radius: 圆角半径

    Returns:
        处理后的图片
    """
    # 创建带阴影的画布（增加边距以容纳阴影）
    shadow_margin = max(SHADOW_OFFSET) + SHADOW_BLUR
    canvas_size = (
        image.width + shadow_margin * 2,
        image.height + shadow_margin * 2
    )

    # 创建阴影层
    shadow = Image.new('RGBA', canvas_size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)

    # 绘制阴影（使用半透明黑色）
    shadow_rect = [
        (shadow_margin + SHADOW_OFFSET[0], shadow_margin + SHADOW_OFFSET[1]),
        (shadow_margin + image.width + SHADOW_OFFSET[0], shadow_margin + image.height + SHADOW_OFFSET[1])
    ]
    shadow_draw.rounded_rectangle(
        shadow_rect,
        radius=radius,
        fill=(0, 0, 0, 100)
    )

    # 模糊阴影
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=SHADOW_BLUR))

    # 创建圆角遮罩
    mask = create_rounded_rectangle_mask(image.size, radius)

    # 如果原图有透明通道，应用遮罩
    if image.mode == 'RGBA':
        image = image.copy()
        image.putalpha(mask)
    else:
        image = image.convert('RGBA')
        image.putalpha(mask)

    # 将图片粘贴到阴影层上
    shadow.paste(image, (shadow_margin, shadow_margin), image)

    return shadow


def overlay_images(base: Image.Image, overlay: Image.Image) -> Image.Image:
    """
    将覆盖图片叠加到底图上

    Args:
        base: 底图
        overlay: 覆盖图

    Returns:
        叠加后的图片
    """
    # 确保两张图片尺寸一致
    if base.size != overlay.size:
        overlay = overlay.resize(base.size, Image.Resampling.LANCZOS)

    # 如果底图没有透明通道，转换为 RGBA
    if base.mode != 'RGBA':
        base = base.convert('RGBA')

    # 如果覆盖图没有透明通道，转换为 RGBA
    if overlay.mode != 'RGBA':
        overlay = overlay.convert('RGBA')

    # 创建新图片并叠加
    result = Image.alpha_composite(base, overlay)

    return result


def get_image_file(work_dir: Path, base_name: str) -> Optional[Path]:
    """
    获取图片文件（支持多种格式）

    Args:
        work_dir: 工作目录
        base_name: 基础文件名（不含扩展名）

    Returns:
        图片文件路径，如果不存在则返回 None
    """
    for ext in ['.png', '.jpg', '.jpeg', '.webp']:
        file_path = work_dir / f"{base_name}{ext}"
        if file_path.exists():
            return file_path
    return None


def create_background(size: Tuple[int, int], main_color: Optional[str] = None, source_image: Optional[Image.Image] = None) -> Image.Image:
    """
    创建背景图片

    背景逻辑：
    - main_color = None: 使用默认背景（back.jpg）
    - main_color = "": 自动提取主色调（如果提供了 source_image）
    - main_color = "#ffffff": 使用指定的纯色背景

    Args:
        size: 背景尺寸
        main_color: 主色调（16进制颜色代码，如 #ffffff）。如果为空字符串，则自动提取主色调；如果为 None，则使用默认背景
        source_image: 用于提取主色调的源图片（仅在 main_color="" 时使用）

    Returns:
        背景图片
    """
    # 如果 main_color 是 None，始终使用默认背景（back.jpg）
    if main_color is None:
        bg = Image.open(BACK_IMAGE)
        return bg.resize(size, Image.Resampling.LANCZOS)

    # 如果 main_color 是空字符串，表示自动提取主色调
    if main_color == '':
        if source_image:
            # 从源图片提取主色调
            bg_color = extract_main_color(source_image)
            return Image.new('RGB', size, bg_color)
        else:
            # 没有源图片，使用默认背景
            bg = Image.open(BACK_IMAGE)
            return bg.resize(size, Image.Resampling.LANCZOS)

    # 如果 main_color 有值，使用纯色背景
    # 解析颜色代码
    color_str = main_color
    if color_str.startswith('#'):
        color_str = color_str[1:]

    if len(color_str) == 3:
        # 短格式 #fff -> #ffffff
        color_str = ''.join([c * 2 for c in color_str])

    try:
        r = int(color_str[0:2], 16)
        g = int(color_str[2:4], 16)
        b = int(color_str[4:6], 16)
        bg_color = (r, g, b)
        return Image.new('RGB', size, bg_color)
    except (ValueError, IndexError):
        logger.warning(f"  无效的颜色代码: {main_color}，使用默认背景")
        bg = Image.open(BACK_IMAGE)
        return bg.resize(size, Image.Resampling.LANCZOS)


def resize_to_fit_ratio(image: Image.Image, target_ratio: float, max_size: Tuple[int, int]) -> Image.Image:
    """
    调整图片尺寸以适应目标比例，同时不超过最大尺寸

    Args:
        image: 原始图片
        target_ratio: 目标宽高比
        max_size: 最大尺寸 (width, height)

    Returns:
        调整后的图片
    """
    current_ratio = image.width / image.height

    if abs(current_ratio - target_ratio) < 0.01:
        # 比例已经匹配，只需缩放
        scale = min(max_size[0] / image.width, max_size[1] / image.height)
        new_size = (int(image.width * scale), int(image.height * scale))
        return image.resize(new_size, Image.Resampling.LANCZOS)

    # 需要调整比例
    # 计算在目标比例下的最大尺寸
    if current_ratio > target_ratio:
        # 图片更宽，以高度为准
        max_height = min(max_size[1], int(max_size[0] / target_ratio))
        max_width = int(max_height * target_ratio)
    else:
        # 图片更高，以宽度为准
        max_width = min(max_size[0], int(max_size[1] * target_ratio))
        max_height = int(max_width / target_ratio)
    
    # 计算缩放比例
    scale = min(max_width / image.width, max_height / image.height)
    new_size = (int(image.width * scale), int(image.height * scale))

    # 调整到目标比例
    if new_size[0] / new_size[1] > target_ratio:
        # 需要裁剪宽度
        new_width = int(new_size[1] * target_ratio)
        crop_left = (new_size[0] - new_width) // 2
        resized = image.resize(new_size, Image.Resampling.LANCZOS)
        return resized.crop((crop_left, 0, crop_left + new_width, new_size[1]))
    else:
        # 需要裁剪高度
        new_height = int(new_size[0] / target_ratio)
        crop_top = (new_size[1] - new_height) // 2
        resized = image.resize(new_size, Image.Resampling.LANCZOS)
        return resized.crop((0, crop_top, new_size[0], crop_top + new_height))


def save_optimized_image(image: Image.Image, output_file: Path, quality: int = 95) -> None:
    """
    保存图片并优化文件大小

    Args:
        image: 图片对象
        output_file: 输出文件路径
        quality: 初始质量（用于 JPEG）
    """
    # 先尝试保存为 PNG
    image.save(output_file, 'PNG', optimize=True)

    # 检查文件大小
    file_size = output_file.stat().st_size

    if file_size > MAX_FILE_SIZE:
        # 如果超过 2MB，转换为 JPEG 并降低质量
        logger.info(f"  文件大小 {file_size / 1024 / 1024:.2f}MB 超过限制，转换为 JPEG")

        # 如果原图有透明通道，需要添加白色背景
        if image.mode == 'RGBA':
            bg = Image.new('RGB', image.size, (255, 255, 255))
            bg.paste(image, mask=image.split()[3])
            image = bg
        else:
            image = image.convert('RGB')

        # 删除 PNG 文件
        output_file.unlink()

        # 生成 JPG 文件路径
        output_file_jpg = output_file.with_suffix('.jpg')

        # 逐步降低质量直到文件大小符合要求
        current_quality = quality
        while current_quality > 50:
            image.save(output_file_jpg, 'JPEG', quality=current_quality, optimize=True)
            file_size = output_file_jpg.stat().st_size

            if file_size <= MAX_FILE_SIZE:
                logger.info(f"  已优化为 JPEG，质量: {current_quality}，大小: {file_size / 1024 / 1024:.2f}MB")
                return

            current_quality -= 5

        # 如果质量降到 50 还是太大，需要缩小尺寸
        if file_size > MAX_FILE_SIZE:
            scale = (MAX_FILE_SIZE / file_size) ** 0.5
            new_size = (int(image.width * scale), int(image.height * scale))
            image = image.resize(new_size, Image.Resampling.LANCZOS)
            image.save(output_file_jpg, 'JPEG', quality=75, optimize=True)
            file_size = output_file_jpg.stat().st_size
            logger.info(f"  已缩小尺寸并保存为 JPEG，大小: {file_size / 1024 / 1024:.2f}MB")


def save_optimized_jpeg(image: Image.Image, output_file: Path, max_size: int = MAX_JPEG_SIZE, quality: int = 95) -> None:
    """
    保存 JPEG 图片并优化文件大小，确保不超过指定大小（默认 500KB）

    Args:
        image: 图片对象
        output_file: 输出文件路径
        max_size: 最大文件大小（字节），默认 500KB
        quality: 初始质量（用于 JPEG）
    """
    # 确保图片是 RGB 模式（JPEG 不支持透明通道）
    if image.mode == 'RGBA':
        bg = Image.new('RGB', image.size, (255, 255, 255))
        bg.paste(image, mask=image.split()[3])
        image = bg
    elif image.mode != 'RGB':
        image = image.convert('RGB')

    # 逐步降低质量直到文件大小符合要求
    current_quality = quality
    while current_quality > 30:
        image.save(output_file, 'JPEG', quality=current_quality, optimize=True)
        file_size = output_file.stat().st_size

        if file_size <= max_size:
            logger.info(f"  已保存 JPEG，质量: {current_quality}，大小: {file_size / 1024:.2f}KB")
            return

        current_quality -= 5

    # 如果质量降到 30 还是太大，需要缩小尺寸
    file_size = output_file.stat().st_size
    if file_size > max_size:
        # 计算缩放比例
        scale = (max_size / file_size) ** 0.5
        new_size = (int(image.width * scale), int(image.height * scale))
        image = image.resize(new_size, Image.Resampling.LANCZOS)
        
        # 重新尝试保存，从较低质量开始
        current_quality = 75
        while current_quality > 30:
            image.save(output_file, 'JPEG', quality=current_quality, optimize=True)
            file_size = output_file.stat().st_size
            
            if file_size <= max_size:
                logger.info(f"  已缩小尺寸并保存为 JPEG，质量: {current_quality}，大小: {file_size / 1024:.2f}KB")
                return
            
            current_quality -= 5
        
        # 如果还是太大，使用最低质量
        image.save(output_file, 'JPEG', quality=30, optimize=True)
        file_size = output_file.stat().st_size
        logger.info(f"  已缩小尺寸并保存为 JPEG（最低质量），大小: {file_size / 1024:.2f}KB")


def save_final_puzzle_image(image: Image.Image, output_file: Path, target_size: int = 250 * 1024) -> None:
    """
    保存最终拼图结果图片，统一压缩到200-300KB之间
    
    Args:
        image: 图片对象
        output_file: 输出文件路径
        target_size: 目标文件大小（字节），默认250KB，会在200-300KB范围内调整
    """
    # 确保目标大小在合理范围内
    min_size = FINAL_PUZZLE_MIN_SIZE  # 200KB
    max_size = FINAL_PUZZLE_MAX_SIZE  # 300KB
    if target_size < min_size:
        target_size = min_size
    elif target_size > max_size:
        target_size = max_size
    
    # 确保图片是 RGB 模式（JPEG 不支持透明通道）
    if image.mode == 'RGBA':
        bg = Image.new('RGB', image.size, (255, 255, 255))
        bg.paste(image, mask=image.split()[3])
        image = bg
    elif image.mode != 'RGB':
        image = image.convert('RGB')
    
    # 如果输出文件是PNG，改为JPG
    if output_file.suffix.lower() == '.png':
        output_file = output_file.with_suffix('.jpg')
    
    # 先尝试高质量保存，检查文件大小
    current_quality = 95
    best_quality = current_quality
    best_size = 0
    
    # 从高质量开始逐步降低，找到最接近目标大小的质量
    while current_quality >= 30:
        image.save(output_file, 'JPEG', quality=current_quality, optimize=True)
        file_size = output_file.stat().st_size
        
        # 如果文件大小在目标范围内，直接返回
        if min_size <= file_size <= max_size:
            logger.info(f"  已保存最终拼图结果，质量: {current_quality}，大小: {file_size / 1024:.2f}KB")
            return
        
        # 记录最接近目标大小的质量
        if best_size == 0 or abs(file_size - target_size) < abs(best_size - target_size):
            best_quality = current_quality
            best_size = file_size
        
        # 如果文件太大，继续降低质量
        if file_size > max_size:
            current_quality -= 5
        # 如果文件太小，需要提高质量（但我们已经从高到低，所以这种情况不应该发生）
        else:
            break
    
    # 如果找到的质量对应的文件大小不在范围内，需要调整
    if best_size > max_size:
        # 文件太大，需要缩小尺寸
        # 计算缩放比例，使文件大小接近目标大小
        scale = (target_size / best_size) ** 0.5
        new_size = (int(image.width * scale), int(image.height * scale))
        resized_image = image.resize(new_size, Image.Resampling.LANCZOS)
        
        # 重新尝试保存，从较高质量开始
        current_quality = 85
        while current_quality >= 30:
            resized_image.save(output_file, 'JPEG', quality=current_quality, optimize=True)
            file_size = output_file.stat().st_size
            
            if min_size <= file_size <= max_size:
                logger.info(f"  已缩小尺寸并保存最终拼图结果，质量: {current_quality}，大小: {file_size / 1024:.2f}KB")
                return
            
            if file_size > max_size:
                current_quality -= 5
            else:
                # 文件太小，使用当前质量即可
                logger.info(f"  已缩小尺寸并保存最终拼图结果，质量: {current_quality}，大小: {file_size / 1024:.2f}KB")
                return
        
        # 如果还是太大，使用最低质量
        resized_image.save(output_file, 'JPEG', quality=30, optimize=True)
        file_size = output_file.stat().st_size
        logger.info(f"  已缩小尺寸并保存最终拼图结果（最低质量），大小: {file_size / 1024:.2f}KB")
    elif best_size < min_size:
        # 文件太小，使用最佳质量即可（这种情况很少见）
        image.save(output_file, 'JPEG', quality=best_quality, optimize=True)
        logger.info(f"  已保存最终拼图结果，质量: {best_quality}，大小: {best_size / 1024:.2f}KB")
    else:
        # 使用最佳质量
        image.save(output_file, 'JPEG', quality=best_quality, optimize=True)
        logger.info(f"  已保存最终拼图结果，质量: {best_quality}，大小: {best_size / 1024:.2f}KB")


def get_font_path() -> Optional[str]:
    """
    获取支持中文的字体路径
    
    Returns:
        字体路径，如果找不到则返回 None
    """
    system = platform.system()
    
    if system == 'Windows':
        # Windows 系统
        font_paths = [
            'C:/Windows/Fonts/msyh.ttc',  # 微软雅黑
            'C:/Windows/Fonts/msyhbd.ttc',  # 微软雅黑 Bold
            'C:/Windows/Fonts/simhei.ttf',  # 黑体（备选）
            'C:/Windows/Fonts/simsun.ttc',  # 宋体
        ]
    elif system == 'Darwin':  # macOS
        font_paths = [
            '/System/Library/Fonts/PingFang.ttc',  # 苹方
            '/System/Library/Fonts/STHeiti Light.ttc',  # 黑体
            '/System/Library/Fonts/STSong.ttc',  # 宋体
        ]
    else:  # Linux
        font_paths = [
            # 微软雅黑（如果安装了）
            '/usr/share/fonts/truetype/microsoft/msyh.ttc',
            '/usr/share/fonts/truetype/microsoft/msyhbd.ttc',
            # 文泉驿字体
            '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',  # 文泉驿微米黑
            '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',  # 文泉驿正黑
            '/usr/share/fonts/truetype/wqy/wqy-unibit.ttc',  # 文泉驿点阵正黑
            # AR PL 字体
            '/usr/share/fonts/truetype/arphic/uming.ttc',  # AR PL UMing
            '/usr/share/fonts/truetype/arphic/ukai.ttc',  # AR PL UKai
            # Noto 字体（Google 开源字体）
            '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc',
            '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.otf',
            # 思源字体
            '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.otf',
            '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc',
            # 其他常见路径
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',  # DejaVu（不支持中文，但作为最后备选）
        ]
    
    # 按顺序检查字体文件是否存在
    for font_path in font_paths:
        if Path(font_path).exists():
            # 验证字体是否支持中文（简单测试：尝试加载字体）
            try:
                test_font = ImageFont.truetype(font_path, 12)
                # 如果能成功加载，返回路径
                return font_path
            except Exception:
                # 如果加载失败，继续尝试下一个
                continue
    
    # 如果所有预设路径都找不到，尝试使用 fontconfig 查找（如果可用）
    try:
        import subprocess
        result = subprocess.run(
            ['fc-list', ':lang=zh', 'family'],
            capture_output=True,
            text=True,
            timeout=2
        )
        if result.returncode == 0 and result.stdout:
            # 尝试查找字体文件路径
            result_path = subprocess.run(
                ['fc-match', '-f', '%{file}', ':lang=zh'],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result_path.returncode == 0 and result_path.stdout.strip():
                font_file = result_path.stdout.strip()
                if Path(font_file).exists():
                    return font_file
    except Exception:
        pass
    
    return None


def add_size_watermark(image: Image.Image, original_width: int, original_height: int, font_size: Optional[int] = None) -> Image.Image:
    """
    在图片上添加尺寸水印（显示原始图片尺寸）
    
    Args:
        image: 图片对象（最终拼图结果）
        original_width: 原始待拼图图片的宽度
        original_height: 原始待拼图图片的高度
        font_size: 字体大小，如果为 None 则根据图片尺寸自动计算
    
    Returns:
        添加水印后的图片
    """
    # 获取最终图片尺寸（用于计算位置）
    width, height = image.size
    
    # 生成文字：图片尺寸：宽度x高度
    size_text = f"图片尺寸：{original_width}x{original_height}"
    
    # 计算字体大小（根据图片高度）
    if font_size is None:
        font_size = max(24, int(height * 0.025))  # 至少24px，或图片高度的2.5%
    
    # 创建图片副本
    result_img = image.copy()
    
    # 创建绘图对象
    draw = ImageDraw.Draw(result_img)
    
    # 尝试加载支持中文的字体
    font = None
    font_path = get_font_path()
    if font_path:
        try:
            font = ImageFont.truetype(font_path, font_size)
            logger.debug(f"成功加载中文字体: {font_path}")
        except Exception as e:
            logger.debug(f"加载字体失败 {font_path}: {e}")
            font = None
    
    # 如果字体加载失败，尝试使用 fontconfig 查找字体（如果可用）
    if font is None:
        try:
            import subprocess
            result = subprocess.run(
                ['fc-match', '-f', '%{file}', ':lang=zh'],
                capture_output=True,
                text=True,
                timeout=2,
                stderr=subprocess.DEVNULL
            )
            if result.returncode == 0 and result.stdout.strip():
                font_file = result.stdout.strip()
                if Path(font_file).exists():
                    try:
                        font = ImageFont.truetype(font_file, font_size)
                        logger.debug(f"通过 fontconfig 加载中文字体: {font_file}")
                    except Exception as e:
                        logger.debug(f"通过 fontconfig 加载字体失败: {e}")
        except FileNotFoundError:
            # fontconfig 未安装，跳过
            pass
        except Exception as e:
            logger.debug(f"使用 fontconfig 查找字体时出错: {e}")
    
    # 如果仍然没有找到支持中文的字体，尝试查找系统中任何可能的中文字体
    if font is None:
        # 尝试查找常见的中文字体目录
        common_font_dirs = [
            '/usr/share/fonts',
            '/usr/local/share/fonts',
            '~/.fonts',
            '~/.local/share/fonts',
        ]
        
        for font_dir in common_font_dirs:
            font_dir_path = Path(font_dir).expanduser()
            if font_dir_path.exists():
                # 查找可能的中文字体文件
                for pattern in ['*.ttc', '*.ttf', '*.otf']:
                    for font_file in font_dir_path.rglob(pattern):
                        try:
                            # 尝试加载字体
                            test_font = ImageFont.truetype(str(font_file), font_size)
                            # 简单测试：检查字体是否支持中文（通过检查字体名称或尝试渲染）
                            font = test_font
                            logger.info(f"找到并使用中文字体: {font_file}")
                            break
                        except Exception:
                            continue
                    if font is not None:
                        break
                if font is not None:
                    break
    
    # 如果仍然没有找到支持中文的字体，尝试使用默认字体并给出警告
    if font is None:
        logger.warning("未找到支持中文的字体，'图片尺寸'四个字可能显示为乱码。")
        logger.warning("建议安装中文字体，例如：")
        logger.warning("  Ubuntu/Debian: sudo apt-get install fonts-wqy-microhei")
        logger.warning("  或者: sudo apt-get install fonts-noto-cjk")
        
        # 尝试使用默认字体（虽然不支持中文，但至少不会崩溃）
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            try:
                font = ImageFont.truetype("DejaVuSans.ttf", font_size)
            except:
                # 使用默认字体，但需要处理中文编码问题
                font = ImageFont.load_default()
                # 如果使用默认字体，将中文替换为英文
                size_text = f"Size: {original_width}x{original_height}"
                logger.warning("使用默认字体，将中文替换为英文以避免乱码")
    
    # 获取文字尺寸（处理可能的编码错误）
    try:
        bbox = draw.textbbox((0, 0), size_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
    except (UnicodeEncodeError, UnicodeError):
        # 如果出现编码错误，使用英文替代
        size_text = f"Size: {original_width}x{original_height}"
        logger.warning("字体不支持中文，使用英文替代")
        bbox = draw.textbbox((0, 0), size_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
    
    # 计算文字位置：水平居中，距离底部3%
    x = (width - text_width) // 2
    y = int(height * 0.97) - text_height  # 距离底部3%
    
    # 绘制文字（黑色）
    try:
        draw.text((x, y), size_text, fill=(0, 0, 0), font=font)
    except (UnicodeEncodeError, UnicodeError):
        # 如果绘制时出现编码错误，使用英文替代
        size_text = f"Size: {original_width}x{original_height}"
        logger.warning("绘制文字时出现编码错误，使用英文替代")
        draw.text((x, y), size_text, fill=(0, 0, 0), font=font)
    
    return result_img
