"""
集成功能模块 - 基于everyday项目的日历、天气、一诗一图、早报功能
"""
import os
import requests
import json
import datetime
import cnlunar
from PIL import Image
import tkinter as tk
from tkinter import messagebox, scrolledtext
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import threading
import urllib3

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class IntegratedFeaturesManager:
    def __init__(self):
        # API配置
        self.alapi_token = "heniptlw1z24ua5pcavpcp9nnmubti"  # ALAPI Token
        self.city = "北京"
        self.sentence_api = "https://v1.jinrishici.com/all.json"
        self.sentence_token = ""
        self.zhipu_api_key = ""  # 智谱AI API Key
        
        # 缓存设置
        self.cache_dir = os.path.join(os.getenv('APPDATA', ''), 'WallpaperApp')
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # 数据缓存
        self.weather_cache = None
        self.calendar_cache = None
        self.poetry_cache = None
        self.last_update = {}
        
    def get_inspirational_quote(self):
        """获取励志语"""
        try:
            current_date = datetime.datetime.now().strftime("%Y-%m-%d")
            url = f"https://open.iciba.com/dsapi/?date={current_date}"
            response = requests.get(url, timeout=10, verify=False)
            if response.status_code == 200:
                data = response.json()
                content = data.get("content", "")
                note = data.get("note", "")
                return f"{content}\n{note}" if content and note else "今天也要加油哦！"
            else:
                return "今天也要加油哦！"
        except Exception as e:
            return "今天也要加油哦！"
    
    def get_60s_news(self):
        """获取60秒读懂世界新闻"""
        import re
        
        def clean_text_thoroughly(text):
            """彻底清理文本中的序号"""
            if not text:
                return ""
            
            clean_text = text.strip()
            max_iterations = 10  # 防止无限循环
            iteration = 0
            
            while iteration < max_iterations:
                original = clean_text
                
                # 移除各种序号格式（更全面的正则表达式）
                patterns = [
                    r'^\d+[.、）)】]\s*',           # 1. 2、 3） 4) 5】
                    r'^[\(（]\d+[\)）]\s*',         # (1) （2）
                    r'^【\d+】\s*',                # 【1】
                    r'^[•·▪▫◦‣⁃]\s*',             # 各种点符号
                    r'^\d+\s*[.、）)】]\s*',       # 数字后面有空格的情况
                    r'^\s*\d+[.、）)】]\s*',       # 前面有空格的情况
                    r'^第\d+[条项]\s*',            # 第1条 第2项
                    r'^\d+\s+',                   # 纯数字后面跟空格
                ]
                
                for pattern in patterns:
                    clean_text = re.sub(pattern, '', clean_text)
                
                clean_text = clean_text.strip()
                
                # 如果没有变化，说明清理完成
                if clean_text == original:
                    break
                    
                iteration += 1
            
            return clean_text
        
        try:
            url = 'https://60s-api.viki.moe/v2/60s'
            response = requests.get(url, timeout=10, verify=False)
            if response.ok:
                data = response.json()
                news_data = data.get("data", {})
                news_list = news_data.get("news", [])
                if news_list:
                    cleaned_news = []
                    for i, news in enumerate(news_list[:10], 1):  # 限制显示前10条，从1开始编号
                        clean_item = clean_text_thoroughly(news)
                        if clean_item:
                            cleaned_news.append(f"{i}. {clean_item}")
                    return "\n".join(cleaned_news)
                else:
                    return "暂无新闻数据"
            else:
                return "获取新闻失败"
        except Exception as e:
            return f"获取新闻失败: {str(e)}"
    
    def get_calendar_info(self):
        """获取日历信息（公历+农历）"""
        try:
            today = datetime.datetime.now()
            cntoday = cnlunar.Lunar(today, godType='8char')
            
            calendar_info = {
                'date': f'{today.year}年{today.month}月{today.day}日',
                'weekday': cntoday.weekDayCn,
                'lunar_year': cntoday.year8Char,
                'zodiac': cntoday.chineseYearZodiac,
                'lunar_month': cntoday.lunarMonthCn,
                'lunar_day': cntoday.lunarDayCn,
                'solar_term': cntoday.todaySolarTerms if cntoday.todaySolarTerms else '无',
                'next_solar_term': cntoday.nextSolarTerm,
                'next_solar_term_date': f'{cntoday.nextSolarTermYear}{cntoday.nextSolarTermDate}'
            }
            
            self.calendar_cache = calendar_info
            self.last_update['calendar'] = datetime.datetime.now()
            return calendar_info
            
        except Exception as e:
            return {
                'date': datetime.datetime.now().strftime('%Y年%m月%d日'),
                'weekday': '星期' + ['一', '二', '三', '四', '五', '六', '日'][datetime.datetime.now().weekday()],
                'error': str(e)
            }
    
    def get_weather_info(self):
        """获取天气信息 - 使用免费天气API"""
        try:
            # 使用免费天气API接口
            url = "https://v2.xxapi.cn/api/weather"
            params = {
                'city': self.city
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if data.get('code') == 200 and data.get('data'):
                weather_data = data['data']
                today_data = weather_data['data'][0] if weather_data.get('data') else {}
                
                # 解析温度范围
                temp_range = today_data.get('temperature', '0-0℃')
                temp_parts = temp_range.replace('℃', '').split('-')
                min_temp = float(temp_parts[0]) if len(temp_parts) > 0 else 0
                max_temp = float(temp_parts[1]) if len(temp_parts) > 1 else min_temp
                current_temp = (min_temp + max_temp) / 2  # 估算当前温度
                
                weather_info = {
                    'status': today_data.get('weather', '未知'),
                    'temperature': current_temp,
                    'max_temp': max_temp,
                    'min_temp': min_temp,
                    'humidity': 0,  # 该API不提供湿度数据
                    'visibility': 0,  # 该API不提供能见度数据
                    'forecast': f"今日{today_data.get('weather', '')}，{today_data.get('wind', '')}",
                    'aqi': 0,  # 该API不提供AQI数据
                    'pm25': 0,  # 该API不提供PM2.5数据
                    'wind_dir': today_data.get('wind', '').split('风')[0] + '风' if '风' in today_data.get('wind', '') else '',
                    'wind_scale': today_data.get('wind', '').split('风')[1] if '风' in today_data.get('wind', '') else '',
                    'pressure': '',  # 该API不提供气压数据
                    'city': weather_data.get('city', self.city),
                    'air_quality': today_data.get('air_quality', '未知')
                }
                
                self.weather_cache = weather_info
                self.last_update['weather'] = datetime.datetime.now()
                return weather_info
            else:
                error_msg = data.get('msg', '获取天气数据失败')
                return {"error": f"获取天气数据失败: {error_msg}"}
                
        except Exception as e:
            return {"error": f"获取天气信息失败: {str(e)}"}
    
    def get_poetry_sentence(self):
        """获取诗词句子"""
        try:
            # 默认诗句
            default_sentence = "赏花归去马如飞，去马如飞酒力微。酒力微醒时已暮，醒时已暮赏花归。"
            
            headers = {}
            if self.sentence_token:
                headers["X-User-Token"] = self.sentence_token
                
            response = requests.get(self.sentence_api, headers=headers, timeout=10, verify=False)
            if response.ok:
                data = response.json()
                content = data.get("content", default_sentence)
                author = data.get("author", "")
                origin = data.get("origin", "")
                
                poetry_info = {
                    'content': content,
                    'author': author,
                    'origin': origin,
                    'full_text': f"{content}\n—— {author}《{origin}》" if author and origin else content
                }
                
                self.poetry_cache = poetry_info
                self.last_update['poetry'] = datetime.datetime.now()
                return poetry_info
            else:
                return {'content': default_sentence, 'full_text': default_sentence}
                
        except Exception as e:
            default_sentence = "赏花归去马如飞，去马如飞酒力微。酒力微醒时已暮，醒时已暮赏花归。"
            return {'content': default_sentence, 'full_text': default_sentence, 'error': str(e)}
    
    def set_api_keys(self, alapi_token="", zhipu_key="", sentence_token="", city=""):
        """设置API密钥和城市"""
        if alapi_token:
            self.alapi_token = alapi_token
        if zhipu_key:
            self.zhipu_api_key = zhipu_key
        if sentence_token:
            self.sentence_token = sentence_token
        if city:
            self.city = city
    
    def is_cache_valid(self, feature, hours=1):
        """检查缓存是否有效"""
        if feature not in self.last_update:
            return False
        
        last_time = self.last_update[feature]
        now = datetime.datetime.now()
        return (now - last_time).total_seconds() < hours * 3600
    
    def get_cached_or_fetch(self, feature):
        """获取缓存数据或重新获取"""
        if feature == 'calendar':
            if self.is_cache_valid('calendar', 24):  # 日历缓存24小时
                return self.calendar_cache
            return self.get_calendar_info()
        elif feature == 'weather':
            if self.is_cache_valid('weather', 1):  # 天气缓存1小时
                return self.weather_cache
            return self.get_weather_info()
        elif feature == 'poetry':
            if self.is_cache_valid('poetry', 6):  # 诗词缓存6小时
                return self.poetry_cache
            return self.get_poetry_sentence()
        else:
            return None


class IntegratedFeaturesWindow:
    def __init__(self, parent, features_manager):
        self.parent = parent
        self.features_manager = features_manager
        self.window = None
        
    def show_features_window(self):
        """显示集成功能窗口"""
        if self.window and self.window.winfo_exists():
            self.window.lift()
            return
            
        self.window = ttk.Toplevel(self.parent)
        self.window.title("每日信息 - 日历·天气·诗词")
        self.window.geometry("800x600")
        self.window.resizable(True, True)
        
        # 设置窗口图标
        try:
            icon_path = os.path.join(os.path.dirname(__file__), 'app_icon.ico')
            if os.path.exists(icon_path):
                self.window.iconbitmap(icon_path)
        except:
            pass
        
        self.setup_ui()
        self.load_all_data()
        
    def setup_ui(self):
        """设置UI界面"""
        # 创建主框架
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        # 顶部按钮栏
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=X, pady=(0, 10))
        
        ttk.Button(button_frame, text="刷新全部", command=self.refresh_all_data,
                  bootstyle=PRIMARY).pack(side=LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="设置", command=self.show_settings,
                  bootstyle=SECONDARY).pack(side=LEFT, padx=(0, 5))
        
        # 创建选项卡
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=BOTH, expand=True)
        
        # 日历选项卡
        self.calendar_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.calendar_frame, text="📅 日历")
        self.setup_calendar_tab()
        
        # 天气选项卡
        self.weather_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.weather_frame, text="🌤️ 天气")
        self.setup_weather_tab()
        
        # 诗词选项卡
        self.poetry_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.poetry_frame, text="📖 诗词")
        self.setup_poetry_tab()
        
        # 新闻选项卡
        self.news_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.news_frame, text="📰 新闻")
        self.setup_news_tab()
        
    def setup_calendar_tab(self):
        """设置日历选项卡"""
        # 日历信息显示区域
        calendar_info_frame = ttk.LabelFrame(self.calendar_frame, text="今日信息", padding=15)
        calendar_info_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        self.calendar_text = scrolledtext.ScrolledText(calendar_info_frame, height=15, 
                                                      font=("Microsoft YaHei", 12))
        self.calendar_text.pack(fill=BOTH, expand=True)
        
        # 刷新按钮
        ttk.Button(calendar_info_frame, text="刷新日历", 
                  command=self.refresh_calendar_data,
                  bootstyle=INFO).pack(pady=(10, 0))
        
    def setup_weather_tab(self):
        """设置天气选项卡"""
        # 天气信息显示区域
        weather_info_frame = ttk.LabelFrame(self.weather_frame, text="天气信息", padding=15)
        weather_info_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        self.weather_text = scrolledtext.ScrolledText(weather_info_frame, height=15,
                                                     font=("Microsoft YaHei", 12))
        self.weather_text.pack(fill=BOTH, expand=True)
        
        # 刷新按钮
        ttk.Button(weather_info_frame, text="刷新天气", 
                  command=self.refresh_weather_data,
                  bootstyle=INFO).pack(pady=(10, 0))
        
    def setup_poetry_tab(self):
        """设置诗词选项卡"""
        # 诗词显示区域
        poetry_info_frame = ttk.LabelFrame(self.poetry_frame, text="今日诗词", padding=15)
        poetry_info_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        self.poetry_text = scrolledtext.ScrolledText(poetry_info_frame, height=15,
                                                    font=("Microsoft YaHei", 14))
        self.poetry_text.pack(fill=BOTH, expand=True)
        
        # 刷新按钮
        ttk.Button(poetry_info_frame, text="换一首", 
                  command=self.refresh_poetry_data,
                  bootstyle=INFO).pack(pady=(10, 0))
        
    def setup_news_tab(self):
        """设置新闻选项卡"""
        # 新闻显示区域
        news_info_frame = ttk.LabelFrame(self.news_frame, text="60秒读懂世界", padding=15)
        news_info_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        self.news_text = scrolledtext.ScrolledText(news_info_frame, height=15,
                                                  font=("Microsoft YaHei", 11))
        self.news_text.pack(fill=BOTH, expand=True)
        
        # 刷新按钮
        ttk.Button(news_info_frame, text="刷新新闻", 
                  command=self.refresh_news_data,
                  bootstyle=INFO).pack(pady=(10, 0))
        
    def load_all_data(self):
        """加载所有数据"""
        threading.Thread(target=self._load_all_data_thread, daemon=True).start()
        
    def _load_all_data_thread(self):
        """在后台线程中加载所有数据"""
        self.refresh_calendar_data()
        self.refresh_weather_data()
        self.refresh_poetry_data()
        self.refresh_news_data()
        
    def refresh_calendar_data(self):
        """刷新日历数据"""
        def update_calendar():
            calendar_info = self.features_manager.get_calendar_info()
            if 'error' in calendar_info:
                text = f"获取日历信息失败: {calendar_info['error']}"
            else:
                text = f"""📅 今日日期
{calendar_info['date']} {calendar_info['weekday']}

🏮 农历信息
农历：{calendar_info.get('lunar_year', '')}【{calendar_info.get('zodiac', '')}】年 {calendar_info.get('lunar_month', '')}{calendar_info.get('lunar_day', '')}日

🌸 节气信息
今日节气：{calendar_info.get('solar_term', '无')}
下一节气：{calendar_info.get('next_solar_term', '')} {calendar_info.get('next_solar_term_date', '')}

💡 励志语
{self.features_manager.get_inspirational_quote()}"""
            
            self.calendar_text.delete(1.0, tk.END)
            self.calendar_text.insert(1.0, text)
            
        threading.Thread(target=update_calendar, daemon=True).start()
        
    def refresh_weather_data(self):
        """刷新天气数据"""
        def update_weather():
            weather_info = self.features_manager.get_weather_info()
            if 'error' in weather_info:
                text = f"获取天气信息失败:\n{weather_info['error']}\n\n请在设置中配置彩云天气API Key"
            else:
                text = f"""🌤️ 当前天气
天气：{weather_info['status']} 
温度：{weather_info['temperature']}℃ 【{weather_info['max_temp']}℃/{weather_info['min_temp']}℃】

💧 环境信息
湿度：{weather_info['humidity']:.1f}%
能见度：{weather_info['visibility']}km

🌬️ 空气质量
AQI：{weather_info['aqi']}
PM2.5：{weather_info['pm25']}

📊 天气预报
{weather_info['forecast']}"""
            
            self.weather_text.delete(1.0, tk.END)
            self.weather_text.insert(1.0, text)
            
        threading.Thread(target=update_weather, daemon=True).start()
        
    def refresh_poetry_data(self):
        """刷新诗词数据"""
        def update_poetry():
            poetry_info = self.features_manager.get_poetry_sentence()
            text = f"""📖 今日诗词

{poetry_info['full_text']}

{'=' * 40}

这首诗词来自古典文学，让我们在忙碌的生活中感受一份诗意与美好。"""
            
            self.poetry_text.delete(1.0, tk.END)
            self.poetry_text.insert(1.0, text)
            
        threading.Thread(target=update_poetry, daemon=True).start()
        
    def refresh_news_data(self):
        """刷新新闻数据"""
        def update_news():
            news_text = self.features_manager.get_60s_news()
            formatted_text = f"""📰 60秒读懂世界

{news_text}

{'=' * 40}
更新时间：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
            
            self.news_text.delete(1.0, tk.END)
            self.news_text.insert(1.0, formatted_text)
            
        threading.Thread(target=update_news, daemon=True).start()
        
    def refresh_all_data(self):
        """刷新所有数据"""
        self.load_all_data()
        
    def show_settings(self):
        """显示设置窗口"""
        settings_window = ttk.Toplevel(self.window)
        settings_window.title("功能设置")
        settings_window.geometry("500x400")
        settings_window.resizable(False, False)
        settings_window.transient(self.window)
        settings_window.grab_set()
        
        # API设置
        api_frame = ttk.LabelFrame(settings_window, text="API设置", padding=10)
        api_frame.pack(fill=X, padx=10, pady=10)
        
        # 彩云天气API
        ttk.Label(api_frame, text="彩云天气API Key:").pack(anchor=W)
        caiyun_var = tk.StringVar(value=self.features_manager.caiyun_key)
        ttk.Entry(api_frame, textvariable=caiyun_var, width=60).pack(fill=X, pady=(5, 10))
        
        # 位置设置
        location_frame = ttk.LabelFrame(settings_window, text="位置设置", padding=10)
        location_frame.pack(fill=X, padx=10, pady=10)
        
        ttk.Label(location_frame, text="城市:").pack(anchor=W)
        city_var = tk.StringVar(value=self.features_manager.city)
        ttk.Entry(location_frame, textvariable=city_var, width=60).pack(fill=X, pady=(5, 5))
        
        ttk.Label(location_frame, text="坐标 (经度,纬度):").pack(anchor=W)
        location_var = tk.StringVar(value=self.features_manager.location)
        ttk.Entry(location_frame, textvariable=location_var, width=60).pack(fill=X, pady=(5, 10))
        
        # 保存按钮
        def save_settings():
            self.features_manager.set_api_keys(
                caiyun_key=caiyun_var.get(),
                location=location_var.get(),
                city=city_var.get()
            )
            messagebox.showinfo("设置", "设置已保存！")
            settings_window.destroy()
            
        ttk.Button(settings_window, text="保存设置", command=save_settings,
                  bootstyle=PRIMARY).pack(pady=20)