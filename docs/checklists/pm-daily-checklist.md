# Codzienna lista Product Managera

## Rano — przegląd statusów

- [ ] Otwórz OpenProject → Work Packages → filtruj po statusie **In Progress** i **In Testing**
- [ ] Sprawdź zakładkę **Activity** na każdym WP — komentarze od `github-bot` pokazują postęp prac
- [ ] Nie pytaj developerów o status — wszystko widać w Activity (commity, PR-y, deploye)

## Tworzenie nowych zadań

### BI Feature (funkcjonalność biznesowa)

- [ ] Subject: jasny, zwięzły opis celu biznesowego
- [ ] Description: kryteria akceptacji w formie checkboxów markdown:

```markdown
## Kryteria akceptacji
- [ ] Użytkownik może [akcja] na stronie [nazwa]
- [ ] System zwraca [oczekiwany rezultat] gdy [warunek]
- [ ] Endpoint /api/xxx odpowiada statusem 200 z polem "xyz"
- [ ] Test jednostkowy pokrywa scenariusz [opis]
```

- [ ] Ustaw Priority i szacowany czas
- [ ] Stwórz child **BI Tasks** z konkretnym zakresem technicznym
- [ ] Przypisz (Assignee) do konkretnych developerów

### Zasady dobrych kryteriów akceptacji

- Każdy checkbox = jedna testowalna rzecz
- Używaj języka zrozumiałego dla developera i AI (Claude Code)
- Unikaj ogólników ("powinno działać dobrze") — pisz konkretne warunki
- Developer (i Claude Code) przeczyta te kryteria i na ich podstawie napisze kod + testy

## Weryfikacja wdrożeń (Tested → Closed)

- [ ] Filtruj WP po statusie **Tested** — te czekają na Twoją weryfikację
- [ ] Otwórz Activity → znajdź komentarz **"Deployed to Cloud Run"** z linkiem do Cloud Console
- [ ] Przetestuj na środowisku: `https://my-service-drcdgcyjda-lm.a.run.app`
- [ ] Jeśli **OK** → zmień status na **Closed** (jedyna ręczna zmiana statusu w całym flow)
- [ ] Jeśli **nie OK** → stwórz nowy **Bug WP** jako child, przypisz do developera

## Obsługa feedbacku od użytkowników/testerów

- [ ] Bug od użytkownika → stwórz WP typ **Bug**, ustaw jako child odpowiedniego Feature
- [ ] Ulepszenie/enhancement → stwórz WP typ **BI Task**, ustaw jako child Feature
- [ ] Przypisz do developera, ustaw priorytet
- [ ] Developer zobaczy nowe zadanie w OP i rozpocznie pracę (branch → commit → PR → deploy)

## Jak czytać Activity tab

| Komentarz github-bot | Co to znaczy |
|---|---|
| **Commit pushed** to branch `...` | Developer zaczął pracę, status → In Progress |
| **Pull Request opened** #N | Kod gotowy do review, status → In Testing |
| **Automated Bug created** | Testy CI wykryły błąd, stworzono Bug WP |
| **Pull Request merged** #N | Kod zaakceptowany, status → Tested |
| **Deployed to Cloud Run** | Nowa wersja wdrożona, można testować |
| **Pull Request closed** without merge | Kod odrzucony, status → Rejected |
