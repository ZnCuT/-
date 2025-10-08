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


def load_books_from_raw():
    """Scan RAW_DIR for book folders. Each book folder should contain three files:
    - wenyan.txt (古文)
    - zh.txt (现代汉语)
    - en.txt (英文)

    Each file is split into chapters with lines beginning with '## ' as chapter headers.
    Chapters are aligned by order; if counts mismatch we align up to the minimum count and log a warning.
    Returns list of books: [{'id': slug, 'title': name, 'chapters': [{'id': idx, 'title': t, 'wenyan':..., 'zh':..., 'en':...}, ...]}]
    """
    books = []
    if not os.path.isdir(RAW_DIR):
        return books
    for name in sorted(os.listdir(RAW_DIR)):
        book_path = os.path.join(RAW_DIR, name)
        if not os.path.isdir(book_path):
            continue
        # expected filenames
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
        # parse chapters
        ch_w = parse_chapters_from_text(contents['wenyan'])
        ch_z = parse_chapters_from_text(contents['zh'])
        ch_e = parse_chapters_from_text(contents['en'])
        n = min(len(ch_w), len(ch_z), len(ch_e)) if (ch_w and ch_z and ch_e) else max(len(ch_w), len(ch_z), len(ch_e))
        chapters = []
        for i in range(n):
            # use empty string if missing
            w = ch_w[i]['content'] if i < len(ch_w) else ''
            z = ch_z[i]['content'] if i < len(ch_z) else ''
            e = ch_e[i]['content'] if i < len(ch_e) else ''
            title = ch_w[i]['title'] or ch_z[i]['title'] or ch_e[i]['title'] if i < len(ch_w) or i < len(ch_z) or i < len(ch_e) else f'第{i+1}章'
            chapters.append({'id': i+1, 'title': title, 'wenyan': w, 'zh': z, 'en': e})
        books.append({'id': name, 'title': name, 'chapters': chapters})
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


@app.route('/book/<book_id>')
def book_page(book_id):
    for b in BOOKS:
        if b['id'] == book_id:
            return render_template('book.html', book=b)
    abort(404)


@app.route('/book/<book_id>/chapter/<int:chapter_id>')
def chapter_page(book_id, chapter_id):
    for b in BOOKS:
        if b['id'] == book_id:
            for ch in b['chapters']:
                if ch['id'] == chapter_id:
                    # Provide next/prev urls
                    idx = chapter_id - 1
                    prev_url = None
                    next_url = None
                    if idx - 1 >= 0:
                        prev_url = f"/book/{book_id}/chapter/{chapter_id-1}"
                    if idx + 1 < len(b['chapters']):
                        next_url = f"/book/{book_id}/chapter/{chapter_id+1}"
                    # normalize keys for template (chapter.z and chapter.en)
                    ch_display = {'id': ch['id'], 'title': ch.get('title', ''), 'wenyan': ch.get('wenyan', ''), 'z': ch.get('zh', ''), 'en': ch.get('en', '')}
                    return render_template('chapter.html', book=b, chapter=ch_display, prev_url=prev_url, next_url=next_url)
    abort(404)


@app.route('/entry/<entry_id>')
def entry(entry_id):
    for e in load_corpus():
        if str(e.get('id')) == str(entry_id):
            return render_template('entry.html', e=e)
    abort(404)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
