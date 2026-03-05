# Шрифты для PDF с кириллицей

Эта директория предназначена для локальных шрифтов с поддержкой кириллицы.

## Рекомендуемые шрифты

### Inter (Variable Font)
- **Источник:** https://github.com/rsms/inter/releases
- **Файлы:** `Inter-Variable.woff2`, `Inter-Variable.ttf`
- **Поддержка:** Латиница + Кириллица, переменный шрифт (100–900)

### Montserrat (Variable Font)
- **Источник:** https://fonts.google.com/specimen/Montserrat
- **Файлы:** `Montserrat-Variable.woff2`, `Montserrat-Variable.ttf`
- **Поддержка:** Латиница + Кириллица, переменный шрифт (100–900)

## Установка шрифтов

### Вариант 1: Скачать вручную

1. **Inter:**
   ```
   https://github.com/rsms/inter/releases/latest
   → Скачать Inter-X.X.zip
   → Распаковать и взять из папки:
      - Inter-Variable.woff2
      - Inter-Variable.ttf
   ```

2. **Montserrat:**
   ```
   https://github.com/JulietaUla/Montserrat/releases
   → Скачать Montserrat.zip
   → Распаковать и взять из папки fonts/variable:
      - Montserrat-VariableFont_wght.woff2 (переименовать в Montserrat-Variable.woff2)
      - Montserrat-VariableFont_wght.ttf (переименовать в Montserrat-Variable.ttf)
   ```

### Вариант 2: Google Fonts (онлайн)

Можно использовать Google Fonts, но для PDF рекомендуется локальные файлы:

```html
<!-- В <head> src/index.html -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=Montserrat:wght@400;600;700&display=swap" rel="stylesheet">
```

⚠️ **Внимание:** при использовании онлайн шрифтов PDF генерация может занять больше времени и требует интернет-соединения.

## Структура после установки

```
src/fonts/
├── Inter-Variable.woff2
├── Inter-Variable.ttf
├── Montserrat-Variable.woff2
├── Montserrat-Variable.ttf
└── README.md (этот файл)
```

## Проверка поддержки кириллицы

После установки шрифтов откройте `src/index.html` в браузере и проверьте, что кириллический текст отображается корректно.

Если видите «квадратики» — шрифт не содержит кириллицу или путь указан неверно.

## Альтернативные шрифты (системные)

Если не хотите устанавливать локальные шрифты, используйте системные:

```css
/* В src/print.css */
body {
  font-family: "Segoe UI", "Roboto", system-ui, -apple-system, Arial, sans-serif;
}
```

Системные шрифты уже содержат кириллицу:
- **Windows:** Segoe UI
- **macOS:** SF Pro / San Francisco
- **Linux:** Ubuntu / Roboto

---

**Итог:** для наилучшего качества рекомендуется использовать локальные переменные шрифты (Inter, Montserrat) с полной поддержкой кириллицы.

