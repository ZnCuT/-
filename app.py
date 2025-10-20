from flask import Flask, render_template, request, abort
import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, 'data', 'corpus.json')

app = Flask(__name__, template_folder=os.path.join(BASE_DIR, 'templates'), static_folder=os.path.join(BASE_DIR, 'static'))

# --- New: load raw three-parallel TXT files organized under data/raw/<book_slug>/ ---
RAW_DIR = os.path.join(BASE_DIR, 'data', 'raw')


def parse_chapters_from_text(text):
    """Split text into chapters by lines starting with '## ' (markdown-like).
    Returns list of dicts: [{'title': title, 'content': content}, ...]
    If no chapter markers are found, treat whole file as single chapter with empty title.
    """
    lines = text.splitlines()
    chapters = []
    cur_title = ''
    cur_lines = []
    for line in lines:
        if line.startswith('## '):
            # flush previous
            if cur_lines or cur_title:
                chapters.append({'title': cur_title.strip(), 'content': '\n'.join(cur_lines).strip()})
            cur_title = line[3:].strip()
            cur_lines = []
        else:
            cur_lines.append(line)
    # final flush
    if cur_lines or cur_title:
        chapters.append({'title': cur_title.strip(), 'content': '\n'.join(cur_lines).strip()})
    if not chapters:
        # whole text as single chapter
        return [{'title': '', 'content': text.strip()}]
    return chapters


