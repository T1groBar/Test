from telethon import TelegramClient, events, Button
import random

# Настройки бота
bot_token = '7453960039:AAG5x4YxOz3IRrn5xPPkY7Qa2-DoIU7s9Ms'
api_id = '18778182'
api_hash = 'f5adaf2bbb96d97ff4443fdc0c4ddb38'
admin_id = 5722874142

client = TelegramClient('feedback_bot', api_id, api_hash).start(bot_token=bot_token)

# Определение переменных
user_states = {}
responding_users = {}
message_ids = {}
blocked_users = set()
blocked_users_notified = set()  # Добавляем новый набор для хранения уведомлений

def generate_unique_id():
    """Генерация уникального номера."""
    return random.randint(1000, 9999)

@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    if event.sender_id in blocked_users:
        if event.sender_id not in blocked_users_notified:
            await event.respond("❌ Ви заблоковані і не можете користуватися ботом.")
            blocked_users_notified.add(event.sender_id)
        return
    await event.respond(
        "🕵️Ласкаво просимо в бота зворотнього зв'язку «Назва каналу»\n\n"
        "✏️Якщо ви хочете нам написати, натисніть: «НАПИСАТИ💬»",
        buttons=[Button.inline('НАПИСАТИ💬', 'НАПИСАТИ')]
    )

@client.on(events.CallbackQuery(data='НАПИСАТИ'))
async def handle_write(event):
    if event.sender_id in blocked_users:
        if event.sender_id not in blocked_users_notified:
            await event.respond("❌ Ви заблоковані і не можете користуватися ботом.")
            blocked_users_notified.add(event.sender_id)
        return
    user_states[event.sender_id] = 'awaiting_feedback'
    await event.respond(
        "Напишіть свій запит до адміністрації каналу «Назва каналу».\n\n"
        "⌛Найближчі 24 години ваше повідомлення буде розглянуто!"
    )

@client.on(events.NewMessage)
async def handle_user_message(event):
    if event.is_private and event.sender_id != admin_id:
        if event.sender_id in blocked_users:
            if event.sender_id not in blocked_users_notified:
                await event.respond("❌ Ви заблоковані і не можете надсилати повідомлення.")
                blocked_users_notified.add(event.sender_id)
            return

        state = user_states.get(event.sender_id)
        if state == 'awaiting_feedback':
            unique_id = generate_unique_id()
            message_ids[event.sender_id] = unique_id

            await event.respond(
                "Дякуємо за повідомлення, скоро його розглянемо.\n\n"
                "🧐Якщо це не все, що ви хочете написати, надішліть все одним повідомленням. Як відправити ще одне повідомлення?\n```Головне меню > НАПИСАТИ💬 > Ваше повідомлення```",
                buttons=[Button.inline('Головне меню', 'Головне_меню')]
            )

            sender = await event.get_sender()
            first_name = sender.first_name if sender.first_name else "Без имени"
            last_name = sender.last_name if sender.last_name else ""
            full_name = f"{first_name} {last_name}".strip()
            username = f"@{sender.username}" if sender.username else "Немає"

            unique_number = message_ids.get(event.sender_id, generate_unique_id())
            message_to_admin = (
                "📥Нове повідомлення\n"
                f"👤Від користувача: {full_name}\n"
                f"🔢UserID: tg://openmessage?user_id={event.sender_id}\n"
                f"🕵️Username:{username}\n"
                f"♻️Унікальний номер: #id{unique_number}\n\n"
                f"📥Повідомлення:\n```{event.message.text}```"
            )

            await client.send_message(
                admin_id,
                message_to_admin,
                buttons=[
                    Button.inline('ВІДПОВІСТИ', f'ВІДПОВІСТИ_{event.sender_id}'),
                    Button.inline('⛔ ЗАБЛОКУВАТИ⛔', f'BLOCK_{event.sender_id}'),
                    Button.inline('🟢РОЗБЛОКУВАТИ 🟢', f'UNBLOCK_{event.sender_id}')
                ]
            )
            user_states[event.sender_id] = 'none'

