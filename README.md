# mdtopdf

`pandoc`（Markdown → HTML）と Playwright（HTML → PDF）で、表組み崩れをCSSで制御しやすい **テキストPDF** を生成します。

## Install

### uv を使う場合（推奨）

```bash
uv sync
uv run --no-sync python -m playwright install chromium
```

### pip を使う場合

```bash
pip install -e .
python -m playwright install chromium
```

### Requirements

- `pandoc`（外部コマンド）
- Playwright のブラウザ（chromium, firefox, webkit）

### ツールとしてインストール

```bash
# uv tool を使う（推奨）
uv tool install .

# または pipx で隔離インストール
pipx install .
```

インストールすれば `uv run` 不要:

```bash
mdtopdf input.md
```

## Usage

```bash
# uv を使う場合
uv run mdtopdf input.md
uv run mdtopdf input.md -o out.pdf
uv run mdtopdf a.md b.md --outdir ./pdfs
uv run mdtopdf input.md --css ./custom.css
uv run mdtopdf input.md --browser firefox

# インストール済みの場合
mdtopdf input.md
```

ブラウザを指定する場合:

```bash
uv run mdtopdf input.md --browser chromium
uv run mdtopdf input.md --browser firefox
uv run mdtopdf input.md --browser webkit
```

環境によっては Chromium の実行ファイルを明示したい場合があります:

```bash
MDTOPDF_CHROMIUM_EXECUTABLE=/path/to/chromium uv run mdtopdf input.md
```

## Options

- `-o, --output PATH`（単一入力時のみ）
- `--outdir DIR`（複数入力時の出力先）
- `--css PATH`（複数指定可、後勝ち）
- `--no-default-css`
- `--paper A4`（デフォルト `A4`）
- `--margin 20mm`（デフォルト `20mm`）
- `--table-font-size 10pt`（デフォルト `10pt`）
- `--font-family FONT`（デフォルト `Noto Sans JP, Hiragino Kaku Gothic ProN, Yu Gothic, Meiryo, sans-serif`）
- `--browser BROWSER`（デフォルト `chromium`、選択肢: `chromium`, `firefox`, `webkit`）
- `--timeout 30000`（デフォルト 30000ms）
- `--embed-resources / --no-embed-resources`（デフォルト embed on）
