__OpenProject \+ GitHub \+ GCP__

Przewodnik konfiguracyjny — wersja MVP

Integracja BI Feature / BI Task • Claude Code Skills • Success Scenario

# __Cel i zakres MVP__

Ten przewodnik opisuje minimalną, działającą konfigurację trzech systemów tak, żeby zobaczyć realne benefity ich połączenia w ciągu jednego dnia roboczego\. Nie instalujemy nic nowego — konfigurujemy to, co już posiadacie\.

__ℹ INFO  __OpenProject Cloud → GitHub → GitHub Actions → GCP Cloud Run\. Nadzorcą jest OpenProject: to tam ludzie patrzą, modyfikują i zarządzają strukturą projektową\.

__Trzy główne benefity po skonfigurowaniu:__

- Automatyczna zmiana statusu BI Feature/Task w OpenProject gdy developer robi commita lub otwiera PR — bez ręcznego klikania \(działa przez REST API, dostępne na każdym planie\)
- Automatyczne tworzenie zadań Bug w OpenProject gdy testy CI failują — z linkiem do runu GitHub Actions i przypisaniem do rodzica BI Feature
- Claude Code / VS Code Copilot 'wie' o kontekście projektu — plik CLAUDE\.md łączy nomenklaturę OP z kodem, konwencjami branchów i stackiem technicznym

# __1\. Konfiguracja OpenProject__

__⚠ UWAGA  __WAŻNE: Natywna zakładka GitHub na kartach work package \(widok PR\-ów i CI wewnątrz OP\) wymaga planu Enterprise\. Automatyczne zmiany statusów i tworzenie bugów przez GitHub Actions działają przez REST API — na KAŻDYM planie, w tym Community i Basic Cloud\. Ten przewodnik opisuje podejście API\-first, które nie wymaga Enterprise\.

## __1\.1  Użytkownik techniczny \(GitHub Bot\)__

GitHub Actions komunikuje się z OpenProject wyłącznie przez REST API v3\. Potrzebny jest dedykowany użytkownik techniczny z tokenem API — nie używaj konta osobistego\.

1. Administration → Users and permissions → Users → \+ User
2. Utwórz użytkownika: Login: github\-bot, Email: github\-bot@twoja\-firma\.com
3. Dodaj go do każdego projektu z rolą zawierającą uprawnienia: 'View work packages' i 'Edit work packages'
4. Zaloguj się jako github\-bot → kliknij awatar → My account → Access tokens → \+ API access token
5. Skopiuj wygenerowany token — zapisz go jako GitHub Secret: OPENPROJECT\_API\_TOKEN
6. W GitHub Actions używaj formatu: Authorization: Basic base64\(apikey:TOKEN\)

__⚠ UWAGA  __Nie używaj tokena konta admina w GitHub Actions — tworzy zależność od konkretnej osoby i daje zbyt szerokie uprawnienia\.

## __1\.2  Sprawdzenie ID statusów i typów w swojej instancji__

ID statusów, typów i priorytetów są różne w każdej instancji OpenProject\. Przed skonfigurowaniem GitHub Actions musisz sprawdzić swoje wartości przez API:

\# Pobierz listę statusów \(zapisz id dla: New, In Progress, In Review, Resolved, Rejected\)

curl \-s \-H "Authorization: Basic $\(echo \-n 'apikey:TWOJ\_TOKEN' | base64 \-w 0\)" \\

  https://TWOJA\-INSTANCJA\.openproject\.com/api/v3/statuses | jq '\.\.\_embedded\.elements\[\] | \{id, name\}'

\# Pobierz typy work packages \(potrzebne ID dla: Bug, Task, Feature\)

curl \-s \-H "Authorization: Basic $\(echo \-n 'apikey:TWOJ\_TOKEN' | base64 \-w 0\)" \\

  https://TWOJA\-INSTANCJA\.openproject\.com/api/v3/types | jq '\.\.\_embedded\.elements\[\] | \{id, name\}'

\# Pobierz priorytety

curl \-s \-H "Authorization: Basic $\(echo \-n 'apikey:TWOJ\_TOKEN' | base64 \-w 0\)" \\

  https://TWOJA\-INSTANCJA\.openproject\.com/api/v3/priorities | jq '\.\.\_embedded\.elements\[\] | \{id, name\}'

__ℹ INFO  __Wyniki tych zapytań wpisz do tabeli poniżej i zachowaj — będą potrzebne przy konfiguracji plików GitHub Actions w rozdziale 2\.

__Nazwa__

__Twoje ID__

__Użycie w Actions__

Status: New

1

status przy tworzeniu Buga przez CI

Status: In Progress

7

status po pierwszym push na branch

Status: In Testing \(In Review\)

9

status po otwarciu PR

Status: Tested \(Resolved\)

10

status po merge PR do main

Status: Rejected

14

status po zamknięciu PR bez merge

Typ: Bug

7

typ WP tworzonych automatycznie z CI

Priorytet: High

9

priorytet Bugów z failujących testów

## __1\.3  Konwencja ID w BI Feature i BI Task__

OpenProject automatycznie nadaje ID każdemu work package \(WP\)\. Te ID są jedynym kluczem integracji z GitHub — GitHub Actions wyciąga je z nazwy brancha\.

