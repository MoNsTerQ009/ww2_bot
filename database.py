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
        result = self.supabase.table("users").select("*").eq("user_id", user_id).execute()
        if result.data:
            user = result.data[0]
            if user.get("country_id"):
                country_result = self.supabase.table("countries").select("name").eq("id", user["country_id"]).execute()
                if country_result.data:
                    user["country_name"] = country_result.data[0]["name"]
            return user
        return None
    
    def get_available_countries(self):
        result = self.supabase.table("countries").select("id, name").eq("is_taken", 0).execute()
        return result.data
    
    def is_country_available(self, country_id):
        result = self.supabase.table("countries").select("is_taken").eq("id", country_id).execute()
        if result.data and result.data[0]["is_taken"] == 0:
            return True
        return False
    
    def register_user(self, user_id, username, country_id):
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
        
        self.supabase.table("countries").update({"is_taken": 1}).eq("id", country_id).execute()
    
    def get_other_countries(self, my_country_id):
        result = self.supabase.table("users").select("country_id").neq("country_id", my_country_id).execute()
        country_ids = [row["country_id"] for row in result.data]
        if country_ids:
            countries_result = self.supabase.table("countries").select("id, name").in_("id", country_ids).execute()
            return countries_result.data
        return []
    
    def get_country_name(self, country_id):
        result = self.supabase.table("countries").select("name").eq("id", country_id).execute()
        if result.data:
            return result.data[0]["name"]
        return "ناشناس"
    
    def build_steel_factory(self, user_id):
        user = self.get_user(user_id)
        if user["money"] >= 500:
            self.supabase.table("users").update({
                "money": user["money"] - 500,
                "steel_factories": user["steel_factories"] + 1
            }).eq("user_id", user_id).execute()
            return {"success": True, "message": "✅ کارخانه فولاد ساخته شد!"}
        return {"success": False, "message": "❌ پول کافی ندارید! (نیاز: 500)"}
    
    def build_oil_factory(self, user_id):
        user = self.get_user(user_id)
        if user["money"] >= 500:
            self.supabase.table("users").update({
                "money": user["money"] - 500,
                "oil_factories": user["oil_factories"] + 1
            }).eq("user_id", user_id).execute()
            return {"success": True, "message": "✅ کارخانه نفت ساخته شد!"}
        return {"success": False, "message": "❌ پول کافی ندارید! (نیاز: 500)"}
    
    def build_lab(self, user_id):
        user = self.get_user(user_id)
        if user["money"] >= 1000:
            self.supabase.table("users").update({
                "money": user["money"] - 1000,
                "labs": user["labs"] + 1
            }).eq("user_id", user_id).execute()
            return {"success": True, "message": "✅ آزمایشگاه فناوری ساخته شد!"}
        return {"success": False, "message": "❌ پول کافی ندارید! (نیاز: 1000)"}
    
    def collect_daily_profit(self, user_id):
        user = self.get_user(user_id)
        today = datetime.date.today().isoformat()
        
        if user.get("last_collect") == today:
            return {"success": False, "message": "❌ امروز قبلاً سود خود را برداشت کردی!"}
        
        steel_gain = random.randint(50, 100) * user["steel_factories"]
        oil_gain = random.randint(40, 80) * user["oil_factories"]
        tech_gain = random.randint(5, 15) * user["labs"]
        
        self.supabase.table("users").update({
            "steel": user["steel"] + steel_gain,
            "oil": user["oil"] + oil_gain,
            "tech": user["tech"] + tech_gain,
            "last_collect": today
        }).eq("user_id", user_id).execute()
        
        return {"success": True, "steel": steel_gain, "oil": oil_gain, "tech": tech_gain}
    
    def purchase_item(self, user_id, item):
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
            return {"success": False, "message": "❌ منابع کافی ندارید!"}
        
        elif item == "buy_plane":
            if user["oil"] >= 200 and user["money"] >= 150:
                self.supabase.table("users").update({
                    "oil": user["oil"] - 200,
                    "money": user["money"] - 150,
                    "planes": user["planes"] + 1
                }).eq("user_id", user_id).execute()
                return {"success": True, "message": "✅ یک هواپیما خریداری شد!"}
            return {"success": False, "message": "❌ منابع کافی ندارید!"}
        
        elif item == "upgrade_tech":
            if user["tech"] >= 50:
                self.supabase.table("users").update({
                    "tech": user["tech"] - 50
                }).eq("user_id", user_id).execute()
                return {"success": True, "message": "✅ فناوری ارتقاء یافت!"}
            return {"success": False, "message": "❌ فناوری کافی ندارید!"}
        
        return {"success": False, "message": "❌ آیتم نامعتبر!"}
    
    def get_user_by_country_id(self, country_id):
        result = self.supabase.table("users").select("user_id").eq("country_id", country_id).execute()
        if result.data:
            return result.data[0]
        return None
