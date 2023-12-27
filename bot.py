import os
import requests
import time
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Replace 'YOUR_BOT_TOKEN' with your actual bot token
TOKEN = '5032426994:AAFTz0n2jDGKRAubthsGbCO1u3A01UNydKQ'

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('سلام! برای دانلود فایل، لطفاً لینک مستقیم فایل را ارسال کنید.')

def download_file(update: Update, context: CallbackContext) -> None:
    url = update.message.text
    chat_id = update.message.chat_id

    try:
        response = requests.get(url, stream=True)
        total_size = int(response.headers.get('content-length', 0))
        downloaded_size = 0

        # Send initial download message
        message = context.bot.send_message(chat_id, 'در حال دانلود...')
        context.user_data['message_id'] = message.message_id

        with open('downloaded_file', 'wb') as file:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    file.write(chunk)
                    downloaded_size += len(chunk)
                    percentage = (downloaded_size / total_size) * 100
                    remaining_size = total_size - downloaded_size

                    # Update the existing message with download progress
                    new_content = f'در حال دانلود... {int(percentage)}%\n' \
                                  f'حجم دانلود شده: {downloaded_size / (1024 * 1024):.2f} MB\n' \
                                  f'حجم باقی‌مانده: {remaining_size / (1024 * 1024):.2f} MB'
                    
                    if not context.user_data.get('last_content') or context.user_data['last_content'] != new_content:
                        # Update the existing message with download progress
                        context.bot.edit_message_text(
                            chat_id=chat_id,
                            message_id=context.user_data['message_id'],
                            text=new_content
                        )
                        context.user_data['last_content'] = new_content
                    else:
                        # If content hasn't changed, wait for a short delay
                        time.sleep(1)

        # Upload the downloaded file to Telegram
        with open('downloaded_file', 'rb') as file:
            context.bot.send_document(chat_id, document=file)

        # Send completion message
        context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=context.user_data['message_id'],
            text='دانلود کامل شد!'
        )

    except Exception as e:
        context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=context.user_data['message_id'],
            text=f'خطا: {e}'
        )

    finally:
        os.remove('downloaded_file')

def main() -> None:
    updater = Updater(TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, download_file))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
