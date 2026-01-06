import requests
import json
from datetime import datetime

class WeatherService:
    def __init__(self):
        self.geocoding_url = "https://geocoding-api.open-meteo.com/v1/search"
        self.weather_url = "https://api.open-meteo.com/v1/forecast"
        self.weather_codes = {
            0: "晴", 1: "多云", 2: "多云", 3: "阴",
            45: "雾", 48: "冻雾",
            51: "小毛毛雨", 53: "毛毛雨", 55: "大毛毛雨",
            56: "冻毛毛雨", 57: "大冻毛毛雨",
            61: "小雨", 63: "中雨", 65: "大雨",
            66: "冻雨", 67: "大冻雨",
            71: "小雪", 73: "中雪", 75: "大雪",
            77: "雪粒",
            80: "小阵雨", 81: "中阵雨", 82: "大阵雨",
            85: "小阵雪", 86: "大阵雪",
            95: "雷雨", 96: "雷雨伴有冰雹", 99: "大雷雨伴有冰雹"
        }

    def _normalize_city_name(self, name: str):
        if not name:
            return None
        s = str(name).strip()
        if not s:
            return None

        for suffix in [
            "特别行政区",
            "自治区",
            "自治州",
            "地区",
            "盟",
            "省",
            "市",
            "区",
            "县",
        ]:
            if s.endswith(suffix) and len(s) > len(suffix):
                s = s[: -len(suffix)]
                break

        return s.strip() or None

    def get_location_by_ip(self):
        """通过IP自动获取城市"""
        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        # 增加国内IP查询接口
        providers = [
            ("https://r.inews.qq.com/api/ip2city", "qqnews"),
            ("https://api.vore.top/api/IPdata?ip=", "vore"),
            ("https://whois.pconline.com.cn/ipJson.jsp?json=true", "pconline"),
            ("http://ip-api.com/json/?lang=zh-CN", "ip-api"),
            ("https://api.ip.sb/geoip", "ipsb"), 
            ("https://myip.ipip.net/json", "ipip"),
            ("https://ipapi.co/json/", "ipapi"),
            ("https://ipinfo.io/json", "ipinfo"),
        ]

        for url, provider in providers:
            try:
                res = requests.get(url, timeout=5, headers=headers)
                if res.status_code != 200:
                    continue
                if provider == "pconline":
                    try:
                        res.encoding = res.encoding or "GBK"
                        data = json.loads(res.text.strip())
                    except Exception:
                        continue
                else:
                    data = res.json()
                
                if provider == "pconline":
                    city = data.get("city") or data.get("pro")
                    city = self._normalize_city_name(city)
                    if city:
                        return city

                elif provider == "vore":
                    if data.get("code") == 200:
                        ipdata = data.get("ipdata") or {}
                        city = ipdata.get("info2") or ipdata.get("info1")
                        city = self._normalize_city_name(city)
                        if city:
                            return city

                elif provider == "qqnews":
                    if data.get("ret") == 0:
                        city = data.get("city") or data.get("province")
                        city = self._normalize_city_name(city)
                        if city:
                            return city

                elif provider == "ip-api":
                    if data.get("status") == "success":
                        city = data.get("city") or data.get("regionName")
                        city = self._normalize_city_name(city)
                        if city:
                            return city
                            
                elif provider == "ipsb":
                    city = data.get("city") or data.get("region")
                    city = self._normalize_city_name(city)
                    if city:
                        return city
                        
                elif provider == "ipip":
                    # ipip returns data like: {"ret": "ok", "data": {"ip": "...", "location": ["中国", "广东", "深圳", "", "电信"]}}
                    # Or simple json structure depending on endpoint. 
                    # The myip.ipip.net/json return: {"ret": "ok", "data": { ... "location": ["中国", "四川", "成都", "", "移动"] } }
                    if data.get("ret") == "ok" and "data" in data:
                        loc = data["data"].get("location", [])
                        if len(loc) >= 3 and loc[2]:
                            city = self._normalize_city_name(loc[2])
                            if city:
                                return city

                elif provider in ["ipapi", "ipinfo"]:
                    city = data.get("city") or data.get("region")
                    city = self._normalize_city_name(city) or (str(city).strip() if city else None)
                    if city:
                        return city
            except Exception as e:
                print(f"IP provider {provider} failed: {e}")
                continue

        return None

    def get_weather(self, city_name):
        """获取城市天气"""
        try:
            candidates = []
            if city_name:
                candidates.append(str(city_name).strip())
            normalized = self._normalize_city_name(city_name)
            if normalized and normalized not in candidates:
                candidates.append(normalized)

            location = None
            for name in candidates:
                geo_params = {
                    "name": name,
                    "count": 1,
                    "language": "zh",
                    "format": "json"
                }
                geo_res = requests.get(self.geocoding_url, params=geo_params, timeout=5)
                if geo_res.status_code != 200:
                    continue
                geo_data = geo_res.json()
                if geo_data.get("results"):
                    location = geo_data["results"][0]
                    city_name = name
                    break

            if not location:
                return {"error": "未找到该城市"}

            lat = location["latitude"]
            lon = location["longitude"]
            
            # 2. Weather Forecast
            weather_params = {
                "latitude": lat,
                "longitude": lon,
                "current_weather": "true",
                "daily": "temperature_2m_max,temperature_2m_min",
                "timezone": "auto"
            }
            weather_res = requests.get(self.weather_url, params=weather_params, timeout=5)
            if weather_res.status_code != 200:
                return {"error": "无法获取天气信息"}
                
            weather_data = weather_res.json()
            current = weather_data.get("current_weather", {})
            daily = weather_data.get("daily", {})
            
            weather_code = current.get("weathercode", 0)
            status = self.weather_codes.get(weather_code, "未知")
            temp = current.get("temperature")
            
            temp_max = daily.get("temperature_2m_max", [0])[0] if daily.get("temperature_2m_max") else 0
            temp_min = daily.get("temperature_2m_min", [0])[0] if daily.get("temperature_2m_min") else 0
            
            return {
                "city": city_name,
                "status": status,
                "temperature": temp,
                "temp_max": temp_max,
                "temp_min": temp_min,
                "code": weather_code
            }
            
        except Exception as e:
            return {"error": str(e)}

    def get_weather_icon_name(self, code):
        """根据天气代码返回图标名称（对应ttkbootstrap/emoji）"""
        if code == 0: return "☀️"
        if code in [1, 2, 3]: return "☁️"
        if code in [45, 48]: return "🌫️"
        if code in [51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82]: return "🌧️"
        if code in [71, 73, 75, 77, 85, 86]: return "❄️"
        if code in [95, 96, 99]: return "⚡"
        return "❓"
