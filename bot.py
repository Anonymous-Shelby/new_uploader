import os
import requests
from telegram import Bot, InputFile
from telegram.ext import Updater, MessageHandler, Filters
from tqdm import tqdm

# توکن ربات تلگرام خود را در اینجا قرار دهید
TELEGRAM_BOT_TOKEN = '5032426994:AAFTz0n2jDGKRAubthsGbCO1u3A01UNydKQ'

def download_and_upload_video(update, context):
    # دریافت لینک از پیام
    video_link = update.message.text

    try:
        # دانلود فایل ویدیو
        video_file = download_video(video_link, update)

        # آپلود فایل به تلگرام
        upload_video_to_telegram(update, context, video_file)

        # حذف فایل موقت
        os.remove(video_file)

    except Exception as e:
        print(f"Error: {e}")
        update.message.reply_text("مشکلی در دانلود یا آپلود فایل وجود دارد.")

def download_video(video_link, update):
    # ایجاد یک نام فایل موقت
    temp_file_name = "temp_video.mp4"

    # دریافت اندازه فایل
    response = requests.head(video_link)
    file_size = int(response.headers.get('content-length', 0))

    # نمایش نوار پیشرفت
    with tqdm(total=file_size, unit='B', unit_scale=True, unit_divisor=1024, desc='Downloading') as progress_bar:
        # دانلود فایل ویدیو
        response = requests.get(video_link, stream=True)
        with open(temp_file_name, 'wb') as video_file:
            for chunk in response.iter_content(chunk_size=8192):
                video_file.write(chunk)
                progress_bar.update(len(chunk))

    update.message.reply_text("دانلود فایل با موفقیت انجام شد.")
    return temp_file_name

def upload_video_to_telegram(update, context, video_file):
    # دریافت chat_id
    chat_id = update.message.chat_id

    # ارسال فایل به تلگرام
    context.bot.send_video(chat_id=chat_id, video=InputFile(video_file))

def main():
    # ساخت یک ربات تلگرام
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    updater = Updater(token=TELEGRAM_BOT_TOKEN, use_context=True)

    # ایجاد یک MessageHandler برای پاسخ به پیام‌های متنی کاربران
    message_handler = MessageHandler(Filters.text & ~Filters.command, download_and_upload_video)
    updater.dispatcher.add_handler(message_handler)

    # شروع ربات
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
