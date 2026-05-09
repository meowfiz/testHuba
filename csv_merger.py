#!/usr/bin/env python3
"""
CSV Merger - łączy pliki CSV z src_dir i zapisuje wynik do dst_dir.
Filtruje pliki i kolumny według parametrów z config.ini.

Użycie:
    python csv_merger.py <src_dir> <dst_dir> [--config config.ini]
"""

import argparse
import configparser
import glob
import os
import sys
from datetime import datetime

import pandas as pd


POLISH_CHARS = set('ąćęłńóśźżĄĆĘŁŃÓŚŹŻ')


def contains_polish(df: pd.DataFrame) -> bool:
    """Sprawdza czy jakikolwiek tekst w DataFrame zawiera polskie litery."""
    for col in df.select_dtypes(include='object').columns:
        for val in df[col].dropna():
            if POLISH_CHARS & set(str(val)):
                return True
    return False


def load_config(config_path: str) -> configparser.ConfigParser:
    config = configparser.ConfigParser()
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Brak pliku konfiguracyjnego: {config_path}")
    config.read(config_path, encoding='utf-8')
    return config


def read_csv_safe(filepath: str) -> pd.DataFrame:
    """Wczytuje CSV próbując UTF-8, a następnie CP1250."""
    for enc in ('utf-8-sig', 'utf-8', 'cp1250'):
        try:
            return pd.read_csv(filepath, encoding=enc)
        except (UnicodeDecodeError, pd.errors.ParserError):
            continue
    raise ValueError(f"Nie udało się wczytać pliku: {filepath}")


def build_report_text(report: dict) -> str:
    sep = "=" * 62
    lines = [
        sep,
        "  RAPORT ŁĄCZENIA PLIKÓW CSV",
        f"  Data: {report['timestamp']}",
        sep,
        "",
        "[ PLIKI WEJŚCIOWE ]",
    ]
    for f in report['input_files']:
        lines.append(f"  {f['file']:20s}  {f['rows']:>4} wierszy  |  kolumny: {', '.join(f['cols'])}")
    lines.append(f"  {'ŁĄCZNIE':20s}  {report['total_input_rows']:>4} wierszy  |  {len(report['input_files'])} plików")

    lines += [
        "",
        "[ ZASTOSOWANE FILTRY ]",
        f"  kryterium1 – polskie litery : {report['kryterium1']}",
        f"  kryterium2 – maks. % braków : {report['kryterium2']}%",
    ]

    lines += ["", "[ ODRZUCONE PLIKI  –  kryterium1 ]"]
    if report['files_removed']:
        for f in report['files_removed']:
            lines.append(f"  {f['file']:20s}  powód: {f['reason']}")
    else:
        lines.append("  brak (żaden plik nie odrzucony)")

    lines += ["", "[ USUNIĘTE KOLUMNY  –  kryterium2 ]"]
    if report['columns_removed_missing']:
        for c in report['columns_removed_missing']:
            lines.append(
                f"  '{c['column']}' – {c['missing_pct']:.1f}% braków "
                f"(próg: {report['kryterium2']}%)"
            )
    else:
        lines.append("  brak (żadna kolumna nie usunięta)")

    lines += [
        "",
        "[ PLIK WYNIKOWY ]",
        f"  Plik    : {report['output_file']}",
        f"  Wiersze : {report['total_output_rows']}  "
        f"(odrzucono z powodu braków kolumn: "
        f"{report['total_input_rows'] - report['rows_before_col_drop'] } wierszy z usuniętych plików)",
        f"  Kolumny ({len(report['output_columns'])}): {', '.join(report['output_columns'])}",
        sep,
    ]
    return "\n".join(lines)


