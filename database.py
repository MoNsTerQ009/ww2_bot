import os
import random
import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

class Database:
    def __init__(self):
        self.supabase: Client = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_KEY")
        )
    
    def get_user(self, user_id):
        """گرفتن اطلاعات کاربر با user_id"""
        result = self.supabase.table("users").select("*").eq("user_id", user_id).execute()
        if result.data:
            user = result.data[0]
            # گرفتن اسم کشور از جدول countries
            if user.get("country_id"):
                country_result = self.supabase.table("countries").select("name").eq("id", user["country_id"]).execute()
                if country_result.data:
                    user["country_name"] = country_result.data[0]["name"]
            return user
        return None
    
    def get_available_countries(self):
        """لیست کشورهای هنوز گرفته نشده"""
        result = self.supabase.table("countries").select("id, name").eq("is_taken", 0).execute()
        return result.data
    
    def is_country_available(self, country_id):
        """چک کردن اینکه کشور گرفته شده یا نه"""
        result = self.supabase.table("countries").select("is_taken").eq("id", country_id).execute()
        if result.data and result.data[0]["is_taken"] == 0:
            return True
        return False
    
    def register_user(self, user_id, username, country_id):
        """ثبت نام کاربر جدید"""
        # ثبت کاربر
        self.supabase.table("users").insert({
            "user_id": user_id,
            "username": username,
            "country_id": country_id,
            "money": 1000,
            "steel": 100,
            "oil": 100,
            "tech": 0,
            "rifles": 10,
            "tanks": 0,
            "planes": 0,
            "steel_factories": 1,
            "oil_factories": 1,
            "labs": 0
        }).execute()
        
        # آپدیت وضعیت کشور به گرفته شده
        self.supabase.table("countries").update({"is_taken": 1}).eq("id", country_id).execute()
    
    def get_other_countries(self, my_country_id):
        """لیست کشورهای دیگه به جز کشور خود کاربر"""
        result = self.supabase.table("users").select("country_id").neq("country_id", my_country_id).execute()
        country_ids = [row["country_id"] for row in result.data]
        if country_ids:
            countries_result = self.supabase.table("countries").select("id, name").in_("id", country_ids).execute()
            return countries_result.data
        return []
    
    def get_country_name(self, country_id):
        """گرفتن اسم کشور با ID"""
        result = self.supabase.table("countries").select("name").eq("id", country_id).execute()
        if result.data:
            return result.data[0]["name"]
        return "ناشناس"
    
    def build_steel_factory(self, user_id):
        """ساخت کارخانه فولاد"""
        user = self.get_user(user_id)
        if user["money"] >= 500:
            self.supabase.table("users").update({
                "money": user["money"] - 500,
                "steel_factories": user["steel_factories"] + 1
            }).eq("user_id", user_id).execute()
            return {"success": True, "message": "✅ کارخانه فولاد ساخته شد!"}
        return {"success": False, "message": "❌ پول کافی ندارید! (نیاز: 500)"}
    
    def build_oil_factory(self, user_id):
        """ساخت کارخانه نفت"""
        user = self.get_user(user_id)
        if user["money"] >= 500:
            self.supabase.table("users").update({
                "money": user["money"] - 500,
                "oil_factories": user["oil_factories"] + 1
            }).eq("user_id", user_id).execute()
            return {"success": True, "message": "✅ کارخانه نفت ساخته شد!"}
        return {"success": False, "message": "❌ پول کافی ندارید! (نیاز: 500)"}
    
    def build_lab(self, user_id):
        """ساخت آزمایشگاه"""
        user = self.get_user(user_id)
        if user["money"] >= 1000:
            self.supabase.table("users").update({
                "money": user["money"] - 1000,
                "labs": user["labs"] + 1
            }).eq("user_id", user_id).execute()
            return {"success": True, "message": "✅ آزمایشگاه فناوری ساخته شد!"}
        return {"success": False, "message": "❌ پول کافی ندارید! (نیاز: 1000)"}
    
    def collect_daily_profit(self, user_id):
        """برداشت سود روزانه از کارخانه‌ها"""
        user = self.get_user(user_id)
        today = datetime.date.today().isoformat()
        
        if user.get("last_collect") == today:
            return {"success": False, "message": "❌ امروز قبلاً سود خود را برداشت کردی! فردا بیا."}
        
        # تولید رندوم بر اساس تعداد کارخانه‌ها
        steel_gain = random.randint(50, 100) * user["steel_factories"]
        oil_gain = random.randint(40, 80) * user["oil_factories"]
        tech_gain = random.randint(5, 15) * user["labs"]
        
        self.supabase.table("users").update({
            "steel": user["steel"] + steel_gain,
            "oil": user["oil"] + oil_gain,
            "tech": user["tech"] + tech_gain,
            "last_collect": today
        }).eq("user_id", user_id).execute()
        
        return {
            "success": True, 
            "steel": steel_gain, 
            "oil": oil_gain, 
            "tech": tech_gain
        }
    
    def purchase_item(self, user_id, item):
        """خرید از فروشگاه"""
        user = self.get_user(user_id)
        
        if item == "buy_rifle":
            if user["money"] >= 50:
                self.supabase.table("users").update({
                    "money": user["money"] - 50,
                    "rifles": user["rifles"] + 1
                }).eq("user_id", user_id).execute()
                return {"success": True, "message": "✅ یک قبضه تفنگ خریداری شد!"}
            return {"success": False, "message": "❌ پول کافی ندارید!"}
        
        elif item == "buy_tank":
            if user["steel"] >= 200 and user["money"] >= 100:
                self.supabase.table("users").update({
                    "steel": user["steel"] - 200,
                    "money": user["money"] - 100,
                    "tanks": user["tanks"] + 1
                }).eq("user_id", user_id).execute()
                return {"success": True, "message": "✅ یک تانک خریداری شد!"}
            return {"success": False, "message": "❌ منابع کافی ندارید! (نیاز: 200 فولاد + 100 پول)"}
        
        elif item == "buy_plane":
            if user["oil"] >= 200 and user["money"] >= 150:
                self.supabase.table("users").update({
                    "oil": user["oil"] - 200,
                    "money": user["money"] - 150,
                    "planes": user["planes"] + 1
                }).eq("user_id", user_id).execute()
                return {"success": True, "message": "✅ یک هواپیما خریداری شد!"}
            return {"success": False, "message": "❌ منابع کافی ندارید! (نیاز: 200 نفت + 150 پول)"}
        
        elif item == "upgrade_tech":
            if user["tech"] >= 50:
                self.supabase.table("users").update({
                    "tech": user["tech"] - 50
                }).eq("user_id", user_id).execute()
                return {"success": True, "message": "✅ فناوری ارتقاء یافت!"}
            return {"success": False, "message": "❌ فناوری کافی ندارید! (نیاز: 50)"}
        
        return {"success": False, "message": "❌ آیتم نامعتبر!"}
    
    def get_user_by_country_id(self, country_id):
        """گرفتن کاربر بر اساس country_id"""
        result = self.supabase.table("users").select("user_id, username").eq("country_id", country_id).execute()
        if result.data:
            return result.data[0]
        return None
    
    def execute_attack(self, attacker_id, target_country_id, rifles, tanks, planes):
        """اجرای حمله (توسط ادمین)"""
        attacker = self.get_user(attacker_id)
        defender = self.get_user_by_country_id(target_country_id)
        
        if not defender:
            return {
                "success": False,
                "message": "کشور مورد نظر یافت نشد!",
                "attacker_losses": "",
                "defender_losses": "",
                "loot": ""
            }
        
        # محاسبه قدرت
        attacker_power = rifles + (tanks * 3) + (planes * 5)
        
        # گرفتن اطلاعات مدافع
        defender_data = self.get_user(defender["user_id"])
        defender_power = defender_data["rifles"] + (defender_data["tanks"] * 3) + (defender_data["planes"] * 5)
        
        # شانس پیروزی
        total_power = attacker_power + defender_power
        attacker_chance = (attacker_power / total_power) * 100 if total_power > 0 else 50
        is_win = random.randint(1, 100) <= attacker_chance
        
        # محاسبه تلفات
        if is_win:
            attacker_loss_rate = random.uniform(0.2, 0.5)
            defender_loss_rate = random.uniform(0.6, 0.9)
        else:
            attacker_loss_rate = random.uniform(0.6, 0.9)
            defender_loss_rate = random.uniform(0.2, 0.5)
        
        attacker_losses = {
            "rifles": int(rifles * attacker_loss_rate),
            "tanks": int(tanks * attacker_loss_rate),
            "planes": int(planes * attacker_loss_rate)
        }
        
        defender_losses = {
            "rifles": int(defender_data["rifles"] * defender_loss_rate),
            "tanks": int(defender_data["tanks"] * defender_loss_rate),
            "planes": int(defender_data["planes"] * defender_loss_rate)
        }
        
        # اعمال تلفات به مهاجم
        self.supabase.table("users").update({
            "rifles": attacker["rifles"] - attacker_losses["rifles"],
            "tanks": attacker["tanks"] - attacker_losses["tanks"],
            "planes": attacker["planes"] - attacker_losses["planes"]
        }).eq("user_id", attacker_id).execute()
        
        # اعمال تلفات به مدافع
        self.supabase.table("users").update({
            "rifles": defender_data["rifles"] - defender_losses["rifles"],
            "tanks": defender_data["tanks"] - defender_losses["tanks"],
            "planes": defender_data["planes"] - defender_losses["planes"]
        }).eq("user_id", defender["user_id"]).execute()
        
        # غارت در صورت پیروزی
        if is_win:
            loot_money = random.randint(200, 800)
            loot_steel = random.randint(50, 200)
            loot_oil = random.randint(50, 200)
            
            self.supabase.table("users").update({
                "money": attacker["money"] + loot_money,
                "steel": attacker["steel"] + loot_steel,
                "oil": attacker["oil"] + loot_oil
            }).eq("user_id", attacker_id).execute()
            
            self.supabase.table("users").update({
                "money": defender_data["money"] - loot_money,
                "steel": defender_data["steel"] - loot_steel,
                "oil": defender_data["oil"] - loot_oil
            }).eq("user_id", defender["user_id"]).execute()
            
            loot_text = f"💰 {loot_money} پول + 🏭 {loot_steel} فولاد + ⛽ {loot_oil} نفت"
        else:
            loot_text = "هیچ غارتی به دست نیامد"
        
        target_name = self.get_country_name(target_country_id)
        attacker_name = attacker["country_name"]
        
        return {
            "success": is_win,
            "message": f"{'✅ پیروزی' if is_win else '❌ شکست'}! شما {'پیروز شدید' if is_win else 'شکست خوردید'}.",
            "defender_message": f"{'❌ شکست' if is_win else '✅ پیروزی'}! شما {'شکست خوردید' if is_win else 'پیروز شدید'}.",
            "attacker_losses": f"🔫 {attacker_losses['rifles']} تفنگ | 💣 {attacker_losses['tanks']} تانک | ✈️ {attacker_losses['planes']} هواپیما",
            "defender_losses": f"🔫 {defender_losses['rifles']} تفنگ | 💣 {defender_losses['tanks']} تانک | ✈️ {defender_losses['planes']} هواپیما",
            "loot": loot_text,
            "attacker_country": attacker_name,
            "target_country": target_name
        }