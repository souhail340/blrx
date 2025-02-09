import telebot
from telebot import types
import requests
import json
from datetime import datetime, timedelta
import sys

# Configurer l'encodage UTF-8 pour éviter les erreurs Unicode
sys.stdout.reconfigure(encoding='utf-8')

# Token du bot
TOKEN = "7518483817:AAFM0i1k1ZNy03665qt8Q0o4BYqluGfszec"
bot = telebot.TeleBot(TOKEN)

# Informations du propriétaire
owner_id = 6927323442  # Remplace par ton ID Telegram
owner_user = "@Souhail_oukili20"  # Ton username
activated_users = set()
user_activation_dates = {}

# Fonction pour charger les données à partir du fichier JSON
def load_data():
    global activated_users, user_activation_dates
    try:
        with open("activated_users.json", "r") as file:
            data = json.load(file)
            # Vérification du format du fichier JSON
            if "users" in data and "expiration_dates" in data:
                activated_users = set(data["users"])
                # Conversion des dates d'expiration en objets datetime
                user_activation_dates = {
                    int(user_id): datetime.fromisoformat(expiration_date)
                    for user_id, expiration_date in data["expiration_dates"].items()
                }
    except FileNotFoundError:
        # Si le fichier n'existe pas, initialiser les données vides
        activated_users = set()
        user_activation_dates = {}

# Fonction pour sauvegarder les données dans le fichier JSON
def save_data():
    data = {
        "users": list(activated_users),
        "expiration_dates": {user_id: expiration_date.isoformat() for user_id, expiration_date in user_activation_dates.items()}
    }
    with open("activated_users.json", "w") as file:
        json.dump(data, file, indent=4)

# Fonction pour obtenir les infos TikTok
def get_tiktok_info(username):
    try:
        res = requests.post(
            "https://ttpub.linuxtech.io:5004/api/search",
            data=json.dumps({"username": username}),
            headers={
                'Host': "ttpub.linuxtech.io:5004",
                'User-Agent': "Dart/3.5 (dart:io)",
                'Accept-Encoding': "gzip",
                'Content-Type': "application/json"
            }
        )
        sid = res.json()['user']["sid"]

        response = requests.post(
            "https://ttpub.linuxtech.io:5004/api/search_by_sid_build_request",
            data=json.dumps({"sid": sid, "count_requests": 3}),
            headers={
                'Host': "ttpub.linuxtech.io:5004",
                'User-Agent': "Dart/3.5 (dart:io)",
                'Accept-Encoding': "gzip",
                'Content-Type': "application/json"
            }
        ).json()

        url2 = response['request'][0]["url"]
        head = eval(response['request'][0]["headers"])
        data = requests.get(url2, headers=head).json()

        return data

    except Exception as e:
        return {"error": str(e)}

# Commande pour afficher les utilisateurs activés
@bot.message_handler(commands=['acu'])
def working(message):
    user_id = message.from_user.id
    bot.send_message(user_id, text=f"Utilisateurs activés : {activated_users}")

# Commande /start avec vérification d'activation
@bot.message_handler(commands=['start'])
def work(message):
    user_id = message.from_user.id
    if user_id == owner_id or user_id in activated_users:
        bot.reply_to(message, "✅ Bot activé pour vous !")
    else:
        bot.reply_to(message, f"🚫 Accès refusé. Contactez {owner_user} pour activer le bot.")

# Commande pour gérer l'activation et désactivation des utilisateurs
@bot.message_handler(commands=['activate', 'deactivate'])
def manage_users(message):
    if message.from_user.id == owner_id:
        if message.text.startswith("/activate"):
            msg = bot.send_message(message.chat.id, "📌 Combien de jours voulez-vous pour l'activation ? (Par exemple : 7, 30, 60)")
            bot.register_next_step_handler(msg, ask_activation_duration)
        elif message.text.startswith("/deactivate"):
            msg = bot.send_message(message.chat.id, "📌 Envoyez l'ID Telegram de l'utilisateur à désactiver :")
            bot.register_next_step_handler(msg, unactivate_user)
    else:
        bot.reply_to(message, "❌ Accès refusé. Seul l'admin peut exécuter cette commande.")