__Element OP__

__Przykładowe ID__

__Użycie w GitHub__

BI Feature

OP \#42

Branch: feature/OP\-42\-user\-login

BI Task

OP \#87

Branch: task/OP\-87\-oauth\-implementation

Child BI Feature

OP \#95

Branch: feature/OP\-95\-google\-sso

Bug \(z CI\)

OP \#103

Branch: fix/OP\-103\-token\-expiry

Wystarczy że nazwa brancha zawiera 'OP\-42' — GitHub Actions automatycznie wykrywa ID i wywołuje API OpenProject\.

## __1\.4  Statusy work packages — mapa dla automatyzacji__

Upewnij się że te statusy istnieją w Administration → Work packages → Statuses\. Możesz je dodać jeśli nie ma:

__Status__

__Kiedy ustawiany__

__Przez kogo__

New

Tworzenie zadania / Bug z CI

Ręcznie lub GitHub Actions

In Progress

Pierwszy commit z OP\-ID w nazwie brancha

GitHub Actions \(auto\) — przez API

In Review

Otwarcie Pull Request

GitHub Actions \(auto\) — przez API

Resolved

Merge PR do main

GitHub Actions \(auto\) — przez API

Rejected

Zamknięcie PR bez merge

GitHub Actions \(auto\) — przez API

Closed

Weryfikacja biznesowa na środowisku

Ręcznie przez PO — jedyna ręczna zmiana

__✓ SUKCES  __Statusy In Progress, In Review, Resolved, Rejected są zmieniane przez GitHub Actions przez REST API — działają na każdym planie OpenProject, bez Enterprise\.

## __1\.5  Opcjonalne: Custom Fields dla BI Feature__

Możesz dodać pola tekstowe do BI Feature przez Administration → Custom Fields → Work Packages → New custom field:

- GitHub Repository URL — typ: Text — do ręcznego wpisania linku do repo
- GitHub Branch — typ: Text — informacyjne, przydatne gdy jeden projekt ma wiele repo

__ℹ INFO  __To czysto opcjonalne — nie jest wymagane do działania automatyzacji\. Przydatne jako dokumentacja na karcie zadania\.

# __2\. Konfiguracja GitHub__

## __2\.1  Webhook GitHub → OpenProject \(opcjonalne, wymaga Enterprise dla pełnego efektu\)__

Webhook pozwala OpenProject odbierać zdarzenia z GitHub i wyświetlać je na karcie WP \(zakładka GitHub\)\. Ta zakładka jest jednak funkcją Enterprise\. Bez Enterprise webhook nadal można skonfigurować — OpenProject go odbierze i zaloguje w Activity, ale zakładka GitHub na karcie WP nie pojawi się na planach niższych niż Enterprise\.

__ℹ INFO  __Mechanizm zmiany statusów opisany w sekcji 2\.5 \(GitHub Actions\) działa przez REST API i NIE wymaga webhooka ani Enterprise\. Webhook to dodatkowa warstwa widoczności — nie warunek konieczny\.

Jeśli chcesz skonfigurować webhook \(np\. testujesz Enterprise trial lub planujesz upgrade\):

1. Repozytorium GitHub → Settings → Webhooks → Add webhook
2. Payload URL: https://TWOJA\-INSTANCJA\.openproject\.com/webhooks/github?key=TOKEN\_Z\_PKT\_1\.1
3. Content type: application/json
4. Events: zaznacz 'Send me everything'
5. Save — w Recent Deliveries sprawdź czy pojawia się 200 OK na ping

__⚠ UWAGA  __Jeśli widzisz 404 na /webhooks/github — instancja nie ma włączonego modułu GitHub Integration \(Enterprise\)\. Jeśli widzisz 200 — masz Enterprise i webhook działa\.

## __2\.2  Branch naming convention — fundament integracji__

Cała automatyzacja opiera się na tej jednej konwencji nazewnictwa branchy:

feature/OP\-\{ID\}\-krotka\-nazwa        \# dla BI Feature

task/OP\-\{ID\}\-krotka\-nazwa           \# dla BI Task

fix/OP\-\{ID\}\-krotka\-nazwa            \# dla bugów z testów

\# Przykłady:

feature/OP\-42\-user\-authentication

task/OP\-87\-implement\-oauth2

fix/OP\-103\-token\-expiry\-bug

Konwencja musi być w README\.md projektu oraz w pliku \.claude\_instructions \(sekcja 4 tego przewodnika\)\.

## __2\.3  Branch Protection dla main__

1. Settings → Branches → Add branch protection rule → Branch name pattern: main
2. Zaznacz: Require a pull request before merging
3. Zaznacz: Require status checks to pass \(dodaj 'tests' po skonfigurowaniu Actions\)
4. Zaznacz: Require branches to be up to date before merging
5. Opcjonalnie: Require 1 approving review

__ℹ INFO  __Branch protection chroni main przed bezpośrednimi pushami\. Developer musi zawsze tworzyć branch i PR — co uruchamia automatyzację OP\.

## __2\.4  GitHub Secrets — dane do połączeń__

Settings → Secrets and variables → Actions → New repository secret:

__Nazwa Secretu__

__Wartość__

__Używany przez__

OPENPROJECT\_URL

https://twoja\-instancja\.openproject\.com

op\-status\-update\.yml, tests\.yml

OPENPROJECT\_API\_TOKEN

apikey:xxxxx\.\.\.

op\-status\-update\.yml, tests\.yml

OPENPROJECT\_PROJECT\_ID

1

tests\.yml \(tworzenie Bugów\)

GCP\_PROJECT\_ID

twoj\-projekt\-id

deploy\.yml \(gcloud builds submit\)

GCP\_REGION

us\-central1

deploy\.yml

GCP\_WIF\_PROVIDER

projects/\.\.\./providers/github\-provider

deploy\.yml \(auth bez klucza JSON\)

GCP\_SERVICE\_ACCOUNT

github\-actions@\.\.\.iam\.gserviceaccount\.com

deploy\.yml \(auth WIF\)

__✓ SUKCES  __Nie potrzebujesz już secretów do Artifact Registry ani Cloud Run — GitHub Actions tylko wywołuje Cloud Build, który sam ma uprawnienia do push i deploy wewnątrz GCP\.

## __2\.5  GitHub Actions — trzy kluczowe workflow__

Utwórz katalog \.github/workflows/ w repozytorium i dodaj trzy pliki:

### __Plik 1: op\-status\-update\.yml — automatyczne statusy w OpenProject__

name: Update OpenProject Status

on:

  push:

    branches: \['feature/OP\-\*', 'task/OP\-\*', 'fix/OP\-\*'\]

  pull\_request:

    types: \[opened, closed, reopened\]

