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

# ID группового чата (из https://t.me/c/3159637873/...)
GROUP_CHAT_ID = -1003159637873

# ID тем (threads) в групповом чате
SUPPORT_THREAD_ID = 242
MODELS_THREAD_ID = 241
CUSTOMERS_THREAD_ID = 243

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
    weekday = now.weekday()  # 0=Понедельник, 6=Воскресенье
    current_time = now.time()
    
    # Воскресенье = выходной
    if weekday == 6:
        return False
    
    # Проверка времени
    if WORK_START <= current_time <= WORK_END:
        return True
    
    return False

def get_next_working_time():
    """Получить текст о следующем рабочем времени"""
    now = datetime.now()
    weekday = now.weekday()
    current_time = now.time()
    
    if weekday == 6:  # Воскресенье
        return "Мы ответим в понедельник с 10:00"
    elif current_time < WORK_START:
        return "Мы ответим сегодня с 10:00"
    else:  # После 22:00
        if weekday == 5:  # Суббота
            return "Мы ответим в понедельник с 10:00"
        else:
            return "Мы ответим завтра с 10:00"

def main_menu():
    """Главное меню"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Для заказчиков", callback_data='customer')],
        [InlineKeyboardButton("Для моделей", callback_data='model')],
        [InlineKeyboardButton("Поддержка", callback_data='support')]
    ])

def back_button():
    """Кнопка назад"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("◀️ Назад", callback_data='back')]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    context.user_data.clear()
    
    # Отправляем GIF
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
    
    if query.data == 'customer':
        # Для заказчиков
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
        # Для моделей
        await query.edit_message_text(
            "Здравствуйте, звезда!\n\n"
            "Мы — агентство NUDA.\n"
            "Напишите ваш вопрос — ответим максимально быстро и с любовью ✨",
            reply_markup=back_button()
        )
        context.user_data['section'] = 'Для моделей'
    
    elif query.data == 'support':
        # Поддержка
        await query.edit_message_text(
            "Здравствуйте! Техподдержка NUDA на связи\n\n"
            "Опишите вашу проблему — мы поможем в ближайшее время!",
            reply_markup=back_button()
        )
        context.user_data['section'] = 'Поддержка'
    
    elif query.data == 'back':
        # Возврат в главное меню
        await query.edit_message_text(
            "Выберите раздел:",
            reply_markup=main_menu()
        )
        context.user_data.clear()

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текстовых сообщений"""
    user = update.effective_user
    
    # ========== ОБРАБОТКА ОТВЕТА АДМИНА ==========
    # Админ отвечает через Reply на сообщение бота в группе
    logger.info(f"Проверка: user.id={user.id}, ADMIN_IDS={ADMIN_IDS}, has_reply={bool(update.message.reply_to_message)}")
    
    if user.id in ADMIN_IDS and update.message.reply_to_message:
        replied = update.message.reply_to_message
        logger.info(f"Есть reply. replied.from_user.id={replied.from_user.id}, bot.id={context.bot.id}")
        
        # Проверяем, что это ответ на сообщение от бота
        if replied.from_user.id == context.bot.id:
            replied_text = replied.text or replied.caption or ""
            logger.info(f"Это сообщение от бота! Ищу ID в тексте: {replied_text[:100]}")
            
            # Пытаемся найти ID несколькими способами
            user_id = None
            
            # Способ 1: Явный формат [ID:123456789]
            user_id_match = re.search(r'\[ID:(\d+)\]', replied_text)
            if user_id_match:
                user_id = int(user_id_match.group(1))
                logger.info(f"Найден ID способом 1: {user_id}")
            
            # Способ 2: Если ID не найден, проверяем в replied_text по словам
            if not user_id:
                numbers = re.findall(r'\b(\d{9,})\b', replied_text)
                logger.info(f"Найденные числа: {numbers}")
                if numbers:
                    user_id = int(numbers[-1])  # Берём последнее число (обычно ID)
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
    # Обрабатываем только в личных чатах
    if update.message.chat.type != "private":
        return
    
    section = context.user_data.get('section')
    text = update.message.text
    
    # Если пользователь не в разделе - игнорируем
    if not section:
        return
    
    # Проверка анкеты только для заказчиков
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
    
    # Добавляем подсказку и ID только для Поддержки и Моделей
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
            await context.bot.send_message(
                chat_id=GROUP_CHAT_ID,
                message_thread_id=MODELS_THREAD_ID,
                text=admin_message,
                disable_web_page_preview=True
            )
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
    
    # Ответ пользователю (только в рабочее время)
    if is_working_hours():
        if section == 'Для заказчиков':
            thanks_message = (
                "Благодарим за заполнение анкеты!\n\n"
                "В ближайшее время с вами свяжется наш агент ❤️"
            )
        elif section == 'Поддержка' or section == 'Для моделей':
            thanks_message = (
                "Спасибо! Мы получили ваше сообщение и ответим в ближайшее время ✨"
            )
        else:
            thanks_message = (
                "Спасибо! Мы получили ваше сообщение ✨"
            )
        
        await update.message.reply_text(thanks_message)
        
        # Для поддержки и моделей оставляем возможность продолжить диалог
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
    
    # Очищаем состояние только для заказчиков
    if section == 'Для заказчиков':
        context.user_data.clear()

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ошибок"""
    logger.error(f"Update {update} caused error {context.error}")

def main():
    """Главная функция запуска бота"""
    # Токен бота
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN не задан!")
    
    # Создание приложения
    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .connect_timeout(30)
        .read_timeout(30)
        .write_timeout(30)
        .pool_timeout(30)
        .build()
    )
    
    # Регистрация обработчиков
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    
    # Обработчик ошибок
    application.add_error_handler(error_handler)
    
    logger.info("🤖 Бот запущен — всё работает идеально")
    logger.info(f"⏰ Рабочее время: Пн-Сб, 10:00-22:00")
    logger.info(f"📊 Автоответчик для нерабочего времени активен")
    logger.info(f"💬 Функция ответов через Reply активна")
    
    # Запуск бота
    application.run_polling(
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES
    )

if __name__ == '__main__':
    main()

