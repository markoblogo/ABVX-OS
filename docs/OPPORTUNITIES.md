# ABVX OS — единый каталог возможностей

Основной вход для будущего ABVX Hub: `./bin/abvx opportunities catalog`.
Каталог принадлежит ABVX OS; Nantes Radar остаётся источником контекста в ChatGPT.
Поиск работы не смешивается с Multi-Market Radar (Amazon/Etsy/Udemy/Kickstarter).

- Постоянное приватное состояние: `opportunities/private/state.json` (исключено из Git).
- Код: `src/abvx_harness/nantes_radar.py`; контракт: `schemas/nantes_radar.schema.json`.
- Исходный чат: [Nantes Radar — фокус дня](chatgpt-conversation://6ad477c6-9780-83eb-bfae-621e86a5490d).
- История, очередь переноса, вакансии, профили, черновики и решения находятся в одном состоянии. `career` — алиас того же входа.

## Обычная работа

```sh
./bin/abvx opportunities catalog
./bin/abvx opportunities plan --profile anton-marketing
./bin/abvx opportunities search --query marketing --limit 20
./bin/abvx opportunities rank --profile anton-marketing
./bin/abvx opportunities report --profile anton-marketing
```

`search` делает только бесплатный GET Remotive, без профиля кандидата и личных данных в запросе. Общий кэш на шесть часов, максимум 10 MB, таймаут 25 секунд; редиректы отклоняются. Источник и исходные Remotive URLs сохраняются. API запаздывает относительно площадки; наличие вакансии и условия надо проверять перед откликом.

Для France Travail, Apec, Welcome to the Jungle используется существующий browser/manual acquisition подход ABVX OS: `plan` выдаёт запросы и источники, агент читает страницы и импортирует подтверждённые данные. Новый скрейпер, платная подписка или авторизация не устанавливаются. Результат поиска/сниппет не заменяет полный текст вакансии.

```sh
./bin/abvx opportunities import --file /absolute/path/postings.json
./bin/abvx opportunities draft --job JOB_ID --profile anton-marketing --language en
./bin/abvx opportunities packet --id DRAFT_ID
# Только после просмотра всего текста, источников и flags человеком:
./bin/abvx opportunities review --id DRAFT_ID --decision APPROVED --reviewer owner --digest EXACT_DISPLAYED_SHA256
```

CV и письмо — редактируемые Markdown-тексты внутри пакета JSON, выводятся командой `packet`. Они выбирают подтверждённые факты исходного CV; неподтверждённые факты не включаются. Это начальный фактический черновик, не готовый персональный рассказ о компании. PDF/DOCX, семантическая оценка, перевод CV и ATS QA в v1 не добавлены. Для FR нужны подтверждённые французские факты: английские сведения не переводятся молча.

Одобрение относится к точному SHA-256 пакета и снимку профиля/вакансии. Изменения требуют нового черновика и просмотра. Одобрение не отправляет документ и не означает отклик. При ручном изменении текста в приватном состоянии проверка прежнего пакета блокируется; готовьте новый пакет, не исправляйте digest вручную.

```sh
# Только запись уже совершённого человеком действия с его основанием:
./bin/abvx opportunities track --job JOB_ID --profile anton-marketing --event submitted --date YYYY-MM-DD --packet APPROVED_DRAFT_ID --evidence 'owner report / local receipt reference'
./bin/abvx opportunities track --job JOB_ID --profile anton-marketing --event interview --date YYYY-MM-DD --evidence 'owner report reference'
```

Поддерживаются submitted, interview, rejected, offer, hired, withdrawn, no_response. Повтор идентичного события не дублируется. Это журнал свидетельств пользователя, не проверка доставки. Старые отклики без нового approved-пакета импортируются как история, без фиктивного прохождения современных gates.

## Импорт исторического Nantes Radar

История Epic Gift, Yellow Recruiting, Honeytech, Biomère, Nautile, Jacques Demy, Mercor и Contra перенесена 23 октября с источниками сообщений. Четыре вакансии, две платформы, один творческий конкурс и один инициативный трудовой контакт (`employment_prospect`). Для каждой записи отдельно сохранены application_status и owner_decision: UNKNOWN, если нет прямого подтверждения. Старые рекомендации ChatGPT не считаются отправленными откликами или решениями владельца.

`./bin/abvx opportunities reconcile-history --file /absolute/path/history.json --expected-digest CURRENT_OPPORTUNITIES_DIGEST` явно обогащает существующие записи, сохраняя прежнюю версию в истории и все источники; изменение каталога после просмотра блокирует операцию. Текущий digest выводит `catalog`. `observations` различает user, assistant, saved_automation и tool; утверждения без пользовательского/инструментального источника не устанавливают owner_decision/application_status.

`./bin/abvx opportunities import-history --file /absolute/path/history.json` принимает `$defs/history` из контракта. `kind`: vacancy, platform, creative_call, client_project, employment_prospect, UNKNOWN. Каждое событие содержит `opportunity_id`, `status`, `occurred_at` (null при неизвестной дате), `source_refs`, `notes`. Нужны исходные сообщения/экспорт, точные URL и решения. Сохраняйте исходные формулировки статусов; автоматической интерпретации статусов нет.

```json
{
  "schema_version": "v1",
  "opportunities": [{"id":"example-history","name":"Synthetic example","kind":"UNKNOWN","status":"UNKNOWN","source_refs":["chatgpt-conversation://SOURCE#message"],"notes":"Synthetic example only","url":null}],
  "events": [{"opportunity_id":"example-history","status":"UNKNOWN","occurred_at":null,"source_refs":["chatgpt-conversation://SOURCE#message"],"notes":"No date invented"}]
}
```

Повторный импорт идентичных записей идемпотентен; конфликт существующего ID блокируется для ручной сверки. Когда историческая запись соответствует импортированной вакансии, `./bin/abvx opportunities link --id OPPORTUNITY_ID --job JOB_ID --source "owner reconciliation reference"` сохраняет `linked_job_id` и запись истории; второй трекер не создаётся. Ручное решение по возможности добавляет историю:

```sh
./bin/abvx opportunities decide --id OPPORTUNITY_ID --status deferred --reason 'owner decision' --source 'chat/message reference'
```

## Оценка и границы

Ранжирование — объяснимая keyword-triage-v1: до 80 баллов за совпадения навыков, 20 за роль. Это не вероятность найма и не семантическая оценка опыта/культуры. Язык объявления не считается языковым требованием. Французский A2, рабочий английский без выдуманного CEFR, неизвестные права/контрактная допустимость, география и сроки показываются явно. US-only remote исключается, неизвестная география остаётся REVIEW. Отсутствие текста блокирует черновик. Истёкшие/закрытые вакансии исключаются из shortlist. Возможные дубли без общего URL или requisition ID показываются для сверки.

Сохранены три представления одного кандидата: anton-marketing, anton-product, anton-ai-evaluation. Они используют один исходный Mercor Profile DOCX и ссылки на точные абзацы; это версии позиционирования, не три разных человека. Зарплата, доступность, разрешение на работу, спорные дипломы/метрики не додумываются.

## Scheduler, Learning Loop и журналирование

23 октября три существовавших ChatGPT-обзора объединены: прежний ежедневный разбор Gmail переименован в **Nantes Radar — единый обзор**, ежедневно 10:00 Europe/Paris; по понедельникам недельная сверка включается в этот же отчёт. Отдельные «Nantes Radar — фокус дня» и «Понедельничное меню возможностей» приостановлены, не удалены. Другие расписания не затронуты. Статус контрольного запуска и квитанции синхронизации: `opportunities/private/reports/NANTES-SYNC.md`.

Единый рабочий чат: https://chatgpt.com/c/6ac8a06b-fae0-83ed-b55e-fd23524d85f9 . Локальный каталог ABVX OS остаётся каноническим. Существующая задача обзора использует уже подключённый Remote Desktop Commander для доступа к Mac. Новый daemon, scheduler, HTTP-сервер, подписка или API key не добавлены. `./bin/abvx opportunities context-pack` сохраняет ограниченный снимок без CV, контактов и текстов черновиков; `sync-read` добавляет одноразовый пакет и команды записи.

### Автоматическая сверка обзора и каталога

```sh
./bin/abvx opportunities sync-read
./bin/abvx opportunities sync-apply --file /absolute/path/returned-sync-inbox-RUN_ID.json
```

Обзор перед анализом читает актуальный каталог через подключённый Mac, затем передаёт JSON по отдельному пути для каждого запуска и применяет его через существующий CLI. После записи повторно читает каталог и сверяет digest. Пакет содержит `schema_version`, `run_id`, `expected_digest`, `updates`; каждая правка — существующий `opportunity_id`, разрешённые `changes` и `source` с видом, ID, URL, исходным фрагментом и точной цитатой. Шаблон, допустимые поля и значения возвращает `sync-read`.

Поддерживаются `status`, `application_status`, `owner_decision` исторических возможностей. Решения владельца устанавливаются только из прямого сообщения в едином чате; письмо может дать наблюдаемый статус, но не решение владельца. Рекомендации ассистента сохраняются отдельно в `review_sync.proposals` со статусом REVIEW. Новые возможности, расширенные onboarding-поля, профили, CV/письма, approved-пакеты и журнал фактических отправок этим адаптером не изменяются. Неизвестный ID требует обычного intake; связь с вакансией задаётся существующим `link`.

Повтор пакета не создаёт дубль; повтор содержимого с новым run_id также отсеивается. Конфликт digest блокирует пакет целиком, задача может один раз перечитать каталог. `UNKNOWN` не затирает известное значение. История хранит прежнюю запись, источник и цитату; квитанция — run_id, digest до/после, applied/queued/skipped. Счётчики относятся к обновлениям, не к письмам или отправленным заявкам. Пустая сверка с нулём изменений допустима.

Контрольный запуск 23.10.2026 прочитал каталог и записал пустую квитанцию с повторной проверкой digest. Первый запуск потребовал разового подтверждения. Затем по прямому разрешению владельца включён full_access только для Remote Desktop Commander; повторный запуск существующей задачи записал квитанцию без ручного подтверждения. Следующий регулярный запуск в 10:00 ещё не наблюдался. Доказательства: `opportunities/private/reports/NANTES-background-sync.md`. Gmail в первом запуске вернул FORBIDDEN, а в повторном чтение прошло успешно без изменения его разрешений. Источник временной ошибки не установлен.

Для работы нужны включённый Mac, доступный том Work, запущенный существующий Remote Desktop Commander и доступ этого инструмента из облачной задачи. При недоступности — SYNC_BLOCKED; устаревший снимок не считается актуальным и автоматического обхода доступа нет. Синхронизация выполняется при запуске обзора (обычно ежедневно в 10:00), не мгновенно после каждого сообщения. Решения из других чатов автоматически не подтягиваются.

Проверка URL и точного вхождения цитаты обеспечивает трассируемость, но не удостоверяет автора письма и не доказывает правильность смысловой интерпретации. Доверенным посредником остаётся исполнитель обзора: он обязан отличать прямое решение пользователя от цитаты и рекомендации. При неоднозначности — REVIEW, без изменения статуса. Не выводите `SYNC_OK` без квитанции и повторного чтения. Остановить плановую синхронизацию можно паузой существующей задачи; это не удаляет каталог или историю. Старые Nantes-чаты остаются источниками истории, новые решения ведутся в одном рабочем чате.

Общий обзор читает почту, отделяет новые сообщения от старых, связывает изменения с существующими возможностями и не повторяет неизменившиеся рекомендации без нового факта/согласованной даты. Ошибка доступа не означает отсутствие изменений. Gmail/Calendar и отправка сообщений остаются запрещены без отдельного прямого запроса.

Переиспользованы CLI, capability/donor registries, `harness` validation/now_iso и атомарная запись `content_ops`, добавлена блокировка единого состояния. `collections`, `provenance`, `history`, `events` содержат источники, hashes и историю. Общий `process_learning` рассчитан на отдельные измеренные workload outcomes: вакансии и контактные данные туда автоматически не экспортируются. Данные для последующего анализа конверсии остаются в локальном журнале; нулевое число локальных записей не доказывает отсутствие прошлых откликов.

Локальный модуль не отправляет заявки/письма, не синхронизирует Gmail/Calendar, не вызывает платные API или LLM и не устанавливает daemon. Облачное задание использует уже существовавшее чтение Gmail, без изменений почтовых данных. Используйте один писатель через CLI; прямое редактирование файла обходит проверки. Резервное копирование приватного каталога остаётся обязанностью существующего локального backup процесса.

## Заимствованные элементы

[ai-job-search](https://github.com/ai-job-search-dev/ai-job-search/tree/e16acee3abdaae57f8026789338a3c6eebf4608b), ревизия `e16acee3abdaae57f8026789338a3c6eebf4608b`, MIT: рассмотрены candidate profile, evaluation/language gates, rank, job_key и outcome. Использованы паттерны; донорский код и команды не установлены. Страновые/юридические обобщения донора не принимаются как установленный факт. Датские CLIs, Claude-specific orchestration, Gmail/Notion sync, LaTeX и salary tools не перенесены. Проверены существующие ABVX capabilities и Opportunity/CRM donor trycompai/crm; полный CRM избыточен для этой локальной адаптации.

[Remotive public API](https://github.com/remotive-com/remote-jobs-api): бесплатное чтение, атрибуция, сохранение исходных ссылок и редкий опрос. API results не подтверждают право кандидата работать по конкретной вакансии.

### Восстановление Desktop Commander после входа в macOS

24 октября установлен пользовательский LaunchAgent `io.abvx.desktop-commander-remote`: RunAtLoad и KeepAlive, закреплённая существующая версия 0.3.1 вне npm-кэша, прежняя сохранённая сессия. Перезапуск после SIGTERM проверен, затем удалённое чтение каталога успешно. После reboot требуется вход в macOS; реальная перезагрузка пока не проверена. Отчёт и обратимое отключение: `opportunities/private/reports/NANTES-autostart.md`. Следующая проверка существующего обзора: 25 октября 10:15 Europe/Paris, после штатного запуска 10:00; отдельный Radar не создаётся.