jobs:

  update\-status:

    runs\-on: ubuntu\-latest

    steps:

      \- name: Extract OP Work Package ID

        id: extract

        run: |

          BRANCH=$\{GITHUB\_HEAD\_REF:\-$\{GITHUB\_REF\#refs/heads/\}\}

          WP\_ID=$\(echo "$BRANCH" | grep \-oP 'OP\-\\K\[0\-9\]\+' | head \-1\)

          echo "wp\_id=$\{WP\_ID\}" >> $GITHUB\_OUTPUT

      \- name: Set status based on event

        id: status

        run: |

          if \[ "$\{\{ github\.event\_name \}\}" = "push" \]; then

            echo "status\_id=7" >> $GITHUB\_OUTPUT   \# In Progress

          elif \[ "$\{\{ github\.event\.action \}\}" = "opened" \]; then

            echo "status\_id=9" >> $GITHUB\_OUTPUT   \# In Testing (In Review)

          elif \[ "$\{\{ github\.event\.pull\_request\.merged \}\}" = "true" \]; then

            echo "status\_id=10" >> $GITHUB\_OUTPUT  \# Tested (Resolved)

          elif \[ "$\{\{ github\.event\.action \}\}" = "closed" \]; then

            echo "status\_id=14" >> $GITHUB\_OUTPUT   \# Rejected

          fi

      \- name: Get lockVersion from OpenProject

        id: get\_wp

        if: steps\.extract\.outputs\.wp\_id \!= ''

        run: |

          AUTH=$\(echo \-n "apikey:$\{\{ secrets\.OPENPROJECT\_API\_TOKEN \}\}" | base64 \-w 0\)

          RESPONSE=$\(curl \-sf \\

            "$\{\{ secrets\.OPENPROJECT\_URL \}\}/api/v3/work\_packages/$\{\{ steps\.extract\.outputs\.wp\_id \}\}" \\

            \-H "Authorization: Basic $\{AUTH\}"\)

          echo "lock\_version=$\(echo $RESPONSE | jq \-r '\.lockVersion'\)" >> $GITHUB\_OUTPUT

      \- name: Update OpenProject status

        if: steps\.extract\.outputs\.wp\_id \!= '' && steps\.status\.outputs\.status\_id \!= ''

        run: |

          AUTH=$\(echo \-n "apikey:$\{\{ secrets\.OPENPROJECT\_API\_TOKEN \}\}" | base64 \-w 0\)

          curl \-sf \-X PATCH \\

            "$\{\{ secrets\.OPENPROJECT\_URL \}\}/api/v3/work\_packages/$\{\{ steps\.extract\.outputs\.wp\_id \}\}" \\

            \-H "Content\-Type: application/json" \\

            \-H "Authorization: Basic $\{AUTH\}" \\

            \-d '\{

              "lockVersion": $\{\{ steps\.get\_wp\.outputs\.lock\_version \}\},

              "\_links": \{

                "status": \{

                  "href": "/api/v3/statuses/$\{\{ steps\.status\.outputs\.status\_id \}\}"

                \}

              \}

            \}'

### __Plik 2: tests\.yml — testy \+ raportowanie błędów do OpenProject__

name: Tests

on: \[push, pull\_request\]

jobs:

  test:

    runs\-on: ubuntu\-latest

    steps:

      \- uses: actions/checkout@v4

      \- uses: actions/setup\-python@v5

        with: \{ python\-version: '3\.12' \}

      \- run: pip install \-r requirements\.txt

      \- name: Run pytest

        id: pytest

        run: pytest \-\-tb=short \-\-json\-report \-\-json\-report\-file=test\_report\.json || true

      \- name: Create Bug in OpenProject on test failure

        if: failure\(\)

        run: |

          BRANCH=$\{GITHUB\_HEAD\_REF:\-$\{GITHUB\_REF\#refs/heads/\}\}

          WP\_ID=$\(echo "$BRANCH" | grep \-oP 'OP\-\\K\[0\-9\]\+' | head \-1\)

          FAILURES=$\(cat test\_report\.json | jq \-r '\.summary\.failed // 0'\)

          AUTH=$\(echo \-n "apikey:$\{\{ secrets\.OPENPROJECT\_API\_TOKEN \}\}" | base64 \-w 0\)

          curl \-sf \-X POST \\

            "$\{\{ secrets\.OPENPROJECT\_URL \}\}/api/v3/projects/$\{\{ secrets\.OPENPROJECT\_PROJECT\_ID \}\}/work\_packages" \\

            \-H "Content\-Type: application/json" \\

            \-H "Authorization: Basic $\{AUTH\}" \\

            \-d "\{

              \\"subject\\": \\"\[BUG\] Test failure in $\{BRANCH\} — $\{FAILURES\} tests failed\\",

              \\"description\\": \{\\"format\\": \\"markdown\\", \\"raw\\": \\"\#\# Automatyczny Bug z GitHub Actions\\\\n\\\\n\*\*Branch:\*\* $\{BRANCH\}\\\\n\*\*PR:\*\* $\{\{ github\.event\.pull\_request\.html\_url \}\}\\\\n\*\*Run:\*\* $\{\{ github\.server\_url \}\}/$\{\{ github\.repository \}\}/actions/runs/$\{\{ github\.run\_id \}\}\\\\n\\\\nSzczegóły w powyższym linku\.\\"\},

              \\"\_links\\": \{

                \\"type\\": \{\\"href\\": \\"/api/v3/types/7\\"\},

                \\"status\\": \{\\"href\\": \\"/api/v3/statuses/1\\"\},

                \\"priority\\": \{\\"href\\": \\"/api/v3/priorities/9\\"\},

                \\"parent\\": \{\\"href\\": \\"/api/v3/work\_packages/$\{WP\_ID\}\\"\}

              \}

            \}"

### __Plik 3: deploy\.yml — trigger Cloud Build po merge do main__

GitHub Actions NIE buduje obrazu — tylko uwierzytelnia się do GCP i wywołuje Cloud Build\. Cały build, push i deploy dzieje się w GCP wewnętrznie\.

name: Trigger Cloud Build

on:

  push:

    branches: \[main\]

permissions:

  contents: read

  id\-token: write   \# Wymagane dla Workload Identity Federation

jobs:

  trigger\-build:

    runs\-on: ubuntu\-latest

    steps:

      \- uses: actions/checkout@v4

      \- id: auth

        uses: google\-github\-actions/auth@v2

        with:

          workload\_identity\_provider: $\{\{ secrets\.GCP\_WIF\_PROVIDER \}\}

          service\_account: $\{\{ secrets\.GCP\_SERVICE\_ACCOUNT \}\}

      \- uses: google\-github\-actions/setup\-gcloud@v2

      \- name: Submit build to Cloud Build

        run: |

          gcloud builds submit \\

            \-\-config=cloudbuild\.yaml \\

            \-\-substitutions=SHORT\_SHA=$\{\{ github\.sha \}\},\_REGION=$\{\{ secrets\.GCP\_REGION \}\} \\

            \-\-project=$\{\{ secrets\.GCP\_PROJECT\_ID \}\}

### __Plik cloudbuild\.yaml — build, push i deploy w GCP \(w repo obok Dockerfile\)__

Ten plik trafia do korzenia repozytorium\. Cloud Build wykonuje wszystkie kroki wewnątrz GCP — bez transferu przez internet\.

substitutions:

  \_REGION: us\-central1

  \_SERVICE: my\-service

  \_REPO: app

steps:

  \# Krok 1: Pobierz poprzedni obraz jako cache warstw

  \- name: gcr\.io/cloud\-builders/docker

    entrypoint: bash

    args:

      \- \-c

      \- |

        docker pull $\{\_REGION\}\-docker\.pkg\.dev/$PROJECT\_ID/$\{\_REPO\}/$\{\_SERVICE\}:latest || true

  \# Krok 2: Zbuduj obraz z cache \(szybszy przy niezmienionej bazie\)

  \- name: gcr\.io/cloud\-builders/docker

    args:

      \- build

      \- \-\-cache\-from

      \- $\{\_REGION\}\-docker\.pkg\.dev/$PROJECT\_ID/$\{\_REPO\}/$\{\_SERVICE\}:latest

      \- \-t

      \- $\{\_REGION\}\-docker\.pkg\.dev/$PROJECT\_ID/$\{\_REPO\}/$\{\_SERVICE\}:$SHORT\_SHA

      \- \-t

      \- $\{\_REGION\}\-docker\.pkg\.dev/$PROJECT\_ID/$\{\_REPO\}/$\{\_SERVICE\}:latest

      \- \.

  \# Krok 3: Push do Artifact Registry \(sieć wewnętrzna GCP — szybki\)

  \- name: gcr\.io/cloud\-builders/docker

    args: \[push, \-\-all\-tags,

           $\{\_REGION\}\-docker\.pkg\.dev/$PROJECT\_ID/$\{\_REPO\}/$\{\_SERVICE\}\]

  \# Krok 4: Deploy na Cloud Run

  \- name: gcr\.io/google\.com/cloudsdktool/cloud\-sdk

    entrypoint: gcloud

    args:

      \- run

      \- deploy

      \- $\{\_SERVICE\}

      \- \-\-image=$\{\_REGION\}\-docker\.pkg\.dev/$PROJECT\_ID/$\{\_REPO\}/$\{\_SERVICE\}:$SHORT\_SHA

      \- \-\-region=$\{\_REGION\}

      \- \-\-platform=managed

      \- \-\-quiet

images:

  \- $\{\_REGION\}\-docker\.pkg\.dev/$PROJECT\_ID/$\{\_REPO\}/$\{\_SERVICE\}:$SHORT\_SHA

  \- $\{\_REGION\}\-docker\.pkg\.dev/$PROJECT\_ID/$\{\_REPO\}/$\{\_SERVICE\}:latest

options:

  machineType: E2\_HIGHCPU\_8   \# 8 vCPU — szybszy build ML dependencies

  logging: CLOUD\_LOGGING\_ONLY

# __3\. Konfiguracja GCP__

Architektura: GitHub Actions obsługuje testy i logikę CI, Cloud Build przejmuje build Docker \+ push do Artifact Registry \+ deploy na Cloud Run\. Build działa w sieci wewnętrznej GCP — szybszy, tańszy, bez transferu przez internet\.

__ℹ INFO  __Dla ML/AI projektów z dużymi obrazami Docker \(torch, transformers, etc\.\) Cloud Build jest wyraźnie lepszy niż budowanie w GitHub runners: brak egress cost, natywny cache warstw w Artifact Registry, możliwość użycia maszyn high\-CPU\.

## __3\.1  Wymagane usługi do aktywacji__

gcloud services enable \\

  run\.googleapis\.com \\

  cloudbuild\.googleapis\.com \\

  artifactregistry\.googleapis\.com \\

  iamcredentials\.googleapis\.com

## __3\.2  Artifact Registry — repozytorium obrazów Docker__

gcloud artifacts repositories create app \\

  \-\-repository\-format=docker \\

  \-\-location=$\{REGION\} \\

  \-\-description='Application Docker images'

## __3\.3  Service Account dla GitHub Actions \(tylko trigger\)__

GitHub Actions potrzebuje tylko jednego uprawnienia: uruchomienie Cloud Buildu\. Sama budowa i push dzieje się po stronie GCP na koncie Cloud Build SA — nie na tym samym SA co GitHub\.

\# SA dla GitHub Actions — minimalny zakres

gcloud iam service\-accounts create github\-actions \\

  \-\-display\-name='GitHub Actions — Cloud Build trigger only'

SA="github\-actions@$\{PROJECT\_ID\}\.iam\.gserviceaccount\.com"

\# Tylko jedno uprawnienie — uruchomienie buildu

gcloud projects add\-iam\-policy\-binding $\{PROJECT\_ID\} \\

  \-\-member="serviceAccount:$\{SA\}" \\

  \-\-role="roles/cloudbuild\.builds\.editor"

\# Cloud Build SA \(domyślny\) potrzebuje uprawnień do Artifact Registry i Cloud Run

CB\_SA="$\(gcloud projects describe $\{PROJECT\_ID\} \-\-format='value\(projectNumber\)'\)@cloudbuild\.gserviceaccount\.com"

gcloud projects add\-iam\-policy\-binding $\{PROJECT\_ID\} \\

  \-\-member="serviceAccount:$\{CB\_SA\}" \\

  \-\-role="roles/artifactregistry\.writer"

gcloud projects add\-iam\-policy\-binding $\{PROJECT\_ID\} \\

  \-\-member="serviceAccount:$\{CB\_SA\}" \\

  \-\-role="roles/run\.developer"

gcloud projects add\-iam\-policy\-binding $\{PROJECT\_ID\} \\

  \-\-member="serviceAccount:$\{CB\_SA\}" \\

  \-\-role="roles/iam\.serviceAccountUser"

## __3\.4  Workload Identity Federation — bez kluczy JSON w GitHub__

WIF pozwala GitHub Actions uwierzytelniać się do GCP tokenem krótkoterminowym — bez przechowywania kluczy service account w Secrets\. Rekomendowane dla każdego projektu produkcyjnego\.

\# Utwórz Workload Identity Pool

gcloud iam workload\-identity\-pools create github\-pool \\

  \-\-location=global \\

  \-\-display\-name='GitHub Actions Pool'

\# Utwórz Provider OIDC

gcloud iam workload\-identity\-pools providers create\-oidc github\-provider \\

  \-\-location=global \\

  \-\-workload\-identity\-pool=github\-pool \\

  \-\-issuer\-uri=https://token\.actions\.githubusercontent\.com \\

  \-\-attribute\-mapping='google\.subject=assertion\.sub,attribute\.repository=assertion\.repository'

\# Pobierz POOL\_ID

POOL\_ID=$\(gcloud iam workload\-identity\-pools describe github\-pool \\

  \-\-location=global \-\-format='value\(name\)'\)

\# Powiąż Pool z Service Account — tylko dla Twojego repo

gcloud iam service\-accounts add\-iam\-policy\-binding $\{SA\} \\

  \-\-role=roles/iam\.workloadIdentityUser \\

  \-\-member="principalSet://iam\.googleapis\.com/$\{POOL\_ID\}/attribute\.repository/TWOJA\_ORG/TWOJE\_REPO"

\# Skopiuj poniższy URL do GitHub Secret GCP\_WIF\_PROVIDER:

gcloud iam workload\-identity\-pools providers describe github\-provider \\

  \-\-location=global \-\-workload\-identity\-pool=github\-pool \\

  \-\-format='value\(name\)'

## __3\.5  Porównanie: GitHub Actions build vs Cloud Build__

__Kryterium__

__GitHub Actions build__

__Cloud Build \(ten przewodnik\)__

Sieć push do Artifact Registry

Internet \(wolny, płatny egress\)

Wewnętrzna GCP \(szybki, bezpłatny\)

Cache warstw Docker

GitHub cache action \(ograniczony\)

Natywny cache w Artifact Registry

Duże obrazy ML \(3–8 GB\)

Długi upload, drogi

Szybki, bez egress cost

Dostęp do GCS/Cloud SQL w build

Wymaga dodatkowej auth

Natywny — ten sam projekt

Moc obliczeniowa

2 vCPU, 7 GB RAM \(free runner\)

Do 32 vCPU, 120 GB RAM \(E2\_HIGHCPU\)

Darmowe minuty

2 000 min/mies\.

120 min/dzień \(~3 600/mies\.\)

Koszt powyżej limitu

$0\.008/min

~$0\.003/min

Widoczność logów

GitHub Actions tab

GCP Console → Cloud Build

Przenośność

Niezależna od chmury

GCP\-specific

# __4\. Pliki Claude Code — kontekst AI powiązany z OP/GitHub__

Te pliki umieszczasz w głównym katalogu repozytorium\. Claude Code \(i GitHub Copilot\) automatycznie je czytają jako kontekst — AI 'wie' jak działa Wasz projekt, jakie są konwencje i jak się komunikować z OpenProject\.

## __4\.1  CLAUDE\.md — główny plik instrukcji dla Claude Code__

Plik CLAUDE\.md jest czytany przez Claude Code przy każdej sesji\. Zawiera reguły zachowania AI powiązane z waszym setupem\.

\# CLAUDE\.md — Instrukcje dla Claude Code

\#\# Kontekst projektu

\- Projekt zarządzany w OpenProject: https://twoja\-firma\.openproject\.com

\- Repozytorium: https://github\.com/twoja\-org/twoje\-repo

\- Stack: Python / FastAPI / Django / AI agenting

\- Cloud: GCP \(Cloud Run, Artifact Registry, Cloud Build\)

\- Build: Cloud Build \(NIE Docker w GitHub Actions — build dzieje się w GCP\)

\#\# Konwencje Git — KRYTYCZNE

Zawsze twórz branche według wzorca:

  feature/OP\-\{ID\}\-nazwa    \# dla BI Feature

  task/OP\-\{ID\}\-nazwa       \# dla BI Task

  fix/OP\-\{ID\}\-nazwa        \# dla bugów

Nigdy nie commituj bezpośrednio do main\.

\#\# Formaty commit message

  feat\(OP\-42\): opis zmiany

  fix\(OP\-103\): opis poprawki

  task\(OP\-87\): opis zadania technicznego

\#\# Opis Pull Request — szablon

Każdy PR musi zawierać w opisie:

  \#\# OP Work Package

  Closes OP \#42

  \#\# Co zrobiono

  \.\.\.

  \#\# Jak testować

  \.\.\.

\#\# Zasady kodu

\- Python: type hints wszędzie, docstrings dla publicznych funkcji

\- FastAPI: Pydantic models dla request/response, HTTPException z kodami

\- Testy: pytest, coverage > 80%, testy w tests/ z prefixem test\_

\- Przed commitem: ruff check \. && python \-m pytest

\#\# Pytania o zadania

Gdy użytkownik pyta 'nad czym pracujesz' lub podaje numer OP, zakładaj że

chodzi o BI Feature lub BI Task z OpenProject\. Pytaj o ID jeśli nie podano\.

## __4\.2  \.github/PULL\_REQUEST\_TEMPLATE\.md — szablon PR__

GitHub automatycznie wypełnia tym szablonem każdy nowy PR:

\#\# OpenProject Work Package

Closes OP \#<\!\-\- wstaw ID z OpenProject \-\->

\#\# Opis zmian

<\!\-\- Co zostało zrobione i dlaczego \-\->

\#\# Typ zmiany

\- \[ \] BI Feature

\- \[ \] BI Task \(techniczny\)

\- \[ \] Bug fix

\- \[ \] Refactor

\#\# Jak testować

1\. \.\.\.

2\. \.\.\.

\#\# Checklist

\- \[ \] Testy napisane i przechodzą

\- \[ \] Brak nowych warnings w ruff

\- \[ \] Dokumentacja zaktualizowana \(jeśli dotyczy\)

## __4\.3  \.github/CODEOWNERS — przypisanie reviewerów__

\# Domyślni reviewerzy dla całego repo

\* @twoja\-org/senior\-devs

\# AI\-agenting code wymaga review ML engineera

src/agents/ @twoja\-org/ml\-engineers

src/ml/ @twoja\-org/ml\-engineers

## __4\.4  \.vscode/settings\.json — VS Code z kontekstem projektu__

Konfiguracja VS Code wspólna dla całego zespołu — commitowana do repo:

\{

  "editor\.formatOnSave": true,

  "python\.defaultInterpreterPath": "\.venv/bin/python",

  "editor\.rulers": \[88\],

  "github\.copilot\.editor\.enableAutoCompletions": true,

  "github\.copilot\.chat\.welcomeMessage": "never",

  "files\.associations": \{

    "CLAUDE\.md": "markdown",

    "\*\.openproject": "json"

  \},

  "\[python\]": \{

    "editor\.defaultFormatter": "charliermarsh\.ruff",

    "editor\.codeActionsOnSave": \{"source\.fixAll\.ruff": "always"\}

  \}

\}

# __5\. Success Scenario — pełny przebieg__

Poniżej pełny scenariusz pokazujący jak trzy systemy współpracują na realnym przykładzie\. Aktorzy: Ania \(Product Owner\), Marcin \(Developer\)\.

## __Krok 1 — Ania tworzy BI Feature w OpenProject__

1. Ania wchodzi do OpenProject, tworzy BI Feature: 'Logowanie przez Google OAuth2'
2. System nadaje ID: OP \#42\. Status: New
3. Ania wypełnia opis, acceptance criteria, priority: High
4. Przypisuje BI Feature do Marcina

__ℹ INFO  __OpenProject jest nadzorcą — Ania tu zarządza strukturą, może dodawać child BI Features, modyfikować opisy, nie dotykając GitHub ani kodu\.

## __Krok 2 — Marcin zaczyna pracę \(status zmienia się automatycznie\)__

1. Marcin widzi zadanie w OpenProject, notuje ID: OP\-42
2. Tworzy branch: git checkout \-b feature/OP\-42\-google\-oauth
3. Pisze pierwszy commit: feat\(OP\-42\): add OAuth2 base configuration
4. Push do GitHub: git push origin feature/OP\-42\-google\-oauth

__✓ SUKCES  __W tym momencie GitHub Actions \(op\-status\-update\.yml\) wykrywa push na branch z 'OP\-42', wywołuje OpenProject API i zmienia status BI Feature \#42 na 'In Progress' — Ania widzi zmianę bez żadnego działania Marcina\.

## __Krok 3 — Claude Code pomaga Marcinowi__

1. Marcin otwiera VS Code, uruchamia Claude Code
2. Pyta: 'pracuję nad OP\-42, zaimplementuj OAuth2 login przez Google do FastAPI'
3. Claude Code czyta CLAUDE\.md — wie o stacku \(FastAPI\), konwencjach branchów, strukturze projektu
4. Claude generuje kod z właściwymi type hints, Pydantic models, HTTPException patterns
5. Kod jest zgodny z konwencjami — nie trzeba poprawiać formatowania

__ℹ INFO  __Bez CLAUDE\.md Claude generowałby kod z losowymi konwencjami\. Z CLAUDE\.md odpowiedzi są dostosowane do waszego stacku, nazewnictwa i zasad commitów\.

## __Krok 4 — Testy failują, automatyczny Bug w OpenProject__

1. Marcin pusuje kod, GitHub Actions uruchamia pytest
2. Dwa testy failują — token refresh i session timeout
3. GitHub Actions \(tests\.yml\) tworzy automatycznie dwa work packages w OpenProject:

- \[BUG\] Test failure: token\_refresh\_test — z linkiem do run Actions
- \[BUG\] Test failure: session\_timeout\_test — parent: OP \#42

1. Ania widzi bugi jako child zadania pod BI Feature \#42, może je opisać dokładniej

__ℹ INFO  __Bugi tworzone przez CI są 'surowymi' sygnałami — Ania lub Marcin mogą je wzbogacić o kontekst biznesowy i przerobić na doprecyzowania \(child BI Feature\), co opisałeś w swoim procesie\.

## __Krok 5 — PR otwarto, status 'In Review'__

1. Marcin naprawia bugi, testy przechodzą
2. Otwiera Pull Request — szablon automatycznie się wypełnia \(\.github/PULL\_REQUEST\_TEMPLATE\.md\)
3. Wpisuje w opisie: 'Closes OP \#42'
4. GitHub Actions \(op\-status\-update\.yml\) wykrywa otwarcie PR, wywołuje API — status BI Feature \#42 → 'In Review'
5. W OpenProject na karcie BI Feature \#42 w sekcji Activity pojawia się wpis o zmianie statusu z linkiem do PR

__ℹ INFO  __Na planie Enterprise: na karcie WP pojawia się dodatkowo zakładka GitHub z wizualnym widokiem PR i statusu CI\. Na planach Basic/Community: zmiana statusu w Activity jest widoczna, ale bez dedykowanej zakładki GitHub\.

## __Krok 6 — Merge i deploy__

1. Senior dev robi code review, zatwierdza PR
2. PR zostaje zmergowany do main
3. GitHub Actions: status BI Feature \#42 → 'Resolved'
4. GitHub Actions \(deploy\.yml\): buduje Docker image, pushuje do Artifact Registry, deployuje na Cloud Run
5. Ania weryfikuje na środowisku testowym, zmienia status na 'Closed' — to jedyna ręczna zmiana w całym flow

__✓ SUKCES  __Podsumowanie: jedynym ręcznym działaniem Ani było stworzenie BI Feature i finalne zamknięcie\. Wszystkie zmiany statusów 'w trakcie' były automatyczne\.

# __6\. Weryfikacja — jak sprawdzić czy integracja działa__

## __Testy integracji po konfiguracji__

__Test__

__Oczekiwany efekt__

__Gdzie sprawdzić__

Push do feature/OP\-42\-test

Status WP \#42 → In Progress

OpenProject → WP \#42 → Activity

Open PR z 'Closes OP \#42'

Status WP \#42 → In Review

OpenProject → WP \#42 → Activity

Failujący pytest na branchu

Nowy Bug WP w OpenProject

OpenProject → projekt → lista WP

Merge PR do main

Status → Resolved \+ deploy na GCP

OP Activity \+ GCP Cloud Run console

Webhook test \(tylko Enterprise\)

200 OK w Recent Deliveries \+ Activity

GitHub → Settings → Webhooks

## __Pierwsze 3 kroki — minimalna weryfikacja \(30 min\)__

1. Utwórz test WP \#1 w OpenProject, pobierz jego ID z URL \(np\. /work\_packages/1\)
2. Wywołaj ręcznie API żeby zmienić status — sprawdź czy działa token: curl z pkt 1\.2 i PATCH na /api/v3/work\_packages/1
3. Stwórz branch 'feature/OP\-1\-test', zrób push — sprawdź w OpenProject → WP \#1 → Activity czy pojawia się zmiana statusu na In Progress

__✓ SUKCES  __Jeśli krok 2 \(ręczne API\) działa, a krok 3 \(automatyczny z Actions\) nie — problem leży w konfiguracji GitHub Secrets lub pliku op\-status\-update\.yml, nie w OpenProject\.

# __Appendix A — Co działa na jakim planie OpenProject__

__Funkcja__

__Community \(self\-hosted\)__

__Basic Cloud__

__Enterprise__

Zmiana statusu WP przez GitHub Actions \(REST API\)

✅ TAK

✅ TAK

✅ TAK

Tworzenie Bugów z CI przez GitHub Actions \(REST API\)

✅ TAK

✅ TAK

✅ TAK

Odczyt/zapis work packages przez API

✅ TAK

✅ TAK

✅ TAK

Zakładka GitHub na karcie WP \(widok PR \+ CI\)

❌ NIE

❌ NIE

✅ TAK

Git snippets \(tworzenie brancha z WP\)

❌ NIE

❌ NIE

✅ TAK

Webhook /webhooks/github \(odbiór zdarzeń GitHub\)

❌ NIE

❌ NIE

✅ TAK

Custom fields

✅ TAK

✅ TAK

✅ TAK

Outgoing Webhooks \(OP → zewnętrzny system\)

❌ NIE

❌ NIE

✅ TAK

__✓ SUKCES  __Wszystko co opisuje ten przewodnik \(GitHub Actions → REST API → zmiana statusów i bugi\) leży w pierwszych trzech wierszach — dostępne na każdym planie\.

# __Appendix B — ID statusów OpenProject API__

ID statusów w OpenProject API są różne w każdej instancji\. Sprawdź swoje i wypełnij tabelę w pkt 1\.2:

\# Statusy — z autoryzacją Base64\(apikey:TOKEN\)

curl \-s \-H "Authorization: Basic $\(echo \-n 'apikey:TWOJ\_TOKEN' | base64 \-w 0\)" \\

  https://TWOJA\-INSTANCJA\.openproject\.com/api/v3/statuses \\

  | python3 \-m json\.tool | grep \-E '"id"|"name"'

Podobnie dla typów i priorytetów:

curl \-s \-H "Authorization: Basic $\(echo \-n 'apikey:TOKEN' | base64 \-w 0\)" \\

  https://TWOJA\-INSTANCJA\.openproject\.com/api/v3/types \\

  | python3 \-m json\.tool | grep \-E '"id"|"name"'

curl \-s \-H "Authorization: Basic $\(echo \-n 'apikey:TOKEN' | base64 \-w 0\)" \\

  https://TWOJA\-INSTANCJA\.openproject\.com/api/v3/priorities \\

  | python3 \-m json\.tool | grep \-E '"id"|"name"'

Pobrane ID wpisz w pliku op\-status\-update\.yml w miejscach: echo "status\_id=\.\.\.", a w tests\.yml przy tworzeniu Buga w polach type i priority\.

