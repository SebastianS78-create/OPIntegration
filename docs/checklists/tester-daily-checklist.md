# Codzienna lista Testera / Użytkownika

## Co jest gotowe do testów

- [ ] OpenProject → Work Packages → filtruj Status = **Tested**
- [ ] Otwórz zakładkę **Activity** → znajdź komentarz **"Deployed to Cloud Run"**
- [ ] Ten komentarz oznacza że nowa wersja jest wdrożona i można testować

## Testowanie

- [ ] URL środowiska: `https://my-service-drcdgcyjda-lm.a.run.app`
- [ ] Testuj zgodnie z **kryteriami akceptacji** z opisu WP (checkboxy w Description)
- [ ] Sprawdź scenariusze brzegowe (nieprawidłowe dane, duże ilości, timeout)
- [ ] Sprawdź czy nie ma regresji w istniejącej funkcjonalności

## Raportowanie wyników

### Wszystko OK

- [ ] Dodaj komentarz w Activity WP: *"Zweryfikowano na środowisku, działa poprawnie"*
- [ ] PM zmieni status na **Closed**

### Znaleziono błąd

- [ ] Zgłoś do PM używając szablonu poniżej
- [ ] PM stworzy nowy **Bug WP** w OpenProject i przypisze do developera
- [ ] Developer dostanie zadanie, naprawi, i nowa wersja zostanie wdrożona automatycznie

### Propozycja ulepszenia

- [ ] Opisz PM co można poprawić i dlaczego
- [ ] PM stworzy **BI Task** jako child Feature i przypisze do developera

## Szablon raportu błędu

Wyślij do PM (email, Slack, lub komentarz w OP):

```
Tytuł: [krótki opis problemu]
Feature: OP #[numer parent feature]

Kroki do odtworzenia:
1. Wejdź na [URL/stronę]
2. Kliknij [element]
3. Wpisz [dane]

Oczekiwany rezultat:
[co powinno się stać]

Faktyczny rezultat:
[co się dzieje zamiast tego]

Przeglądarka/urządzenie: [np. Chrome 120, Windows 11]
Screenshot: [załącz jeśli możliwe]
```

## Szablon propozycji ulepszenia

```
Tytuł: [krótki opis ulepszenia]
Feature: OP #[numer parent feature]

Obecne zachowanie:
[jak działa teraz]

Proponowane zachowanie:
[jak powinno działać]

Uzasadnienie:
[dlaczego ta zmiana jest wartościowa]
```

## Cykl życia zgłoszenia

```
Tester znajduje problem
    ↓
Tester zgłasza do PM (szablon powyżej)
    ↓
PM tworzy Bug/Task WP w OpenProject
    ↓
PM przypisuje do Developera
    ↓
Developer tworzy branch fix/OP-{ID}-nazwa
    ↓
Developer naprawia, pushuje, otwiera PR
    ↓
Automatycznie: testy + status update + deploy
    ↓
Status → Tested → Tester weryfikuje ponownie
```