def merge_csvs(src_dir: str, dst_dir: str, config_path: str) -> None:
    config = load_config(config_path)

    kryterium1 = config.get('filters', 'kryterium1', fallback='ignoruj').lower().strip()
    kryterium2 = config.getfloat('filters', 'kryterium2', fallback=50.0)

    if kryterium1 not in ('ma', 'nie_ma', 'ignoruj'):
        print(f"Błąd: kryterium1 musi być 'ma', 'nie_ma' lub 'ignoruj' (jest: '{kryterium1}')")
        sys.exit(1)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    report: dict = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'kryterium1': kryterium1,
        'kryterium2': kryterium2,
        'input_files': [],
        'files_removed': [],
        'columns_removed_missing': [],
        'total_input_rows': 0,
        'rows_before_col_drop': 0,
        'total_output_rows': 0,
        'output_columns': [],
        'output_file': '',
    }

    csv_files = sorted(glob.glob(os.path.join(src_dir, '*.csv')))
    if not csv_files:
        print(f"Brak plików CSV w katalogu: {src_dir}")
        sys.exit(1)

    dfs = []
    for filepath in csv_files:
        df = read_csv_safe(filepath)
        df.columns = [c.lower().strip() for c in df.columns]
        fname = os.path.basename(filepath)

        report['input_files'].append({
            'file': fname,
            'rows': len(df),
            'cols': list(df.columns),
        })
        report['total_input_rows'] += len(df)

        has_polish = contains_polish(df)

        if kryterium1 == 'ma' and not has_polish:
            report['files_removed'].append({
                'file': fname,
                'reason': 'brak polskich liter (kryterium1 = ma)',
            })
            continue
        if kryterium1 == 'nie_ma' and has_polish:
            report['files_removed'].append({
                'file': fname,
                'reason': 'zawiera polskie litery (kryterium1 = nie_ma)',
            })
            continue

        dfs.append(df)

    if not dfs:
        print("Żaden plik nie przeszedł filtrowania kryterium1.")
        sys.exit(1)

    merged = pd.concat(dfs, ignore_index=True)
    report['rows_before_col_drop'] = len(merged)

    # kryterium2 – usuń kolumny z nadmierną liczbą braków
    missing_pct = (merged.isnull().sum() / len(merged)) * 100
    cols_to_drop = missing_pct[missing_pct > kryterium2].index.tolist()

    report['columns_removed_missing'] = [
        {'column': c, 'missing_pct': round(float(missing_pct[c]), 2)}
        for c in cols_to_drop
    ]
    merged = merged.drop(columns=cols_to_drop)

    report['total_output_rows'] = len(merged)
    report['output_columns'] = list(merged.columns)

    os.makedirs(dst_dir, exist_ok=True)
    output_file = os.path.join(dst_dir, f'merged_{timestamp}.csv')
    merged.to_csv(output_file, index=False, encoding='utf-8-sig')
    report['output_file'] = os.path.basename(output_file)

    report_text = build_report_text(report)
    report_file = os.path.join(dst_dir, f'raport_{timestamp}.txt')
    with open(report_file, 'w', encoding='utf-8') as fh:
        fh.write(report_text)

    print(report_text)
    print(f"\nPlik wynikowy : {output_file}")
    print(f"Raport        : {report_file}")


def _fix_console_encoding() -> None:
    """Ustawia UTF-8 na stdout/stderr w środowiskach Windows."""
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Łączy pliki CSV z src_dir i zapisuje wynik do dst_dir.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Przykłady:
  python csv_merger.py sample_data output
  python csv_merger.py sample_data output --config config.ini
        """,
    )
    parser.add_argument('src_dir', help='Katalog z plikami CSV wejściowymi')
    parser.add_argument('dst_dir', help='Katalog docelowy dla pliku wynikowego')
    parser.add_argument(
        '--config',
        default='config.ini',
        help='Ścieżka do pliku konfiguracyjnego (domyślnie: config.ini)',
    )
    _fix_console_encoding()
    args = parser.parse_args()
    merge_csvs(args.src_dir, args.dst_dir, args.config)


if __name__ == '__main__':
    main()
