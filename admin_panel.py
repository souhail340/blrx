import flet as ft
import json
from datetime import datetime, timedelta

# Charger les données des utilisateurs
def load_data():
    try:
        with open("activated_users.json", "r") as file:
            data = json.load(file)
            return data.get("users", []), {
                int(user_id): datetime.fromisoformat(expiration_date)
                for user_id, expiration_date in data.get("expiration_dates", {}).items()
            }
    except FileNotFoundError:
        return [], {}

# Sauvegarder les données mises à jour
def save_data(users, expiration_dates):
    data = {
        "users": users,  # Garde la liste au lieu de set
        "expiration_dates": {str(user_id): exp.isoformat() for user_id, exp in expiration_dates.items()}
    }
    with open("activated_users.json", "w") as file:
        json.dump(data, file, indent=4)

# Initialiser les utilisateurs activés
activated_users, user_activation_dates = load_data()

# Fonction principale du panneau admin
def main(page: ft.Page):
    page.title = "Admin Panel - Telegram Bot"
    page.vertical_alignment = ft.MainAxisAlignment.START

    # Liste des utilisateurs activés
    users_list = ft.Column()

    def update_users_list():
        users_list.controls.clear()
        for user_id in activated_users:
            expiration = user_activation_dates.get(user_id, "Inconnu")
            expiration_text = expiration.strftime("%Y-%m-%d %H:%M") if isinstance(expiration, datetime) else "Inconnu"
            users_list.controls.append(ft.Text(f"👤 ID: {user_id} - Expire: {expiration_text}"))
        page.update()

    update_users_list()

    # Activer un utilisateur
    user_id_input = ft.TextField(label="ID Utilisateur")
    days_input = ft.TextField(label="Durée (jours)", keyboard_type=ft.KeyboardType.NUMBER)
    
    def show_snackbar(text, color="red"):
        snackbar = ft.SnackBar(ft.Text(text), bgcolor=color)
        page.overlay.append(snackbar)
        snackbar.open = True
        page.update()

    def activate_user(e):
        try:
            user_id = int(user_id_input.value)
            days = int(days_input.value)
            if user_id not in activated_users:
                activated_users.append(user_id)  # Correction ici (append au lieu de add)
                user_activation_dates[user_id] = datetime.now() + timedelta(days=days)
                save_data(activated_users, user_activation_dates)
                update_users_list()
                show_snackbar(f"✅ Utilisateur {user_id} activé pour {days} jours", "green")
        except ValueError:
            show_snackbar("⚠️ Entrée invalide")

    # Désactiver un utilisateur
    def deactivate_user(e):
        try:
            user_id = int(user_id_input.value)
            if user_id in activated_users:
                activated_users.remove(user_id)
                del user_activation_dates[user_id]
                save_data(activated_users, user_activation_dates)
                update_users_list()
                show_snackbar(f"❌ Utilisateur {user_id} désactivé", "orange")
        except ValueError:
            show_snackbar("⚠️ Entrée invalide")

    # Nettoyer les utilisateurs expirés
    def clean_expired_users(e):
        now = datetime.now()
        expired_users = [user_id for user_id, exp in user_activation_dates.items() if exp < now]
        for user_id in expired_users:
            activated_users.remove(user_id)
            del user_activation_dates[user_id]
        if expired_users:
            save_data(activated_users, user_activation_dates)
            update_users_list()
            show_snackbar(f"🗑 {len(expired_users)} utilisateurs expirés supprimés", "blue")

    # Boutons d'action
    page.add(
        ft.Text("📌 Panel d'Administration du Bot", size=20, weight=ft.FontWeight.BOLD),
        user_id_input,
        days_input,
        ft.Row([
            ft.ElevatedButton("➕ Activer", on_click=activate_user),
            ft.ElevatedButton("➖ Désactiver", on_click=deactivate_user),
            ft.ElevatedButton("🗑 Nettoyer Expirés", on_click=clean_expired_users)
        ]),
        ft.Text("📋 Utilisateurs Activés :", size=18, weight=ft.FontWeight.BOLD),
        users_list
    )

ft.app(target=main)
