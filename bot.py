import os
import requests
from telegram import Bot, InputFile
from telegram.ext import Updater, MessageHandler, Filters, CommandHandler
from tqdm import tqdm

# توکن ربات تلگرام خود را در اینجا قرار دهید
TELEGRAM_BOT_TOKEN = '5032426994:AAFTz0n2jDGKRAubthsGbCO1u3A01UNydKQ'

# دیکشنری برای ذخیره اطلاعات دانلود به صورت گلوبال
downloads = {}
# متغیر برای نگهداری وضعیت دستورات دیگر
command_status = {}

def start(update, context):
    update.message.reply_text("ربات استارت شد!")

def cancel(update, context):
    chat_id = update.message.chat_id
    if chat_id in downloads:
        # حذف اطلاعات دانلود
        del downloads[chat_id]
        # غیرفعال کردن دستور cancel
        command_status[chat_id]['cancel'] = False
        update.message.reply_text("دانلود متوقف شد.")
    else:
        update.message.reply_text("هیچ دانلود فعالی برای لغو وجود ندارد.")

def status(update, context):
    chat_id = update.message.chat_id
    if chat_id in downloads:
        # ارسال پیام با اطلاعات دانلود
        file_size, downloaded_size = downloads[chat_id]
        message = f"حجم فایل: {file_size / (1024 * 1024):.2f} MB\nمقدار دانلود شده: {downloaded_size / (1024 * 1024):.2f} MB"
        update.message.reply_text(message)
    else:
        update.message.reply_text("هیچ دانلود فعالی برای نمایش وضعیت وجود ندارد.")

def download_and_upload_video(update, context):
    # دریافت لینک از پیام
    video_link = update.message.text
    chat_id = update.message.chat_id

    try:
        # بررسی وضعیت دستورات دیگر
        if chat_id in command_status and command_status[chat_id].get('cancel', False):
            update.message.reply_text("دانلود لغو شده است.")
            return

        # دانلود فایل ویدیو
        video_file, file_size = download_video(video_link, update)

        # آپلود فایل به تلگرام
        upload_video_to_telegram(update, context, video_file)

        # حذف اطلاعات دانلود
        del downloads[chat_id]

        # حذف فایل موقت
        os.remove(video_file)

    except Exception as e:
        print(f"Error: {e}")
        update.message.reply_text("مشکلی در دانلود یا آپلود فایل وجود دارد.")
        # در صورت بروز خطا هم دانلود را متوقف کنید
        del downloads[chat_id]

def download_video(video_link, update):
    # ایجاد یک نام فایل موقت
    temp_file_name = "temp_video.mp4"

    # دریافت اندازه فایل
    response = requests.head(video_link)
    file_size = int(response.headers.get('content-length', 0))

    # ذخیره اطلاعات دانلود برای نمایش وضعیت
    chat_id = update.message.chat_id
    downloads[chat_id] = (file_size, 0)

    # نمایش نوار پیشرفت
    with tqdm(total=file_size, unit='B', unit_scale=True, unit_divisor=1024, desc='Downloading') as progress_bar:
        # دانلود فایل ویدیو
        response = requests.get(video_link, stream=True)
        with open(temp_file_name, 'wb') as video_file:
            for chunk in response.iter_content(chunk_size=8192):
                video_file.write(chunk)
                progress_bar.update(len(chunk))
                # به‌روزرسانی مقدار دانلود شده برای نمایش وضعیت
                downloads[chat_id] = (file_size, downloads[chat_id][1] + len(chunk))

    update.message.reply_text("دانلود فایل با موفقیت انجام شد.")
    return temp_file_name, file_size

def upload_video_to_telegram(update, context, video_file):
    # دریافت chat_id
    chat_id = update.message.chat_id

    # ارسال فایل به تلگرام
    context.bot.send_video(chat_id=chat_id, video=open(video_file, 'rb'))

def main():
    # ساخت یک ربات تلگرام
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    updater = Updater(token=TELEGRAM_BOT_TOKEN, use_context=True)

    # ایجاد یک CommandHandler برای دستور start
    start_handler = CommandHandler('start', start)
    updater.dispatcher.add_handler(start_handler)

    # ایجاد یک CommandHandler برای دستور cancel
    cancel_handler = CommandHandler('cancel', cancel)
    updater.dispatcher.add_handler(cancel_handler)

    # ایجاد یک CommandHandler برای دستور status
    status_handler = CommandHandler('status', status)
    updater.dispatcher.add_handler(status_handler)

    # ایجاد یک MessageHandler برای پاسخ به پیام‌های متنی کاربران
    message_handler = MessageHandler(Filters.text & ~Filters.command, download_and_upload_video)
    updater.dispatcher.add_handler(message_handler)

    # شروع ربات
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
