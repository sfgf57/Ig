import os
import sys
import time
import threading
import instaloader
import re
import asyncio
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.error import BadRequest
from telegram.constants import ChatMemberStatus

# Replace with your bot token
TELEGRAM_BOT_TOKEN = '7755960315:AAF2COi87xVhLDuXrVdSJlMxYDsNZ74'  

# Replace with your channel details
CHANNEL_ID = -1002309527167  # Your channel's numeric ID
CHANNEL_LINK = "https://t.me/+_ivjK2qY6eI0NzY9"  # Your channel's invite link

# Initialize Instaloader
loader = instaloader.Instaloader()

# Maximum caption length for Telegram
MAX_CAPTION_LENGTH = 1000

# Function to check if a message is a valid Instagram Reels link
def is_instagram_reels_link(text):
    return bool(re.match(r"(https?://)?(www\.)?instagram\.com/reel[\w\-]+", text))

# Check if the user is in the authorized channel
async def is_user_in_channel(user_id, context: ContextTypes.DEFAULT_TYPE):
    try:
        member = await context.bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in (ChatMemberStatus.MEMBER, ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR)
    except BadRequest:
        return False

# Centralized access check
async def check_access(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_user_in_channel(user_id, context):
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("✅ JOIN CHANNEL", url=CHANNEL_LINK)]])
        await update.message.reply_text(" IS Bot Ko Use Karne Ke Liye Hamara Channel Join Kare .", reply_markup=keyboard)
        return False
    return True

# Start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_access(update, context):
        return
    await update.message.reply_text("Hello! Send me an Instagram Reels link, and I'll download it for you!")

# Instagram video downloader
async def download_instagram_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_access(update, context):
        return

    link = update.message.text.strip()

    if not link.startswith("http"):
        return  

    if not is_instagram_reels_link(link):
        await update.message.reply_text("Please send a valid Instagram Reels link.")
        return

    waiting_message = await update.message.reply_text("Downloading... please wait...")

    try:
        shortcode = link.split("/")[-2]
        post = instaloader.Post.from_shortcode(loader.context, shortcode)

        caption = post.caption if post.caption else ""
        caption_with_signature = f"{caption}\n\n©️ @InstagramVideoDownloder_bot"
        if len(caption_with_signature) > MAX_CAPTION_LENGTH:
            caption_with_signature = caption_with_signature[:MAX_CAPTION_LENGTH - 10] + "…\n\n©️ @InstagramVideoDownloder_bot"

        target_dir = "downloads"
        os.makedirs(target_dir, exist_ok=True)

        loader.download_post(post, target=target_dir)

        video_path = None
        for file in os.listdir(target_dir):
            if file.endswith(".mp4"):
                video_path = os.path.join(target_dir, file)
                break

        if video_path:
            with open(video_path, "rb") as video_file:
                await update.message.reply_video(video=video_file, caption=caption_with_signature)

            os.remove(video_path)

        await context.bot.delete_message(chat_id=update.message.chat_id, message_id=waiting_message.message_id)

    except Exception as e:
        await update.message.reply_text(f"Error downloading video: {e}")

# Restart the bot process
def restart_bot():
    print("Restarting bot now...")
    python = sys.executable
    os.execv(python, [python] + sys.argv)

# Start background restart timer
def start_restart_timer(hours=2):
    seconds = hours * 60 * 60
    threading.Timer(seconds, restart_bot).start()

# Main function to run the bot
def main():
    print("Bot started.")
    start_restart_timer(2)  # Restart every 2 hours

    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_instagram_video))

    application.run_polling()

if __name__ == "__main__":
    main()
