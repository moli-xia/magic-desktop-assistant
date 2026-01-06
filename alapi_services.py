import requests
import json
import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from datetime import datetime
import threading
import urllib3

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class ALAPIManager:
    """ALAPI服务管理器"""
    
    def __init__(self):
        self.token = ""  # 移除硬编码Token，强制使用配置
        self.city = "北京" # 默认城市
        self.base_url = "https://v2.alapi.cn/api"
        self.cache = {}
        
        # 服务配置
        self.services = {
            'daily_news': {'name': '每日早报', 'endpoint': '/zaobao'},
            'hitokoto': {'name': '一言', 'endpoint': '/hitokoto'},
            'love_words': {'name': '土味情话', 'endpoint': '/qinghua'},
            'dog_diary': {'name': '舔狗日记', 'endpoint': '/dog'},
            'daily_article': {'name': '每日一文', 'endpoint': '/mryw'},
            'poetry': {'name': '每日诗词', 'endpoint': 'custom_poetry'}
        }
        
        # 格式化方法映射
        self.formatters = {
            'daily_news': self._format_daily_news,
            'hitokoto': self._format_hitokoto,
            'love_words': self._format_love_words,
            'dog_diary': self._format_dog_diary,
            'daily_article': self._format_daily_article,
            'poetry': self._format_poetry
        }
    
    def set_token(self, token):
        """设置API Token"""
        self.token = token

    def set_city(self, city):
        """设置城市"""
        if city:
            self.city = city

    
    def get_token(self):
        """获取API Token"""
        return self.token
    
    def fetch_service_data(self, service_key, **params):
        """获取服务数据"""
        if service_key not in self.services:
            return None
        
        service = self.services[service_key]
        
        # 处理自定义服务
        if service['endpoint'] == 'custom_poetry':
            return self._fetch_poetry_data()
            
        url = f"{self.base_url}{service['endpoint']}"
        
        # 准备请求参数
        request_params = {
            'token': self.token,
            'format': 'json'
        }
        
        request_params.update(params)
        
        try:
            response = requests.get(url, params=request_params, timeout=10, verify=False)
            response.raise_for_status()
            data = response.json()
            
            if data.get('code') == 200:
                return data.get('data', {})
            else:
                return {
                    'error': True,
                    'message': data.get('msg', '请求失败')
                }
        except Exception as e:
            return {
                'error': True,
                'message': f'网络请求失败: {str(e)}'
            }

    def _fetch_poetry_data(self):
        """获取诗词数据 (自定义)"""
        try:
            url = "https://v1.jinrishici.com/all.json"
            response = requests.get(url, timeout=10, verify=False)
            if response.ok:
                return response.json()
            else:
                return {'error': True, 'message': '获取诗词失败'}
        except Exception as e:
            return {'error': True, 'message': f'网络请求失败: {str(e)}'}

    
    def format_service_data(self, service_key, data):
        """格式化服务数据"""
        if not data or data.get('error'):
            return f"获取{self.services.get(service_key, {}).get('name', '数据')}失败: {data.get('message', '未知错误')}"
        
        formatter = self.formatters.get(service_key)
        if formatter:
            return formatter(data)
        else:
            return str(data)
    
    def clear_cache(self, service_key=None):
        """清除缓存"""
        if service_key:
            self.cache.pop(service_key, None)
        else:
            self.cache.clear()
    
    def _format_daily_news(self, data):
        """格式化每日早报"""
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
        
        formatted_text = "📰 每日早报\n\n"
        
        news_list = data.get('news', [])
        if not news_list:
            return formatted_text + "暂无新闻数据"
        
        for i, news_item in enumerate(news_list, 1):
            if isinstance(news_item, str):
                clean_item = clean_text_thoroughly(news_item)
                if clean_item:
                    formatted_text += f"{i}. {clean_item}\n\n"
            elif isinstance(news_item, dict):
                title = news_item.get('title', news_item.get('content', ''))
                clean_title = clean_text_thoroughly(title)
                if clean_title:
                    formatted_text += f"{i}. {clean_title}\n\n"
        
        # 添加日期信息
        date_info = data.get('date', datetime.now().strftime('%Y-%m-%d'))
        formatted_text += f"📅 日期: {date_info}"
        
        return formatted_text

    def _format_poetry(self, data):
        """格式化诗词数据"""
        content = data.get("content", "")
        author = data.get("author", "")
        origin = data.get("origin", "")
        
        formatted_text = "📖 每日诗词\n\n"
        formatted_text += f"{content}\n\n"
        if author and origin:
            formatted_text += f"—— {author}《{origin}》"
            
        return formatted_text

    def _format_hitokoto(self, data):
        """格式化一言"""
        formatted_text = "💭 一言\n\n"
        
        content = data.get('hitokoto', data.get('content', ''))
        author = data.get('from_who', data.get('author', ''))
        source = data.get('from', data.get('source', ''))
        
        formatted_text += f'"{content}"\n\n'
        
        if author or source:
            formatted_text += "—— "
            if author:
                formatted_text += author
            if source:
                if author:
                    formatted_text += f"《{source}》"
                else:
                    formatted_text += source
        
        return formatted_text
    
    def _format_love_words(self, data):
        """格式化土味情话"""
        formatted_text = "💕 土味情话\n\n"
        
        content = data.get('content', data.get('text', ''))
        formatted_text += f'"{content}"'
        
        return formatted_text
    
    def _format_dog_diary(self, data):
        """格式化舔狗日记"""
        formatted_text = "🐕 舔狗日记\n\n"
        
        content = data.get('content', data.get('text', ''))
        formatted_text += content
        
        return formatted_text
    
    def _format_daily_article(self, data):
        """格式化每日一文"""
        formatted_text = "📖 每日一文\n\n"
        
        title = data.get('title', '')
        author = data.get('author', '')
        content = data.get('content', data.get('text', ''))
        
        if title:
            formatted_text += f"《{title}》\n\n"
        
        if author:
            formatted_text += f"作者: {author}\n\n"
        
        formatted_text += content
        
        return formatted_text


