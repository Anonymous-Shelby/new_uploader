import wget
import time

import telebot

bot = telebot.TeleBot("2084351753:AAFz2Rzdy2m7lm7ODq72hKGsladDczSzyg0")

@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, "سلام! برای شروع دانلود، لطفاً یک لینک دانلود مستقیم را ارسال کنید.")

@bot.message_handler(content_types=["text"])
def download(message):
    url = message.text
    filename = url.split("/")[-1]

    response = wget.download(url, filename)

    if response.status_code != 0:
        bot.send_message(message.chat.id, "خطا در دانلود.")
        return

    total_size = response.info().get("Content-Length")
    downloaded_size = 0

    with open(filename, "wb") as f:
        for chunk in response.iter_content(chunk_size=1024):
            downloaded_size += len(chunk)
            f.write(chunk)

            progress = downloaded_size / total_size

            # فقط یکبار پیام را ارسال کن
            if not hasattr(bot, "progress_message"):
                bot.progress_message = bot.send_message(message.chat.id, f"دانلود در حال انجام است... {progress * 100:.2f}%")

            # فقط مقدار نوار پیشرفت را آپدیت کن
            bot.edit_message_text(bot.progress_message, f"دانلود در حال انجام است... {progress * 100:.2f}%")

    bot.send_message(message.chat.id, "دانلود با موفقیت انجام شد.")

bot.polling()
