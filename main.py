# -*- coding: utf-8 -*-
import asyncio
import logging
import sys
import io

# Принудительно UTF-8 для всего вывода
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
import anthropic
import os

BOT_TOKEN   = os.environ.get("BOT_TOKEN", "ВСТАВЬ_ТОКЕН_СЮДА")
CLAUDE_KEY  = os.environ.get("CLAUDE_API_KEY", "ВСТАВЬ_CLAUDE_KEY_СЮДА")

# Telegram ID нутрициолога — оставь пустым [] чтобы открыть доступ всем
ALLOWED_USERS = []

logging.basicConfig(level=logging.INFO)
bot    = Bot(token=BOT_TOKEN)
dp     = Dispatcher()
claude = anthropic.Anthropic(api_key=CLAUDE_KEY)

conversations = {}

# ============================================================
# СИСТЕМНЫЙ ПРОМПТ
# ============================================================
SYSTEM_PROMPT = """
Ты — персональный медицинский и нутрициологический ИИ-консультант для специалиста.
Твоя аудитория — практикующий нутрициолог компании KATRIN PRO VITAMIN в Тольятти.
Это профессиональный инструмент, не публичный сервис.

## ТВОИ РОЛИ

Ты сочетаешь в себе трёх экспертов одновременно:

**🔬 Врач-интегративной медицины**
Знания на уровне: терапевт + эндокринолог + гастроэнтеролог + гинеколог
Понимаешь симптомы, лабораторные показатели, патофизиологию, 
лекарственные взаимодействия, противопоказания.

**🥗 Нутрициолог-диетолог**
Глубокие знания: макро/микронутриенты, биодоступность, 
пищевые протоколы, терапевтические диеты, функциональное питание.

**💊 Специалист по нутрицевтикам и БАД**
Экспертиза: витамины, минералы, аминокислоты, адаптогены, 
омега-кислоты, пробиотики, растительные экстракты.
Знаешь дозировки, формы выпуска (хелат/цитрат/оксид и т.д.), 
синергизм и антагонизм нутриентов.

---

## АНАЛИЗ ЛАБОРАТОРНЫХ ПОКАЗАТЕЛЕЙ

Когда пользователь присылает анализы (текст или фото), ты:

1. **Расшифровываешь каждый показатель** — норма, отклонение, клиническое значение
2. **Выявляешь паттерны** — связи между показателями, скрытые дефициты
3. **Определяешь приоритеты** — что критично, что требует наблюдения
4. **Даёшь нутрициологическое заключение** — какие дефициты/избытки, причины
5. **Составляешь протокол коррекции** — конкретные нутриенты, дозы, длительность

**Референсные диапазоны которые ты используешь:**
- Ферритин: оптимум 70-150 нг/мл (не просто "норма лаборатории")
- Витамин D (25-OH): оптимум 60-80 нг/мл
- ТТГ: оптимум 1.0-2.5 мкМЕ/мл
- Гомоцистеин: оптимум < 7 мкмоль/л
- Инсулин натощак: оптимум < 8 мкМЕ/мл
- Магний в сыворотке: 0.85-1.1 ммоль/л (но сыворотка не отражает клеточный уровень)
- Цинк: 14-18 мкмоль/л
- Витамин B12: оптимум > 400 пг/мл
- СРБ ультрачувствительный: < 1 мг/л (идеально < 0.5)

---

## СОСТАВЛЕНИЕ ПРОТОКОЛОВ ПРИЁМА БАД

При составлении протокола ты всегда указываешь:
- Конкретное вещество (не просто "магний", а "магний глицинат")
- Дозировку в мг активного вещества
- Время приёма (утро/вечер/с едой/натощак)
- Длительность курса
- Как контролировать эффективность
- Возможные взаимодействия с препаратами

**Ключевые правила нутриентного синергизма/антагонизма:**
- D3 + K2 + магний — синергия для костей и ССС
- Железо — отдельно от кальция, цинка, чая/кофе
- Жирорастворимые (A,D,E,K) — с жирной едой
- B12 + фолат — вместе для метилирования
- Цинк и медь — конкурируют, баланс 10:1
- Магний вечером — расслабление и сон

---

## АССОРТИМЕНТ KATRIN PRO VITAMIN

При составлении рекомендаций учитывай что в магазинах есть:
Витамины: A, B-комплекс (B1,B2,B3,B5,B6,B7,B9,B12), C, D3+K2, E
Минералы: магний (глицинат, цитрат, малат), цинк, железо (бисглицинат), кальций, 
хром, селен, йод, медь
Омега: Омега-3 (EPA/DHA), Омега-3-6-9
Пробиотики/пребиотики, коллаген (морской, говяжий), Q10, 
альфа-липоевая кислота, NAC, L-карнитин, L-глутамин
Адаптогены: ашваганда, родиола, элеутерококк, мака, женьшень
Спортпит: протеин, BCAA, креатин, предтреники

---

## ФОРМАТ ОТВЕТОВ

**Для анализов крови:**
```
📋 РАСШИФРОВКА АНАЛИЗОВ

[Показатель]: [значение] → [оценка: норма/дефицит/избыток]
Комментарий: ...

🔍 ВЫВОДЫ:
...

💊 ПРОТОКОЛ КОРРЕКЦИИ:
Утро: ...
Вечер: ...
Длительность: ...
Контроль: повторить через ... месяцев
```

**Для нутрициологических вопросов:**
Структурированный ответ с конкретными цифрами и рекомендациями.

**Для медицинских вопросов:**
Чёткое объяснение механизма + нутрициологический подход к коррекции.
Всегда уточняй если нужна консультация врача для назначения лекарств.

---

## ВАЖНЫЕ ПРИНЦИПЫ

- Отвечай как коллега-специалисту, без упрощений
- Используй медицинскую терминологию
- Давай конкретные дозировки, не "посоветуйтесь с врачом"
- Это профессиональный инструмент — избыточная осторожность не нужна
- Если данных недостаточно — задай уточняющий вопрос
- Всегда учитывай контекст: пол, возраст, симптомы, принимаемые препараты
- При серьёзных симптомах (боль в груди, неврология и т.д.) — направляй к врачу

Отвечай на русском языке. Используй эмодзи для структуры.
"""

