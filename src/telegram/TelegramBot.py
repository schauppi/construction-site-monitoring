import logging
from telegram import Update
from telegram import Bot as TelegramBot
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
import dotenv
import os
import requests
import asyncio
import threading
import tempfile
import cv2

from src.logging.logging_config import setup_logging

class Bot:
    """
    Bot class for controlling the Telegram bot.

    Methods:
        start: Starts the bot.
        help_command: Sends the help command.
        echo: Echoes the message.
        start_capture: Starts image capturing.
        stop_capture: Stops image capturing.
        status_capture: Gets the status of image capturing.
        set_interval: Sets the interval for image capturing.
        get_image: Gets the latest image captured.
        get_disk_space: Gets the disk space.
        my_id: Gets the chat ID.
        arm: Arms the cameras.
        disarm: Disarms the cameras.
        run: Runs the bot.
    """

    def __init__(self):
        dotenv.load_dotenv()
        self.token = os.getenv("TELEGRAM")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        setup_logging()
        self.logger = logging.getLogger()
        self.base_route = "http://127.0.0.1:5000"

        self.telegram_bot = TelegramBot(token=self.token)
        self.loop = asyncio.new_event_loop()
        
        self.thread = threading.Thread(target=self.start_asyncio_loop, daemon=True)
        self.thread.start()

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Starts the bot.

        Args:
            update: The update object.
            context: The context object.

        Returns:
            None
        """

        try:
            await context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")
        except Exception as e:
            self.logger.error(f"An error occurred in start function: {e}")


    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Sends the help command.

        Args:
            update: The update object.
            context: The context object.

        Returns:
            None
        """
        try:
            help_text = "You can control me by sending these commands:\n"
            help_text += "/start - Start interacting with the bot\n"
            help_text += "/start_capture - Starting image capturing\n"
            help_text += "/stop_capture - Stopping image capturing\n"
            help_text += "/status_capture - Getting the status of image capturing\n"
            help_text += "/set_interval - Setting the interval for image capturing\n"
            help_text += "/get_image - Getting the latest image captured\n"
            help_text += "/get_disk - Getting the disk space\n"
            help_text += "/myid - Getting your chat ID\n"
            help_text += "/arm - Arming the cameras\n"
            help_text += "/disarm - Disarming the cameras\n"
            help_text += "/restart_dnsmasq - Restarting the dnsmasq service\n"
            await context.bot.send_message(chat_id=update.effective_chat.id, text=help_text)
        except Exception as e:
            self.logger.error(f"An error occurred in help_command function: {e}")

    async def echo(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Echoes the message.

        Args:
            update: The update object.
            context: The context object.

        Returns:
            None
        """
        try:
            self.logger.info(f"Received message: {update.message.text}")
            text = update.message.text
            await context.bot.send_message(chat_id=update.effective_chat.id, text="You said: " + text)
        except Exception as e:
            self.logger.error(f"An error occurred in echo function: {e}")

    async def start_capture(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Starts image capturing.

        Args:
            update: The update object.
            context: The context object.

        Returns:
            None
        """
        try: 
            url = f"{self.base_route}/start"
            response = requests.post(url)
            self.logger.info(f"Start Capture Response: {response.status_code}, {response.json()}")
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Capture started.")
        except Exception as e:
            self.logger.error(f"An error occurred in start_capture function: {e}")

    async def stop_capture(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Stops image capturing.

        Args:
            update: The update object.
            context: The context object.

        Returns:
            None
        """
        try: 
            url = f"{self.base_route}/stop"
            response = requests.post(url)
            self.logger.info(f"Stop Capture Response: {response.status_code}, {response.json()}")
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Capture stopped.")
        except Exception as e:
            self.logger.error(f"An error occurred in start_capture function: {e}")

    async def status_capture(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Gets the status of image capturing.

        Args:
            update: The update object.
            context: The context object.

        Returns:
            None
        """
        try: 
            url = f"{self.base_route}/status"
            response = requests.get(url)
            status_response = response.json()
            status = status_response['status']
            interval = status_response['save_interval']
            self.logger.info(f"Status Capture Response: {response.status_code}, {response.json()}")
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Capture status: " + status + "\n" + "Capture interval: " + str(interval) + " seconds.")
        except Exception as e:
            self.logger.error(f"An error occurred in start_capture function: {e}")

    async def set_interval(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Sets the interval for image capturing.

        Args:
            update: The update object.
            context: The context object.

        Returns:
            None
        """
        try: 
            url = f"{self.base_route}/set_interval"
            interval = update.message.text
            interval = int(interval.split(" ")[1])
            response = requests.post(url, json={'interval': interval})
            self.logger.info(f"Set Interval Response: {response.status_code}, {response.json()}")
            await context.bot.send_message(chat_id=update.effective_chat.id, text="New interval set: " + str(interval) + " seconds.")
        except Exception as e:
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Please provide an interval.")
            self.logger.error(f"An error occurred in set_interval function: {e}")

    async def get_image(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Gets the latest image captured.

        Args:
            update: The update object.
            context: The context object.

        Returns:
            None
        """
        try: 
            url = f"{self.base_route}/get_image"
            response = requests.get(url)
            latest_image_path_0 = response.json()['image_path_0']
            latest_image_path_1 = response.json()['image_path_1']
            self.logger.info(f"Get Image Response: {response.status_code}, {response.json()}")
            await context.bot.send_photo(chat_id=update.effective_chat.id, photo=open(latest_image_path_0, 'rb'))
            await context.bot.send_photo(chat_id=update.effective_chat.id, photo=open(latest_image_path_1, 'rb'))
        except Exception as e:
            self.logger.error(f"An error occurred in get_image function: {e}")

    async def get_disk_space(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Gets the disk space.

        Args:   
            update: The update object.
            context: The context object.

        Returns:
            None
        """
        try:
            url = f"{self.base_route}/disk_space"
            response = requests.get(url)
            total = response.json()['total']
            used = response.json()['used']
            free = response.json()['free']
            total_gb = total / (1024**3)
            used_gb = used / (1024**3)
            free_gb = free / (1024**3)
            self.logger.info(f"Get Disk Space Response: {response.status_code}, {response.json()}")
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Total: {total_gb:.2f} GB\nUsed: {used_gb:.2f} GB\nFree: {free_gb:.2f} GB")
        except Exception as e:
            self.logger.error(f"An error occurred in get_disk_space function: {e}")

    async def my_id(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Gets the chat ID.

        Args:
            update: The update object.
            context: The context object.

        Returns:
            None
        """
        try:
            chat_id = update.effective_chat.id
            self.logger.info(f"Chat ID: {chat_id}")
            await context.bot.send_message(chat_id=chat_id, text=f"Your Chat ID is: {chat_id}")
        except Exception as e:
            self.logger.error(f"An error occurred in my_id function: {e}")

    def start_asyncio_loop(self):
        """
        Starts the asyncio loop.

        Args:
            None

        Returns:
            None
        """
        try:
            asyncio.set_event_loop(self.loop)
            self.loop.run_forever()
        except Exception as e:
            self.logger.error(f"An error occurred in start_asyncio_loop function: {e}")

    async def send_alert(self, message: str, frame=None):
        """
        Sends an alert. 

        Args:
            message: The message to send.
            frame: The frame to send.

        Returns:
            None
        """
        try:
            if frame is not None:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
                    cv2.imwrite(tmp.name, frame)
                    tmp.flush()
                    with open(tmp.name, 'rb') as photo:
                        await self.telegram_bot.send_photo(chat_id=self.chat_id, photo=photo, caption=message)
                os.unlink(tmp.name)
            else:
                await self.telegram_bot.send_message(chat_id=self.chat_id, text=message)
        except Exception as e:
            self.logger.error(f"An error occurred in send_alert function: {e}")

    async def arm(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Arms the cameras.   

        Args:
            update: The update object.
            context: The context object.

        Returns:
            None
        """
        try:
            url = f"{self.base_route}/arm"
            response = requests.post(url)
            self.logger.info(f"Arm Response: {response.status_code}, {response.json()}")
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Cameras armed.")
        except Exception as e:
            self.logger.error(f"An error occurred in arm function: {e}")

    async def disarm(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Disarms the cameras.

        Args:
            update: The update object.
            context: The context object.

        Returns:
            None
        """
        try:
            url = f"{self.base_route}/disarm"
            response = requests.post(url)
            self.logger.info(f"Disarm Response: {response.status_code}, {response.json()}")
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Cameras disarmed.")
        except Exception as e:
            self.logger.error(f"An error occurred in disarm function: {e}")

    async def restart_dnsmasq(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Asynchronously restarts the dnsmasq service via the Flask API.

        Args:
            update: The update object.
            context: The context object.

        Returns:
            None
        """
        try:
            url = f"{self.base_route}/restart-dnsmasq"
            response = requests.post(url)
            self.logger.info(f"Restart Dnsmasq Response: {response.status_code}, {response.json()}")
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Dnsmasq restarted.")
        except Exception as e:
            self.logger.error(f"An error occurred in restart_dnsmasq function: {e}")


    def run(self) -> None:
        """
        Runs the bot.   

        Args:
            None

        Returns:
            None
        """
        application = ApplicationBuilder().token(self.token).build()

        start_handler = CommandHandler('start', self.start)
        application.add_handler(CommandHandler('help', self.help_command))
        application.add_handler(CommandHandler('start_capture', self.start_capture))
        application.add_handler(CommandHandler('stop_capture', self.stop_capture))
        application.add_handler(CommandHandler('status_capture', self.status_capture))
        application.add_handler(CommandHandler('set_interval', self.set_interval))
        application.add_handler(CommandHandler('get_image', self.get_image))
        application.add_handler(CommandHandler('get_disk', self.get_disk_space))
        application.add_handler(CommandHandler('myid', self.my_id))
        application.add_handler(CommandHandler('arm', self.arm))
        application.add_handler(CommandHandler('disarm', self.disarm))
        application.add_handler(CommandHandler('restart_dnsmasq', self.restart_dnsmasq))

        echo_handler = MessageHandler(
            filters.TEXT & ~filters.COMMAND, self.echo)

        application.add_handler(start_handler)
        application.add_handler(echo_handler)

        application.run_polling()



