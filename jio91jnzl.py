import json
import os
import time
import urllib.request
import urllib.parse
import re
import random
from datetime import datetime, timedelta

# ========== НАСТРОЙКИ ==========
TOKEN = "8500293211:AAEOM4iPCURkCIjr9tlR-t2_vCyiKtZXVVU"
MASTER_ADMIN = "Senko_live"
CARD = "2202 2084 4905 4841"
BANK = "Сбербанк"

# Файлы
PRICES_FILE = "prices.json"
PENDING_FILE = "pending.json"
USERS_FILE = "users.json"
HISTORY_FILE = "history.json"
PROMOS_FILE = "promos.json"
SESSIONS_FILE = "sessions.json"
CONFIG_FILE = "config.json"
DISCOUNTS_FILE = "discounts.json"
NEWS_FILE = "news.json"
ADMINS_FILE = "admins.json"
TICKETS_FILE = "tickets.json"
BALANCE_FILE = "balance.json"
BALANCE_PENDING_FILE = "balance_pending.json"
# ===============================

def api_request(method, data=None):
    url = f"https://api.telegram.org/bot{TOKEN}/{method}"
    if data:
        data = urllib.parse.urlencode(data).encode('utf-8')
    try:
        with urllib.request.urlopen(url, data=data, timeout=30) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        print(f"API ошибка: {e}")
        return None