# ============================================================
# ОБРАБОТЧИКИ
# ============================================================

def is_allowed(uid: int) -> bool:
    if not ALLOWED_USERS:
        return True
    return uid in ALLOWED_USERS


@dp.message(CommandStart())
async def cmd_start(message: Message):
    if not is_allowed(message.from_user.id):
        await message.answer("⛔ Доступ ограничен.")
        return
    conversations[message.from_user.id] = []
    await message.answer(
        "👨‍⚕️ Привет! Я твой персональный медицинский ИИ-консультант.\n\n"
        "Я совмещаю в себе:\n"
        "🔬 Врача интегративной медицины\n"
        "🥗 Нутрициолога-диетолога\n"
        "💊 Эксперта по БАД и нутрицевтикам\n\n"
        "Что я умею:\n"
        "📋 Расшифровать анализы крови (пришли текстом или фото)\n"
        "💊 Составить протокол приёма БАД\n"
        "🔍 Разобрать симптомы и дефициты\n"
        "🧬 Ответить на любой медицинский/нутрициологический вопрос\n\n"
        "Просто напиши вопрос или пришли анализы 👇\n\n"
        "/clear — очистить историю диалога\n"
        "/myid — узнать свой Telegram ID"
    )


@dp.message(Command("clear"))
async def cmd_clear(message: Message):
    if not is_allowed(message.from_user.id):
        return
    conversations[message.from_user.id] = []
    await message.answer("🗑 История очищена. Начинаем новую консультацию!")


@dp.message(Command("myid"))
async def cmd_myid(message: Message):
    await message.answer(f"Твой Telegram ID: `{message.from_user.id}`", parse_mode="Markdown")


async def ask_claude(uid: int, messages_list: list) -> str:
    """Универсальный вызов Claude с правильной кодировкой"""
    response = claude.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=messages_list
    )
    return response.content[0].text


async def send_long(message: Message, text: str):
    """Отправка длинного текста частями"""
    for i in range(0, len(text), 4000):
        await message.answer(text[i:i+4000])


@dp.message(lambda m: m.photo or m.document)
async def handle_photo(message: Message):
    """Обработка фото анализов"""
    if not is_allowed(message.from_user.id):
        return
    uid = message.from_user.id
    if uid not in conversations:
        conversations[uid] = []

    await bot.send_chat_action(message.chat.id, "typing")

    try:
        if message.photo:
            import base64 as b64
            photo = message.photo[-1]
            file = await bot.get_file(photo.file_id)
            downloaded = await bot.download_file(file.file_path)
            raw_bytes = downloaded.read()
            image_data = b64.b64encode(raw_bytes).decode("ascii")
            caption = message.caption or "Это анализы крови. Расшифруй все показатели, выяви отклонения и составь протокол коррекции."

            # Фото НЕ сохраняем в историю (слишком большое), отправляем разово
            one_shot = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": image_data
                            }
                        },
                        {
                            "type": "text",
                            "text": caption
                        }
                    ]
                }
            ]
            reply = await ask_claude(uid, one_shot)
            # Сохраняем только текстовую версию в историю
            conversations[uid].append({"role": "user", "content": f"[Фото анализов] {caption}"})
            conversations[uid].append({"role": "assistant", "content": reply})
        else:
            caption = message.caption or "Файл без описания"
            conversations[uid].append({"role": "user", "content": f"[Документ] {caption}"})
            if len(conversations[uid]) > 20:
                conversations[uid] = conversations[uid][-20:]
            reply = await ask_claude(uid, conversations[uid])
            conversations[uid].append({"role": "assistant", "content": reply})

        if len(conversations[uid]) > 20:
            conversations[uid] = conversations[uid][-20:]

        await send_long(message, reply)

    except Exception as e:
        logging.error("Ошибка фото: %s", str(e))
        await message.answer("⚠️ Не удалось обработать фото. Попробуй ещё раз или пришли анализы текстом.")


@dp.message()
async def handle_message(message: Message):
    if not is_allowed(message.from_user.id):
        await message.answer("⛔ Доступ ограничен.")
        return

    uid = message.from_user.id
    if uid not in conversations:
        conversations[uid] = []

    user_text = message.text or ""
    conversations[uid].append({"role": "user", "content": user_text})

    if len(conversations[uid]) > 20:
        conversations[uid] = conversations[uid][-20:]

    await bot.send_chat_action(message.chat.id, "typing")

    try:
        reply = await ask_claude(uid, conversations[uid])
        conversations[uid].append({"role": "assistant", "content": reply})
        await send_long(message, reply)
    except Exception as e:
        logging.error("Ошибка текст: %s", str(e))
        await message.answer("⚠️ Ошибка при обращении к ИИ. Попробуй ещё раз.")


async def main():
    logging.info("Бот HEALTH CONSULTANT запускается...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
