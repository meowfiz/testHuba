# Prerejestracja analizy — szablon i reguła

## Dlaczego

Sesja 60 prawie zaraportowała wynik pozorny. Osiem statystyk histogramu przetestowanych na
dziewięciu preparatach, jedna rozdzieliła oceny użytkownika — i przy 3 dobrych na 9 szansa, że
**którakolwiek** z ośmiu rozdzieli przez sam szum, wynosi **17,5%**. Uratowała mnie poprawka na
wielokrotność, ale dopisałem ją **po** zobaczeniu wyniku. To zadziałało przez przypadek: gdybym
policzył ją inaczej albo w ogóle o niej nie pomyślał, jedna z ośmiu statystyk trafiłaby do
notatki jako zależność.

Jedyne, co usuwa tę klasę błędu na zawsze, to **zapisanie planu przed przebiegiem**. Nie chodzi
o formalność — chodzi o to, że po zobaczeniu liczb nie da się już uczciwie zdecydować, ile
testów „się właściwie zrobiło".

## Reguła

Przed każdą analizą, która ma zakończyć się zdaniem „X zależy od Y" albo „X przewiduje Y",
w `openspec/changes/<zmiana>/tasks.md` powstaje wpis wg szablonu poniżej. **Przed uruchomieniem.**

Nie dotyczy: pomiarów opisowych (ile czego jest, jakie zakresy), diagnostyki pojedynczych
przypadków, przebiegów odtwarzających wcześniejszą liczbę.

Dotyczy zawsze: testów rozdzielenia, korelacji, AUC, porównań konfiguracji, wyboru cech.

## Szablon

```
### PREREJESTRACJA: <jednozdaniowe pytanie>            [data, przed przebiegiem]

- **Hipoteza**: ...  (co konkretnie ma być prawdą, jeśli hipoteza jest trafna)
- **Dane**: ...      (które preparaty, ile, skąd; co jest wykluczone i dlaczego)
- **Etykieta**: ...  (co znaczy "dobry" i "zły" — wybrane TERAZ, nie po wyniku)
- **Statystyka**: ... (AUC / rho / rozłączność przedziałów; jedna, wybrana z góry)
- **Testowanych porównań**: N   (statystyki x etykiety — LICZBA PODANA TERAZ)
- **Poprawka**: ...   (Holm / Bonferroni / permutacyjna; jaka i na jaką rodzinę)
- **Konfuzje do zmierzenia**: ...  (wiek, aparat, rozmiar — wypisane z góry)
- **Co uznam za NEGATYW**: ...  (warunek, przy którym zapiszę wynik negatywny i nie szukam dalej)
- **Czego wynik NIE będzie uprawniał**: ...  (np. wycięcia progu do produkcji)
```

Najważniejsze są dwie ostatnie linie. Bez zapisanego warunku negatywu zawsze da się poszukać
jeszcze jednej cechy; a bez wypisanego ograniczenia interpretacji wynik z korpusu wędruje do
produkcji, czego w tym projekcie popełniliśmy siedem razy pod inną postacią.

## Przykład wypełniony — jak wyglądałaby sekcja 21, gdyby powstała przed przebiegiem

```
### PREREJESTRACJA: czy rozkład gęstości pozwala odrzucić preparat automatycznie?   [2026-09-09]

- Hipoteza: plamka szumu ma SZERSZY rozkład HU niż jądro kostnienia, więc rozrzut
  histogramu odróżni preparat użyteczny od zasypanego szumem.
- Dane: korpus 89 preparatów z prawdą (na strukturę) + 9 niewidzianych z ocenami użytkownika
  (na preparat). Wykluczone 3 preparaty z wadliwą prawdą (018F, 032M, 051-290).
- Etykieta: na strukturę — jądro miednicy wobec "nie kość miednicy" z prawdy;
  na preparat — ocena użytkownika, dobre = {"oba biodra dobre", "jedyny dobry"}.
- Statystyka: rozłączność przedziałów p05–p95 (na strukturę); istnienie cięcia (na preparat).
- Testowanych porównań: 3 deskryptory x 1 etykieta + 8 statystyk x 1 etykieta = 11.
- Poprawka: dla dziewiątki policzyć 2/C(9,3) na test i 1-(1-p)^k na rodzinę.
- Konfuzje: wiek (mineralizacja rośnie z wiekiem), aparat (mediana HU korpus vs niewidziane).
- NEGATYW: jeśli przedziały na korpusie zachodzą, kończę i zapisuję negatyw — NIE dokładam
  kolejnych deskryptorów.
- NIE uprawnia: wycięcia progu jakości z dziewięciu preparatów.
```

Dwie rzeczy zostałyby wtedy inne. Po pierwsze, **hipoteza była odwrotna do prawdy** (struktury
obce są bardziej jednorodne, nie szersze) i zapisanie jej z góry uczyniłoby to jawnym obaleniem,
a nie odkryciem po fakcie. Po drugie, warunek negatywu zatrzymałby mnie po pomiarze na korpusie —
a ja doszedłem do dziesięciu statystyk, przy rodzinnej szansie fałszywego rozdzielenia ~21%.

## Powiązane narzędzia (sesja 61)

- `project_files/python/tests/test_jk_analysis.py` — testy maszynerii statystycznej; każdy test
  nazywa realną porażkę, której zapobiega. Uruchamiać `python -m pytest` przed każdym
  raportowaniem liczb.
- `project_files/python/jk_provenance.py` — nagłówek pochodzenia w każdym raporcie: commit,
  czystość drzewa, komenda i **skrót SHA-256 każdego pliku wejściowego**. Ścieżka nie jest
  tożsamością: `jk_pair_features.json` znaczył w sesji 60 dwie różne rzeczy.
