# govnoboy wallpapers
Автоматическая смена обоев рабочего стола через заданный интервал с помощью API ТГ-бота @govnoboybot

Проект поддерживает KDE Plasma, GNOME, MATE, XFCE и Windows.

## 📦 Установка

1. **Клонируйте репозиторий:**
```bash
git clone https://github.com/Alexander397172/telegram-stats.git
cd telegram-stats
```

2. **Установите зависимости:**
```bash
pip install -r requirements.txt
```

## 🔧 Использование

### 1. Настройка конфигурации

В файле `config.json` укажите желаемый интервал смены обоев:
```python
INTERVAL_SECONDS = 10 # Интервал смены обоев в секундах
API_URL = "http://ge1.rock.hosts.name:34633/images" # Ссылка на govnoboy API
```

### 2. Запуск

```bash
python3 main.py
```

## 🤝 Участие в разработке

Если вы хотите помочь проекту:
- Нашли ошибку или есть идея/предложение — создайте Issue с подробным описанием;
- Нашли способ улучшить код или хотите добавить поддержку нового рабочего окружения - создайте Fork, внесите в него изменения, создайте Pull Request
