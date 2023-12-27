import os
import requests
from telegram import Bot
from telegram import Update
from telegram import InputFile
from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram.ext import CallbackContext
from tqdm import tqdm

# توکن ربات تلگرام خود را اینجا قرار دهید
BOT_TOKEN = "5032426994:AAFTz0n2jDGKRAubthsGbCO1u3A01UNydKQ"

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('سلام! این ربات لینک مستقیم فایل را دریافت و در تلگرام آپلود می‌کند.')

def download_and_upload(update: Update, context: CallbackContext) -> None:
    # دریافت لینک مستقیم فایل از پیام کاربر
    direct_link = context.args[0] if context.args else None

    if direct_link:
        try:
            # درخواست اطلاعات فایل (حجم)
            response = requests.head(direct_link)
            file_size = int(response.headers.get('Content-Length', 0))

            # درخواست دانلود فایل
            response = requests.get(direct_link, stream=True)
            response.raise_for_status()

            # ذخیره فایل در سرور با نمایش progress bar
            file_path = "downloaded_file"
            with open(file_path, "wb") as file, tqdm(
                    desc="در حال دانلود",
                    total=file_size,
                    unit="B",
                    unit_scale=True,
                    unit_divisor=1024,
            ) as bar:
                for data in response.iter_content(chunk_size=1024):
                    bar.update(len(data))
                    file.write(data)

            # ارسال فایل به تلگرام به عنوان فیلم
            bot = Bot(token=BOT_TOKEN)
            chat_id = update.message.chat_id
            with open(file_path, "rb") as file:
                bot.send_video(chat_id=chat_id, video=file, supports_streaming=True)

            # پاک کردن فایل موقت
            os.remove(file_path)

        except Exception as e:
            update.message.reply_text(f'خطا در دریافت یا ارسال فایل: {e}')
    else:
        update.message.reply_text('لطفاً یک لینک مستقیم فایل را به عنوان پارامتر ارسال کنید.')

def main() -> None:
    updater = Updater(token=BOT_TOKEN)
    dispatcher = updater.dispatcher

    # دریافت دستورهای /start و /download
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("download", download_and_upload, pass_args=True))

    # شروع ربات
    updater.start_polling()

    # ربات را به حالت اجرای دائمی ببرید
    updater.idle()

if __name__ == '__main__':
    main()
