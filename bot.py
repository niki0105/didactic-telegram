import logging
import os
import re
from datetime import datetime, time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes


GIF_PATH = os.path.join(os.path.dirname(__file__), "nuda.gif")


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ID администраторов
ADMIN_IDS = [8326248354, 1054023698, 890563826, 6332321011, 7801938560]

# ID группового чата
GROUP_CHAT_ID = -1003159637873

# ID тем (threads) в групповом чате
SUPPORT_THREAD_ID = 242
MODELS_THREAD_ID = 241
CUSTOMERS_THREAD_ID = 243

# ID канала для обязательной подписки
REQUIRED_CHANNEL = "nudagency"  # Без @
REQUIRED_CHANNEL_ID = -1003229159162

# Шаблон анкеты для заказчиков
CUSTOMER_TEMPLATE = """Имя:
Компания:
Контакт для связи:
Интересующая модель:
Дата съемки:
ТЗ:
Бюджет:"""

# Рабочее время: Пн-Сб 10:00-22:00
WORK_START = time(10, 0)
WORK_END = time(22, 0)

def is_working_hours():
    """Проверка рабочего времени (Пн-Сб 10:00-22:00)"""
    now = datetime.now()
    weekday = now.weekday()
    current_time = now.time()
    
    if weekday == 6:
        return False
    
    if WORK_START <= current_time <= WORK_END:
        return True
    
    return False

def get_next_working_time():
    """Получить текст о следующем рабочем времени"""
    now = datetime.now()
    weekday = now.weekday()
    current_time = now.time()
    
    if weekday == 6:
        return "Мы ответим в понедельник с 10:00"
    elif current_time < WORK_START:
        return "Мы ответим сегодня с 10:00"
    else:
        if weekday == 5:
            return "Мы ответим в понедельник с 10:00"
        else:
            return "Мы ответим завтра с 10:00"

def main_menu():
    """Главное меню"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Забукировать модель", callback_data='customer')],
        [InlineKeyboardButton("Заполнить модельную анкету", callback_data='model')],
        [InlineKeyboardButton("Поддержка", callback_data='support')],
        [InlineKeyboardButton("О нас", callback_data='about')]
    ])

def back_button():
    """Кнопка назад"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("◀️ Назад", callback_data='back')]
    ])