class ShopBot:
    def __init__(self):
        self.offset = 0
        self.states = {}
        self.admin_password = "n121n1"
        self.user_discounts = {}
        self.news = []
        self.sessions = {}
        self.admins = {}
        self.tickets = {}
        self.user_ticket = {}
        self.admin_reply_mode = {}
        self.balance = {}
        self.balance_pending = {}
        self.crashed_users = {}
        self.load_data()
        print("GiwProject Shop запущен!")

    def load_data(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                self.admin_password = json.load(f).get("password", "n121n1")
        else:
            self.save_json(CONFIG_FILE, {"password": "n121n1"})
        
        self.user_discounts = self.load_json(DISCOUNTS_FILE, {})
        self.news = self.load_json(NEWS_FILE, [])
        self.sessions = self.load_json(SESSIONS_FILE, {})
        self.tickets = self.load_json(TICKETS_FILE, {})
        self.balance = self.load_json(BALANCE_FILE, {})
        self.balance_pending = self.load_json(BALANCE_PENDING_FILE, {})
        
        if os.path.exists(ADMINS_FILE):
            with open(ADMINS_FILE, 'r', encoding='utf-8') as f:
                self.admins = json.load(f)
        else:
            self.admins = {
                "Senko_live": {"level": 3, "added_by": "system", "can_give_items": True, "can_manage_prices": True, "can_manage_promos": True, "can_manage_admins": True, "can_manage_balance": True},
                "SailexGP": {"level": 2, "added_by": "system", "can_give_items": True, "can_manage_prices": True, "can_manage_promos": True, "can_manage_balance": True}
            }
            self.save_admins()
        
        if os.path.exists(PRICES_FILE):
            with open(PRICES_FILE, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
                self.prices = {}
                for key, val in loaded.items():
                    if isinstance(val, dict):
                        self.prices[key] = val.get("sale", val.get("base", 0))
                    else:
                        self.prices[key] = val
        else:
            self.prices = {"10k": 50, "20k": 120, "40k": 150, "50k": 200, "70k": 250, "90k": 300, "100k": 320, "id": 20, "knife": 160, "medal": 100}
            self.save_prices()
        
        self.pending = self.load_json(PENDING_FILE, {})
        self.users = self.load_json(USERS_FILE, {})
        self.history = self.load_json(HISTORY_FILE, [])
        
        if os.path.exists(PROMOS_FILE):
            with open(PROMOS_FILE, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
                self.promos = {"discount": {}, "money": {}}
                if "discount" in loaded:
                    self.promos["discount"] = loaded["discount"]
                if "money" in loaded:
                    self.promos["money"] = loaded["money"]
        else:
            self.promos = {"discount": {}, "money": {}}
            self.save_promos()

    def load_json(self, filename, default):
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        return default

    def save_json(self, filename, data):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def save_config(self): self.save_json(CONFIG_FILE, {"password": self.admin_password})
    def save_discounts(self): self.save_json(DISCOUNTS_FILE, self.user_discounts)
    def save_prices(self): self.save_json(PRICES_FILE, self.prices)
    def save_pending(self): self.save_json(PENDING_FILE, self.pending)
    def save_users(self): self.save_json(USERS_FILE, self.users)
    def save_history(self): self.save_json(HISTORY_FILE, self.history)
    def save_promos(self): self.save_json(PROMOS_FILE, self.promos)
    def save_sessions(self): self.save_json(SESSIONS_FILE, self.sessions)
    def save_news(self): self.save_json(NEWS_FILE, self.news)
    def save_admins(self): self.save_json(ADMINS_FILE, self.admins)
    def save_tickets(self): self.save_json(TICKETS_FILE, self.tickets)
    def save_balance(self): self.save_json(BALANCE_FILE, self.balance)
    def save_balance_pending(self): self.save_json(BALANCE_PENDING_FILE, self.balance_pending)

    def send(self, chat_id, text, markup=None):
        data = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
        if markup: data["reply_markup"] = json.dumps(markup)
        return api_request("sendMessage", data)

    def edit(self, chat_id, msg_id, text, markup=None):
        data = {"chat_id": chat_id, "message_id": msg_id, "text": text, "parse_mode": "HTML"}
        if markup: data["reply_markup"] = json.dumps(markup)
        api_request("editMessageText", data)

    def delete(self, chat_id, msg_id):
        api_request("deleteMessage", {"chat_id": chat_id, "message_id": msg_id})

    def answer(self, cb_id, text="", alert=False):
        api_request("answerCallbackQuery", {"callback_query_id": cb_id, "text": text, "show_alert": alert})

    def is_admin(self, uid):
        uid = str(uid)
        if uid in self.sessions:
            exp = datetime.fromisoformat(self.sessions[uid]["exp"])
            if datetime.now() < exp:
                return True
            del self.sessions[uid]
            self.save_sessions()
        return False

    def is_registered_admin(self, username):
        if not username: return False
        if username.lower() == MASTER_ADMIN.lower(): return True
        return username in self.admins

    def get_admin_level(self, username):
        if not username: return 0
        if username.lower() == MASTER_ADMIN.lower(): return 3
        if username in self.admins:
            return self.admins[username].get("level", 0)
        return 0

    def can_manage_balance(self, username):
        if username.lower() == MASTER_ADMIN.lower(): return True
        if username in self.admins:
            return self.admins[username].get("can_manage_balance", False)
        return False

    def can_give_items(self, username):
        if username.lower() == MASTER_ADMIN.lower(): return True
        if username in self.admins:
            return self.admins[username].get("can_give_items", False)
        return False

    def can_manage_prices(self, username):
        if username.lower() == MASTER_ADMIN.lower(): return True
        if username in self.admins:
            return self.admins[username].get("can_manage_prices", False)
        return False

    def can_manage_promos(self, username):
        if username.lower() == MASTER_ADMIN.lower(): return True
        if username in self.admins:
            return self.admins[username].get("can_manage_promos", False)
        return False

    def can_manage_admins(self, username):
        if username.lower() == MASTER_ADMIN.lower(): return True
        if username in self.admins:
            return self.admins[username].get("can_manage_admins", False)
        return False

    def get_user_balance(self, uid):
        uid = str(uid)
        return self.balance.get(uid, 0)

    def add_balance(self, uid, amount):
        uid = str(uid)
        self.balance[uid] = self.balance.get(uid, 0) + amount
        self.save_balance()

    def remove_balance(self, uid, amount):
        uid = str(uid)
        if uid in self.balance:
            self.balance[uid] = max(0, self.balance[uid] - amount)
            self.save_balance()

    def get_price_with_discount(self, uid, base_price):
        uid = str(uid)
        if uid in self.user_discounts:
            return int(base_price * (100 - self.user_discounts[uid]) / 100)
        return base_price

    def validate_id(self, id_text):
        forbidden = ["dev", "admin", "tester"]
        id_lower = id_text.lower()
        for word in forbidden:
            if word in id_lower:
                return False, "ID не может содержать Dev, Admin или Tester!"
        if not re.match(r'^[a-zA-Z0-9]+$', id_text):
            return False, "ID должен быть на английском, содержать только буквы и цифры!"
        return True, ""

    def back_button(self, text="◀️ Назад", callback="back_to_main"):
        return {"inline_keyboard": [[{"text": text, "callback_data": callback}]]}

    def main_menu(self, username=""):
        menu = {"keyboard": [
            [{"text": "🪙 Купить Голду"}],
            [{"text": "🆔 Купить ID"}, {"text": "🔪 Купить Нож"}],
            [{"text": "🏅 Купить Медаль"}],
            [{"text": "💎 Баланс"}, {"text": "🎫 Промокод"}],
            [{"text": "👤 Профиль"}, {"text": "📢 Новости"}],
            [{"text": "💬 Поддержка"}],
            [{"text": "💥 Крашнуть Бота"}]
        ], "resize_keyboard": True}
        if self.is_registered_admin(username):
            menu["keyboard"].append([{"text": "🔐 Админ-панель"}])
        return menu

    def balance_menu(self):
        return {"inline_keyboard": [
            [{"text": "💰 Пополнить баланс", "callback_data": "add_balance"}],
            [{"text": "◀️ Назад", "callback_data": "back_to_main"}]
        ]}

    def gold_menu(self, uid=None):
        p = self.prices
        disc = self.user_discounts.get(str(uid), 0) if uid else 0
        if disc:
            return {"inline_keyboard": [
                [{"text": f"10к - {int(p['10k']*(100-disc)/100)}р", "callback_data": "gold_10k"}],
                [{"text": f"20к - {int(p['20k']*(100-disc)/100)}р", "callback_data": "gold_20k"}],
                [{"text": f"40к - {int(p['40k']*(100-disc)/100)}р", "callback_data": "gold_40k"}],
                [{"text": f"50к - {int(p['50k']*(100-disc)/100)}р", "callback_data": "gold_50k"}],
                [{"text": f"70к - {int(p['70k']*(100-disc)/100)}р", "callback_data": "gold_70k"}],
                [{"text": f"90к - {int(p['90k']*(100-disc)/100)}р", "callback_data": "gold_90k"}],
                [{"text": f"100к - {int(p['100k']*(100-disc)/100)}р", "callback_data": "gold_100k"}],
                [{"text": "◀️ Назад", "callback_data": "back_to_main"}]
            ]}
        return {"inline_keyboard": [
            [{"text": f"10к - {p['10k']}р", "callback_data": "gold_10k"}],
            [{"text": f"20к - {p['20k']}р", "callback_data": "gold_20k"}],
            [{"text": f"40к - {p['40k']}р", "callback_data": "gold_40k"}],
            [{"text": f"50к - {p['50k']}р", "callback_data": "gold_50k"}],
            [{"text": f"70к - {p['70k']}р", "callback_data": "gold_70k"}],
            [{"text": f"90к - {p['90k']}р", "callback_data": "gold_90k"}],
            [{"text": f"100к - {p['100k']}р", "callback_data": "gold_100k"}],
            [{"text": "◀️ Назад", "callback_data": "back_to_main"}]
        ]}

    def knife_menu(self):
        return {"inline_keyboard": [
            [{"text": "M9 Dragon Glass", "callback_data": "knife_M9_Dragon_Glass"}],
            [{"text": "M9 Ancient", "callback_data": "knife_M9_Ancient"}],
            [{"text": "M9 Scratch", "callback_data": "knife_M9_Scratch"}],
            [{"text": "M9 Blue Blood", "callback_data": "knife_M9_Blue_Blood"}],
            [{"text": "Karambit Dragon Glass", "callback_data": "knife_Karambit_Dragon_Glass"}],
            [{"text": "Karambit Scratch", "callback_data": "knife_Karambit_Scratch"}],
            [{"text": "Karambit Universe", "callback_data": "knife_Karambit_Universe"}],
            [{"text": "G-Command Ancient", "callback_data": "knife_GCommand_Ancient"}],
            [{"text": "G-Command Reaper", "callback_data": "knife_GCommand_Reaper"}],
            [{"text": "Другой нож", "callback_data": "knife_custom"}],
            [{"text": "◀️ Назад", "callback_data": "back_to_main"}]
        ]}

    def admin_panel(self, username):
        btns = []
        if self.can_give_items(username):
            btns.append([{"text": "📋 Заказы", "callback_data": "pending"}])
        if self.can_manage_prices(username):
            btns.append([{"text": "💰 Цены", "callback_data": "prices"}])
        if self.can_manage_promos(username):
            btns.append([{"text": "🎫 Промокоды", "callback_data": "promos"}])
        if self.can_manage_balance(username):
            btns.append([{"text": "💎 Управление балансом", "callback_data": "manage_balance"}])
            btns.append([{"text": "⏳ Заявки на пополнение", "callback_data": "balance_pending"}])
        btns.extend([
            [{"text": "📊 Статистика", "callback_data": "stats"}],
            [{"text": "📜 История", "callback_data": "history"}],
            [{"text": "👥 Пользователи", "callback_data": "users"}],
            [{"text": "💬 Тикеты", "callback_data": "tickets"}]
        ])
        if self.can_manage_admins(username):
            btns.append([{"text": "👑 Админы", "callback_data": "manage_admins"}])
        if self.get_admin_level(username) >= 2:
            btns.append([{"text": "📢 Новость", "callback_data": "add_news"}])
            btns.append([{"text": "🔄 Сброс скидок", "callback_data": "reset_discounts"}])
        if username.lower() == MASTER_ADMIN.lower():
            btns.append([{"text": "🔑 Пароль", "callback_data": "pass"}])
        btns.append([{"text": "◀️ Назад", "callback_data": "back_to_main"}])
        return {"inline_keyboard": btns}

    def prices_menu(self):
        p = self.prices
        return {"inline_keyboard": [
            [{"text": f"10к: {p['10k']}р", "callback_data": "edit_10k"}],
            [{"text": f"20к: {p['20k']}р", "callback_data": "edit_20k"}],
            [{"text": f"40к: {p['40k']}р", "callback_data": "edit_40k"}],
            [{"text": f"50к: {p['50k']}р", "callback_data": "edit_50k"}],
            [{"text": f"70к: {p['70k']}р", "callback_data": "edit_70k"}],
            [{"text": f"90к: {p['90k']}р", "callback_data": "edit_90k"}],
            [{"text": f"100к: {p['100k']}р", "callback_data": "edit_100k"}],
            [{"text": f"ID: {p['id']}р", "callback_data": "edit_id"}],
            [{"text": f"Нож: {p['knife']}р", "callback_data": "edit_knife"}],
            [{"text": f"Медаль: {p['medal']}р", "callback_data": "edit_medal"}],
            [{"text": "◀️ Назад", "callback_data": "admin_back"}]
        ]}

    def promos_menu(self):
        return {"inline_keyboard": [
            [{"text": "🏷️ Создать скидочный", "callback_data": "create_discount"}],
            [{"text": "💰 Создать на деньги", "callback_data": "create_money_promo"}],
            [{"text": "📋 Список", "callback_data": "list_promos"}],
            [{"text": "🗑 Удалить", "callback_data": "delete_promo"}],
            [{"text": "◀️ Назад", "callback_data": "admin_back"}]
        ]}

    def manage_admins_menu(self):
        return {"inline_keyboard": [
            [{"text": "➕ Добавить админа", "callback_data": "add_admin"}],
            [{"text": "📋 Список админов", "callback_data": "list_admins"}],
            [{"text": "➖ Снять админа", "callback_data": "remove_admin"}],
            [{"text": "◀️ Назад", "callback_data": "admin_back"}]
        ]}

    def manage_balance_menu(self):
        return {"inline_keyboard": [
            [{"text": "💎 Выдать баланс", "callback_data": "give_balance"}],
            [{"text": "💸 Забрать баланс", "callback_data": "take_balance"}],
            [{"text": "◀️ Назад", "callback_data": "admin_back"}]
        ]}

    def update_user(self, uid, username, name):
        uid = str(uid)
        if uid not in self.users:
            self.users[uid] = {"name": name, "user": username, "purchases": 0, "spent": 0}
            self.save_users()

    def broadcast_news(self, text):
        for uid in self.users:
            try: self.send(int(uid), f"📢 НОВОСТЬ!\n\n{text}")
            except: pass

    def notify_admins(self, text):
        for admin_id in self.sessions:
            try: self.send(int(admin_id), text)
            except: pass

    def generate_crash_symbols(self):
        symbols = []
        for _ in range(30):
            symbols.append(chr(random.randint(0x1F600, 0x1F64F)))
            symbols.append(chr(random.randint(0x2580, 0x259F)))
            symbols.append(chr(random.randint(0x1F300, 0x1F5FF)))
            symbols.append(chr(random.randint(0x1F680, 0x1F6FF)))
        return " ".join(symbols)

    def process(self):
        resp = api_request("getUpdates", {"offset": self.offset, "timeout": 30})
        if not resp or not resp.get("ok"): return
        
        for upd in resp["result"]:
            self.offset = upd["update_id"] + 1
            
            if "message" in upd:
                msg = upd["message"]
                chat_id = msg["chat"]["id"]
                uid = str(msg["from"]["id"])
                username = msg["from"].get("username", "")
                name = msg["from"].get("first_name", "Юзер")
                text = msg.get("text", "")
                
                self.update_user(uid, username, name)
                
                # Проверка на крашнутого пользователя
                if uid in self.crashed_users:
                    if text == "/start":
                        del self.crashed_users[uid]
                        self.send(chat_id, "🎮 Бот восстановлен! Выберите что хотите купить:", self.main_menu(username))
                    return
                
                if uid in self.user_ticket:
                    self.handle_ticket_message(chat_id, uid, username, name, msg)
                    return
                
                if uid in self.admin_reply_mode:
                    self.handle_admin_reply(chat_id, uid, username, text)
                    return
                
                if "photo" in msg:
                    self.handle_photo(msg)
                elif uid in self.states:
                    self.handle_state(chat_id, uid, username, text)
                elif text == "/start":
                    self.send(chat_id, "🎮 GiwProject Shop\n\nВыберите что хотите купить:", self.main_menu(username))
                elif text == "🪙 Купить Голду":
                    self.send(chat_id, "Выберите количество:", self.gold_menu(uid))
                elif text == "🆔 Купить ID":
                    price = self.get_price_with_discount(uid, self.prices["id"])
                    disc = self.user_discounts.get(uid, 0)
                    txt = f"Цена: {price}р"
                    if disc: txt += f" (скидка {disc}%)"
                    txt += "\n\nВведите свой ID (англ. буквы и цифры):"
                    self.states[uid] = {"action": "buy_id_step1", "price": price}
                    self.send(chat_id, txt, self.back_button())
                elif text == "🔪 Купить Нож":
                    self.send(chat_id, "Выберите нож:", self.knife_menu())
                elif text == "🏅 Купить Медаль":
                    price = self.get_price_with_discount(uid, self.prices["medal"])
                    disc = self.user_discounts.get(uid, 0)
                    txt = f"Цена: {price}р"
                    if disc: txt += f" (скидка {disc}%)"
                    txt += "\n\nНапишите какую медаль хотите приобрести:"
                    self.states[uid] = {"action": "buy_medal", "price": price}
                    self.send(chat_id, txt, self.back_button())
                elif text == "💎 Баланс":
                    bal = self.get_user_balance(uid)
                    self.send(chat_id, f"💎 Ваш баланс: {bal}р", self.balance_menu())
                elif text == "🎫 Промокод":
                    self.states[uid] = {"action": "promo"}
                    self.send(chat_id, "Введите промокод:", self.back_button())
                elif text == "👤 Профиль":
                    u = self.users.get(uid, {})
                    disc = self.user_discounts.get(uid, 0)
                    bal = self.get_user_balance(uid)
                    txt = f"👤 Профиль\n\nИмя: {name}\nUsername: @{username}\nID: {uid}\n💎 Баланс: {bal}р\n\n📊 Статистика:\nПокупок: {u.get('purchases', 0)}\nПотрачено: {u.get('spent', 0)}р"
                    if disc: txt += f"\n\n🎫 Скидка: {disc}%"
                    self.send(chat_id, txt, self.back_button())
                elif text == "📢 Новости":
                    if self.news:
                        for n in self.news[-5:][::-1]:
                            self.send(chat_id, f"📢 {n}")
                    else:
                        self.send(chat_id, "Нет новостей")
                    self.send(chat_id, "Выберите действие:", self.back_button())
                elif text == "💬 Поддержка":
                    self.show_support_menu(chat_id, uid, username)
                elif text == "💥 Крашнуть Бота":
                    kb = {"inline_keyboard": [
                        [{"text": "✅ Да, крашнуть", "callback_data": "crash_confirm"}],
                        [{"text": "❌ Нет, отмена", "callback_data": "back_to_main"}]
                    ]}
                    self.send(chat_id, "⚠️ Вы точно хотите крашнуть бота?\n\nПосле этого бот перестанет отвечать на все команды кроме /start!", kb)
                elif text == "🔐 Админ-панель":
                    if self.is_registered_admin(username):
                        if self.is_admin(uid):
                            self.send(chat_id, "🔐 Админ-панель:", self.admin_panel(username))
                        else:
                            self.states[uid] = {"action": "login"}
                            self.send(chat_id, "Введите пароль:", self.back_button())
                    else:
                        self.send(chat_id, "❌ У вас нет доступа к админ-панели!")
            
            elif "callback_query" in upd:
                self.handle_callback(upd["callback_query"])

    def show_support_menu(self, chat_id, uid, username):
        if uid in self.tickets:
            ticket = self.tickets[uid]
            if ticket["status"] == "open":
                self.send(chat_id, f"У вас уже есть открытый тикет.\n\nСообщений: {len(ticket['messages'])}\n\nОтправьте сообщение или /close для закрытия.")
                self.user_ticket[uid] = True
                return
        
        kb = {"inline_keyboard": [
            [{"text": "📝 Открыть тикет", "callback_data": "open_ticket"}],
            [{"text": "📋 Мои тикеты", "callback_data": "my_tickets"}],
            [{"text": "◀️ Назад", "callback_data": "back_to_main"}]
        ]}
        self.send(chat_id, "💬 Поддержка\n\nВыберите действие:", kb)

    def handle_ticket_message(self, chat_id, uid, username, name, msg):
        text = msg.get("text", "")
        
        if text == "/close":
            if uid in self.tickets:
                self.tickets[uid]["status"] = "closed"
                self.tickets[uid]["closed_time"] = datetime.now().strftime("%d.%m.%Y %H:%M")
                self.save_tickets()
                del self.user_ticket[uid]
                self.send(chat_id, "✅ Тикет закрыт.", self.main_menu(username))
                self.notify_admins(f"📪 Тикет от @{username} закрыт.")
            return
        
        if "photo" in msg:
            file_id = msg["photo"][-1]["file_id"]
            caption = msg.get("caption", "Фото")
            message_data = {"type": "photo", "file_id": file_id, "text": caption, "from": "user", "time": datetime.now().strftime("%H:%M")}
        else:
            message_data = {"type": "text", "text": text, "from": "user", "time": datetime.now().strftime("%H:%M")}
        
        if uid not in self.tickets:
            self.tickets[uid] = {
                "user_id": uid, "username": username, "name": name,
                "status": "open", "messages": [], "created": datetime.now().strftime("%d.%m.%Y %H:%M")
            }
        
        self.tickets[uid]["messages"].append(message_data)
        self.save_tickets()
        
        admin_msg = f"💬 Новое сообщение от @{username}\n🆔 {uid}"
        kb = {"inline_keyboard": [[{"text": "📝 Ответить", "callback_data": f"reply_{uid}"}]]}
        
        if message_data["type"] == "photo":
            for admin_id in self.sessions:
                try:
                    api_request("sendPhoto", {"chat_id": int(admin_id), "photo": message_data["file_id"], "caption": admin_msg, "reply_markup": json.dumps(kb)})
                except: pass
        else:
            for admin_id in self.sessions:
                try:
                    self.send(int(admin_id), f"{admin_msg}\n\n{text}", kb)
                except: pass
        
        self.send(chat_id, "✅ Сообщение отправлено! Ожидайте ответа.")

    def handle_admin_reply(self, chat_id, uid, username, text):
        ticket_uid = self.admin_reply_mode[uid]
        
        if ticket_uid not in self.tickets:
            self.send(chat_id, "❌ Тикет не найден!")
            del self.admin_reply_mode[uid]
            return
        
        ticket = self.tickets[ticket_uid]
        message_data = {"type": "text", "text": text, "from": f"admin_{username}", "time": datetime.now().strftime("%H:%M")}
        ticket["messages"].append(message_data)
        self.save_tickets()
        
        try:
            self.send(int(ticket_uid), f"💬 Ответ от @{username}:\n\n{text}")
        except: pass
        
        self.send(chat_id, f"✅ Ответ отправлен!")
        del self.admin_reply_mode[uid]

    def handle_photo(self, msg):
        chat_id = msg["chat"]["id"]
        uid = str(msg["from"]["id"])
        username = msg["from"].get("username", "")
        name = msg["from"].get("first_name", "Юзер")
        file_id = msg["photo"][-1]["file_id"]
        
        if uid in self.states and self.states[uid].get("action") == "add_balance_photo":
            state = self.states[uid]
            amount = state["amount"]
            
            pid = f"bal_{len(self.balance_pending) + 1}"
            self.balance_pending[pid] = {
                "uid": uid, "username": username, "name": name,
                "amount": amount, "file_id": file_id,
                "time": datetime.now().strftime("%H:%M"), "status": "pending"
            }
            self.save_balance_pending()
            
            del self.states[uid]
            self.send(chat_id, "✅ Скриншот отправлен! Ожидайте пополнения баланса.", self.main_menu(username))
            self.notify_admins(f"💰 Новая заявка на пополнение #{pid}\n👤 @{username}\n💎 Сумма: {amount}р")
            return
        
        if uid not in self.states or not self.states[uid].get("action", "").startswith("pay_"):
            self.send(chat_id, "❌ Сначала выберите товар!")
            return
        
        state = self.states[uid]
        pid = str(len(self.history) + 1)
        
        self.pending[pid] = {
            "uid": uid, "username": username, "name": name,
            "item": state["item"], "details": state["details"], "price": state["price"],
            "file_id": file_id, "time": datetime.now().strftime("%H:%M"), "status": "pending"
        }
        self.save_pending()
        self.history.append({
            "id": pid, "uid": uid, "user": username,
            "item": state["item"], "price": state["price"],
            "status": "pending", "time": datetime.now().strftime("%d.%m.%Y %H:%M")
        })
        self.save_history()
        
        if uid in self.user_discounts:
            del self.user_discounts[uid]
            self.save_discounts()
        
        del self.states[uid]
        self.send(chat_id, "✅ Скриншот отправлен! Ожидайте.", self.main_menu(username))
        self.notify_admins(f"🆕 Новый заказ #{pid} от @{username}")

    def handle_state(self, chat_id, uid, username, text):
        state = self.states[uid]
        action = state["action"]
        
        if action == "login":
            if text == self.admin_password:
                if self.is_registered_admin(username):
                    self.sessions[uid] = {"exp": (datetime.now() + timedelta(hours=24)).isoformat(), "user": username}
                    self.save_sessions()
                    self.send(chat_id, "✅ Доступ разрешен!", self.main_menu(username))
                    self.send(chat_id, "🔐 Админ-панель:", self.admin_panel(username))
                else:
                    self.send(chat_id, "❌ Вы не зарегистрированы как админ!")
            else:
                self.send(chat_id, "❌ Неверный пароль!")
            del self.states[uid]
        
        elif action == "add_balance_amount":
            try:
                amount = int(text)
                if amount <= 0:
                    self.send(chat_id, "❌ Введите сумму больше 0!")
                    return
                self.states[uid] = {"action": "add_balance_photo", "amount": amount}
                self.send(chat_id, f"💳 Переведите {amount}р на карту:\n{CARD}\n({BANK})\n\n📸 Затем пришлите скриншот.", self.back_button())
            except:
                self.send(chat_id, "❌ Введите число!")
        
        elif action == "buy_id_step1":
            valid, error = self.validate_id(text)
            if not valid:
                self.send(chat_id, f"❌ {error}")
                return
            self.states[uid] = {"action": "buy_id_step2", "price": state["price"], "my_id": text}
            self.send(chat_id, "📝 Введите ID, который хотите купить (англ. буквы и цифры):", self.back_button())
        
        elif action == "buy_id_step2":
            valid, error = self.validate_id(text)
            if not valid:
                self.send(chat_id, f"❌ {error}")
                return
            
            price = state["price"]
            bal = self.get_user_balance(uid)
            
            if bal >= price:
                self.remove_balance(uid, price)
                pid = str(len(self.history) + 1)
                self.pending[pid] = {
                    "uid": uid, "username": username, "name": self.users.get(uid, {}).get("name", "Юзер"),
                    "item": "ID игрока", "details": f"Ваш ID: {state['my_id']}\nЖелаемый ID: {text}",
                    "price": price, "file_id": None, "time": datetime.now().strftime("%H:%M"), "status": "pending"
                }
                self.save_pending()
                self.history.append({
                    "id": pid, "uid": uid, "user": username,
                    "item": "ID игрока", "price": price,
                    "status": "pending", "time": datetime.now().strftime("%d.%m.%Y %H:%M")
                })
                self.save_history()
                del self.states[uid]
                self.send(chat_id, "✅ Заказ оформлен! Ожидайте выполнения.", self.main_menu(username))
                self.notify_admins(f"🆕 Новый заказ #{pid} от @{username}\nID игрока (оплата с баланса)")
            else:
                self.send(chat_id, f"❌ Недостаточно средств на балансе!\n\nВаш баланс: {bal}р\nЦена: {price}р\n\nПерейдите в раздел 💎 Баланс -> Пополнить баланс", self.back_button())
                del self.states[uid]
        
        elif action == "buy_medal":
            price = state["price"]
            bal = self.get_user_balance(uid)
            
            if bal >= price:
                self.remove_balance(uid, price)
                pid = str(len(self.history) + 1)
                self.pending[pid] = {
                    "uid": uid, "username": username, "name": self.users.get(uid, {}).get("name", "Юзер"),
                    "item": "Медаль", "details": f"Медаль: {text}",
                    "price": price, "file_id": None, "time": datetime.now().strftime("%H:%M"), "status": "pending"
                }
                self.save_pending()
                self.history.append({
                    "id": pid, "uid": uid, "user": username,
                    "item": "Медаль", "price": price,
                    "status": "pending", "time": datetime.now().strftime("%d.%m.%Y %H:%M")
                })
                self.save_history()
                del self.states[uid]
                self.send(chat_id, "✅ Заказ оформлен! Ожидайте выполнения.", self.main_menu(username))
                self.notify_admins(f"🆕 Новый заказ #{pid} от @{username}\nМедаль (оплата с баланса)")
            else:
                self.send(chat_id, f"❌ Недостаточно средств на балансе!\n\nВаш баланс: {bal}р\nЦена: {price}р\n\nПерейдите в раздел 💎 Баланс -> Пополнить баланс", self.back_button())
                del self.states[uid]
        
        elif action == "pay_gold":
            price = state["price"]
            gold_type = state["gold_type"]
            bal = self.get_user_balance(uid)
            
            if bal >= price:
                self.remove_balance(uid, price)
                pid = str(len(self.history) + 1)
                self.pending[pid] = {
                    "uid": uid, "username": username, "name": self.users.get(uid, {}).get("name", "Юзер"),
                    "item": f"Голда {gold_type}", "details": f"ID: {text}\nКоличество: {gold_type}",
                    "price": price, "file_id": None, "time": datetime.now().strftime("%H:%M"), "status": "pending"
                }
                self.save_pending()
                self.history.append({
                    "id": pid, "uid": uid, "user": username,
                    "item": f"Голда {gold_type}", "price": price,
                    "status": "pending", "time": datetime.now().strftime("%d.%m.%Y %H:%M")
                })
                self.save_history()
                del self.states[uid]
                self.send(chat_id, "✅ Заказ оформлен! Ожидайте выполнения.", self.main_menu(username))
                self.notify_admins(f"🆕 Новый заказ #{pid} от @{username}\nГолда {gold_type} (оплата с баланса)")
            else:
                self.send(chat_id, f"❌ Недостаточно средств на балансе!\n\nВаш баланс: {bal}р\nЦена: {price}р\n\nПерейдите в раздел 💎 Баланс -> Пополнить баланс", self.back_button())
                del self.states[uid]
        
        elif action == "promo":
            promo = text.upper()
            
            if promo in self.promos["discount"]:
                d = self.promos["discount"][promo]
                if d.get("used", 0) >= d.get("max", 1):
                    self.send(chat_id, "❌ Промокод закончился!")
                else:
                    self.promos["discount"][promo]["used"] = d.get("used", 0) + 1
                    self.save_promos()
                    self.user_discounts[uid] = d["discount"]
                    self.save_discounts()
                    self.send(chat_id, f"✅ Скидка {d['discount']}% активирована!")
            
            elif promo in self.promos["money"]:
                d = self.promos["money"][promo]
                if d.get("used", 0) >= d.get("max", 1):
                    self.send(chat_id, "❌ Промокод закончился!")
                else:
                    self.promos["money"][promo]["used"] = d.get("used", 0) + 1
                    self.save_promos()
                    amount = d["amount"]
                    self.add_balance(uid, amount)
                    self.send(chat_id, f"✅ На ваш баланс зачислено {amount}р!")
            else:
                self.send(chat_id, "❌ Промокод не найден!")
            del self.states[uid]
        
        elif action == "edit_price":
            try:
                self.prices[state["key"]] = int(text)
                self.save_prices()
                self.send(chat_id, "✅ Цена обновлена!")
            except:
                self.send(chat_id, "❌ Введите число!")
            del self.states[uid]
        
        elif action == "new_pass":
            if username.lower() == MASTER_ADMIN.lower():
                self.admin_password = text
                self.save_config()
                self.send(chat_id, "✅ Пароль изменен!")
            del self.states[uid]
        
        elif action == "create_discount":
            self.states[uid] = {"action": "discount_percent", "code": text.upper()}
            self.send(chat_id, "📊 Введите процент скидки (1-99):", self.back_button())
        
        elif action == "discount_percent":
            try:
                p = int(text)
                if 1 <= p <= 99:
                    self.states[uid] = {"action": "discount_uses", "code": state["code"], "percent": p}
                    self.send(chat_id, "🔢 Количество активаций (0 - безлимит):", self.back_button())
                else:
                    self.send(chat_id, "❌ Введите 1-99!")
                    del self.states[uid]
            except:
                self.send(chat_id, "❌ Введите число!")
                del self.states[uid]
        
        elif action == "discount_uses":
            try:
                u = int(text)
                if u >= 0:
                    self.promos["discount"][state["code"]] = {"discount": state["percent"], "max": u if u > 0 else 0, "used": 0}
                    self.save_promos()
                    self.send(chat_id, f"✅ Скидочный промокод {state['code']} создан!")
                else:
                    self.send(chat_id, "❌ Введите 0 или больше!")
            except:
                self.send(chat_id, "❌ Введите число!")
            del self.states[uid]
        
        elif action == "create_money_promo_code":
            self.states[uid] = {"action": "money_promo_amount", "code": text.upper()}
            self.send(chat_id, "💰 Введите сумму (в рублях):", self.back_button())
        
        elif action == "money_promo_amount":
            try:
                amount = int(text)
                if amount <= 0:
                    self.send(chat_id, "❌ Введите сумму больше 0!")
                    return
                self.states[uid] = {"action": "money_promo_uses", "code": state["code"], "amount": amount}
                self.send(chat_id, "🔢 Количество активаций (0 - безлимит):", self.back_button())
            except:
                self.send(chat_id, "❌ Введите число!")
                del self.states[uid]
        
        elif action == "money_promo_uses":
            try:
                u = int(text)
                if u >= 0:
                    self.promos["money"][state["code"]] = {"amount": state["amount"], "max": u if u > 0 else 0, "used": 0}
                    self.save_promos()
                    self.send(chat_id, f"✅ Денежный промокод {state['code']} на {state['amount']}р создан!")
                else:
                    self.send(chat_id, "❌ Введите 0 или больше!")
            except:
                self.send(chat_id, "❌ Введите число!")
            del self.states[uid]
        
        elif action == "delete_promo":
            code = text.upper()
            deleted = False
            if code in self.promos["discount"]:
                del self.promos["discount"][code]
                deleted = True
            elif code in self.promos["money"]:
                del self.promos["money"][code]
                deleted = True
            
            if deleted:
                self.save_promos()
                self.send(chat_id, f"✅ Промокод {code} удален!")
            else:
                self.send(chat_id, "❌ Промокод не найден!")
            del self.states[uid]
        
        elif action == "add_news":
            self.news.append(text)
            self.save_news()
            self.broadcast_news(text)
            self.send(chat_id, "✅ Новость добавлена!")
            del self.states[uid]
        
        elif action == "approve_msg":
            pid = state["pid"]
            if pid in self.pending:
                p = self.pending[pid]
                p["status"] = "done"
                p["completed_by"] = username
                p["completed_time"] = datetime.now().strftime("%H:%M")
                p["admin_message"] = text
                self.save_pending()
                
                if p["uid"] in self.users:
                    u = self.users[p["uid"]]
                    u["purchases"] = u.get("purchases", 0) + 1
                    u["spent"] = u.get("spent", 0) + p["price"]
                    self.save_users()
                
                for h in self.history:
                    if h["id"] == pid:
                        h["status"] = "done"
                        h["completed_by"] = username
                self.save_history()
                
                self.send(int(p["uid"]), f"✅ Заказ #{pid} выполнен!\n\n{p['item']}\n{p['details']}\n\n💬 Сообщение от @{username}: {text}\n\n❤️ Спасибо!")
                self.send(chat_id, f"✅ Заказ #{pid} выдан!")
            del self.states[uid]
        
        elif action == "add_admin_username":
            new_admin = text.lstrip('@')
            if new_admin.lower() == MASTER_ADMIN.lower():
                self.send(chat_id, "❌ Нельзя изменить главного админа!")
                del self.states[uid]
                return
            self.states[uid] = {"action": "add_admin_level", "username": new_admin}
            self.send(chat_id, "📊 Выберите уровень:\n1 - Выдача товаров\n2 - +Цены/Промо/Баланс\n3 - +Управление админами", self.back_button())
        
        elif action == "add_admin_level":
            try:
                level = int(text)
                if level not in [1, 2, 3]:
                    self.send(chat_id, "❌ Введите 1, 2 или 3!")
                    return
                new_admin = state["username"]
                rights = {"level": level, "added_by": username, "added_time": datetime.now().strftime("%d.%m.%Y")}
                if level >= 1:
                    rights["can_give_items"] = True
                    rights["can_manage_balance"] = True
                if level >= 2:
                    rights["can_manage_prices"] = True
                    rights["can_manage_promos"] = True
                if level >= 3:
                    rights["can_manage_admins"] = True
                self.admins[new_admin] = rights
                self.save_admins()
                self.send(chat_id, f"✅ Админ @{new_admin} добавлен с уровнем {level}!")
            except:
                self.send(chat_id, "❌ Введите число!")
            del self.states[uid]
        
        elif action == "remove_admin_username":
            admin_to_remove = text.lstrip('@')
            if admin_to_remove.lower() == MASTER_ADMIN.lower():
                self.send(chat_id, "❌ Невозможно снять главного админа @Senko_live!")
                del self.states[uid]
                return
            if admin_to_remove in self.admins:
                del self.admins[admin_to_remove]
                self.save_admins()
                self.send(chat_id, f"✅ Админ @{admin_to_remove} снят!")
            else:
                self.send(chat_id, "❌ Админ не найден!")
            del self.states[uid]
        
        elif action == "give_balance_username":
            target = text.lstrip('@')
            self.states[uid] = {"action": "give_balance_amount", "target": target}
            self.send(chat_id, f"💰 Введите сумму для выдачи @{target}:", self.back_button())
        
        elif action == "give_balance_amount":
            try:
                amount = int(text)
                if amount <= 0:
                    self.send(chat_id, "❌ Введите сумму больше 0!")
                    return
                target = state["target"]
                found = False
                for u_id, u_data in self.users.items():
                    if u_data.get("user") == target:
                        self.add_balance(u_id, amount)
                        found = True
                        try:
                            self.send(int(u_id), f"💰 На ваш баланс зачислено {amount}р!")
                        except: pass
                        break
                if found:
                    self.send(chat_id, f"✅ Баланс @{target} пополнен на {amount}р!")
                else:
                    self.send(chat_id, f"❌ Пользователь @{target} не найден в базе!")
            except:
                self.send(chat_id, "❌ Введите число!")
            del self.states[uid]
        
        elif action == "take_balance_username":
            target = text.lstrip('@')
            self.states[uid] = {"action": "take_balance_amount", "target": target}
            self.send(chat_id, f"💸 Введите сумму для списания у @{target}:", self.back_button())
        
        elif action == "take_balance_amount":
            try:
                amount = int(text)
                if amount <= 0:
                    self.send(chat_id, "❌ Введите сумму больше 0!")
                    return
                target = state["target"]
                found = False
                for u_id, u_data in self.users.items():
                    if u_data.get("user") == target:
                        self.remove_balance(u_id, amount)
                        found = True
                        try:
                            self.send(int(u_id), f"💸 С вашего баланса списано {amount}р!")
                        except: pass
                        break
                if found:
                    self.send(chat_id, f"✅ С баланса @{target} списано {amount}р!")
                else:
                    self.send(chat_id, f"❌ Пользователь @{target} не найден в базе!")
            except:
                self.send(chat_id, "❌ Введите число!")
            del self.states[uid]

    def handle_callback(self, cb):
        cid = cb["id"]
        data = cb["data"]
        msg = cb.get("message", {})
        chat_id = msg["chat"]["id"]
        msg_id = msg["message_id"]
        uid = str(cb["from"]["id"])
        username = cb["from"].get("username", "")
        
        # Краш бота
        if data == "crash_confirm":
            self.answer(cid)
            self.crashed_users[uid] = True
            self.delete(chat_id, msg_id)
            crash_text = "💀💀💀 " + self.generate_crash_symbols() + " 💀💀💀"
            self.send(chat_id, crash_text)
            return
        
        # Назад в главное меню
        if data == "back_to_main":
            self.answer(cid)
            self.delete(chat_id, msg_id)
            self.send(chat_id, "🎮 GiwProject Shop", self.main_menu(username))
            if uid in self.states:
                del self.states[uid]
            return
        
        # Поддержка
        if data == "open_ticket":
            self.answer(cid)
            self.user_ticket[uid] = True
            self.send(chat_id, "💬 Опишите вашу проблему. Можете отправить фото.\n\n/close - закрыть тикет")
            self.delete(chat_id, msg_id)
            return
        
        if data == "my_tickets":
            self.answer(cid)
            if uid in self.tickets:
                t = self.tickets[uid]
                txt = f"💬 Ваш тикет\nСтатус: {'Открыт' if t['status'] == 'open' else 'Закрыт'}\nСоздан: {t['created']}\nСообщений: {len(t['messages'])}"
                self.send(chat_id, txt, self.back_button())
            else:
                self.send(chat_id, "У вас нет тикетов", self.back_button())
            return
        
        if data.startswith("reply_"):
            self.answer(cid)
            ticket_uid = data[6:]
            if ticket_uid in self.tickets:
                self.admin_reply_mode[uid] = ticket_uid
                self.send(chat_id, f"💬 Введите ответ для @{self.tickets[ticket_uid]['username']}:", self.back_button())
                self.delete(chat_id, msg_id)
            return
        
        # Пополнение баланса
        if data == "add_balance":
            self.answer(cid)
            self.states[uid] = {"action": "add_balance_amount"}
            self.edit(chat_id, msg_id, "💰 Введите сумму для пополнения:", self.back_button())
            return
        
        # Ножи
        if data.startswith("knife_"):
            self.answer(cid)
            knife = data[6:]
            
            if knife == "custom":
                self.states[uid] = {"action": "buy_knife", "price": self.get_price_with_discount(uid, self.prices["knife"])}
                self.send(chat_id, "🔪 Напишите название ножа:", self.back_button())
                self.delete(chat_id, msg_id)
                return
            
            knife_names = {
                "M9_Dragon_Glass": "M9 Dragon Glass",
                "M9_Ancient": "M9 Ancient",
                "M9_Scratch": "M9 Scratch",
                "M9_Blue_Blood": "M9 Blue Blood",
                "Karambit_Dragon_Glass": "Karambit Dragon Glass",
                "Karambit_Scratch": "Karambit Scratch",
                "Karambit_Universe": "Karambit Universe",
                "GCommand_Ancient": "G-Command Ancient",
                "GCommand_Reaper": "G-Command Reaper"
            }
            
            knife_name = knife_names.get(knife, knife.replace("_", " "))
            price = self.get_price_with_discount(uid, self.prices["knife"])
            bal = self.get_user_balance(uid)
            
            if bal >= price:
                self.remove_balance(uid, price)
                pid = str(len(self.history) + 1)
                self.pending[pid] = {
                    "uid": uid, "username": username, "name": self.users.get(uid, {}).get("name", "Юзер"),
                    "item": "Нож", "details": f"Нож: {knife_name}",
                    "price": price, "file_id": None, "time": datetime.now().strftime("%H:%M"), "status": "pending"
                }
                self.save_pending()
                self.history.append({
                    "id": pid, "uid": uid, "user": username,
                    "item": "Нож", "price": price,
                    "status": "pending", "time": datetime.now().strftime("%d.%m.%Y %H:%M")
                })
                self.save_history()
                self.delete(chat_id, msg_id)
                self.send(chat_id, "✅ Заказ оформлен! Ожидайте выполнения.", self.main_menu(username))
                self.notify_admins(f"🆕 Новый заказ #{pid} от @{username}\nНож (оплата с баланса)")
            else:
                self.send(chat_id, f"❌ Недостаточно средств на балансе!\n\nВаш баланс: {bal}р\nЦена: {price}р\n\nПерейдите в раздел 💎 Баланс -> Пополнить баланс", self.back_button())
            return
        
        if data.startswith("gold_"):
            self.answer(cid)
            gold = data.replace("gold_", "")
            price = self.get_price_with_discount(uid, self.prices[gold])
            bal = self.get_user_balance(uid)
            
            if bal >= price:
                self.states[uid] = {"action": "pay_gold", "item": f"Голда {gold}", "details": f"{gold}", "price": price, "gold_type": gold}
                self.edit(chat_id, msg_id, f"🪙 Голда {gold}\n💰 {price}р\n\n📝 Введите свой ID:", self.back_button())
            else:
                self.answer(cid, f"❌ Недостаточно средств! Баланс: {bal}р, нужно: {price}р", True)
            return
        
        if not self.is_admin(uid):
            self.answer(cid, "❌ Нет доступа!", True)
            return
        
        # Админ-панель
        if data == "pending":
            self.answer(cid)
            if not self.can_give_items(username): return
            if not self.pending:
                self.send(chat_id, "📋 Нет заказов", self.back_button())
                return
            for pid, p in list(self.pending.items())[:10]:
                if p["status"] == "pending":
                    txt = f"📋 Заказ #{pid}\n👤 {p['name']} (@{p['username']})\n🆔 {p['uid']}\n🛍 {p['item']}\n📝 {p['details']}\n💰 {p['price']}р"
                    kb = {"inline_keyboard": [
                        [{"text": "✅ Выдать", "callback_data": f"ok_{pid}"}],
                        [{"text": "💬 С сообщением", "callback_data": f"msg_{pid}"}],
                        [{"text": "❌ Отклонить", "callback_data": f"no_{pid}"}]
                    ]}
                    if p.get("file_id"):
                        api_request("sendPhoto", {"chat_id": chat_id, "photo": p["file_id"], "caption": txt, "reply_markup": json.dumps(kb)})
                    else:
                        self.send(chat_id, txt, kb)
        
        elif data.startswith("ok_"):
            self.answer(cid, "✅ Выдано!")
            if not self.can_give_items(username): return
            pid = data[3:]
            if pid in self.pending:
                p = self.pending[pid]
                p["status"] = "done"
                p["completed_by"] = username
                p["completed_time"] = datetime.now().strftime("%H:%M")
                self.save_pending()
                if p["uid"] in self.users:
                    u = self.users[p["uid"]]
                    u["purchases"] = u.get("purchases", 0) + 1
                    u["spent"] = u.get("spent", 0) + p["price"]
                    self.save_users()
                for h in self.history:
                    if h["id"] == pid:
                        h["status"] = "done"
                        h["completed_by"] = username
                self.save_history()
                self.send(int(p["uid"]), f"✅ Заказ #{pid} выполнен!\n\n{p['item']}\n{p['details']}\n\n👤 Выдал: @{username}\n❤️ Спасибо!")
                self.delete(chat_id, msg_id)
        
        elif data.startswith("msg_"):
            self.answer(cid)
            if not self.can_give_items(username): return
            pid = data[4:]
            if pid in self.pending:
                self.states[uid] = {"action": "approve_msg", "pid": pid}
                self.send(chat_id, f"💬 Введите сообщение для заказа #{pid}:", self.back_button())
                self.delete(chat_id, msg_id)
        
        elif data.startswith("no_"):
            self.answer(cid, "❌ Отклонено!")
            if not self.can_give_items(username): return
            pid = data[3:]
            if pid in self.pending:
                p = self.pending[pid]
                p["status"] = "rejected"
                p["rejected_by"] = username
                self.save_pending()
                for h in self.history:
                    if h["id"] == pid:
                        h["status"] = "rejected"
                        h["rejected_by"] = username
                self.save_history()
                self.send(int(p["uid"]), f"❌ Заказ #{pid} отклонен.")
                self.delete(chat_id, msg_id)
        
        elif data == "prices":
            self.answer(cid)
            if not self.can_manage_prices(username): return
            self.edit(chat_id, msg_id, "💰 Управление ценами:", self.prices_menu())
        
        elif data.startswith("edit_"):
            self.answer(cid)
            if not self.can_manage_prices(username): return
            key = data[5:]
            self.states[uid] = {"action": "edit_price", "key": key}
            self.edit(chat_id, msg_id, f"💰 Новая цена для {key}:", self.back_button())
        
        elif data == "admin_back":
            self.answer(cid)
            self.edit(chat_id, msg_id, "🔐 Админ-панель:", self.admin_panel(username))
        
        elif data == "promos":
            self.answer(cid)
            if not self.can_manage_promos(username): return
            self.edit(chat_id, msg_id, "🎫 Управление промокодами:", self.promos_menu())
        
        elif data == "create_discount":
            self.answer(cid)
            if not self.can_manage_promos(username): return
            self.states[uid] = {"action": "create_discount"}
            self.edit(chat_id, msg_id, "🏷️ Введите код промокода:", self.back_button())
        
        elif data == "create_money_promo":
            self.answer(cid)
            if not self.can_manage_promos(username): return
            self.states[uid] = {"action": "create_money_promo_code"}
            self.edit(chat_id, msg_id, "💰 Введите код промокода на деньги:", self.back_button())
        
        elif data == "list_promos":
            self.answer(cid)
            txt = "🎫 Скидочные промокоды:\n"
            for c, d in self.promos["discount"].items():
                txt += f"\n{c} - {d['discount']}% ({d['used']}/{d['max'] if d['max'] else '∞'})"
            txt += "\n\n💰 Денежные промокоды:\n"
            for c, d in self.promos["money"].items():
                txt += f"\n{c} - {d['amount']}р ({d['used']}/{d['max'] if d['max'] else '∞'})"
            self.edit(chat_id, msg_id, txt, self.promos_menu())
        
        elif data == "delete_promo":
            self.answer(cid)
            if not self.can_manage_promos(username): return
            self.states[uid] = {"action": "delete_promo"}
            self.edit(chat_id, msg_id, "🗑 Введите код промокода для удаления:", self.back_button())
        
        elif data == "stats":
            self.answer(cid)
            total = len(self.users)
            purchases = sum(1 for h in self.history if h["status"] == "done")
            revenue = sum(h["price"] for h in self.history if h["status"] == "done")
            txt = f"📊 Статистика\n\n👥 Пользователей: {total}\n🛍 Покупок: {purchases}\n💰 Оборот: {revenue}р"
            self.edit(chat_id, msg_id, txt, self.admin_panel(username))
        
        elif data == "history":
            self.answer(cid)
            txt = "📜 Последние 10:\n\n"
            for h in self.history[-10:][::-1]:
                s = "✅" if h["status"] == "done" else "⏳" if h["status"] == "pending" else "❌"
                admin_info = f" (@{h.get('completed_by', '')})" if h.get("completed_by") else ""
                txt += f"{s} #{h['id']} {h['item']} - {h['price']}р\n   {h['user']}{admin_info}\n\n"
            self.edit(chat_id, msg_id, txt, self.admin_panel(username))
        
        elif data == "users":
            self.answer(cid)
            txt = f"👥 Пользователи ({len(self.users)}):\n\n"
            for u in list(self.users.values())[-10:][::-1]:
                txt += f"• {u['name']} (@{u['user']})\n  🛍 {u.get('purchases', 0)}, 💰 {u.get('spent', 0)}р\n\n"
            self.edit(chat_id, msg_id, txt, self.admin_panel(username))
        
        elif data == "tickets":
            self.answer(cid)
            if not self.tickets:
                self.send(chat_id, "💬 Нет тикетов", self.back_button())
                return
            txt = "💬 Тикеты:\n\n"
            for tuid, t in list(self.tickets.items())[:10]:
                status = "🟢" if t["status"] == "open" else "🔴"
                txt += f"{status} @{t['username']} - {len(t['messages'])} сообщ.\n"
            self.edit(chat_id, msg_id, txt, self.admin_panel(username))
        
        elif data == "manage_balance":
            self.answer(cid)
            if not self.can_manage_balance(username): return
            self.edit(chat_id, msg_id, "💎 Управление балансом:", self.manage_balance_menu())
        
        elif data == "give_balance":
            self.answer(cid)
            if not self.can_manage_balance(username): return
            self.states[uid] = {"action": "give_balance_username"}
            self.edit(chat_id, msg_id, "👤 Введите username получателя (без @):", self.back_button())
        
        elif data == "take_balance":
            self.answer(cid)
            if not self.can_manage_balance(username): return
            self.states[uid] = {"action": "take_balance_username"}
            self.edit(chat_id, msg_id, "👤 Введите username для списания (без @):", self.back_button())
        
        elif data == "balance_pending":
            self.answer(cid)
            if not self.can_manage_balance(username): return
            if not self.balance_pending:
                self.send(chat_id, "⏳ Нет заявок на пополнение", self.back_button())
                return
            for pid, p in list(self.balance_pending.items())[:10]:
                if p["status"] == "pending":
                    txt = f"💰 Заявка #{pid}\n👤 {p['name']} (@{p['username']})\n💎 Сумма: {p['amount']}р"
                    kb = {"inline_keyboard": [
                        [{"text": "✅ Подтвердить", "callback_data": f"approve_bal_{pid}"}],
                        [{"text": "❌ Отклонить", "callback_data": f"reject_bal_{pid}"}]
                    ]}
                    if p.get("file_id"):
                        api_request("sendPhoto", {"chat_id": chat_id, "photo": p["file_id"], "caption": txt, "reply_markup": json.dumps(kb)})
                    else:
                        self.send(chat_id, txt, kb)
        
        elif data.startswith("approve_bal_"):
            self.answer(cid, "✅ Подтверждено!")
            pid = data[12:]
            if pid in self.balance_pending:
                p = self.balance_pending[pid]
                p["status"] = "approved"
                p["approved_by"] = username
                self.save_balance_pending()
                self.add_balance(p["uid"], p["amount"])
                self.send(int(p["uid"]), f"✅ Ваш баланс пополнен на {p['amount']}р!")
                self.delete(chat_id, msg_id)
        
        elif data.startswith("reject_bal_"):
            self.answer(cid, "❌ Отклонено!")
            pid = data[11:]
            if pid in self.balance_pending:
                p = self.balance_pending[pid]
                p["status"] = "rejected"
                p["rejected_by"] = username
                self.save_balance_pending()
                self.send(int(p["uid"]), f"❌ Заявка на пополнение отклонена.")
                self.delete(chat_id, msg_id)
        
        elif data == "manage_admins":
            self.answer(cid)
            if not self.can_manage_admins(username): return
            self.edit(chat_id, msg_id, "👑 Управление админами:", self.manage_admins_menu())
        
        elif data == "add_admin":
            self.answer(cid)
            if not self.can_manage_admins(username): return
            self.states[uid] = {"action": "add_admin_username"}
            self.edit(chat_id, msg_id, "➕ Введите username нового админа (без @):", self.back_button())
        
        elif data == "list_admins":
            self.answer(cid)
            txt = "👑 Админы:\n\n👑 @Senko_live - Главный\n"
            for admin, rights in self.admins.items():
                txt += f"├ @{admin} - Ур.{rights.get('level', 0)} ({rights.get('added_by', 'system')})\n"
            self.edit(chat_id, msg_id, txt, self.manage_admins_menu())
        
        elif data == "remove_admin":
            self.answer(cid)
            if not self.can_manage_admins(username): return
            self.states[uid] = {"action": "remove_admin_username"}
            self.edit(chat_id, msg_id, "➖ Введите username для снятия (без @):", self.back_button())
        
        elif data == "add_news":
            self.answer(cid)
            if self.get_admin_level(username) < 2: return
            self.states[uid] = {"action": "add_news"}
            self.edit(chat_id, msg_id, "📢 Введите текст новости:", self.back_button())
        
        elif data == "reset_discounts":
            self.answer(cid, "🔄 Сброшено!")
            if self.get_admin_level(username) < 2: return
            self.user_discounts = {}
            self.save_discounts()
            self.edit(chat_id, msg_id, "✅ Все скидки сброшены!", self.admin_panel(username))
        
        elif data == "pass":
            self.answer(cid)
            if username.lower() != MASTER_ADMIN.lower(): return
            self.states[uid] = {"action": "new_pass"}
            self.edit(chat_id, msg_id, "🔑 Введите новый пароль:", self.back_button())

    def run(self):
        while True:
            try:
                self.process()
            except KeyboardInterrupt:
                print("Стоп!")
                break
            except Exception as e:
                print(f"Ошибка: {e}")
                time.sleep(5)

if __name__ == "__main__":
    ShopBot().run()