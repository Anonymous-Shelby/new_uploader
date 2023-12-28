import os
import requests
import psutil
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from multiprocessing import Manager

TOKEN = '5032426994:AAFTz0n2jDGKRAubthsGbCO1u3A01UNydKQ'
DOWNLOAD_FOLDER = 'downloads'

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Hello! Send me a direct download link to get started.')

def download_file(url, file_path, progress_dict):
    try:
        with open(file_path, 'wb') as file, requests.get(url, stream=True, timeout=(30, 30)) as req:
            total_size = int(req.headers.get('content-length', 0))
            downloaded_size = 0

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

    except requests.exceptions.HTTPError as e:
        print(f'HTTP Error: {e}')
        # اقدامات مناسب برای مدیریت خطا
    except requests.exceptions.ConnectionError as e:
        print(f'Connection Error: {e}')
        # اقدامات مناسب برای مدیریت خطا
    except requests.exceptions.Timeout as e:
        print(f'Timeout Error: {e}')
        # اقدامات مناسب برای مدیریت خطا
    except requests.exceptions.RequestException as e:
        print(f'Request Error: {e}')
        # اقدامات مناسب برای مدیریت خطا

def upload_to_telegram(file_path, chat_id, context):
    with open(file_path, 'rb') as file:
        try:
            context.bot.send_document(chat_id, document=file, timeout=120)  # افزایش timeout به 120 ثانیه
        except Exception as e:
            print(f'Error during file upload: {str(e)}')
            # اقدامات مناسب برای مدیریت خطا

def get_disk_usage():
    # Get disk usage in GB
    usage = psutil.disk_usage('/')
    return f'Disk Usage: Total: {usage.total / (1024 ** 3):.2f} GB, Used: {usage.used / (1024 ** 3):.2f} GB, Free: {usage.free / (1024 ** 3):.2f} GB'

def send_message(chat_id, message_text, context: CallbackContext):
    context.bot.send_message(chat_id, message_text)

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

    try:
        # Start the download directly (without using multiprocessing)
        download_file(download_url, file_name, progress_dict)

        # Display progress in console for upload
        print('Uploading to Telegram...')
        
        # Upload the file to Telegram
        upload_to_telegram(file_name, chat_id, context)

        print('Upload complete!')

        # Display disk usage information
        disk_usage_info = get_disk_usage()
        context.bot.send_message(chat_id, disk_usage_info)

        # Send download complete message
        send_message(chat_id, 'Download and upload complete!')

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
