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

# ID администратора (@zhdanova_eliz)
ADMIN_ID = 8326248354

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
    if user.id == ADMIN_ID and update.message.reply_to_message:
        replied_message = update.message.reply_to_message
        
        # Проверяем, что это reply на сообщение от бота
        if replied_message.from_user.id == context.bot.id:
            replied_text = replied_message.text
            
            try:
                # Ищем скрытый ID пользователя в конце сообщения
                user_id_match = re.search(r'\[ID:(\d+)\]', replied_text)
                
                if user_id_match:
                    target_user_id = int(user_id_match.group(1))
                    admin_response = update.message.text
                    
                    # Отправляем ответ пользователю БЕЗ Markdown
                    await context.bot.send_message(
                        chat_id=target_user_id,
                        text=f"💬 Ответ от NUDA Agency:\n\n{admin_response}\n\nЕсли у вас есть ещё вопросы, просто напишите здесь"
                    )
                    
                    # Подтверждение админу
                    await update.message.reply_text(
                        f"✅ Ответ отправлен пользователю"
                    )
                    
                    logger.info(f"Админ ответил пользователю {target_user_id}")
                    return
                else:
                    await update.message.reply_text(
                        "❌ Не удалось найти ID пользователя в сообщении"
                    )
                    return
                    
            except Exception as e:
                logger.error(f"Ошибка при обработке ответа админа: {e}")
                await update.message.reply_text(
                    "❌ Ошибка при отправке ответа. Попробуйте ещё раз."
                )
                return
    
    # ========== ОБЫЧНАЯ ОБРАБОТКА СООБЩЕНИЙ ==========
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
    
    # Добавляем подсказку и скрытый ID только для Поддержки и Моделей
    if section in ['Поддержка', 'Для моделей']:
        reply_hint = f"\n💡 Чтобы ответить, нажмите Reply на это сообщение"
        user_id_tag = f"\n[ID:{user.id}]"  # Скрытый тег для поиска
    
    admin_message = (
        f"{admin_prefix}"
        f"📨 Новый запрос\n\n"
        f"👤 Username: @{user.username or 'без username'}\n"
        f"📂 Раздел: {section}\n"
        f"🕐 Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
        f"Сообщение:\n{text}"
        f"{reply_hint}"
        f"{user_id_tag}"
    )
    
    # Отправляем в зависимости от раздела БЕЗ форматирования
    try:
        if section == 'Поддержка':
            await context.bot.send_message(
                chat_id=GROUP_CHAT_ID,
                message_thread_id=SUPPORT_THREAD_ID,
                text=admin_message
            )
        elif section == 'Для моделей':
            await context.bot.send_message(
                chat_id=GROUP_CHAT_ID,
                message_thread_id=MODELS_THREAD_ID,
                text=admin_message
            )
        elif section == 'Для заказчиков':
            # Отправляем в личку @zhdanova_eliz (ADMIN_ID)
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=admin_message
            )
            # Дублируем в группу
            await context.bot.send_message(
                chat_id=GROUP_CHAT_ID,
                message_thread_id=CUSTOMERS_THREAD_ID,
                text=admin_message
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