# Обработчик для кнопки "Головне меню"
@client.on(events.CallbackQuery(data='Головне_меню'))
async def handle_main_menu(event):
    if event.sender_id in blocked_users:
        if event.sender_id not in blocked_users_notified:
            await event.respond("❌ Ви заблоковані і не можете користуватися ботом.")
            blocked_users_notified.add(event.sender_id)
        return
    await start(event)

@client.on(events.CallbackQuery)
async def handle_query(event):
    data = event.data.decode('utf-8')

    if data.startswith('ВІДПОВІСТИ'):
        parts = data.split('_')
        if len(parts) > 1:
            user_id_to_respond = int(parts[1])
            user_states[event.sender_id] = 'awaiting_message'
            responding_users[event.sender_id] = user_id_to_respond
            await event.respond("Напишіть повідомлення для користувача нижче:",
                                buttons=[Button.inline('ЗАВЕРШИТИ', f'ЗАВЕРШИТИ_{event.sender_id}')])
            await client.send_message(user_id_to_respond, "👁️Ваше повідомлення вже розглядають!")

    elif data.startswith('ЗАВЕРШИТИ'):
        parts = data.split('_')
        if len(parts) > 1:
            admin_id = int(parts[1])
            if admin_id in responding_users:
                user_id_to_respond = responding_users.pop(admin_id, None)
                if user_id_to_respond:
                    # Отправка уведомления пользователю
                    await client.send_message(user_id_to_respond, "**🔔Розмову з вами було завершено адміністрацією!**")
                    await event.respond("🛑Відповідь завершено. Ви можете тепер виконати інші дії.")

    elif data.startswith('BLOCK'):
        parts = data.split('_')
        if len(parts) > 1:
            user_id_to_block = int(parts[1])
            blocked_users.add(user_id_to_block)
            blocked_users_notified.add(user_id_to_block)  # Добавляем пользователя в список уведомленных
            await client.send_message(user_id_to_block, "**__🔒Ви були заблоковані адміністрацією.__**")
            await event.respond("✅Користувача заблоковано!")

    elif data.startswith('UNBLOCK'):
        parts = data.split('_')
        if len(parts) > 1:
            user_id_to_unblock = int(parts[1])
            if user_id_to_unblock in blocked_users:
                blocked_users.remove(user_id_to_unblock)
                blocked_users_notified.discard(user_id_to_unblock)  # Удаляем пользователя из списка уведомленных
                await event.respond("✅Користувача розблоковано!")
                await client.send_message(user_id_to_unblock, "**🟢Ви були розблоковані адміністратором.**")
            else:
                await event.respond("```❌Користувач не був заблокований.```")

@client.on(events.NewMessage)
async def handle_admin_message(event):
    if event.sender_id == admin_id:
        if event.reply_to_msg_id and event.message.text:
            # Check if this message is a response to a block request
            if event.message.text:
                reason = event.message.text
                user_id_to_block = None
                for user_id in blocked_users:
                    if user_id not in blocked_users:
                        user_id_to_block = user_id
                        break
                if user_id_to_block:
                    await client.send_message(user_id_to_block, f"**__🔒Ви були заблоковані адміністрацією.\n⛔Причина: {reason}__**")
                    blocked_users.add(user_id_to_block)
                    await event.respond("✅Користувача заблоковано!")
        elif event.sender_id in responding_users:
            user_id_to_respond = responding_users[event.sender_id]
            try:
                await client.send_message(user_id_to_respond, event.message.text)
                await event.respond("Ваше повідомлення було відправлено користувачу.")
            except Exception as e:
                await event.respond("Виникла помилка при відправці повідомлення.")
                print(f"Ошибка при отправке сообщения: {e}")

client.run_until_disconnected()

