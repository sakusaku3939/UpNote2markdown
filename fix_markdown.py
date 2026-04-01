"""
UpNote から Obsidian へエクスポートした Markdown ファイルを
標準 Markdown に修正するスクリプト。

修正内容:
  1. \\[ \\] の不要なエスケープを除去  (例: \\[結果\\] → [結果])
  2. 見出し内の数字エスケープを除去  (例: # 1\\. → # 1.)
  3. 画像リンク直後の <br> を除去    (例: ![](img.png)<br> → ![](img.png))
  4. <br> のみの見出しを空行に置換   (例: ### <br> → 空行)
  5. 数式ブロック内の \\_ → _       (例: $$S\\_{i,j}$$ → $$S_{i,j}$$)
  6. 数式ブロック内の \\\\cmd → \\cmd  (例: $$\\\\hat{p}$$ → $$\\hat{p}$$)
  7. ゼロ幅スペース (U+200B) を除去
  8. テーブルセル内の <br> を除去   (例: value<br> → value)
  9. 単独行の <br> を空行に置換     (例: \n<br>\n → \n\n)
 10. $$ 行末の余分なスペース除去    (例: $$formula$$  → $$formula$$)
"""

import os
import re
import sys
import shutil
from pathlib import Path


# ─────────────────────────── ユーティリティ ───────────────────────────

def split_by_code_blocks(content: str):
    """
    コンテンツをコードブロック内外に分割して返す。
    戻り値: [(is_code_block: bool, text: str), ...]
    """
    pattern = re.compile(r'(```.*?```)', re.DOTALL)
    parts = []
    last = 0
    for m in pattern.finditer(content):
        if m.start() > last:
            parts.append((False, content[last:m.start()]))
        parts.append((True, m.group()))
        last = m.end()
    if last < len(content):
        parts.append((False, content[last:]))
    return parts


def fix_math_in_block(text: str) -> str:
    """数式ブロック ($$...$$) 内のエスケープを修正する。"""
    def replace_math(m):
        math = m.group()
        # \_ → _  (エスケープされたアンダースコアをサブスクリプト用に修正)
        math = math.replace('\\_', '_')
        # \\cmd → \cmd  (コマンド名・特殊記号前の二重バックスラッシュを修正)
        # 対象: アルファベット、{ } [ ] など LaTeX でよく使う文字
        math = re.sub(r'\\\\([a-zA-Z{}\[\]])', r'\\\1', math)
        return math

    return re.sub(r'\$\$.+?\$\$', replace_math, text, flags=re.DOTALL)


# ─────────────────────────── 各修正処理 ───────────────────────────────

def fix_escaped_brackets(text: str) -> str:
    r"""
    コードブロック外の \[ と \] を [ と ] に戻す。
    ただしリンク構文 [text](url) を壊さないよう、
    \[ \] の形のエスケープのみを対象にする。
    """
    text = re.sub(r'\\\[', '[', text)
    text = re.sub(r'\\\]', ']', text)
    return text


def fix_escaped_dot_in_headings(text: str) -> str:
    r"""見出し行内の 数字\. を 数字. に修正する。例: # 1\. → # 1."""
    return re.sub(r'^(#{1,6} .*?)(\d+)\\\.', r'\1\2.', text, flags=re.MULTILINE)


def fix_br_after_image(text: str) -> str:
    """画像リンク直後の <br> を除去する。"""
    return re.sub(r'(!\[.*?\]\([^)]*\))<br>', r'\1', text)


def fix_heading_only_br(text: str) -> str:
    """<br> のみを含む見出し行を空行に置換する。"""
    return re.sub(r'^#{1,6} <br>\s*$', '', text, flags=re.MULTILINE)


def fix_math_trailing_spaces(text: str) -> str:
    """行末の $$ の後にある余分なスペース・タブを除去する。
    一部のレンダラーは $$ の後にスペースがあると閉じタグを認識できない。"""
    return re.sub(r'(\$\$)[ \t]+$', r'\1', text, flags=re.MULTILINE)


def fix_standalone_br(text: str) -> str:
    """単独行の <br>（段落区切りとして挿入されたもの）を行ごと除去する。"""
    return re.sub(r'^<br>[ \t]*\n', '', text, flags=re.MULTILINE)


def fix_br_in_table(text: str) -> str:
    """テーブルセル内の <br> を除去する（| で囲まれた行のみ対象）。"""
    lines = text.split('\n')
    result = []
    for line in lines:
        if line.strip().startswith('|') and '<br>' in line:
            line = line.replace('<br>', '')
        result.append(line)
    return '\n'.join(result)


def remove_zero_width_spaces(text: str) -> str:
    """ゼロ幅スペース (U+200B) を除去する。"""
    return text.replace('\u200b', '')


# ─────────────────────────── メイン処理 ───────────────────────────────

def fix_content(content: str) -> str:
    """1ファイル分の Markdown コンテンツを修正して返す。"""

    # コードブロック外のみに適用する修正
    parts = split_by_code_blocks(content)
    processed = []
    for is_code, chunk in parts:
        if not is_code:
            chunk = fix_escaped_brackets(chunk)
            chunk = fix_escaped_dot_in_headings(chunk)
            chunk = fix_br_after_image(chunk)
            chunk = fix_heading_only_br(chunk)
            chunk = fix_standalone_br(chunk)
            chunk = fix_br_in_table(chunk)
            chunk = fix_math_trailing_spaces(chunk)
            chunk = fix_math_in_block(chunk)
        processed.append(chunk)
    result = ''.join(processed)

    # ファイル全体に適用する修正
    result = remove_zero_width_spaces(result)

    return result


def process_directory(target_dir: str, backup: bool = True, dry_run: bool = False):
    target = Path(target_dir)
    md_files = sorted(target.glob('*.md'))

    if not md_files:
        print(f'Markdown ファイルが見つかりません: {target_dir}')
        return

    if backup and not dry_run:
        backup_dir = target.parent / (target.name + '_backup')
        if backup_dir.exists():
            shutil.rmtree(backup_dir)
        shutil.copytree(target, backup_dir)
        print(f'バックアップ作成: {backup_dir}')

    changed_count = 0
    for path in md_files:
        original = path.read_text(encoding='utf-8')
        fixed = fix_content(original)

        if original != fixed:
            changed_count += 1
            if dry_run:
                print(f'[DRY-RUN] 変更あり: {path.name}')
                # 差分を簡易表示
                orig_lines = original.splitlines()
                fix_lines = fixed.splitlines()
                for i, (ol, fl) in enumerate(zip(orig_lines, fix_lines)):
                    if ol != fl:
                        print(f'  行{i+1} 前: {repr(ol[:80])}')
                        print(f'  行{i+1} 後: {repr(fl[:80])}')
            else:
                path.write_text(fixed, encoding='utf-8')
                print(f'修正済み: {path.name}')
        else:
            if dry_run:
                print(f'[DRY-RUN] 変更なし: {path.name}')

    print(f'\n完了: {changed_count}/{len(md_files)} ファイルを修正しました。')


# ──────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='UpNote→Obsidian Markdown の書式を標準 Markdown に修正する'
    )
    parser.add_argument(
        'directory',
        nargs='?',
        default=r'UpNote_2026-04-01_22-34-01',
        help='修正対象ディレクトリ (デフォルト: UpNote_2026-04-01_22-34-01)',
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='実際には書き込まず、変更内容のみ表示する',
    )
    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='バックアップを作成しない',
    )

    args = parser.parse_args()

    process_directory(
        args.directory,
        backup=not args.no_backup,
        dry_run=args.dry_run,
    )
