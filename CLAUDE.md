# Kontekst projektu – huba / csv_merger

## Repozytorium

- **Lokalizacja:** `D:\programming\huba\`
- **Remote:** https://github.com/meowfiz/testHuba (branch `main`)
- **Stan:** 2 commity, wszystko wypchnięte

## Czym jest projekt

`csv_merger.py` – CLI w Pythonie do łączenia plików CSV.

```
python csv_merger.py <src_dir> <dst_dir> [--config config.ini]
```

Wczytuje wszystkie `.csv` z `src_dir`, filtruje je i kolumny według `config.ini`, zapisuje połączony plik i raport tekstowy do `dst_dir`.

## Struktura plików

```
huba/
├── csv_merger.py          # główny skrypt
├── config.ini             # parametry filtrowania
├── sample_data/
│   ├── plik1.csv          # polskie litery, 2 braki w wynagrodzenie
│   ├── plik2.csv          # bez polskich liter, braki w ocena
│   ├── plik3.csv          # polskie litery, kolumna telefon prawie pusta
│   ├── plik4.csv          # bez polskich liter, kompletny
│   └── plik5.csv          # polskie litery, kompletny
└── output/                # gitignored – tu trafiają wyniki
```

## Parametry config.ini

| Klucz | Sekcja | Wartości | Opis |
|---|---|---|---|
| `kryterium1` | `[filters]` | `ma` / `nie_ma` / `ignoruj` | Filtruje **całe pliki** po obecności polskich liter |
| `kryterium2` | `[filters]` | `0.0–100.0` | Usuwa **kolumny** z % braków powyżej progu |

Aktualnie: `kryterium1 = ma`, `kryterium2 = 40.0`

## Dane przykładowe – wspólne kolumny

Wszystkie pliki mają co najmniej `imie` i `wiek` (ignorując wielkość liter).
`plik1`, `plik2`, `plik5` mają też `nazwisko` i `miasto`/`kraj`.

## Wynik przy domyślnej konfiguracji

- Odrzucone pliki: `plik2.csv`, `plik4.csv` (brak polskich liter)
- Usunięte kolumny (>40% braków po złączeniu): `wynagrodzenie`, `telefon`, `email`, `stanowisko`, `hobby`
- Wynik: 22 wiersze, 4 kolumny (`imie`, `nazwisko`, `wiek`, `miasto`)

## Zależności

```
pandas>=2.0
```

Brak `requirements.txt` – do dodania jeśli potrzebne.

## Konfiguracja Claude Code (globalna, ~/.claude/)

### settings.json – aktywne hooki

| Event | Akcja |
|---|---|
| `PreToolUse` / `Bash` | `rtk hook claude` – optymalizacja tokenów przez RTK |
| `Stop` | `daily_notes.ps1` – dopisuje wpis sesji do `D:\programming\notes\YYYY-MM-DD.md` |

### Skill /start

Plik `~/.claude/skills/start.md`. Po wywołaniu `/start`:
1. Wykonuje `git pull`
2. Czyta wszystkie `.md` w repo
3. Wyświetla podsumowanie projektu

### Notatki dzienne

Katalog `D:\programming\notes\` – automatycznie uzupełniany po każdej sesji.
Plik `TODO.md` – ręcznie prowadzony.

## Stan na ostatni commit (`dce7da3`)

Wszystko zaimplementowane i wypchnięte. Projekt działa.
Brak otwartych zadań – TODO.md jest pusty.
