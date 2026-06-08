# -*- coding: utf-8 -*-
import asyncio
import logging
import os
import sys

os.environ.setdefault("PYTHONIOENCODING", "utf-8")

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
import anthropic

logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,
    format="%(asctime)s %(levelname)s %(name)s %(message)s"
)

BOT_TOKEN  = os.environ.get("BOT_TOKEN", "")
CLAUDE_KEY = os.environ.get("CLAUDE_API_TOKEN", "")
ALLOWED_USERS = []

bot    = Bot(token=BOT_TOKEN)
dp     = Dispatcher()
claude = anthropic.Anthropic(api_key=CLAUDE_KEY)
conversations = {}

SYSTEM_PROMPT = """
Ты — персональный медицинский и нутрициологический ИИ-консультант для специалиста.
Твоя аудитория — практикующий нутрициолог компании KATRIN PRO VITAMIN в Тольятти.
Это профессиональный инструмент, не публичный сервис.

## ТВОИ РОЛИ

Ты сочетаешь в себе трёх экспертов одновременно:

Врач интегративной медицины — терапевт + эндокринолог + гастроэнтеролог + гинеколог.
Понимаешь симптомы, лабораторные показатели, патофизиологию, лекарственные взаимодействия.

Нутрициолог-диетолог — макро/микронутриенты, биодоступность, пищевые протоколы,
терапевтические диеты, функциональное питание.

Специалист по нутрицевтикам и БАД — витамины, минералы, аминокислоты, адаптогены,
омега-кислоты, пробиотики, растительные экстракты. Знаешь дозировки, формы выпуска,
синергизм и антагонизм нутриентов.

## АНАЛИЗЫ КРОВИ

Когда получаешь анализы, ты:
1. Расшифровываешь каждый показатель — норма, отклонение, клиническое значение
2. Выявляешь паттерны — связи между показателями, скрытые дефициты
3. Определяешь приоритеты — что критично, что требует наблюдения
4. Даёшь нутрициологическое заключение
5. Составляешь протокол коррекции — конкретные нутриенты, дозы, длительность

Оптимальные референсы (не лабораторные):
- Ферритин: 70-150 нг/мл
- Витамин D (25-OH): 60-80 нг/мл
- ТТГ: 1.0-2.5 мкМЕ/мл
- Гомоцистеин: < 7 мкмоль/л
- Инсулин натощак: < 8 мкМЕ/мл
- Магний в сыворотке: 0.85-1.1 ммоль/л
- Цинк: 14-18 мкмоль/л
- Витамин B12: > 400 пг/мл
- СРБ ультрачувствительный: < 1 мг/л

## ПРОТОКОЛЫ БАД

Указывай:
- Конкретную форму (магний глицинат, а не просто магний)
- Дозировку в мг активного вещества
- Время приёма (утро/вечер/с едой/натощак)
- Длительность курса
- Контроль эффективности
- Взаимодействия с препаратами

Ключевые правила:
- D3 + K2 + магний — синергия
- Железо отдельно от кальция, цинка, чая
- Жирорастворимые (A,D,E,K) — с жирной едой
- B12 + фолат — вместе для метилирования
- Цинк и медь — баланс 10:1
- Магний вечером

## АССОРТИМЕНТ KATRIN PRO VITAMIN

Витамины: A, B-комплекс, C, D3+K2, E
Минералы: магний (глицинат/цитрат/малат), цинк, железо (бисглицинат), кальций, хром, селен, йод, медь
Омега: Омега-3 (EPA/DHA), Омега-3-6-9
Пробиотики, пребиотики, коллаген (морской, говяжий), Q10, альфа-липоевая кислота,
NAC, L-карнитин, L-глутамин
Адаптогены: ашваганда, родиола, элеутерококк, мака, женьшень
Спортпит: протеин, BCAA, креатин

## СТИЛЬ

- Отвечай как коллега-специалисту, без упрощений
- Конкретные дозировки, не "посоветуйтесь с врачом"
- Если данных мало — задай уточняющий вопрос
- При серьёзных симптомах — направляй к врачу
- Отвечай на русском языке
"""


def is_allowed(uid: int) -> bool:
    if not ALLOWED_USERS:
        return True
    return uid in ALLOWED_USERS


async def ask_claude(messages_list: list) -> str:
    response = claude.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=messages_list
    )
    return response.content[0].text


async def send_long(message: Message, text: str):
    for i in range(0, len(text), 4000):
        await message.answer(text[i:i+4000])


@dp.message(CommandStart())
async def cmd_start(message: Message):
    if not is_allowed(message.from_user.id):
        await message.answer("Dostup ogranichen.")
        return
    conversations[message.from_user.id] = []
    await message.answer(
        "Privet! Ya tvoy lichnyy med. konsultant.\n\n"
        "Umeyu:\n"
        "- Rasshifrovat' analizy krovi (foto ili tekst)\n"
        "- Sostavit' protokol BAD\n"
        "- Otvetit' na med/nutrits. vopros\n\n"
        "/clear - ochistit' istoriyu\n"
        "/myid - uznat' svoy ID"
    )


@dp.message(Command("start_ru"))
async def cmd_start_ru(message: Message):
    conversations[message.from_user.id] = []
    await message.answer(
        "Привет! Я твой персональный медицинский консультант.\n\n"
        "Умею:\n"
        "• Расшифровать анализы крови (фото или текст)\n"
        "• Составить протокол приёма БАД\n"
        "• Ответить на медицинский или нутрициологический вопрос\n\n"
        "/clear — очистить историю\n"
        "/myid — узнать свой ID"
    )


@dp.message(Command("clear"))
async def cmd_clear(message: Message):
    conversations[message.from_user.id] = []
    await message.answer("OK. Novaya konsultatsiya.")


@dp.message(Command("myid"))
async def cmd_myid(message: Message):
    await message.answer(str(message.from_user.id))


@dp.message(lambda m: m.photo)
async def handle_photo(message: Message):
    if not is_allowed(message.from_user.id):
        return
    uid = message.from_user.id
    if uid not in conversations:
        conversations[uid] = []

    await bot.send_chat_action(message.chat.id, "typing")

    try:
        import base64 as b64
        photo = message.photo[-1]
        file  = await bot.get_file(photo.file_id)
        dl    = await bot.download_file(file.file_path)
        image_data = b64.b64encode(dl.read()).decode("ascii")
        caption = message.caption or "Eto analizy krovi. Rasshifruy vse pokazateli i sostaviy protokol korrektsii."

        one_shot = [{
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
                {"type": "text", "text": caption}
            ]
        }]

        reply = await ask_claude(one_shot)

        conversations[uid].append({"role": "user",      "content": "[foto] " + caption})
        conversations[uid].append({"role": "assistant",  "content": reply})
        if len(conversations[uid]) > 20:
            conversations[uid] = conversations[uid][-20:]

        await send_long(message, reply)

    except Exception as e:
        logging.error("photo error: %s", repr(e))
        await message.answer("Oshibka pri obrabotke foto. Poprobuy eshche raz.")


@dp.message()
async def handle_message(message: Message):
    if not is_allowed(message.from_user.id):
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
        reply = await ask_claude(conversations[uid])
        conversations[uid].append({"role": "assistant", "content": reply})
        await send_long(message, reply)
    except Exception as e:
        logging.error("text error: %s", repr(e))
        await message.answer("Oshibka. Povtori zapros.")


async def main():
    logging.info("Bot starting...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
