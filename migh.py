from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext
import requests
import logging
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
        update.message.reply_text("মেনু:\n/gen_img - ইমেজ জেনারেট করুন\n/profile - প্রোফাইল দেখুন\n/upgrade_plan - প্ল্যান আপগ্রেড করুন")
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

def main() -> None:
    # নতুন ভার্সনের জন্য Updater এর পরিবর্তে Application ব্যবহার করুন
    application = Application.builder().token(bot_token).build()

    # কমান্ড হ্যান্ডলার যোগ করুন
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("menu", menu))
    application.add_handler(CommandHandler("gen_img", gen_img))

    # ডেইলি লিমিট রিসেট শুরু করুন
    reset_daily_limits()

    # বট চালু করুন
    application.run_polling()

if __name__ == '__main__':
    main()
