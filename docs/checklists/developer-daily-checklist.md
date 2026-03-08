# Codzienna lista Developera

## Rano — sprawdź zadania

- [ ] OpenProject → My Page lub Work Packages → filtruj **Assignee=ja**, **Status=New**
- [ ] Przeczytaj Description + kryteria akceptacji (checkboxy)
- [ ] Zanotuj numer **OP-{ID}** z URL karty zadania

## Rozpoczęcie pracy

```bash
# 1. Pobierz najnowszy main
git checkout main && git pull

# 2. Stwórz branch z numerem OP
git checkout -b feature/OP-{ID}-krotka-nazwa    # dla BI Feature
git checkout -b task/OP-{ID}-krotka-nazwa       # dla BI Task
git checkout -b fix/OP-{ID}-krotka-nazwa        # dla Bug fix
```

- [ ] Otwórz VS Code w katalogu projektu
- [ ] Uruchom Claude Code (`claude` w terminalu) — automatycznie czyta `CLAUDE.md`

## Kodowanie z Claude Code

### Przykładowe prompty

```
"Pracuję nad OP-42, zaimplementuj funkcjonalność zgodnie z opisem w OpenProject"
"Napisz testy dla OP-42 pokrywające kryteria akceptacji"
"Stwórz PR dla OP-42 z opisem zmian"
```

### Co Claude Code wie z CLAUDE.md

- Konwencje branchów (`feature/OP-{ID}-nazwa`)
- Format commitów (`feat(OP-42): opis`)
- Szablon PR (`.github/PULL_REQUEST_TEMPLATE.md`)
- Stack technologiczny (Python, FastAPI, pytest)
- ID statusów i typów w OpenProject API

### Przed pushem

- [ ] Uruchom testy: `pytest --tb=short`
- [ ] Sprawdź linting: `ruff check .`
- [ ] Upewnij się że commit message zawiera prawidłowy OP-{ID}

## Push i Pull Request

```bash
# Push branch
git push -u origin feature/OP-{ID}-nazwa

# Otwórz PR (opcja 1: GitHub CLI)
gh pr create --fill

# Opcja 2: przez GitHub web
# → PR template wypełni się automatycznie
```

### Co dzieje się automatycznie po push

| Zdarzenie | Automatyczna akcja |
|---|---|
| `git push` na branch `OP-*` | Status → **In Progress** + komentarz w OP Activity |
| Testy failują | Bug WP tworzony jako child + komentarz na parent WP |
| Otwarcie PR | Status → **In Testing** + komentarz z linkiem do PR |
| Merge PR do main | Status → **Tested** + Cloud Build → deploy na Cloud Run |
| Zamknięcie PR bez merge | Status → **Rejected** + komentarz |

## Obsługa błędów z CI

- [ ] Testy failują → sprawdź OP Activity — komentarz **"Automated Bug created"**
- [ ] Bug WP zawiera link do CI run z logami błędów
- [ ] Napraw kod na tym samym branchu
- [ ] `git push` → testy uruchomią się ponownie
- [ ] Gdy testy przejdą — kontynuuj z PR

## Po merge

- [ ] Status w OP zmienia się automatycznie na **Tested**
- [ ] Cloud Build buduje Docker image i deployuje na Cloud Run
- [ ] Sprawdź w GitHub Actions czy deploy się powiódł
- [ ] PM zweryfikuje na środowisku i zmieni status na Closed

## Standardy zespołowe

Każdy developer w zespole powinien:

1. Mieć `CLAUDE.md` w repozytorium (commitowany, wspólny dla wszystkich)
2. Używać `.vscode/settings.json` z repo (ruff, format on save)
3. Nigdy nie zmieniać statusów OP ręcznie — automatyzacja to robi
4. Nigdy nie commitować bezpośrednio do main
5. Zawsze używać wzorca `OP-{ID}` w nazwie brancha
