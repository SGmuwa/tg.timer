# kt.pizza
Данный репозиторий содержит бот оповещения о пицце:

* `telegram.py`

## Пример запуска

### Unix like

```bash
./telegram.py
```

### WindowsNT

```cmd
python3 telegram.py
```

## Переменные среды

| Название               | Значение по-умолчанию                 | Допустимые значения                          | Описание   |
|------------------------|---------------------------------------|----------------------------------------------|------------|
| `TELEGRAM_SECRET_PATH` | `./secret.json5`                      | any path example `/run/checks/secret.json5`  | Место в файловой системе, где хранятся секретные настройки. Пример заполненного фала: `example.secret.json5`.
| `TELEGRAM_SECRET`      | None                                  | Содержимое файла `secret.json5`              | Вместо пути `TELEGRAM_SECRET_PATH` можно передать содержимое json файла прям в этой переменной.
| `LOGURU_LEVEL`         | `DEBUG`                               | `TRACE`, `DEBUG`, `INFO`, `WARNING`, `ERROR` | Уровень журналирования информации в консоль.

Если вдруг заданы одновременно `TELEGRAM_SECRET_PATH` и `TELEGRAM_SECRET`, то будет использован `TELEGRAM_SECRET`.