from alapi_widgets import InfoPushWidget

class ALAPIWindow:
    """ALAPI服务窗口"""
    
    def __init__(self, parent, alapi_manager, on_settings_click=None):
        self.parent = parent
        self.alapi_manager = alapi_manager
        self.on_settings_click = on_settings_click
        self.window = None
        self.selected_services = []
        self.info_widget = None
    
    def show_services(self, selected_services):
        """显示选中的服务"""
        self.selected_services = selected_services
        self.show()
    
    def show(self):
        """显示窗口"""
        if self.window is None or not self.window.winfo_exists():
            self.window = ttk.Toplevel(self.parent)
            self.window.title("信息推送")
            # 设置默认尺寸并居中显示
            try:
                window_width = 800
                window_height = 600
                screen_width = self.window.winfo_screenwidth()
                screen_height = self.window.winfo_screenheight()
                x = (screen_width - window_width) // 2
                y = (screen_height - window_height) // 2
                self.window.geometry(f"{window_width}x{window_height}+{x}+{y}")
            except Exception:
                # 回退到原有固定尺寸
                self.window.geometry("800x600")
            self.window.resizable(True, True)
            
            # 设置窗口图标
            try:
                # 优先使用与主程序一致的多尺寸图标，确保任务栏小图标显示
                import os
                from PIL import Image, ImageTk
                icon_path = os.path.abspath("app_icon.ico")
                if os.path.exists(icon_path):
                    img = Image.open(icon_path)
                    sizes = [16, 24, 32, 48, 64]
                    photos = []
                    for size in sizes:
                        photos.append(ImageTk.PhotoImage(img.resize((size, size), Image.Resampling.LANCZOS)))
                    self.window.iconphoto(True, *photos)
                    self.window._icon_photos = photos
                else:
                    self.window.iconbitmap("app_icon.ico")
            except:
                pass
            
            self.setup_ui()
        
        self.window.deiconify()
        self.window.lift()
        self.window.focus_force()
        
        # 加载选中服务的内容
        if self.info_widget:
            self.info_widget.selected_services = self.selected_services
            self.info_widget.refresh_content()
    
    def setup_ui(self):
        """设置UI"""
        # 主框架
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        # 顶部按钮框架 (用于关闭按钮，其他按钮在InfoPushWidget中)
        # 为了保持一致性，我们可以在InfoPushWidget上方加一个包含关闭按钮的条，或者直接让InfoPushWidget占据主要空间
        # 这里我们简单地把关闭按钮放在底部或者顶部单独一行
        
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=X, pady=(0, 5))
        
        ttk.Button(top_frame, text="关闭窗口", 
                  command=self.window.destroy, 
                  bootstyle=DANGER).pack(side=RIGHT)

        # 使用 InfoPushWidget
        self.info_widget = InfoPushWidget(main_frame, self.alapi_manager, on_settings_click=self.on_settings_click)
        self.info_widget.pack(fill=BOTH, expand=True)

    def refresh_content(self):
        """刷新内容"""
        if self.info_widget:
            self.info_widget.refresh_content()
    
    def refresh_services(self, selected_services):
        """刷新指定服务"""
        self.selected_services = selected_services
        if self.info_widget:
            self.info_widget.selected_services = selected_services
            self.info_widget.refresh_content()
    
    def show_settings(self):
        """显示设置窗口 (Deprecated, delegated to on_settings_click callback or managed externally)"""
        # This method might be called internally if on_settings_click is not provided, 
        # but in our case main.py provides it.
        # If we need to keep it for backward compatibility:
        if self.on_settings_click:
            self.on_settings_click()
        else:
             # Fallback implementation if needed, or just pass
             pass
