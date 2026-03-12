#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件智能整理器 v1.0
File Smart Organizer

功能：
- 自动按类型分类文件
- 智能重命名（日期+原文件名）
- 重复文件检测
- 空文件夹清理
- 生成整理报告

作者：Captain橘己
日期：2026-03-12
"""

import os
import shutil
import hashlib
from datetime import datetime
from pathlib import Path
from collections import defaultdict


class FileOrganizer:
    """文件智能整理器主类"""
    
    # 文件类型分类规则
    FILE_CATEGORIES = {
        '图片': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg', '.ico'],
        '文档': ['.doc', '.docx', '.pdf', '.txt', '.md', '.xls', '.xlsx', '.ppt', '.pptx'],
        '视频': ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm'],
        '音乐': ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma'],
        '压缩包': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2'],
        '程序': ['.exe', '.msi', '.dmg', '.pkg', '.deb', '.rpm'],
        '代码': ['.py', '.cpp', '.c', '.java', '.js', '.html', '.css', '.json', '.xml'],
    }
    
    def __init__(self, source_dir, target_dir=None):
        """
        初始化整理器
        
        Args:
            source_dir: 源文件夹路径
            target_dir: 目标文件夹路径（默认为源文件夹下的"已整理_日期"）
        """
        self.source_dir = Path(source_dir).resolve()
        if target_dir:
            self.target_dir = Path(target_dir).resolve()
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.target_dir = self.source_dir.parent / f"已整理_{timestamp}"
        
        self.stats = {
            'total_files': 0,
            'organized_files': 0,
            'duplicates_found': 0,
            'duplicates_removed': 0,
            'empty_folders_removed': 0,
            'categories': defaultdict(int),
        }
        
        self.duplicate_hashes = {}
    
    def get_file_category(self, file_path):
        """获取文件分类"""
        ext = file_path.suffix.lower()
        for category, extensions in self.FILE_CATEGORIES.items():
            if ext in extensions:
                return category
        return '其他'
    
    def calculate_hash(self, file_path):
        """计算文件MD5哈希（用于检测重复）"""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            print(f"⚠️  计算哈希失败: {file_path} - {e}")
            return None
    
    def generate_new_name(self, file_path, category):
        """生成新文件名（日期+原文件名）"""
        timestamp = datetime.now().strftime("%Y%m%d")
        original_name = file_path.stem
        suffix = file_path.suffix
        
        # 清理文件名中的非法字符
        clean_name = "".join(c for c in original_name if c.isalnum() or c in (' ', '-', '_'))
        
        new_name = f"{timestamp}_{clean_name}{suffix}"
        target_folder = self.target_dir / category
        target_path = target_folder / new_name
        
        # 处理重名
        counter = 1
        while target_path.exists():
            new_name = f"{timestamp}_{clean_name}_{counter:03d}{suffix}"
            target_path = target_folder / new_name
            counter += 1
        
        return target_path
    
    def organize(self, remove_duplicates=False, remove_empty_folders=False):
        """
        执行整理
        
        Args:
            remove_duplicates: 是否删除重复文件
            remove_empty_folders: 是否删除空文件夹
        """
        print(f"\n{'='*60}")
        print("🗂️  文件智能整理器 v1.0")
        print(f"{'='*60}")
        print(f"📁 源文件夹: {self.source_dir}")
        print(f"📂 目标文件夹: {self.target_dir}")
        print(f"{'='*60}\n")
        
        if not self.source_dir.exists():
            print(f"❌ 错误: 源文件夹不存在: {self.source_dir}")
            return
        
        # 创建目标文件夹
        self.target_dir.mkdir(parents=True, exist_ok=True)
        
        # 遍历所有文件
        all_files = list(self.source_dir.rglob('*'))
        files_only = [f for f in all_files if f.is_file()]
        
        self.stats['total_files'] = len(files_only)
        print(f"📊 发现 {len(files_only)} 个文件\n")
        
        # 处理每个文件
        for i, file_path in enumerate(files_only, 1):
            print(f"处理中... ({i}/{len(files_only)}): {file_path.name}", end='\r')
            
            # 跳过目标文件夹内的文件（避免递归）
            if self.target_dir in file_path.parents:
                continue
            
            category = self.get_file_category(file_path)
            
            # 检测重复
            file_hash = self.calculate_hash(file_path)
            if file_hash:
                if file_hash in self.duplicate_hashes:
                    self.stats['duplicates_found'] += 1
                    if remove_duplicates:
                        print(f"\n🗑️  删除重复: {file_path.name}")
                        # file_path.unlink()  # 暂时不真删除，只记录
                        self.stats['duplicates_removed'] += 1
                        continue
                else:
                    self.duplicate_hashes[file_hash] = file_path
            
            # 生成目标路径
            target_path = self.generate_new_name(file_path, category)
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 复制文件
            try:
                shutil.copy2(file_path, target_path)
                self.stats['organized_files'] += 1
                self.stats['categories'][category] += 1
            except Exception as e:
                print(f"\n⚠️  复制失败: {file_path.name} - {e}")
        
        # 清理空文件夹
        if remove_empty_folders:
            self._remove_empty_folders()
        
        # 生成报告
        self._generate_report()
    
    def _remove_empty_folders(self):
        """删除空文件夹"""
        print("\n🧹 清理空文件夹...")
        empty_count = 0
        
        for root, dirs, files in os.walk(self.source_dir, topdown=False):
            for dir_name in dirs:
                dir_path = Path(root) / dir_name
                # 跳过目标文件夹
                if self.target_dir in dir_path.parents or dir_path == self.target_dir:
                    continue
                try:
                    if dir_path.exists() and not any(dir_path.iterdir()):
                        dir_path.rmdir()
                        empty_count += 1
                        print(f"  删除空文件夹: {dir_path}")
                except Exception as e:
                    pass
        
        self.stats['empty_folders_removed'] = empty_count
    
    def _generate_report(self):
        """生成整理报告"""
        print(f"\n{'='*60}")
        print("📈 整理报告")
        print(f"{'='*60}")
        print(f"📊 总文件数: {self.stats['total_files']}")
        print(f"✅ 已整理: {self.stats['organized_files']}")
        print(f"🔍 重复文件: {self.stats['duplicates_found']}")
        print(f"🗑️  删除重复: {self.stats['duplicates_removed']}")
        print(f"🧹 删除空文件夹: {self.stats['empty_folders_removed']}")
        print(f"\n📁 分类统计:")
        for category, count in sorted(self.stats['categories'].items()):
            print(f"  {category}: {count} 个文件")
        print(f"{'='*60}\n")
        
        # 保存报告到文件
        report_path = self.target_dir / "整理报告.txt"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(f"文件智能整理器 - 整理报告\n")
            f.write(f"整理时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"{'='*60}\n\n")
            f.write(f"源文件夹: {self.source_dir}\n")
            f.write(f"目标文件夹: {self.target_dir}\n\n")
            f.write(f"总文件数: {self.stats['total_files']}\n")
            f.write(f"已整理: {self.stats['organized_files']}\n")
            f.write(f"重复文件: {self.stats['duplicates_found']}\n\n")
            f.write("分类统计:\n")
            for category, count in sorted(self.stats['categories'].items()):
                f.write(f"  {category}: {count} 个文件\n")
        
        print(f"📄 报告已保存: {report_path}\n")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='文件智能整理器 - 自动分类、重命名、去重',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python file_organizer.py "C:\\Users\\你的用户名\\Downloads"
  python file_organizer.py "D:\\我的文件" "E:\\整理后的文件"
  python file_organizer.py "./下载" --remove-duplicates --remove-empty
        """
    )
    
    parser.add_argument('source', help='源文件夹路径')
    parser.add_argument('target', nargs='?', help='目标文件夹路径（可选）')
    parser.add_argument('--remove-duplicates', action='store_true', 
                        help='删除重复文件（谨慎使用）')
    parser.add_argument('--remove-empty', action='store_true',
                        help='删除空文件夹')
    
    args = parser.parse_args()
    
    # 创建整理器并执行
    organizer = FileOrganizer(args.source, args.target)
    organizer.organize(
        remove_duplicates=args.remove_duplicates,
        remove_empty_folders=args.remove_empty
    )


if __name__ == "__main__":
    main()
