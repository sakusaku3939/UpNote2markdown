# UpNote2Markdown

UpNote からエクスポートした Markdown を標準形式に修正するツール

## 修正内容

| # | 内容 | 例 |
|---|------|----|
| 1 | `\[ \]` のエスケープ除去 | `\[結果\]` → `[結果]` |
| 2 | 見出し内の数字エスケープ除去 | `# 1\.` → `# 1.` |
| 3 | 画像リンク直後の `<br>` 除去 | `![](img.png)<br>` → `![](img.png)` |
| 4 | `<br>` のみの見出しを空行に置換 | `### <br>` → 空行 |
| 5 | 数式内の `\_` 修正 | `$$S\_{i,j}$$` → `$$S_{i,j}$$` |
| 6 | 数式内の `\\cmd` 修正 | `$$\\hat{p}$$` → `$$\hat{p}$$` |
| 7 | ゼロ幅スペース除去 | U+200B を除去 |
| 8 | テーブルセル内の `<br>` 除去 | `value<br>` → `value` |
| 9 | 単独行の `<br>` を空行に置換 | `\n<br>\n` → `\n\n` |

## 使い方

### Web版

[https://sakusaku3939.github.io/UpNote2markdown/](https://sakusaku3939.github.io/UpNote2markdown/) をブラウザで開き、テキストを貼り付けるかファイルをドロップしてください。

### スクリプト版

```bash
python fix_markdown.py <UpNoteエクスポートフォルダ>
```

実行前に自動でバックアップが作成されます。

```bash
# 変更内容を確認するだけ（書き込みなし）
python fix_markdown.py <フォルダ> --dry-run

# バックアップなしで実行
python fix_markdown.py <フォルダ> --no-backup
```
