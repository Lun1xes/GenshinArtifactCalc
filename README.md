# ⚙️ Genshin Artifact Calculator v2

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)](https://github.com/Lun1xes/GenshinArtifactCalc)
[![CustomTkinter](https://img.shields.io/badge/GUI-CustomTkinter-248cd6.svg)](https://github.com/TomSchimansky/CustomTkinter)
[![Tests](https://img.shields.io/badge/tests-252%20passed-brightgreen.svg)](https://github.com/Lun1xes/GenshinArtifactCalc)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Latest Release](https://img.shields.io/github/v/release/Lun1xes/GenshinArtifactCalc?label=release&color=gold)](https://github.com/Lun1xes/GenshinArtifactCalc/releases/latest)

Профессиональный калькулятор, оценщик и оптимизатор артефактов для **Genshin Impact** с модульным GUI на **CustomTkinter** в аутентичной тёмно-золотой стилистике игры.

Оценивает качество и потенциал артефактов по дискретным роллам 5★, рассчитывает комбинаторную вероятность улучшения до +20 на базе математики AnimeGameData, поддерживает side-by-side сравнение, импорт из Enka.Network, Inventory Kamera (OCR) и стандарта GOOD JSON.

---

## 🚀 Ключевые возможности

* **Модульная архитектура UI (CustomTkinter + MVC/Component Pattern)**:
  Боковая панель навигации (Sidebar) с вкладками:
  1. ⚔️ **Калькулятор**: быстрый ввод артефакта, дискретные роллы, оценка PAV/CV, прогноз прокачки до +20 и рекомендации персонажей.
  2. 📷 **Сканер (Kamera & Enka)**: автоматический OCR-скан рюкзака через Inventory Kamera и загрузка витрин персонажей по UID из Enka.Network.
  3. 📖 **Каталог билдов**: 130+ актуальных сборок персонажей (до версии 5.x+) с пагинацией и фильтрами по стихиям/ролям.
  4. 📜 **История и сравнение**: таблица сохранённых кусков с виртуализированным рендерингом и side-by-side сопоставлением с цветовыми дельтами.
  5. ℹ️ **О программе**: источники формул, данные, кредиты и хоткеи.
* **Глубокая оптимизация производительности (60+ FPS)**:
  - **Move-Filtering**: фильтрация шквала событий `WM_MOVE` при перемещении окна, предотвращающая зависания интерфейса и перегрузку процессора.
  - **Нативный DWM Dark Titlebar**: интеграция темного заголовка через `DwmSetWindowAttribute(hwnd, 20, ...)` без разрывов графического контекста (`withdraw`/`update`).
  - **Ленивая загрузка экранов (`LazyViewsDict`)**: вкладки инициализируются по требованию при первом клике. Число виджетов при старте снижено с **2 312 до 201** (**-91.3%**).
  - **Пагинация и лимит виджетов**: каталог билдов отображает по 24 сборки на страницу; на экране единовременно находится не более 150 виджетов.
  - **Асинхронный IconManager**: PIL-ресайз методом LANCZOS и дисковое чтение вынесены в фон, UI получает мгновенный плейсхолдер.
* **Математика и аналитика**:
  - Точный перебор дискретных шагов 5★ артефактов (low/mid/high).
  - Прогноз вероятности получения рангов **S+**, **SS+**, **SSS** до 20 уровня.
  - Математическое ожидание PAV и Crit Value (CV) на базе комбинаторных весов AnimeGameData.
  - Рекомендация лучших носителей с кнопкой «Примерить» в один клик.
* **Интеграция и форматы**:
  - Поддержка стандарта **GOOD (Genshin Open Object Data)**: экспорт и импорт.
  - Прямой парсинг артефактов из **Inventory Kamera**.
  - Синхронизация профиля по UID через **Enka.Network**.
  - Буфер обмена: поддержка Ctrl+C, Ctrl+V, Ctrl+A при русской и английской раскладках клавиатуры.

---

## 📦 Структура проекта

```text
genshin_artifact_calc_v2/
├── main.py                             # Точка входа в приложение (DPI awareness, theme setup)
├── calculator.py                       # Обратная совместимость и legacy-клиент
├── requirements.txt                    # Python-зависимости (customtkinter, Pillow)
├── README.md                           # Документация проекта
├── .github/workflows/
│   └── release.yml                     # Автоматическая сборка Windows .exe и публикация релизов
├── src/genshin_calc/                   # Исходный код пакета
│   ├── artifact_logic.py               # Логика дискретных роллов, валидация 3/4-stat, расчёт PAV
│   ├── character_builds.py             # База 130+ персонажей, сетов артефактов, весов статов
│   ├── upgrade_probability.py          # Движок теории вероятностей и прогноза улучшения до +20
│   ├── icon_manager.py                 # Асинхронный загрузчик аватарок, PIL LANCZOS, стихийные рамки
│   ├── good_adapter.py                 # Адаптер формата GOOD JSON (Genshin Open Object Data)
│   ├── enka_adapter.py                 # Клиент Enka.Network API для получения витрины по UID
│   ├── kamera_adapter.py               # Интеграция с OCR-сканером Inventory Kamera
│   └── ui/                             # Пользовательский интерфейс (CustomTkinter)
│       ├── app.py                      # Главный каркас приложения (AppWindow, навигация, DWM)
│       ├── theme.py                    # Цветовая палитра, типографика, стили, DWM-патчи
│       ├── hotkeys.py                  # Глобальные горячие клавиши и раскладки Windows
│       ├── components/                 # Переиспользуемые виджеты
│       │   ├── sidebar.py              # Боковая панель навигации
│       │   ├── stat_inputs.py          # Блок ввода слота, сета, главного стата и сабстатов
│       │   └── forecast_panel.py       # Панель прогноза +20, ранга, аватара героя и советов
│       └── views/                      # Модульные представления (экраны)
│           ├── calculator_view.py      # Экран основного калькулятора артефактов
│           ├── scanner_view.py         # Экран сканера (Kamera OCR + Enka UID)
│           ├── builds_view.py          # Экран каталога 130+ сборок с пагинацией (24/стр)
│           ├── history_view.py         # Экран истории и side-by-side сравнения
│           └── about_view.py           # Экран справки, горячих клавиш и источников
├── tests/                              # Комплект автоматических тестов (252 теста)
│   ├── test_artifact_logic.py          # Тесты математики и дискретных роллов
│   ├── test_calculator_state.py        # Тесты состояния и dirty-state GUI
│   ├── test_character_builds.py        # Тесты мета-билдов и совместимости
│   ├── test_history_view_optimized.py  # Тесты оптимизации истории и пагинации
│   ├── test_icon_manager.py            # Тесты асинхронного кэширования иконок
│   ├── test_good_format.py             # Тесты структуры GOOD JSON
│   ├── test_enka_adapter.py            # Тесты Enka API
│   ├── test_kamera_adapter.py          # Тесты адаптера Kamera OCR
│   └── e2e/                            # Сквозные интеграционные тесты интерфейса
├── data/                               # Локальные базы данных (билды, артефакты, веса)
└── kamera/                             # Модуль Inventory Kamera (OCR-движок)
```

---

## 🛠️ Установка и запуск

### Требования
- **ОС**: Windows 10 / 11 (64-bit)
- **Python**: 3.10 или новее

### 1. Установка из исходников
Клонируйте репозиторий и установите зависимости:
```bash
git clone https://github.com/Lun1xes/GenshinArtifactCalc.git
cd GenshinArtifactCalc
pip install -r requirements.txt
```

### 2. Запуск приложения
```bash
python main.py
```
*(Также поддерживается запуск через `python calculator.py`)*

### 3. Готовая сборка (.exe)
Если у вас не установлен Python, скачайте готовый архив из раздела [Releases](https://github.com/Lun1xes/GenshinArtifactCalc/releases/latest), распакуйте его и запустите `GenshinArtifactCalc.exe`.

---

## 🧪 Тестирование

Проект покрыт полным набором модульных и интеграционных тестов:
```powershell
python -m unittest discover -s tests
```
**Результат**: `Ran 252 tests in ~14s. OK (0 failures, 0 errors)`.

---

## ⚡ Оптимизация и производительность

В версии v1.0.4 проведена комплексная оптимизация взаимодействия с оконным менеджером Windows:

| Параметр | До оптимизации | После оптимизации |
| :--- | :--- | :--- |
| **Количество виджетов на старте** | 2 312 | **201** (-91.3%) |
| **Виджетов во вкладке сборок** | 1 395 | **~150** (пагинация по 24) |
| **Время обработки 100 событий драга** | ~526 мс (фриз мыши) | **3.3 мс** (в 159 раз быстрее) |
| **Нагрузка CPU при перетаскивании окна** | 100% | **< 1%** (плавный нативный драг) |
| **Задержка старта из-за ресайза иконок** | 15–40 мс на иконку | **0.0 мс** (асинхронный LANCZOS) |
| **DWM Titlebar** | Деструктивный цикл `withdraw()` | Прямой вызов `DwmSetWindowAttribute` |

---

## 📚 Источники данных и математики

- **[AnimeGameData / Dimbreath](https://github.com/Dimbreath/AnimeGameData)**: точные веса шансов появления сабстатов (`SUBSTAT_SPAWN_WEIGHT`), веса главных характеристик и шаги дискретных роллов.
- **[KeqingMains (KQM)](https://keqingmains.com/) & [Akasha System](https://akasha.cv/)**: экспертные коэффициенты полезности характеристик под персонажей и роли (DPS, Sub-DPS, Healer, Buffer).
- **[Paimon.moe](https://paimon.moe/)**: мета-билды, приоритеты сетов, требования к ВЭ и рекомендации оружия.
- **[Genshin-DB](https://github.com/theBowja/genshin-db)**: локализация персонажей, наборов артефактов и ассеты.

---

## 📄 Лицензия

Распространяется под лицензией **MIT**. Подробности в файле [LICENSE](LICENSE).
Genshin Impact™ является зарегистрированным товарным знаком компании miHoYo Co., Ltd. Данный проект не аффилирован с miHoYo.
