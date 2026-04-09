import os
import logging
import httpx
import json

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message

# --- НАСТРОЙКИ ---
TELEGRAM_TOKEN = "8677238650:AAFF_zE-oNXhwlqofsqFztiSg-LZEg76lkI"
OPENROUTER_API_KEY = "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"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_NAME = "qwen/qwen-2.5-72b-instruct"
CRM_API_URL = "http://backend:8000"

SYSTEM_PROMPT = """Ты — AI-ассистент CRM системы "СтройИм" (ремонтно-строительные проекты).
Твоя задача — помогать пользователям (прорабам, менеджерам) с вопросами по объектам, сметам, материалам и финансам.
Отвечай четко, по делу, используй эмодзи для структуры."""

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("🏗 Привет! Я AI-помощник СтройИм.\n\nЯ подключен к модели Qwen 2.5.\nСпрашивай меня о работе, стройке или управлении проектами!")

@dp.message()
async def handle_message(message: Message):
    user_text = message.text
    await message.answer("🤔 Думаю...")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                OPENROUTER_URL,
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "HTTP-Referer": "https://crm-stroim.ru",
                    "X-Title": "CRM StroIm Bot",
                    "Content-Type": "application/json"
                },
                json={
                    "model": MODEL_NAME,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_text}
                    ],
                    "max_tokens": 500,
                    "temperature": 0.7
                },
                timeout=30.0
            )
            
            data = response.json()
            if "choices" in data and len(data["choices"]) > 0:
                answer = data["choices"][0]["message"]["content"]
                await message.answer(answer)
            else:
                await message.answer("⚠️ Ошибка: Не удалось получить ответ от ИИ.")
                
    except Exception as e:
        logging.error(f"Error: {e}")
        await message.answer(f"⚠️ Произошла ошибка: {e}")


async def send_work_batch_to_contractors(batch_id: int, items: list, object_name: str, contractor_ids: list):
    import random, asyncio
    items_text = "\n".join([f"• {item['name']}: {item['quantity']} {item['unit']}" for item in items])
    message_text = f"🏗 <b>Новая заявка на работы</b>\n📍 Объект: {object_name}\n📋 <b>Список работ:</b>\n{items_text}\nНажмите кнопку ниже, чтобы ответить:"
    for idx, cid in enumerate(contractor_ids):
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{CRM_API_URL}/telegram-users/?contractor_id={cid}")
                users = resp.json()
            if not users: continue
            tid = users[0]["telegram_id"]
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✅ Взять", callback_data=f"accept_{batch_id}")],
                [InlineKeyboardButton(text="💰 Цена", callback_data=f"bid_{batch_id}")],
                [InlineKeyboardButton(text="❌ Отказ", callback_data=f"decline_{batch_id}")]
            ])
            await bot.send_message(chat_id=tid, text=message_text, parse_mode="HTML", reply_markup=keyboard)
            if idx < len(contractor_ids) - 1:
                await asyncio.sleep(random.uniform(2, 4))
        except Exception as e:
            logging.error(f"Error sending to {cid}: {e}")

@dp.callback_query(lambda c: c.data.startswith(("accept_", "bid_", "decline_")))
async def handle_contractor_response(callback: CallbackQuery):
    action, bid = callback.data.split("_", 1)
    if action == "accept":
        await callback.answer("Принято!")
        await callback.message.edit_text(f"{callback.message.text}\n\n✅ <b>Принято</b>")
    elif action == "decline":
        await callback.answer("Отказано")
        await callback.message.edit_text(f"{callback.message.text}\n\n❌ <b>Отказ</b>")

async def main():
    logging.info("Bot starting...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
