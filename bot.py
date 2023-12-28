import os
import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from multiprocessing import Process, Manager

TOKEN = '5032426994:AAFTz0n2jDGKRAubthsGbCO1u3A01UNydKQ'
DOWNLOAD_FOLDER = 'downloads'

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Hello! Send me a direct download link to get started.')

def download_file(url, file_path, progress_dict):
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    downloaded_size = 0

    with open(file_path, 'wb') as file, requests.get(url, stream=True) as req:
        for chunk in req.iter_content(chunk_size=1024):
            if chunk:
                file.write(chunk)
                downloaded_size += len(chunk)

                # Update progress in the shared dictionary
                progress_dict['downloaded_size'] = downloaded_size
                progress_dict['total_size'] = total_size

                # Display progress in console
                print(f'Downloading... {downloaded_size}/{total_size} bytes ({(downloaded_size / total_size) * 100:.2f}%)', end='\r')

    # Mark download as complete
    progress_dict['download_complete'] = True
    print('\nDownload complete!')

def upload_to_telegram(file_path, chat_id, context):
    with open(file_path, 'rb') as file:
        context.bot.send_document(chat_id, document=file)

def download_and_upload(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    download_url = update.message.text

    # Create a folder for each user
    user_download_folder = os.path.join(DOWNLOAD_FOLDER, str(user_id))
    os.makedirs(user_download_folder, exist_ok=True)

    # Generate a unique filename
    file_name = os.path.join(user_download_folder, 'video.mp4')

    # Shared dictionary for progress tracking
    progress_dict = Manager().dict({
        'downloaded_size': 0,
        'total_size': 0,
        'download_complete': False
    })

    # Start the download process in parallel
    download_process = Process(target=download_file, args=(download_url, file_name, progress_dict))
    download_process.start()

    # Wait for the download to complete
    download_process.join()

    # Display progress in console for upload
    print('Uploading to Telegram...')
    
    # Upload the file to Telegram
    upload_to_telegram(file_name, chat_id, context)

    print('Upload complete!')

if __name__ == '__main__':
    updater = Updater(token=TOKEN, use_context=True, request_kwargs={'connect_timeout': 15, 'read_timeout': 15})
    dispatcher = updater.dispatcher

    # Handlers
    start_handler = CommandHandler('start', start)
    download_handler = MessageHandler(Filters.text & ~Filters.command, download_and_upload)

    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(download_handler)

    # Start the Bot
    updater.start_polling()
    updater.idle()
