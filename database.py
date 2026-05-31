import os
import random
import datetime
import json
import urllib.request
import urllib.error
from dotenv import load_dotenv

load_dotenv()

class Database:
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")
    
    def _request(self, method, endpoint, data=None):
        """ارسال درخواست ساده به Supabase"""
        url = f"{self.supabase_url}/rest/v1/{endpoint}"
        headers = {
            "apikey": self.supabase_key,
            "Authorization": f"Bearer {self.supabase_key}",
            "Content-Type": "application/json"
        }
        
        try:
            if method == "GET":
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req) as response:
                    return json.loads(response.read().decode())
            
            elif method == "POST":
                data_bytes = json.dumps(data).encode('utf-8')
                req = urllib.request.Request(url, data=data_bytes, headers=headers, method="POST")
                with urllib.request.urlopen(req) as response:
                    return json.loads(response.read().decode()) if response.getcode() != 204 else []
            
            elif method == "PATCH":
                data_bytes = json.dumps(data).encode('utf-8')
                req = urllib.request.Request(url, data=data_bytes, headers=headers, method="PATCH")
                with urllib.request.urlopen(req) as response:
                    return []
            
            return None
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def get_user(self, user_id):
        result = self._request("GET", f"users?user_id=eq.{user_id}")
        if result and len(result) > 0:
            user = result[0]
            country_result = self._request("GET", f"countries?id=eq.{user['country_id']}")
            if country_result and len(country_result) > 0:
                user["country_name"] = country_result[0]["name"]
            return user
        return None
    
    def get_available_countries(self):
        result = self._request("GET", "countries?is_taken=eq.0&select=id,name")
        return result if result else []
    
    def is_country_available(self, country_id):
        result = self._request("GET", f"countries?is_taken=eq.0&id=eq.{country_id}")
        return result and len(result) > 0
    
    def register_user(self, user_id, username, country_id):
        self._request("POST", "users", {
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
        })
        self._request("PATCH", f"countries?id=eq.{country_id}", {"is_taken": 1})
    
    def get_other_countries(self, my_country_id):
        result = self._request("GET", f"users?select=country_id&country_id=neq.{my_country_id}")
        if not result:
            return []
        country_ids = [str(row["country_id"]) for row in result]
        if country_ids:
            ids = ",".join(country_ids)
            countries = self._request("GET", f"countries?id=in.({ids})&select=id,name")
            return countries if countries else []
        return []
    
    def build_steel_factory(self, user_id):
        user = self.get_user(user_id)
        if user and user["money"] >= 500:
            self._request("PATCH", f"users?user_id=eq.{user_id}", {
                "money": user["money"] - 500,
                "steel_factories": user["steel_factories"] + 1
            })
            return {"success": True, "message": "✅ کارخانه فولاد ساخته شد!"}
        return {"success": False, "message": "❌ پول کافی ندارید!"}
    
    def build_oil_factory(self, user_id):
        user = self.get_user(user_id)
        if user and user["money"] >= 500:
            self._request("PATCH", f"users?user_id=eq.{user_id}", {
                "money": user["money"] - 500,
                "oil_factories": user["oil_factories"] + 1
            })
            return {"success": True, "message": "✅ کارخانه نفت ساخته شد!"}
        return {"success": False, "message": "❌ پول کافی ندارید!"}
    
    def build_lab(self, user_id):
        user = self.get_user(user_id)
        if user and user["money"] >= 1000:
            self._request("PATCH", f"users?user_id=eq.{user_id}", {
                "money": user["money"] - 1000,
                "labs": user["labs"] + 1
            })
            return {"success": True, "message": "✅ آزمایشگاه ساخته شد!"}
        return {"success": False, "message": "❌ پول کافی ندارید!"}
    
    def collect_daily_profit(self, user_id):
        user = self.get_user(user_id)
        today = datetime.date.today().isoformat()
        
        if user and user.get("last_collect") == today:
            return {"success": False, "message": "❌ امروز قبلاً برداشت کردی!"}
        
        steel_gain = random.randint(50, 100) * user["steel_factories"]
        oil_gain = random.randint(40, 80) * user["oil_factories"]
        tech_gain = random.randint(5, 15) * user["labs"]
        
        self._request("PATCH", f"users?user_id=eq.{user_id}", {
            "steel": user["steel"] + steel_gain,
            "oil": user["oil"] + oil_gain,
            "tech": user["tech"] + tech_gain,
            "last_collect": today
        })
        
        return {"success": True, "steel": steel_gain, "oil": oil_gain, "tech": tech_gain}
    
    def purchase_item(self, user_id, item):
        user = self.get_user(user_id)
        if not user:
            return {"success": False, "message": "❌ کاربر یافت نشد!"}
        
        if item == "buy_rifle":
            if user["money"] >= 50:
                self._request("PATCH", f"users?user_id=eq.{user_id}", {
                    "money": user["money"] - 50,
                    "rifles": user["rifles"] + 1
                })
                return {"success": True, "message": "✅ تفنگ خریداری شد!"}
            return {"success": False, "message": "❌ پول کافی ندارید!"}
        
        elif item == "buy_tank":
            if user["steel"] >= 200 and user["money"] >= 100:
                self._request("PATCH", f"users?user_id=eq.{user_id}", {
                    "steel": user["steel"] - 200,
                    "money": user["money"] - 100,
                    "tanks": user["tanks"] + 1
                })
                return {"success": True, "message": "✅ تانک خریداری شد!"}
            return {"success": False, "message": "❌ منابع کافی ندارید!"}
        
        elif item == "buy_plane":
            if user["oil"] >= 200 and user["money"] >= 150:
                self._request("PATCH", f"users?user_id=eq.{user_id}", {
                    "oil": user["oil"] - 200,
                    "money": user["money"] - 150,
                    "planes": user["planes"] + 1
                })
                return {"success": True, "message": "✅ هواپیما خریداری شد!"}
            return {"success": False, "message": "❌ منابع کافی ندارید!"}
        
        elif item == "upgrade_tech":
            if user["tech"] >= 50:
                self._request("PATCH", f"users?user_id=eq.{user_id}", {
                    "tech": user["tech"] - 50
                })
                return {"success": True, "message": "✅ فناوری ارتقاء یافت!"}
            return {"success": False, "message": "❌ فناوری کافی ندارید!"}
        
        return {"success": False, "message": "❌ آیتم نامعتبر!"}
    
    def get_user_by_country_id(self, country_id):
        result = self._request("GET", f"users?country_id=eq.{country_id}&select=user_id")
        if result and len(result) > 0:
            return result[0]
        return None
