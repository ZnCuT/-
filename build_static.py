"""Generate static site into out/ by rendering Flask templates with data from data/raw/.

Usage: python build_static.py
"""
import os
import shutil
from jinja2 import Environment, FileSystemLoader

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(BASE_DIR, 'out')
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'static')
RAW_DIR = os.path.join(BASE_DIR, 'data', 'raw')


def load_books_from_raw():
    books = []
    if not os.path.isdir(RAW_DIR):
        return books
    for name in sorted(os.listdir(RAW_DIR)):
        book_path = os.path.join(RAW_DIR, name)
        if not os.path.isdir(book_path):
            continue
        files = {
            'wenyan': os.path.join(book_path, 'wenyan.txt'),
            'zh': os.path.join(book_path, 'zh.txt'),
            'en': os.path.join(book_path, 'en.txt'),
        }
        contents = {}
        for k, p in files.items():
            try:
                with open(p, 'r', encoding='utf-8') as f:
                    contents[k] = f.read()
            except FileNotFoundError:
                contents[k] = ''
        # simple chapter split by lines beginning with '## '
        def parse(text):
            lines = text.splitlines()
            chapters = []
            cur_title = ''
            cur_lines = []
            for line in lines:
                if line.startswith('## '):
                    if cur_lines or cur_title:
                        chapters.append({'title': cur_title.strip(), 'content': '\n'.join(cur_lines).strip()})
                    cur_title = line[3:].strip()
                    cur_lines = []
                else:
                    cur_lines.append(line)
            if cur_lines or cur_title:
                chapters.append({'title': cur_title.strip(), 'content': '\n'.join(cur_lines).strip()})
            if not chapters:
                return [{'title': '', 'content': text.strip()}]
            return chapters

        ch_w = parse(contents['wenyan'])
        ch_z = parse(contents['zh'])
        ch_e = parse(contents['en'])
        n = min(len(ch_w), len(ch_z), len(ch_e)) if (ch_w and ch_z and ch_e) else max(len(ch_w), len(ch_z), len(ch_e))
        chapters = []
        for i in range(n):
            w = ch_w[i]['content'] if i < len(ch_w) else ''
            z = ch_z[i]['content'] if i < len(ch_z) else ''
            e = ch_e[i]['content'] if i < len(ch_e) else ''
            title = (ch_w[i]['title'] if i < len(ch_w) else '') or (ch_z[i]['title'] if i < len(ch_z) else '') or (ch_e[i]['title'] if i < len(ch_e) else '') or f'第{i+1}章'
            chapters.append({'id': i+1, 'title': title, 'wenyan': w, 'zh': z, 'en': e})
        books.append({'id': name, 'title': name, 'chapters': chapters})
    return books


def render_site(books):
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    # copy static
    out_static = os.path.join(OUT_DIR, 'static')
    if os.path.exists(out_static):
        shutil.rmtree(out_static)
    shutil.copytree(STATIC_DIR, out_static)

    # render home
    tpl = env.get_template('home.html')
    with open(os.path.join(OUT_DIR, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(tpl.render(books=books))

    # render each book page
    book_tpl = env.get_template('book.html')
    for b in books:
        book_dir = os.path.join(OUT_DIR, 'book', b['id'])
        os.makedirs(book_dir, exist_ok=True)
        with open(os.path.join(book_dir, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(book_tpl.render(book=b))

        # render chapters
        ch_tpl = env.get_template('chapter.html')
        for ch in b['chapters']:
            ch_path = os.path.join(book_dir, f'chapter_{ch["id"]}.html')
            # normalize keys expected by template
            ch_display = {'id': ch['id'], 'title': ch.get('title', ''), 'wenyan': ch.get('wenyan', ''), 'z': ch.get('zh', ''), 'en': ch.get('en', '')}
            with open(ch_path, 'w', encoding='utf-8') as f:
                f.write(ch_tpl.render(book=b, chapter=ch_display, prev_url=None, next_url=None))


def main():
    if os.path.exists(OUT_DIR):
        shutil.rmtree(OUT_DIR)
    os.makedirs(OUT_DIR, exist_ok=True)
    books = load_books_from_raw()
    render_site(books)
    print('Static site generated in', OUT_DIR)


if __name__ == '__main__':
    main()
