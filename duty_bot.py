import os
from datetime import datetime, timedelta
from openpyxl import load_workbook

from telegram import Update, BotCommand
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("8711787715:AAFEQ1GnFsR2aqRGZXRDQyibG2LTh-3iQmM")
EXCEL_FILE = "grafik.xlsx"


async def post_init(app):
    await app.bot.set_my_commands([
        BotCommand("start", "Запуск бота"),
        BotCommand("today", "Дежурный сегодня"),
        BotCommand("tomorrow", "Дежурный завтра"),
        BotCommand("week", "График на неделю"),
        BotCommand("month", "График на месяц"),
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Бот дежурств готов.\n\n"
        "Отправьте Excel-файл с графиком.\n\n"
        "Команды:\n"
        "/today - дежурный сегодня\n"
        "/tomorrow - дежурный завтра\n"
        "/week - график на неделю\n"
        "/month - график на месяц"
    )


async def upload_excel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document

    if not document.file_name.endswith(".xlsx"):
        await update.message.reply_text("Отправьте Excel файл в формате .xlsx")
        return

    file = await document.get_file()
    await file.download_to_drive(EXCEL_FILE)

    await update.message.reply_text("✅ График загружен. Теперь напишите /today")


def find_duty(target_date):
    if not os.path.exists(EXCEL_FILE):
        return "Сначала загрузите Excel-файл."

    wb = load_workbook(EXCEL_FILE, data_only=True)
    ws = wb.active

    result = []

    for row in ws.iter_rows(min_row=2):
        name = row[0].value

        if not name:
            continue

        for cell in row[1:8]:
            value = cell.value

            if isinstance(value, datetime):
                cell_date = value.date()
            else:
                try:
                    cell_date = datetime.strptime(str(value), "%d.%m.%Y").date()
                except:
                    continue

            if cell_date == target_date:
                result.append(str(name))

    if not result:
        return f"На {target_date.strftime('%d.%m.%Y')} дежурный не найден."

    text = f"📅 {target_date.strftime('%d.%m.%Y')}\n"
    text += "👤 Дежурный:\n"

    for name in result:
        text += f"• {name}\n"

    return text


async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(find_duty(datetime.now().date()))


async def tomorrow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(find_duty((datetime.now() + timedelta(days=1)).date()))


async def week(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "📅 График на 7 дней:\n\n"

    for i in range(7):
        day = datetime.now().date() + timedelta(days=i)
        text += find_duty(day) + "\n"

    await update.message.reply_text(text)


async def month(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "📅 График на 30 дней:\n\n"

    for i in range(30):
        day = datetime.now().date() + timedelta(days=i)
        text += find_duty(day) + "\n"

    await update.message.reply_text(text)


if not TOKEN:
    raise ValueError("BOT_TOKEN не найден. Добавьте BOT_TOKEN в Environment Variables на Render.")

app = ApplicationBuilder().token(TOKEN).post_init(post_init).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("today", today))
app.add_handler(CommandHandler("tomorrow", tomorrow))
app.add_handler(CommandHandler("week", week))
app.add_handler(CommandHandler("month", month))
app.add_handler(MessageHandler(filters.Document.FileExtension("xlsx"), upload_excel))

app.run_polling()
