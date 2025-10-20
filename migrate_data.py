#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据迁移工具：将现有的大文件格式转换为新的分类目录结构
"""

import os
import shutil
import re
from pathlib import Path

# 当前和目标目录
CURRENT_RAW_DIR = "data/raw"
NEW_RAW_DIR = "data/raw_new"

# 四史的分类定义
BOOK_CATEGORIES = {
    "shiji": {
        "name": "史记",
        "categories": {
            "benji": "本纪",
            "shijia": "世家", 
            "liezhuan": "列传",
            "shu": "书",
            "biao": "表"
        }
    },
    "hanshu": {
        "name": "汉书",
        "categories": {
            "benji": "本纪",
            "biao": "表",
            "zhi": "志", 
            "liezhuan": "列传"
        }
    },
    "houhanshu": {
        "name": "后汉书",
        "categories": {
            "leibian": "类传"
        }
    },
    "sanguozhi": {
        "name": "三国志",
        "categories": {
            "wei": "魏书",
            "shu": "蜀书",
            "wu": "吴书"
        }
    }
}

def parse_chapters_from_text(text):
    """解析章节，同原来的逻辑"""
    lines = text.splitlines()
    chapters = []
    cur_title = ''
    cur_lines = []
    
    for line in lines:
        if line.startswith('## '):
            # 保存前一章
            if cur_lines or cur_title:
                chapters.append({
                    'title': cur_title.strip(),
                    'content': '\n'.join(cur_lines).strip()
                })
            cur_title = line[3:].strip()
            cur_lines = []
        else:
            cur_lines.append(line)
    
    # 保存最后一章
    if cur_lines or cur_title:
        chapters.append({
            'title': cur_title.strip(), 
            'content': '\n'.join(cur_lines).strip()
        })
    
    if not chapters:
        return [{'title': '', 'content': text.strip()}]
    
    return chapters

def categorize_chapter(book_id, chapter_title):
    """
    根据章节标题自动分类到对应的卷
    这个函数需要根据实际的章节标题进行调整
    """
    title = chapter_title.lower()
    
    if book_id == "shiji":
        if "本纪" in chapter_title:
            return "benji"
        elif "世家" in chapter_title:
            return "shijia"
        elif "列传" in chapter_title:
            return "liezhuan" 
        elif "书" in chapter_title:
            return "shu"
        elif "表" in chapter_title:
            return "biao"
        else:
            # 默认分类逻辑，可以根据章节序号等规律调整
            return "liezhuan"  # 默认放到列传
    
    elif book_id == "hanshu":
        if "本纪" in chapter_title:
            return "benji"
        elif "表" in chapter_title:
            return "biao"
        elif "志" in chapter_title:
            return "zhi"
        else:
            return "liezhuan"
    
    elif book_id == "houhanshu":
        return "leibian"
    
    elif book_id == "sanguozhi":
        if "魏" in chapter_title:
            return "wei"
        elif "蜀" in chapter_title:
            return "shu"
        elif "吴" in chapter_title:
            return "wu"
        else:
            return "wei"  # 默认
    
    return "default"

def convert_three_parallel_to_separate(content):
    """
    将三平行格式转换为分离格式
    输入: 三平行内容（文言文\n白话文\n英文\n\n文言文\n白话文\n英文...）
    输出: (wenyan_text, zh_text, en_text)
    """
    # 按双换行分割段落组
    paragraph_groups = content.split('\n\n')
    
    wenyan_parts = []
    zh_parts = []
    en_parts = []
    
    for group in paragraph_groups:
        lines = [line.strip() for line in group.split('\n') if line.strip()]
        
        if len(lines) >= 3:
            # 标准三平行格式
            wenyan_parts.append(lines[0])
            zh_parts.append(lines[1]) 
            en_parts.append(lines[2])
        elif len(lines) == 2:
            # 可能缺少英文
            wenyan_parts.append(lines[0])
            zh_parts.append(lines[1])
            en_parts.append("")
        elif len(lines) == 1:
            # 只有一行，可能是标题或单独内容
            wenyan_parts.append(lines[0])
            zh_parts.append("")
            en_parts.append("")
    
    return (
        '\n\n'.join(wenyan_parts),
        '\n\n'.join(zh_parts), 
        '\n\n'.join(en_parts)
    )

def migrate_book(book_path, book_id):
    """迁移单本书的数据"""
    print(f"正在迁移 {book_id}...")
    
    # 读取三个文件
    files = {
        'wenyan': os.path.join(book_path, 'wenyan.txt'),
        'zh': os.path.join(book_path, 'zh.txt'),
        'en': os.path.join(book_path, 'en.txt'),
    }
    
    contents = {}
    for k, path in files.items():
        try:
            with open(path, 'r', encoding='utf-8') as f:
                contents[k] = f.read()
        except FileNotFoundError:
            print(f"警告: 找不到文件 {path}")
            contents[k] = ""
    
    # 解析章节
    chapters_w = parse_chapters_from_text(contents['wenyan'])
    chapters_z = parse_chapters_from_text(contents['zh']) 
    chapters_e = parse_chapters_from_text(contents['en'])
    
    # 对齐章节数量
    max_chapters = max(len(chapters_w), len(chapters_z), len(chapters_e))
    
    # 创建新的目录结构
    book_config = BOOK_CATEGORIES.get(book_id, {})
    categories = book_config.get('categories', {'default': '默认'})
    
    # 为每个分类创建目录
    for cat_id in categories.keys():
        cat_dir = os.path.join(NEW_RAW_DIR, book_id, cat_id)
        os.makedirs(cat_dir, exist_ok=True)
    
    # 按章节处理
    for i in range(max_chapters):
        # 获取章节内容
        w_content = chapters_w[i]['content'] if i < len(chapters_w) else ""
        z_content = chapters_z[i]['content'] if i < len(chapters_z) else ""
        e_content = chapters_e[i]['content'] if i < len(chapters_e) else ""
        
        # 获取章节标题
        title = ""
        if i < len(chapters_w) and chapters_w[i]['title']:
            title = chapters_w[i]['title']
        elif i < len(chapters_z) and chapters_z[i]['title']:
            title = chapters_z[i]['title']
        elif i < len(chapters_e) and chapters_e[i]['title']:
            title = chapters_e[i]['title']
        else:
            title = f"第{i+1}章"
        
        # 确定分类
        category = categorize_chapter(book_id, title)
        if category not in categories:
            category = list(categories.keys())[0]  # 使用第一个分类作为默认
        
        # 创建三平行格式的文件内容
        # 合并三种语言的对应段落
        parallel_content = create_parallel_content(w_content, z_content, e_content)
        
        # 生成文件名
        safe_title = re.sub(r'[^\w\u4e00-\u9fff]', '_', title)[:50]  # 去除特殊字符，限制长度
        filename = f"{i+1:02d}_{safe_title}.txt"
        
        # 写入文件
        output_path = os.path.join(NEW_RAW_DIR, book_id, category, filename)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(parallel_content)
        
        print(f"  创建: {category}/{filename}")

def create_parallel_content(wenyan, zh, en):
    """
    创建三平行格式的内容
    将三种语言的内容重新组织为段落对应的格式
    """
    # 简单处理：按段落分割并重新组合
    w_paragraphs = [p.strip() for p in wenyan.split('\n\n') if p.strip()]
    z_paragraphs = [p.strip() for p in zh.split('\n\n') if p.strip()]
    e_paragraphs = [p.strip() for p in en.split('\n\n') if p.strip()]
    
    # 对齐段落数量
    max_paras = max(len(w_paragraphs), len(z_paragraphs), len(e_paragraphs))
    
    parallel_groups = []
    for i in range(max_paras):
        w = w_paragraphs[i] if i < len(w_paragraphs) else ""
        z = z_paragraphs[i] if i < len(z_paragraphs) else ""
        e = e_paragraphs[i] if i < len(e_paragraphs) else ""
        
        # 组成三平行段落组
        group = []
        if w: group.append(w)
        if z: group.append(z) 
        if e: group.append(e)
        
        if group:
            parallel_groups.append('\n'.join(group))
    
    return '\n\n'.join(parallel_groups)

def main():
    """主函数"""
    print("开始数据迁移...")
    print(f"源目录: {CURRENT_RAW_DIR}")
    print(f"目标目录: {NEW_RAW_DIR}")
    
    # 创建新目录
    os.makedirs(NEW_RAW_DIR, exist_ok=True)
    
    # 遍历现有的书籍目录
    if not os.path.isdir(CURRENT_RAW_DIR):
        print(f"错误: 找不到源目录 {CURRENT_RAW_DIR}")
        return
    
    for item in os.listdir(CURRENT_RAW_DIR):
        book_path = os.path.join(CURRENT_RAW_DIR, item)
        if os.path.isdir(book_path):
            migrate_book(book_path, item)
    
    print("\n迁移完成!")
    print(f"新的目录结构已创建在: {NEW_RAW_DIR}")
    print("\n请检查结果，确认无误后可以:")
    print(f"1. 备份原目录: mv {CURRENT_RAW_DIR} {CURRENT_RAW_DIR}_backup")
    print(f"2. 使用新目录: mv {NEW_RAW_DIR} {CURRENT_RAW_DIR}")

if __name__ == "__main__":
    main()