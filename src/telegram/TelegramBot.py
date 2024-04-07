import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
import dotenv
import os
import requests

from src.logging.logging_config import setup_logging


class Bot:

    def __init__(self):
        dotenv.load_dotenv()
        self.token = os.getenv("TELEGRAM")
        setup_logging()
        self.logger = logging.getLogger()
        self.base_route = "http://127.0.0.1:5000"

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        try:
            await context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")
        except Exception as e:
            self.logger.error(f"An error occurred in start function: {e}")


    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        try:
            help_text = "You can control me by sending these commands:\n"
            help_text += "/start - Start interacting with the bot\n"
            help_text += "/start_capture - Starting image capturing\n"
            help_text += "/stop_capture - Stopping image capturing\n"
            help_text += "/status_capture - Getting the status of image capturing\n"
            help_text += "/set_interval - Setting the interval for image capturing\n"
            await context.bot.send_message(chat_id=update.effective_chat.id, text=help_text)
        except Exception as e:
            self.logger.error(f"An error occurred in help_command function: {e}")

    async def echo(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        try:
            self.logger.info(f"Received message: {update.message.text}")
            text = update.message.text
            await context.bot.send_message(chat_id=update.effective_chat.id, text="You said: " + text)
        except Exception as e:
            self.logger.error(f"An error occurred in echo function: {e}")

    async def start_capture(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        try: 
            url = f"{self.base_route}/start"
            response = requests.post(url)
            self.logger.info(f"Start Capture Response: {response.status_code}, {response.json()}")
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Capture started.")
        except Exception as e:
            self.logger.error(f"An error occurred in start_capture function: {e}")

    async def stop_capture(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        try: 
            url = f"{self.base_route}/stop"
            response = requests.post(url)
            self.logger.info(f"Stop Capture Response: {response.status_code}, {response.json()}")
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Capture stopped.")
        except Exception as e:
            self.logger.error(f"An error occurred in start_capture function: {e}")

    async def status_capture(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        try: 
            url = f"{self.base_route}/status"
            response = requests.get(url)
            status = response.json()
            status = status['status']
            self.logger.info(f"Stop Capture Response: {response.status_code}, {response.json()}")
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Capture status: " + status)
        except Exception as e:
            self.logger.error(f"An error occurred in start_capture function: {e}")

    async def set_interval(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        try: 
            url = f"{self.base_route}/set_interval"
            interval = update.message.text
            interval = int(interval.split(" ")[1])
            response = requests.post(url, json={'interval': interval})
            self.logger.info(f"Set Interval Response: {response.status_code}, {response.json()}")
            await context.bot.send_message(chat_id=update.effective_chat.id, text="New interval set.")
        except Exception as e:
            self.logger.error(f"An error occurred in start_capture function: {e}")
    def run(self) -> None:

        application = ApplicationBuilder().token(self.token).build()

        start_handler = CommandHandler('start', self.start)
        application.add_handler(CommandHandler('help', self.help_command))
        application.add_handler(CommandHandler('start_capture', self.start_capture))
        application.add_handler(CommandHandler('stop_capture', self.stop_capture))
        application.add_handler(CommandHandler('status_capture', self.status_capture))
        application.add_handler(CommandHandler('set_interval', self.set_interval))

        echo_handler = MessageHandler(
            filters.TEXT & ~filters.COMMAND, self.echo)

        application.add_handler(start_handler)
        application.add_handler(echo_handler)

        application.run_polling()

if __name__ == '__main__':
    bot = Bot()
    bot.run()