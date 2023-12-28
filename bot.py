import os
import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from urllib.parse import urlparse
from pathlib import Path
from tqdm import tqdm

TOKEN = '2084351753:AAHFrBEaGJRquO3GpE7nMg0fS3oWC_hIz2I'
DOWNLOAD_FOLDER = 'downloads'

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Hello! Send me a direct download link to get started.')

def download_and_upload(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    download_url = update.message.text

    # Validate URL
    parsed_url = urlparse(download_url)
    if not parsed_url.scheme or not parsed_url.netloc:
        context.bot.send_message(chat_id, 'Invalid URL. Please provide a valid direct download link.')
        return

    # Create a folder for each user
    user_download_folder = os.path.join(DOWNLOAD_FOLDER, str(user_id))
    Path(user_download_folder).mkdir(parents=True, exist_ok=True)

    # Generate a unique filename
    file_name = os.path.join(user_download_folder, 'video.mp4')

    try:
        # Download the file
        with requests.get(download_url, stream=True, timeout=(30, 30)) as req, open(file_name, 'wb') as file:
            total_size = int(req.headers.get('content-length', 0))
            uploaded_size = 0
            last_percentage = 0
            message = context.bot.send_message(chat_id, f'Uploading... {uploaded_size}/{total_size} bytes (0.00%)')

            for chunk in tqdm(req.iter_content(chunk_size=1024), total=total_size // 1024, unit='KB', unit_scale=True):
                if chunk:
                    file.write(chunk)
                    uploaded_size += len(chunk)
                    percentage = (uploaded_size / total_size) * 100

                    # Check if the percentage has changed significantly
                    if abs(percentage - last_percentage) >= 1.0:
                        context.bot.edit_message_text(
                            chat_id=chat_id,
                            message_id=message.message_id,
                            text=f'Uploading... {uploaded_size}/{total_size} bytes ({percentage:.2f}%)'
                        )
                        last_percentage = percentage

        print('\nDownload complete!')

        # Upload the file to Telegram
        with open(file_name, 'rb') as file:
            context.bot.send_document(chat_id, document=file, timeout=120)

        print('Upload complete!')

        # Send a completion message
        context.bot.send_message(chat_id, 'Download and upload complete!')

    except Exception as e:
        context.bot.send_message(chat_id, f'Error: {str(e)}')

if __name__ == '__main__':
    updater = Updater(token=TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    # Handlers
    start_handler = CommandHandler('start', start)
    download_handler = MessageHandler(Filters.text & ~Filters.command, download_and_upload)

    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(download_handler)

    # Start the Bot
    updater.start_polling()
    updater.idle()
