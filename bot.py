import os
import requests
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, CallbackContext, Filters
from tqdm import tqdm
import threading
import time

# توکن ربات تلگرام خود را اینجا قرار دهید
BOT_TOKEN = "5032426994:AAFTz0n2jDGKRAubthsGbCO1u3A01UNydKQ"

# وضعیت‌های مختلف مکالمه
DOWNLOAD, IN_PROGRESS = range(2)

def start(update: Update, context: CallbackContext) -> int:
    update.message.reply_text('سلام! این ربات لینک مستقیم فایل را دریافت و در تلگرام آپلود می‌کند. '
                              'لطفاً لینک مستقیم فایل خود را ارسال کنید.')

    return DOWNLOAD

def download_and_upload(update: Update, context: CallbackContext) -> int:
    # دریافت لینک مستقیم فایل از پیام کاربر
    direct_link = update.message.text

    if direct_link:
        try:
            # درخواست اطلاعات فایل (حجم)
            response = requests.head(direct_link)
            file_size = int(response.headers.get('Content-Length', 0))

            # ایجاد یک کیبورد شیشه‌ای برای نمایش پیشرفت
            keyboard = [[InlineKeyboardButton("لغو دانلود", callback_data='cancel')]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            # ارسال پیام شروع دانلود به همراه کیبورد شیشه‌ای
            update.message.reply_text(f'دانلود فایل شروع شد...\nحجم فایل: {file_size / (1024 * 1024):.2f} MB',
                                      reply_markup=reply_markup)

            # ذخیره فایل در سرور با نمایش progress bar
            file_path = "downloaded_file"
            with open(file_path, "wb") as file:
                for data in requests.get(direct_link, stream=True).iter_content(chunk_size=1024):
                    file.write(data)

                    # ارسال پیام به روزرسانی پیشرفت
                    completed_size = os.path.getsize(file_path)
                    progress = (completed_size / file_size) * 100
                    update.message.edit_text(
                        f'در حال دانلود...\nحجم فایل: {file_size / (1024 * 1024):.2f} MB\n'
                        f'درصد: {progress:.2f}%',
                        reply_markup=reply_markup
                    )

            # ارسال فایل به تلگرام به عنوان فیلم
            chat_id = update.message.chat_id
            with open(file_path, "rb") as file:
                context.bot.send_video(chat_id=chat_id, video=file, supports_streaming=True)

            # پاک کردن فایل موقت
            os.remove(file_path)

            # پیام پایان دانلود
            update.message.edit_text('دانلود با موفقیت انجام شد!')

        except Exception as e:
            update.message.reply_text(f'خطا در دریافت یا ارسال فایل: {e}')
    else:
        update.message.reply_text('لطفاً یک لینک مستقیم فایل را به عنوان پارامتر ارسال کنید.')

    return ConversationHandler.END

def cancel(update: Update, context: CallbackContext) -> int:
    # ارسال پیام لغو به کاربر
    update.callback_query.answer('دانلود لغو شد.')

    return ConversationHandler.END

def main() -> None:
    updater = Updater(token=BOT_TOKEN)
    dispatcher = updater.dispatcher

    # استفاده از ConversationHandler برای مدیریت وضعیت مکالمه
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            DOWNLOAD: [MessageHandler(Filters.text & ~Filters.command, download_and_upload)],
        },
        fallbacks=[CallbackQueryHandler(cancel, pattern='^cancel$')], 

        # fallbacks=[CallbackQueryHandler(cancel, pattern='^cancel$')],
    )

    dispatcher.add_handler(conv_handler)

    # شروع ربات
    updater.start_polling()

    # ربات را به حالت اجرای دائمی ببرید
    updater.idle()

if __name__ == '__main__':
    main()
