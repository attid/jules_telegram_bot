"""
Telegram Bot for Jules API monitoring.
"""

import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, html
from aiogram.filters import Command
from aiogram.types import Message
from dotenv import load_dotenv

from jules_client import JulesClient

# Load environment variables
load_dotenv()

TG_TOKEN = os.getenv("TG_TOKEN")
JULES_TOKEN = os.getenv("JULES_TOKEN")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")

# Configure logging
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)

# Initialize dependencies
if not TG_TOKEN or not JULES_TOKEN or not ADMIN_CHAT_ID:
    logger.error("Missing environment variables. Please check .env file.")
    sys.exit(1)

bot = Bot(token=TG_TOKEN)
dp = Dispatcher()
jules_client = JulesClient(api_key=JULES_TOKEN)

# Global state for monitoring
MONITORING_ACTIVE = False
MONITORING_TASK_REF = None
SESSION_STATES = {}  # Key: session_id, Value: state string

@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Handle /start command."""
    await message.answer(
        "Hello! I am the Jules Monitoring Bot.\n"
        "Commands:\n"
        "/list - List recent sessions\n"
        "/monitor - Start monitoring sessions for 1 hour"
    )

@dp.message(Command("list"))
async def cmd_list(message: Message):
    """Handle /list command."""
    if str(message.chat.id) != str(ADMIN_CHAT_ID):
        await message.answer("Unauthorized.")
        return

    await message.answer("Fetching sessions...")

    # Run blocking call in a separate thread
    data = await asyncio.to_thread(jules_client.list_sessions, page_size=10)
    sessions = data.get("sessions", [])

    if not sessions:
        await message.answer("No sessions found.")
        return

    response_lines = [html.bold("Recent Sessions:")]
    for session in sessions:
        s_id = session.get("id", "Unknown ID")
        s_title = session.get("title", "No Title")
        # Ensure we display clean ID
        response_lines.append(f"🆔 {html.code(s_id)}\nTitle: {html.quote(s_title)}\n")

    await message.answer("\n".join(response_lines), parse_mode="HTML")

async def monitoring_loop():
    """Background task to monitor sessions for changes."""
    global MONITORING_ACTIVE
    logger.info("Starting monitoring loop...")

    end_time = datetime.now() + timedelta(hours=1)

    while datetime.now() < end_time and MONITORING_ACTIVE:
        logger.info("Starting monitoring cycle...")
        try:
            # 1. Fetch recent sessions (blocking)
            data = await asyncio.to_thread(jules_client.list_sessions, page_size=10)
            sessions = data.get("sessions", [])

            changes_detected = []

            for session in sessions:
                s_id = session.get("id")
                s_title = session.get("title", "No Title")
                s_state = session.get("state", "UNKNOWN")

                if not s_id:
                    continue

                # Log found session and its status to console
                logger.info(f"Found session {s_id} ({s_title}) with status: {s_state}")

                previous_state = SESSION_STATES.get(s_id)
                should_notify = False

                # Condition 1: Critical status on first sight
                if previous_state is None:
                    if s_state in ["AWAITING_PLAN_APPROVAL", "AWAITING_USER_FEEDBACK"]:
                        should_notify = True

                # Condition 2: State change
                elif s_state != previous_state:
                    should_notify = True

                if should_notify:
                    changes_detected.append(f"Session: {html.quote(s_title)} ({html.code(s_id)})\nStatus: {html.bold(s_state)}")

                # Update state
                SESSION_STATES[s_id] = s_state

            # 4. Notify if changes
            if changes_detected:
                msg = html.bold("Updates:") + "\n" + "\n".join(changes_detected)
                await bot.send_message(chat_id=ADMIN_CHAT_ID, text=msg, parse_mode="HTML")

        except Exception as e:
            logger.error("Error in monitoring loop: %s", e)

        # Wait for 60 seconds
        await asyncio.sleep(60)

    # Finished
    MONITORING_ACTIVE = False
    await bot.send_message(chat_id=ADMIN_CHAT_ID, text="Monitoring finished (1 hour completed).")

@dp.message(Command("monitor"))
async def cmd_monitor(message: Message):
    """Handle /monitor command."""
    global MONITORING_ACTIVE, MONITORING_TASK_REF

    if str(message.chat.id) != str(ADMIN_CHAT_ID):
        await message.answer("Unauthorized.")
        return

    if MONITORING_ACTIVE:
        await message.answer("Monitoring is already active.")
        return

    MONITORING_ACTIVE = True
    await message.answer(
        "Monitoring started. I will check for changes every minute for the next hour."
    )

    # Create background task
    MONITORING_TASK_REF = asyncio.create_task(monitoring_loop())

async def main():
    """Main entry point."""
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
