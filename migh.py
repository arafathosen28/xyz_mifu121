import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext
import requests
import json
from datetime import datetime, timedelta
import threading

# লগিং সেটআপ
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# ডেটাবেস সিমুলেশন (বাস্তবে আপনি ডেটাবেস ব্যবহার করুন)
users = {}
admin_id = 6971072737
bot_token = "7702995975:AAGvVO3SYdkkKkBrULOBZk-Sr0F7jYM79jU"
api_key = "870b91dfdb6050f4b1d6fc01bfc8bdcdc1c206f75a90f4c38c477bb004bd4d02"
image_generation_url = "https://api.together.xyz/v1/images/generations"

# ডেইলি লিমিট রিসেট ফাংশন
def reset_daily_limits():
    for user_id in users:
        if users[user_id]["plan"] == "free":
            users[user_id]["image_count"] = 0
    threading.Timer(86400, reset_daily_limits).start()  # 86400 সেকেন্ড = 24 ঘন্টা

# স্টার্ট কমান্ড
def start(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if user_id not in users:
        users[user_id] = {"plan": "free", "referrals": 0, "image_count": 0, "daily_limit": 5, "premium_end_date": None}
        update.message.reply_text("বট আনলক করতে ১ জন বন্ধুকে রেফার করুন এবং রেফার লিঙ্ক দিন।")
    else:
        if users[user_id]["referrals"] >= 1:
            update.message.reply_text("আপনি ইতিমধ্যে ১ জন রেফার করেছেন। /menu কমান্ড ব্যবহার করুন।")
        else:
            update.message.reply_text("বট আনলক করতে ১ জন বন্ধুকে রেফার করুন এবং রেফার লিঙ্ক দিন।")

# মেনু কমান্ড
def menu(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if users[user_id]["referrals"] >= 1:
        keyboard = [
            [InlineKeyboardButton("ইমেজ জেনারেট করুন", callback_data='gen_img')],
            [InlineKeyboardButton("প্রোফাইল", callback_data='profile')],
            [InlineKeyboardButton("চ্যানেল", callback_data='channel')],
            [InlineKeyboardButton("প্ল্যান আপগ্রেড করুন", callback_data='upgrade_plan')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text('মেনু:', reply_markup=reply_markup)
    else:
        update.message.reply_text("বট আনলক করতে ১ জন বন্ধুকে রেফার করুন এবং রেফার লিঙ্ক দিন।")

# ইমেজ জেনারেট কমান্ড
def gen_img(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    user = users[user_id]
    
    if user["plan"] == "premium" and user["premium_end_date"] > datetime.now():
        # প্রিমিয়াম ইউজাররা আনলিমিটেড ইমেজ জেনারেট করতে পারবে
        update.message.reply_text("ইমেজ জেনারেট করা হচ্ছে...")
        prompt = update.message.text
        payload = {
            "model": "black-forest-labs/FLUX.1-schnell-Free", 
            "steps": 4, 
            "n": 2, 
            "height": 768, 
            "width": 1024,
            'prompt': f"{prompt}."
        }
        headers = {
            "accept": "application/json", 
            "content-type": "application/json",
            "authorization": f"Bearer {api_key}"
        }
        response = requests.post(image_generation_url, json=payload, headers=headers).json()
        if 'data' in response and len(response['data']) > 0:
            image_url = response['data'][0]['url']
            update.message.reply_photo(image_url)
        else:
            update.message.reply_text("ইমেজ জেনারেট করতে সমস্যা হয়েছে।")
    elif user["plan"] == "free":
        if user["image_count"] < user["daily_limit"]:
            update.message.reply_text("ইমেজ জেনারেট করা হচ্ছে...")
            prompt = update.message.text
            payload = {
                "model": "black-forest-labs/FLUX.1-schnell-Free", 
                "steps": 4, 
                "n": 2, 
                "height": 768, 
                "width": 1024,
                'prompt': f"{prompt}."
            }
            headers = {
                "accept": "application/json", 
                "content-type": "application/json",
                "authorization": f"Bearer {api_key}"
            }
            response = requests.post(image_generation_url, json=payload, headers=headers).json()
            if 'data' in response and len(response['data']) > 0:
                image_url = response['data'][0]['url']
                update.message.reply_photo(image_url)
                users[user_id]["image_count"] += 1
            else:
                update.message.reply_text("ইমেজ জেনারেট করতে সমস্যা হয়েছে।")
        else:
            update.message.reply_text(f"আপনার দৈনিক লিমিট শেষ হয়েছে। আজ আপনি {user['daily_limit']} টি ইমেজ জেনারেট করতে পারেন।")

# অ্যাডমিন প্যানেল
def admin_panel(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if user_id == admin_id:
        update.message.reply_text("অ্যাডমিন প্যানেল:\n/notify_all - সকল ইউজারকে নোটিশ পাঠান\n/notify_user - নির্দিষ্ট ইউজারকে নোটিশ পাঠান\n/ban_user - ইউজার বান করুন\n/unban_user - ইউজার আনবান করুন\n/set_referral - রেফার মান সেট করুন\n/set_daily_limit - দৈনিক লিমিট সেট করুন\n/add_admin - অ্যাডমিন যোগ করুন\n/remove_admin - অ্যাডমিন সরান\n/list_admins - অ্যাডমিন তালিকা দেখুন\n/view_user - ইউজার ডিটেইলস দেখুন\n/upgrade_user - ইউজার প্ল্যান আপগ্রেড করুন")
    else:
        update.message.reply_text("আপনি অ্যাডমিন নন।")

# ইউজার ডিটেইলস দেখান
def view_user(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if user_id == admin_id:
        try:
            target_user_id = int(context.args[0])
            if target_user_id in users:
                user = users[target_user_id]
                plan = user["plan"]
                referrals = user["referrals"]
                image_count = user["image_count"]
                daily_limit = user["daily_limit"]
                premium_end_date = user["premium_end_date"]
                update.message.reply_text(f"ইউজার আইডি: {target_user_id}\nপ্ল্যান: {plan}\nরেফার: {referrals}\nইমেজ কাউন্ট: {image_count}\nদৈনিক লিমিট: {daily_limit}\nপ্রিমিয়াম শেষের তারিখ: {premium_end_date}")
            else:
                update.message.reply_text("ইউজার খুঁজে পাওয়া যায়নি।")
        except (IndexError, ValueError):
            update.message.reply_text("ইউজার আইডি দিন।")
    else:
        update.message.reply_text("আপনি অ্যাডমিন নন।")

# ইউজার প্ল্যান আপগ্রেড
def upgrade_user(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if user_id == admin_id:
        try:
            target_user_id = int(context.args[0])
            plan_duration = int(context.args[1])  # দিনে
            if target_user_id in users:
                users[target_user_id]["plan"] = "premium"
                users[target_user_id]["premium_end_date"] = datetime.now() + timedelta(days=plan_duration)
                update.message.reply_text(f"ইউজার {target_user_id} কে {plan_duration} দিনের জন্য প্রিমিয়াম প্ল্যানে আপগ্রেড করা হয়েছে।")
            else:
                update.message.reply_text("ইউজার খুঁজে পাওয়া যায়নি।")
        except (IndexError, ValueError):
            update.message.reply_text("ইউজার আইডি এবং প্ল্যান ডিউরেশন দিন।")
    else:
        update.message.reply_text("আপনি অ্যাডমিন নন।")

def main() -> None:
    updater = Updater(bot_token)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("menu", menu))
    dispatcher.add_handler(CommandHandler("gen_img", gen_img))
    dispatcher.add_handler(CommandHandler("adminPanel", admin_panel))
    dispatcher.add_handler(CommandHandler("view_user", view_user))
    dispatcher.add_handler(CommandHandler("upgrade_user", upgrade_user))

    # ডেইলি লিমিট রিসেট শুরু করুন
    reset_daily_limits()

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