async def check_subscription(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Проверка подписки на канал"""
    try:
        member = await context.bot.get_chat_member(chat_id=f"@{REQUIRED_CHANNEL}", user_id=user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        logger.error(f"Ошибка проверки подписки: {e}")
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    context.user_data.clear()
    
    try:
        await update.message.reply_animation(
            animation=open("nuda.gif", "rb")
        )
    except Exception as e:
        logger.warning(f"Не удалось отправить GIF: {e}")
    
    await update.message.reply_text(
        "Добро пожаловать в NUDA Agency!\n\nВыберите раздел:",
        reply_markup=main_menu()
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатий на кнопки"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    if query.data == 'customer':
        # Проверка подписки
        is_subscribed = await check_subscription(user_id, context)
        if not is_subscribed:
            await query.edit_message_text(
                f"⚠️ Для использования этого раздела необходимо подписаться на наш канал.\n\n"
                f"Подпишитесь: https://t.me/{REQUIRED_CHANNEL}\n\n"
                f"После подписки вернитесь сюда.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("◀️ Назад", callback_data='back')]
                ])
            )
            return
        
        text = (
            "Добрый день!\n\n"
            "Рады вашему интересу к NUDA ✨\n\n"
            "Заполните анкету по шаблону ниже — это ускорит обработку вашего запроса\n\n"
            "*Пример заполнения:*\n"
            "Имя: Елизавета\n"
            "Компания: NUDA\n"
            "Контакт для связи: @nuda\n"
            "Интересующая модель: Никита Кондратьев\n"
            "Дата съемки: 22.02, 10:00–16:00\n"
            "ТЗ: Каталожная съемка для бренда...\n"
            "Бюджет: до 50.000 за смену\n\n"
            "*Шаблон для заполнения:*\n"
            "```\n"
            f"{CUSTOMER_TEMPLATE}\n"
            "```"
        )
        
        await query.edit_message_text(
            text=text,
            reply_markup=back_button(),
            parse_mode="Markdown"
        )
        context.user_data['section'] = 'Для заказчиков'
    
    elif query.data == 'model':
        # Проверка подписки
        is_subscribed = await check_subscription(user_id, context)
        if not is_subscribed:
            await query.edit_message_text(
                f"⚠️ Для использования этого раздела необходимо подписаться на наш канал.\n\n"
                f"Подпишитесь: https://t.me/{REQUIRED_CHANNEL}\n\n"
                f"После подписки вернитесь сюда.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("◀️ Назад", callback_data='back')]
                ])
            )
            return
        
        await query.edit_message_text(
            "Здравствуйте, звезда! ✨\n\n"
            "Заполните модельную анкету:\n\n"
            "• ФИО\n"
            "• Возраст\n"
            "• Город\n"
            "• Рост + параметры\n"
            "• @Telegram / Телефон\n"
            "• Instagram\n"
            "• Фото (3–10)\n"
            "• Опыт\n"
            "• Готовность к TFP\n"
            "• Портфолио\n\n"
            "Отправьте текст анкеты вместе с фотографиями (добавьте текст в подпись к фото).",
            reply_markup=back_button()
        )
        context.user_data['section'] = 'Для моделей'
    
    elif query.data == 'support':
        await query.edit_message_text(
            "Здравствуйте! Техподдержка NUDA на связи\n\n"
            "Опишите вашу проблему — мы поможем в ближайшее время!",
            reply_markup=back_button()
        )
        context.user_data['section'] = 'Поддержка'
    
    elif query.data == 'about':
        await query.edit_message_text(
            "_NUDA — новая база моделей_, где естественность становится роскошью\n"
            "Без фальши, без курсов, без шаблонов — только живой свет, вкус и уверенность в кадре\n\n"
            "Мы формируем *новое сообщество моделей* для реальных съёмок и проектов\n"
            "Нам важна не только внешность, а энергия, движение и ощущение в кадре\n\n"
            "❗️Важно: мы *не продаём обучение, а* работаем, развиваем, продюсируем",
            reply_markup=back_button(),
            parse_mode="MarkdownV2"
        )
    
    elif query.data == 'back':
        await query.edit_message_text(
            "Выберите раздел:",
            reply_markup=main_menu()
        )
        context.user_data.clear()

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текстовых сообщений"""
    user = update.effective_user
    
    # ========== ОБРАБОТКА ОТВЕТА АДМИНА ==========
    logger.info(f"Проверка: user.id={user.id}, ADMIN_IDS={ADMIN_IDS}, has_reply={bool(update.message.reply_to_message)}")
    
    if user.id in ADMIN_IDS and update.message.reply_to_message:
        replied = update.message.reply_to_message
        logger.info(f"Есть reply. replied.from_user.id={replied.from_user.id}, bot.id={context.bot.id}")
        
        if replied.from_user.id == context.bot.id:
            replied_text = replied.text or replied.caption or ""
            logger.info(f"Это сообщение от бота! Ищу ID в тексте: {replied_text[:100]}")
            
            user_id = None
            
            user_id_match = re.search(r'\[ID:(\d+)\]', replied_text)
            if user_id_match:
                user_id = int(user_id_match.group(1))
                logger.info(f"Найден ID способом 1: {user_id}")
            
            if not user_id:
                numbers = re.findall(r'\b(\d{9,})\b', replied_text)
                logger.info(f"Найденные числа: {numbers}")
                if numbers:
                    user_id = int(numbers[-1])
                    logger.info(f"Найден ID способом 2: {user_id}")
            
            logger.info(f"Финальный user_id: {user_id}")
            
            if user_id:
                admin_response = update.message.text or update.message.caption or "Без текста"
                logger.info(f"Отправляю ответ пользователю {user_id}: {admin_response}")
                try:
                    result = await context.bot.send_message(
                        chat_id=user_id,
                        text=f"Ответ от NUDA Agency:\n\n{admin_response}\n\nЕсть ещё вопросы? Пишите сюда!"
                    )
                    logger.info(f"✅ Ответ успешно отправлен! Message ID: {result.message_id}")
                    await update.message.reply_text("✅ Ответ отправлен пользователю")
                except Exception as e:
                    logger.error(f"❌ Ошибка при отправке ответа пользователю {user_id}: {e}", exc_info=True)
                    await update.message.reply_text(f"❌ Ошибка: {e}")
                return
            else:
                logger.warning("⚠️ ID не найден в сообщении")
                return
    
    # ========== ОБЫЧНАЯ ОБРАБОТКА СООБЩЕНИЙ ==========
    if update.message.chat.type != "private":
        return
    
    section = context.user_data.get('section')
    text = update.message.text
    
    if not section:
        return
    
    # Проверка анкеты для заказчиков
    if section == 'Для заказчиков':
        required_fields = [
            'Имя:', 'Компания:', 'Контакт для связи:', 
            'Интересующая модель:', 'Дата съемки:', 'ТЗ:', 'Бюджет:'
        ]
        
        missing_fields = [field for field in required_fields if field not in text]
        
        if missing_fields:
            await update.message.reply_text(
                "⚠️ Пожалуйста, заполните все поля анкеты.\n\n"
                f"Не хватает: {', '.join(missing_fields)}\n\n"
                "Попробуйте снова.",
                reply_markup=back_button()
            )
            return
    
    # Проверка рабочего времени
    if not is_working_hours():
        next_time = get_next_working_time()
        await update.message.reply_text(
            f"Спасибо за ваше обращение!\n\n"
            f"⏰ Сейчас нерабочее время.\n"
            f"Наш график: Пн-Сб, 10:00-22:00\n\n"
            f"{next_time}\n\n"
            f"Ваше сообщение сохранено, мы обязательно ответим!",
            reply_markup=main_menu()
        )
        admin_prefix = "⏰ НЕРАБОЧЕЕ ВРЕМЯ\n\n"
    else:
        admin_prefix = ""
    
    # Формируем сообщение для администратора
    reply_hint = ""
    user_id_tag = ""
    
    if section in ['Поддержка', 'Для моделей']:
        reply_hint = "\n\nЧтобы ответить пользователю — нажмите Reply на это сообщение"
        user_id_tag = f"\n[ID:{user.id}]"
    
    admin_message = (
        f"{admin_prefix}"
        f"Новый запрос\n\n"
        f"Username: @{user.username or 'без username'}\n"
        f"Раздел: {section}\n"
        f"Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
        f"Сообщение:\n{text}"
        f"{reply_hint}"
        f"{user_id_tag}"
    )
    
    # Отправляем в зависимости от раздела
    try:
        if section == 'Поддержка':
            await context.bot.send_message(
                chat_id=GROUP_CHAT_ID,
                message_thread_id=SUPPORT_THREAD_ID,
                text=admin_message,
                disable_web_page_preview=True
            )
        elif section == 'Для моделей':
            # Отправляем текст
            await context.bot.send_message(
                chat_id=GROUP_CHAT_ID,
                message_thread_id=MODELS_THREAD_ID,
                text=admin_message,
                disable_web_page_preview=True
            )
            
            # Отправляем фото если они есть
            photos = context.user_data.get('photos', [])
            if photos:
                await update.message.reply_text(
                    f"📸 Отправляю {len(photos)} фото в анкету..."
                )
                for photo_id in photos:
                    try:
                        await context.bot.send_photo(
                            chat_id=GROUP_CHAT_ID,
                            photo=photo_id,
                            message_thread_id=MODELS_THREAD_ID
                        )
                    except Exception as e:
                        logger.error(f"Ошибка отправки фото: {e}")
        elif section == 'Для заказчиков':
            await context.bot.send_message(
                chat_id=ADMIN_IDS[0],
                text=admin_message,
                disable_web_page_preview=True
            )
            await context.bot.send_message(
                chat_id=GROUP_CHAT_ID,
                message_thread_id=CUSTOMERS_THREAD_ID,
                text=admin_message,
                disable_web_page_preview=True
            )
        logger.info(f"Сообщение от {user.id} отправлено (раздел: {section})")
    except Exception as e:
        logger.error(f"Ошибка отправки: {e}")
    
    # Ответ пользователю
    if is_working_hours():
        if section == 'Для заказчиков':
            thanks_message = (
                "Благодарим за заполнение анкеты!\n\n"
                "В ближайшее время с вами свяжется наш агент ❤️"
            )
        elif section == 'Для моделей':
            thanks_message = (
                "Спасибо за вашу заявку и уделённое время!\n\n"
                "Мы внимательно изучим предоставлённую информацию.\n"
                "Если ваш типаж заинтересует наше агентство, наши специалисты свяжутся с вами в течение 1–2 недель.\n\n"
                "Если в этот период обратная связь не поступит — не переживайте.\n"
                "Ваши данные остаются в нашей базе, и при появлении подходящих проектов мы обязательно вернёмся к вам.\n\n"
                "Спасибо за доверие к NUDA 🤍\n"
                "Мы ценим ваш интерес и открыты к дальнейшему взаимодействию"
            )
        elif section == 'Поддержка':
            thanks_message = (
                "Спасибо! Мы получили ваше сообщение и ответим в ближайшее время ✨"
            )
        else:
            thanks_message = (
                "Спасибо! Мы получили ваше сообщение ✨"
            )
        
        await update.message.reply_text(thanks_message)
        
        if section in ['Поддержка', 'Для моделей']:
            await update.message.reply_text(
                "Если у вас есть дополнительные вопросы, просто напишите их здесь.\n\n"
                "Или вернитесь в главное меню:",
                reply_markup=main_menu()
            )
        else:
            await update.message.reply_text(
                "Готовы к новому запросу? Выберите ниже:",
                reply_markup=main_menu()
            )
    
    if section == 'Для заказчиков':
        context.user_data.clear()

async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка фотографий"""
    user = update.effective_user
    
    # Обрабатываем только в личных чатах
    if update.message.chat.type != "private":
        return
    
    section = context.user_data.get('section')
    
    # Фото принимаем только в разделе "Для моделей"
    if section != 'Для моделей':
        await update.message.reply_text("📸 Фото принимаются только в разделе 'Заполнить модельную анкету'")
        return
    
    # Инициализируем список фото если его нет
    if 'photos' not in context.user_data:
        context.user_data['photos'] = []
    
    photos = context.user_data['photos']
    
    # Максимум 10 фото
    if len(photos) >= 10:
        await update.message.reply_text("⚠️ Максимум 10 фото. Отправьте оставшуюся информацию текстом.")
        return
    
    # Сохраняем ID фото
    photo_id = update.message.photo[-1].file_id
    photos.append(photo_id)
    
    # Если есть подпись (caption) с текстом анкеты - обрабатываем как полную заявку
    caption = update.message.caption
    if caption and len(caption) > 50:  # Если подпись достаточно длинная
        # Сохраняем текст анкеты
        context.user_data['application_text'] = caption
        
        # Проверяем рабочее время
        if not is_working_hours():
            next_time = get_next_working_time()
            await update.message.reply_text(
                f"Спасибо за ваше обращение!\n\n"
                f"⏰ Сейчас нерабочее время.\n"
                f"Наш график: Пн-Сб, 10:00-22:00\n\n"
                f"{next_time}\n\n"
                f"Ваша анкета сохранена, мы обязательно рассмотрим!",
                reply_markup=main_menu()
            )
            admin_prefix = "⏰ НЕРАБОЧЕЕ ВРЕМЯ\n\n"
        else:
            admin_prefix = ""
        
        # Формируем сообщение для администратора
        reply_hint = "\n\nЧтобы ответить пользователю — нажмите Reply на это сообщение"
        user_id_tag = f"\n[ID:{user.id}]"
        
        admin_message = (
            f"{admin_prefix}"
            f"Новый запрос\n\n"
            f"Username: @{user.username or 'без username'}\n"
            f"Раздел: Для моделей\n"
            f"Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
            f"Анкета:\n{caption}"
            f"{reply_hint}"
            f"{user_id_tag}"
        )
        
        # Отправляем текст анкеты
        try:
            await context.bot.send_message(
                chat_id=GROUP_CHAT_ID,
                message_thread_id=MODELS_THREAD_ID,
                text=admin_message,
                disable_web_page_preview=True
            )
            
            # Отправляем все собранные фото
            for photo_id in photos:
                try:
                    await context.bot.send_photo(
                        chat_id=GROUP_CHAT_ID,
                        photo=photo_id,
                        message_thread_id=MODELS_THREAD_ID
                    )
                except Exception as e:
                    logger.error(f"Ошибка отправки фото: {e}")
            
            logger.info(f"Модельная анкета от {user.id} отправлена с {len(photos)} фото")
        except Exception as e:
            logger.error(f"Ошибка отправки: {e}")
        
        # Ответ пользователю
        if is_working_hours():
            thanks_message = (
                "Спасибо за вашу заявку и уделённое время!\n\n"
                "Мы внимательно изучим предоставлённую информацию.\n"
                "Если ваш типаж заинтересует наше агентство, наши специалисты свяжутся с вами в течение 1–2 недель.\n\n"
                "Если в этот период обратная связь не поступит — не переживайте.\n"
                "Ваши данные остаются в нашей базе, и при появлении подходящих проектов мы обязательно вернёмся к вам.\n\n"
                "Спасибо за доверие к NUDA 🤍\n"
                "Мы ценим ваш интерес и открыты к дальнейшему взаимодействию"
            )
            await update.message.reply_text(thanks_message)
            await update.message.reply_text(
                "Если у вас есть дополнительные вопросы, просто напишите их здесь.\n\n"
                "Или вернитесь в главное меню:",
                reply_markup=main_menu()
            )
        
        # Очищаем данные
        context.user_data.clear()
    else:
        # Просто сохраняем фото, ждём ещё
        await update.message.reply_text(f"✅ Фото {len(photos)}/10 сохранено")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ошибок"""
    logger.error(f"Update {update} caused error {context.error}")

def main():
    """Главная функция запуска бота"""
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN не задан!")
    
    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .connect_timeout(30)
        .read_timeout(30)
        .write_timeout(30)
        .pool_timeout(30)
        .build()
    )
    
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    application.add_handler(MessageHandler(filters.PHOTO, photo_handler))
    
    application.add_error_handler(error_handler)
    
    logger.info("🤖 Бот запущен — всё работает идеально")
    logger.info(f"⏰ Рабочее время: Пн-Сб, 10:00-22:00")
    logger.info(f"📊 Автоответчик для нерабочего времени активен")
    logger.info(f"💬 Функция ответов через Reply активна")
    logger.info(f"📸 Поддержка фото с подписью активна")
    
    application.run_polling(
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES
    )

if __name__ == '__main__':
    main()
