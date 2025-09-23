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
        self.token = "heniptlw1z24ua5pcavpcp9nnmubti"  # 默认测试Token
        self.base_url = "https://v2.alapi.cn/api"
        self.cache = {}
        
        # 服务配置
        self.services = {
            'daily_news': {'name': '每日早报', 'endpoint': '/zaobao'},
            'weibo_hot': {'name': '微博热搜', 'endpoint': '/weibo/hot'},
            'hitokoto': {'name': '一言', 'endpoint': '/hitokoto'},
            'love_words': {'name': '土味情话', 'endpoint': '/qinghua'},
            'dog_diary': {'name': '舔狗日记', 'endpoint': '/dog'},
            'daily_article': {'name': '每日一文', 'endpoint': '/mryw'}
        }
        
        # 格式化方法映射
        self.formatters = {
            'daily_news': self._format_daily_news,
            'weibo_hot': self._format_weibo_hot,
            'hitokoto': self._format_hitokoto,
            'love_words': self._format_love_words,
            'dog_diary': self._format_dog_diary,
            'daily_article': self._format_daily_article
        }
    
    def set_token(self, token):
        """设置API Token"""
        self.token = token
    
    def get_token(self):
        """获取API Token"""
        return self.token
    
    def fetch_service_data(self, service_key, **params):
        """获取服务数据"""
        if service_key not in self.services:
            return None
        
        service = self.services[service_key]
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
    
    def _format_weibo_hot(self, data):
        """格式化微博热搜"""
        formatted_text = "🔥 微博热搜\n\n"
        
        hot_list = data.get('hot', [])
        if not hot_list:
            return formatted_text + "暂无热搜数据"
        
        for i, item in enumerate(hot_list[:10], 1):  # 只显示前10条
            title = item.get('title', item.get('keyword', ''))
            hot_value = item.get('hot', '')
            formatted_text += f"{i}. {title}"
            if hot_value:
                formatted_text += f" ({hot_value})"
            formatted_text += "\n\n"
        
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


class ALAPIWindow:
    """ALAPI服务窗口"""
    
    def __init__(self, parent, alapi_manager):
        self.parent = parent
        self.alapi_manager = alapi_manager
        self.window = None
        self.selected_services = []
    
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
        self.load_selected_services()
    
    def setup_ui(self):
        """设置UI"""
        # 主框架
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        # 顶部按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=X, pady=(0, 10))
        
        ttk.Button(button_frame, text="刷新内容", 
                  command=self.refresh_content, 
                  bootstyle=SUCCESS).pack(side=LEFT, padx=(0, 5))
        
        ttk.Button(button_frame, text="设置", 
                  command=self.show_settings, 
                  bootstyle=SECONDARY).pack(side=LEFT, padx=5)
        
        ttk.Button(button_frame, text="关闭", 
                  command=self.window.destroy, 
                  bootstyle=DANGER).pack(side=RIGHT)
        
        # 内容显示区域
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=BOTH, expand=True)
        
        # 创建滚动文本框
        self.content_text = tk.Text(content_frame, wrap=tk.WORD, font=("Microsoft YaHei", 10))
        scrollbar = ttk.Scrollbar(content_frame, orient=VERTICAL, command=self.content_text.yview)
        self.content_text.configure(yscrollcommand=scrollbar.set)
        
        self.content_text.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)
    
    def load_selected_services(self):
        """加载选中服务的内容"""
        if not self.selected_services:
            self._update_content("请先在主界面选择要查看的服务")
            return
        
        self._update_content("正在加载数据，请稍候...")
        
        # 在后台线程中加载数据
        threading.Thread(target=self._load_services_data, daemon=True).start()
    
    def _load_services_data(self):
        """在后台线程中加载服务数据"""
        content = ""
        
        for service_key in self.selected_services:
            service_name = self.alapi_manager.services.get(service_key, {}).get('name', service_key)
            
            try:
                # 获取数据
                data = self.alapi_manager.fetch_service_data(service_key)
                
                # 格式化数据
                formatted_data = self.alapi_manager.format_service_data(service_key, data)
                
                content += formatted_data + "\n\n" + "="*50 + "\n\n"
                
            except Exception as e:
                content += f"❌ 获取{service_name}失败: {str(e)}\n\n" + "="*50 + "\n\n"
        
        # 在主线程中更新UI
        self.window.after(0, lambda: self._update_content(content))
    
    def _update_content(self, content):
        """更新内容显示"""
        if hasattr(self, 'content_text'):
            self.content_text.delete(1.0, tk.END)
            self.content_text.insert(1.0, content)
    
    def refresh_content(self):
        """刷新内容"""
        self.load_selected_services()
    
    def refresh_services(self, selected_services):
        """刷新指定服务"""
        self.selected_services = selected_services
        self.refresh_content()
    
    def show_settings(self):
        """显示设置窗口"""
        settings_window = ttk.Toplevel(self.window)
        settings_window.title("API设置")
        settings_window.geometry("400x200")
        settings_window.resizable(False, False)
        
        # 设置窗口图标
        try:
            settings_window.iconbitmap("app_icon.ico")
        except:
            pass
        
        # 主框架
        main_frame = ttk.Frame(settings_window)
        main_frame.pack(fill=BOTH, expand=True, padx=20, pady=20)
        
        # Token设置
        ttk.Label(main_frame, text="ALAPI Token:", font=("Microsoft YaHei", 10)).pack(anchor=W, pady=(0, 5))
        
        token_entry = ttk.Entry(main_frame, width=50, font=("Microsoft YaHei", 9), show="*")
        token_entry.pack(fill=X, pady=(0, 15))
        token_entry.insert(0, self.alapi_manager.get_token())
        
        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=X, pady=(10, 0))
        
        def save_token():
            token = token_entry.get().strip()
            self.alapi_manager.set_token(token)
            messagebox.showinfo("成功", "Token已保存")
            settings_window.destroy()
        
        ttk.Button(button_frame, text="保存", 
                  command=save_token, 
                  bootstyle=SUCCESS).pack(side=LEFT)
        
        ttk.Button(button_frame, text="取消", 
                  command=settings_window.destroy, 
                  bootstyle=SECONDARY).pack(side=RIGHT, padx=(0, 10))