# Fonction pour demander la durée de l'activation
def ask_activation_duration(message):
    try:
        days = int(message.text)
        if days > 0:
            msg = bot.send_message(message.chat.id, "📌 Envoyez l'ID Telegram de l'utilisateur à activer :")
            bot.register_next_step_handler(msg, lambda msg: activate_user(msg, days))
        else:
            bot.reply_to(message, "⚠️ Le nombre de jours doit être positif. Essayez à nouveau.")
    except ValueError:
        bot.reply_to(message, "⚠️ Veuillez entrer un nombre valide de jours.")

# Fonction d'activation d'un utilisateur
def activate_user(message, days):
    try:
        user_id = int(message.text)
        if user_id not in activated_users:
            activated_users.add(user_id)
            expiration_date = datetime.now() + timedelta(days=days)
            user_activation_dates[user_id] = expiration_date
            bot.reply_to(message, f"✅ Utilisateur {user_id} activé.")
            remaining_time = get_remaining_time(expiration_date)
            bot.send_message(user_id, f"🎉 Votre accès au bot a été activé !\n🕒 Heure d'activation : {datetime.now()}\n⏳ Expiration : {remaining_time}")
            save_data()
        else:
            bot.reply_to(message, f"ℹ️ Utilisateur {user_id} déjà activé.")
    except (ValueError, TypeError):
        bot.reply_to(message, "⚠️ Veuillez entrer un ID valide.")

# Fonction pour calculer le temps restant jusqu'à l'expiration
def get_remaining_time(expiration_date):
    now = datetime.now()
    remaining_time = expiration_date - now
    if remaining_time.days > 30:
        months = remaining_time.days // 30
        return f"{months} mois"
    else:
        return f"{remaining_time.days} jours"

# Fonction de désactivation d'un utilisateur
def unactivate_user(message):
    try:
        user_id = int(message.text)
        if user_id in activated_users:
            activated_users.remove(user_id)
            del user_activation_dates[user_id]
            bot.reply_to(message, f"❌ Utilisateur {user_id} désactivé.")
            bot.send_message(user_id, "🚫 Votre accès au bot a été révoqué.")
            save_data()
        else:
            bot.reply_to(message, f"ℹ️ Utilisateur {user_id} non activé.")
    except (ValueError, TypeError):
        bot.reply_to(message, "⚠️ Veuillez entrer un ID valide.")

# Vérification d'activation pour les commandes utilisateurs
@bot.message_handler(func=lambda message: True)
def check_activation(message):
    user_id = message.from_user.id
    if user_id == owner_id or user_id in activated_users:
        fetch_tiktok_data(message)
    else:
        bot.reply_to(message, "❌ Accès refusé. Demandez l'activation au propriétaire.")

# Fonction pour récupérer les infos TikTok
def fetch_tiktok_data(message):
    username = message.text.strip().replace("@", "")
    bot.send_message(message.chat.id, f"🔍 Recherche des infos pour @{username}...")

    data = get_tiktok_info(username)

    if "error" in data:
        bot.send_message(message.chat.id, f"❌ Erreur : {data['error']}")
        return

    user = data.get("user", {})
    nickname = user.get("nickname", "Inconnu")
    followers = user.get("follower_count", 0)
    videos = user.get("aweme_count", 0)
    bio = user.get("signature", "Pas de bio")
    avatar_url = user.get("avatar_larger", {}).get("url_list", [""])[0]

    is_banned = user.get("ban_status", 0)
    is_reported = user.get("user_mode", 0)
    live_report = user.get("live_report_status", 0)

    status = "✅ Actif"
    if is_banned == 1:
        status = "🚫 Banni"
    elif is_reported != 0:
        status = "⚠️ Restreint / Signalé"

    live_status = "🎥 ✅ Aucun signalement en Live"
    if live_report == 1:
        live_status = "📡 🛑 Signalé en Live !"

    message_text = f"📌 **Profil TikTok** : @{username}\n"
    message_text += f"👤 Nom : {nickname}\n"
    message_text += f"👥 Abonnés : {followers}\n"
    message_text += f"🎥 Vidéos : {videos}\n"
    message_text += f"📝 Bio : {bio}\n"
    message_text += f"🔍 Statut du compte : {status}\n"
    message_text += f"{live_status}\n"

    if avatar_url:
        bot.send_photo(message.chat.id, avatar_url, caption=message_text)
    else:
        bot.send_message(message.chat.id, message_text)

# Lancer le bot
print("✅ Bot en cours d'exécution...")
load_data()  # Charger les données au démarrage
bot.polling()
