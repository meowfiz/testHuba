"""
Analizator jakości danych CSV – generuje raport HTML z heatmapami braków
i oceną buźką emoji dla każdego pliku wejściowego i połączonego zbioru.
"""

import base64
import io
import os
from datetime import datetime

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd


def calculate_missing_pct(df: pd.DataFrame) -> float:
    """Zwraca procent brakujących wartości (NaN) w całym DataFrame."""
    total = df.size
    if total == 0:
        return 100.0
    return (df.isnull().sum().sum() / total) * 100


def get_emoji(missing_pct: float) -> str:
    if missing_pct < 5:
        return '😊'
    elif missing_pct < 15:
        return '🙂'
    elif missing_pct < 30:
        return '😐'
    elif missing_pct <= 50:
        return '😟'
    return '😢'


def generate_heatmap_base64(df: pd.DataFrame, title: str) -> str:
    """Generuje heatmapę braków danych i zwraca PNG jako string base64."""
    original_len = len(df)
    sampled = original_len > 10_000
    if sampled:
        df = df.sample(500, random_state=42)
        title = f"{title}\n(próbka 500/{original_len} wierszy)"

    ncols = max(1, len(df.columns))
    nrows = max(1, len(df))
    fig_w = max(6, ncols * 0.8)
    fig_h = min(8, max(3, nrows * 0.15))
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))

    if df.empty:
        ax.text(0.5, 0.5, 'Brak danych', ha='center', va='center', transform=ax.transAxes)
        ax.set_title(title)
    elif df.isnull().sum().sum() == 0:
        sns.heatmap(df.isnull(), cmap='YlOrRd', cbar=False, ax=ax, yticklabels=False)
        ax.set_title(f"{title}\nBrak braków danych ✓")
    else:
        sns.heatmap(df.isnull(), cmap='YlOrRd', cbar=False, ax=ax, yticklabels=False)
        ax.set_title(title)

    ax.set_xlabel('Kolumny')
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('ascii')


_CSS = """
body {
    font-family: "Segoe UI Emoji", "Apple Color Emoji", "Noto Color Emoji", sans-serif;
    background: #f5f5f5;
    margin: 0;
    padding: 20px;
    color: #222;
}
h1 {
    font-size: 1.6em;
    border-bottom: 2px solid #ccc;
    padding-bottom: 8px;
}
.section {
    background: white;
    border-radius: 8px;
    padding: 16px 20px;
    margin-bottom: 20px;
    box-shadow: 0 1px 4px rgba(0,0,0,.12);
}
.merged {
    border-left: 4px solid #4a90d9;
}
h2 {
    font-size: 1.15em;
    margin: 0 0 10px 0;
}
.pct {
    font-size: 0.85em;
    font-weight: normal;
    color: #666;
    margin-left: 8px;
}
img {
    max-width: 100%;
    border: 1px solid #ddd;
    border-radius: 4px;
}
.empty-note {
    color: #c0392b;
    font-style: italic;
}
.meta {
    font-size: 0.8em;
    color: #999;
    margin-top: 30px;
    border-top: 1px solid #ddd;
    padding-top: 8px;
}
"""


def _file_section_html(name: str, df: pd.DataFrame, is_merged: bool = False) -> str:
    section_class = 'section merged' if is_merged else 'section'

    if df.empty:
        return (
            f'<div class="{section_class}">'
            f'<h2>😢 {name} <span class="pct">100.0% braków</span></h2>'
            f'<p class="empty-note">Plik pusty</p>'
            f'</div>\n'
        )

    pct = calculate_missing_pct(df)
    emoji = get_emoji(pct)
    img_b64 = generate_heatmap_base64(df, name)

    return (
        f'<div class="{section_class}">'
        f'<h2>{emoji} {name} <span class="pct">{pct:.1f}% braków</span></h2>'
        f'<img src="data:image/png;base64,{img_b64}" alt="heatmapa {name}">'
        f'</div>\n'
    )


def generate_report(
    frames: dict,
    merged_df: pd.DataFrame,
    dst_dir: str,
) -> None:
    """Generuje raport HTML z heatmapami i buźkami; zapisuje do dst_dir/analysis_report.html."""
    sections = [_file_section_html(fname, df) for fname, df in frames.items()]
    sections.append(_file_section_html('Połączony zbiór (po filtracji)', merged_df, is_merged=True))

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    html = (
        '<!DOCTYPE html>\n'
        '<html lang="pl">\n'
        '<head>\n'
        '  <meta charset="utf-8">\n'
        '  <meta name="viewport" content="width=device-width, initial-scale=1">\n'
        '  <title>Analiza jakości danych CSV</title>\n'
        f'  <style>{_CSS}  </style>\n'
        '</head>\n'
        '<body>\n'
        '  <h1>Analiza jakości danych CSV</h1>\n'
        + ''.join(f'  {s}' for s in sections)
        + f'  <p class="meta">Wygenerowano: {timestamp}</p>\n'
        '</body>\n'
        '</html>\n'
    )

    os.makedirs(dst_dir, exist_ok=True)
    out_path = os.path.join(dst_dir, 'analysis_report.html')
    with open(out_path, 'w', encoding='utf-8') as fh:
        fh.write(html)
    print(f"Raport HTML   : {out_path}")