def parse_three_parallel_file(file_path):
    """
    解析三平行格式的单个文件
    格式: 文言文\n白话文\n英文\n\n文言文\n白话文\n英文...
    返回: {'wenyan': str, 'zh': str, 'en': str}
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
    except FileNotFoundError:
        return {'wenyan': '', 'zh': '', 'en': ''}
    
    if not content:
        return {'wenyan': '', 'zh': '', 'en': ''}
    
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
    
    return {
        'wenyan': '\n\n'.join(wenyan_parts),
        'zh': '\n\n'.join(zh_parts),
        'en': '\n\n'.join(en_parts)
    }

def load_books_from_raw():
    """
    扫描新的三级目录结构: data/raw/<book>/<category>/<chapter>.txt
    每个txt文件是三平行格式的单个章节
    返回: [{'id': book_id, 'title': book_title, 'categories': [{'id': cat_id, 'title': cat_title, 'chapters': [...]}]}]
    """
    books = []
    if not os.path.isdir(RAW_DIR):
        return books
    
    # 四史的分类配置
    book_configs = {
        "shiji": {"name": "史记", "categories": {"benji": "本纪", "shijia": "世家", "liezhuan": "列传", "shu": "书", "biao": "表"}},
        "hanshu": {"name": "汉书", "categories": {"benji": "本纪", "biao": "表", "zhi": "志", "liezhuan": "列传"}},
        "houhanshu": {"name": "后汉书", "categories": {"leibian": "类传"}},
        "sanguozhi": {"name": "三国志", "categories": {"wei": "魏书", "shu": "蜀书", "wu": "吴书"}}
    }
    
    for book_id in sorted(os.listdir(RAW_DIR)):
        book_path = os.path.join(RAW_DIR, book_id)
        if not os.path.isdir(book_path):
            continue
        
        # 获取书籍配置
        book_config = book_configs.get(book_id, {"name": book_id, "categories": {}})
        book_title = book_config["name"]
        
        # 加载分类
        categories = []
        for cat_dir in sorted(os.listdir(book_path)):
            cat_path = os.path.join(book_path, cat_dir)
            if not os.path.isdir(cat_path):
                continue
            
            cat_title = book_config["categories"].get(cat_dir, cat_dir)
            
            # 加载该分类下的章节
            chapters = []
            chapter_files = [f for f in os.listdir(cat_path) if f.endswith('.txt')]
            
            for i, filename in enumerate(sorted(chapter_files)):
                file_path = os.path.join(cat_path, filename)
                
                # 从文件名提取章节标题
                chapter_title = filename[:-4]  # 去掉.txt后缀
                # 去掉可能的序号前缀 (如 "01_标题" -> "标题")
                if '_' in chapter_title:
                    chapter_title = chapter_title.split('_', 1)[1]
                
                # 解析三平行内容
                content = parse_three_parallel_file(file_path)
                
                chapters.append({
                    'id': i + 1,
                    'title': chapter_title,
                    'wenyan': content['wenyan'],
                    'zh': content['zh'], 
                    'en': content['en']
                })
            
            if chapters:  # 只添加有章节的分类
                categories.append({
                    'id': cat_dir,
                    'title': cat_title,
                    'chapters': chapters
                })
        
        if categories:  # 只添加有内容的书籍
            books.append({
                'id': book_id,
                'title': book_title,
                'categories': categories
            })
    
    return books


# Load books once at startup (for prototype). Could be reloaded on demand.
BOOKS = load_books_from_raw()



def load_corpus():
    try:
        with open(DATA_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def search_corpus(query):
    if not query:
        return load_corpus()
    q = query.lower()
    results = []
    for entry in load_corpus():
        if q in (entry.get('title', '') or '').lower():
            results.append(entry)
            continue
        for k in ('text_1', 'text_2', 'text_3'):
            if q in (entry.get(k, '') or '').lower():
                results.append(entry)
                break
    return results


@app.route('/')
def index():
    q = request.args.get('q', '').strip()
    selected_history = request.args.get('history', '')
    entries = search_corpus(q)
    if selected_history:
        entries = [e for e in entries if e.get('history') == selected_history]
    histories = sorted({e.get('history', '未分类') for e in load_corpus()})
    # Home: show site intro and book list
    return render_template('home.html', books=BOOKS)


@app.route('/book/<book_id>/')
@app.route('/book/<book_id>')
def book_page(book_id):
    """显示书籍的分类列表"""
    for book in BOOKS:
        if book['id'] == book_id:
            return render_template('book.html', book=book)
    abort(404)


@app.route('/book/<book_id>/<category_id>/')
@app.route('/book/<book_id>/<category_id>')
def category_page(book_id, category_id):
    """显示分类的章节列表"""
    for book in BOOKS:
        if book['id'] == book_id:
            for category in book['categories']:
                if category['id'] == category_id:
                    return render_template('category.html', book=book, category=category)
    abort(404)


@app.route('/book/<book_id>/<category_id>/chapter/<int:chapter_id>/')
@app.route('/book/<book_id>/<category_id>/chapter/<int:chapter_id>')
def chapter_page(book_id, category_id, chapter_id):
    """显示具体章节的三平行内容"""
    for book in BOOKS:
        if book['id'] == book_id:
            for category in book['categories']:
                if category['id'] == category_id:
                    for chapter in category['chapters']:
                        if chapter['id'] == chapter_id:
                            # 计算前后章节链接
                            chapters = category['chapters']
                            chapter_idx = next(i for i, ch in enumerate(chapters) if ch['id'] == chapter_id)
                            
                            prev_url = None
                            next_url = None
                            if chapter_idx > 0:
                                prev_ch = chapters[chapter_idx - 1]
                                prev_url = f"/book/{book_id}/{category_id}/chapter/{prev_ch['id']}/"
                            if chapter_idx < len(chapters) - 1:
                                next_ch = chapters[chapter_idx + 1]
                                next_url = f"/book/{book_id}/{category_id}/chapter/{next_ch['id']}/"
                            
                            # 标准化章节数据格式，兼容模板
                            chapter_display = {
                                'id': chapter['id'], 
                                'title': chapter.get('title', ''), 
                                'wenyan': chapter.get('wenyan', ''), 
                                'z': chapter.get('zh', ''),  # 模板中使用 'z' 
                                'en': chapter.get('en', '')
                            }
                            
                            return render_template('chapter.html', 
                                                 book=book, 
                                                 category=category,
                                                 chapter=chapter_display, 
                                                 prev_url=prev_url, 
                                                 next_url=next_url)
    abort(404)


@app.route('/entry/<entry_id>')
def entry(entry_id):
    for e in load_corpus():
        if str(e.get('id')) == str(entry_id):
            return render_template('entry.html', e=e)
    abort(404)


if __name__ == '__main__':
    # 适配 Vercel 的 PORT 环境变量，默认 fallback 到 5000（本地开发用）
    port = int(os.environ.get('PORT', 5000))
    # 生产环境强制关闭 debug（Vercel 要求）
    app.run(host='0.0.0.0', port=port, debug=False)
