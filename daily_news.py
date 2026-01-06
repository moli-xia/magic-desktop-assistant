import requests
import json
import time
import sys
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import messagebox, scrolledtext
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import threading
import os
import urllib3
import random
import re

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class DailyNewsManager:
    def __init__(self):
        # 多个API源配置
        self.api_sources = {
            "alapi": {
                "url": "https://v2.alapi.cn/api/zaobao",
                "token": None,
                "method": "GET"
            },
            "60s": {
                "url": "https://api.03c3.cn/zb",
                "token": None,
                "method": "GET"
            },
            "backup": {
                "url": "https://api.vvhan.com/api/60s",
                "token": None,
                "method": "GET"
            }
        }
        
        self.current_source = "alapi"  # 默认使用alapi
        self.cache_file = os.path.join(os.getenv('APPDATA', ''), 'WallpaperApp', 'daily_news_cache.json')
        self.last_update = None
        self.news_data = None
        self.notification_enabled = True
        self.notification_time = "08:00"  # 默认早上8点推送
        
        # 确保缓存目录存在
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
        
        # 加载缓存数据
        self.load_cache()
        
    def get_token(self):
        """获取当前源的Token"""
        if self.current_source in self.api_sources:
            return self.api_sources[self.current_source]["token"]
        return ""

    def set_token(self, token):
        """设置API token"""
        if self.current_source in self.api_sources:
            self.api_sources[self.current_source]["token"] = token
    
    def switch_api_source(self, source_name):
        """切换API源"""
        if source_name in self.api_sources:
            self.current_source = source_name
            return True
        return False
        
    def load_cache(self):
        """加载缓存的新闻数据"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                    self.news_data = cache_data.get('news_data')
                    self.last_update = cache_data.get('last_update')
                    self.notification_enabled = cache_data.get('notification_enabled', True)
                    self.notification_time = cache_data.get('notification_time', "08:00")
                    self.current_source = cache_data.get('current_source', "alapi")
        except Exception as e:
            print(f"加载缓存失败: {e}")
            
    def save_cache(self):
        """保存新闻数据到缓存"""
        try:
            cache_data = {
                'news_data': self.news_data,
                'last_update': self.last_update,
                'notification_enabled': self.notification_enabled,
                'notification_time': self.notification_time,
                'current_source': self.current_source
            }
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存缓存失败: {e}")
            
    def fetch_daily_news(self):
        """获取每日新闻，支持多个API源"""
        # 尝试当前源
        result = self._try_fetch_from_source(self.current_source)
        if result and result.get("success"):
            return result
            
        # 如果当前源失败，尝试其他源
        for source_name in self.api_sources:
            if source_name != self.current_source:
                print(f"尝试备用API源: {source_name}")
                result = self._try_fetch_from_source(source_name)
                if result and result.get("success"):
                    # 切换到成功的源
                    self.current_source = source_name
                    return result
        
        return {"success": False, "message": "所有API源都无法访问"}
    
    def _try_fetch_from_source(self, source_name):
        """尝试从指定源获取新闻"""
        try:
            source_config = self.api_sources[source_name]
            
            params = {}
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            # 根据ALAPI文档，使用token参数
            if source_config["token"]:
                params["token"] = source_config["token"]
            
            response = requests.get(
                source_config["url"], 
                params=params,
                headers=headers,
                timeout=10,
                verify=False
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # 根据不同API源处理响应格式
                if source_name == "alapi":
                    if data.get('code') == 200:
                        # 根据ALAPI文档，数据在data字段中
                        news_content = data.get('data', {}).get('news', [])
                        self.news_data = {
                            "news": news_content,
                            "date": datetime.now().strftime("%Y-%m-%d"),
                            "source": source_name
                        }
                        self.last_update = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        self.save_cache()
                        return {"success": True, "data": self.news_data}
                elif source_name == "60s":
                    if data.get('code') == 200:
                        news_list = data.get('data', [])
                        self.news_data = {
                            "news": news_list,
                            "date": datetime.now().strftime("%Y-%m-%d"),
                            "source": source_name
                        }
                        self.last_update = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        self.save_cache()
                        return {"success": True, "data": self.news_data}
                elif source_name == "backup":
                    if 'data' in data:
                        news_list = data.get('data', [])
                        self.news_data = {
                            "news": news_list,
                            "date": datetime.now().strftime("%Y-%m-%d"),
                            "source": source_name
                        }
                        self.last_update = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        self.save_cache()
                        return {"success": True, "data": self.news_data}
                        
            return {"success": False, "message": f"API响应错误: {response.status_code}"}
            
        except requests.exceptions.Timeout:
            return {"success": False, "message": f"{source_name} API请求超时"}
        except requests.exceptions.ConnectionError:
            return {"success": False, "message": f"{source_name} 网络连接错误"}
        except Exception as e:
            return {"success": False, "message": f"{source_name} 请求失败: {str(e)}"}
            
    def get_cached_news(self):
        """获取缓存的新闻数据"""
        if self.news_data and self.is_today_updated():
            return self.news_data
        else:
            # 尝试获取新数据
            result = self.fetch_daily_news()
            if result.get("success"):
                return self.news_data
            return None
            
    def is_today_updated(self):
        """检查今天是否已更新"""
        if not self.last_update:
            return False
            
        try:
            last_date = datetime.strptime(self.last_update, '%Y-%m-%d %H:%M:%S').date()
            today = datetime.now().date()
            return last_date == today
        except:
            return False
            
    def _clean_text(self, text):
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
                r'^(?:\s*\d+\s*[.、）)】]\s*){1,3}',
                r'^\d+[.、）)】]\s*',           # 1. 2、 3） 4) 5】
                r'^[\(（]\d+[\)）]\s*',         # (1) （2）
                r'^【\d+】\s*',                # 【1】
                r'^[•·▪▫◦‣⁃]\s*',             # 各种点符号
                r'^\d+\s*[.、）)】]\s*',       # 数字后面有空格的情况
                r'^\s*\d+[.、）)】]\s*',       # 前面有空格的情况
                r'^第\d+[条项]\s*',            # 第1条 第2项
                r'^\d+\s+',                   # 纯数字后面跟空格
                r'^(?:\(\d+\)|（\d+）)\s*',
            ]
            
            for pattern in patterns:
                clean_text = re.sub(pattern, '', clean_text)
            
            clean_text = clean_text.strip()
            
            # 如果没有变化，说明清理完成
            if clean_text == original:
                break
                
            iteration += 1
        
        return clean_text

    def get_cleaned_news(self, news_data):
        """获取清理后的新闻列表"""
        if not news_data:
            return []
            
        news_list = news_data.get('news', [])
        cleaned_list = []
        
        if isinstance(news_list, list):
            for news_item in news_list:
                clean_item = ""
                if isinstance(news_item, str):
                    clean_item = self._clean_text(news_item)
                elif isinstance(news_item, dict):
                    title = news_item.get('title', news_item.get('content', ''))
                    clean_item = self._clean_text(title)
                
                if clean_item:
                    cleaned_list.append(clean_item)
                    
        return cleaned_list

    def format_news_for_display(self, news_data):
        """格式化新闻数据用于显示"""
        if not news_data:
            return "暂无新闻数据"
            
        formatted_text = f"📅 {news_data.get('date', '未知日期')}\n"
        formatted_text += f"📡 数据源: {news_data.get('source', '未知')}\n"
        formatted_text += "─" * 50 + "\n\n"
        
        cleaned_list = self.get_cleaned_news(news_data)
        for i, item in enumerate(cleaned_list, 1):
            formatted_text += f"{i}. {item}\n\n"
            
        return formatted_text
        
    def set_notification_settings(self, enabled, time_str):
        """设置通知设置"""
        self.notification_enabled = enabled
        self.notification_time = time_str
        self.save_cache()
        
    def should_show_notification(self):
        """检查是否应该显示通知"""
        if not self.notification_enabled:
            return False
            
        current_time = datetime.now().strftime('%H:%M')
        return current_time == self.notification_time


class NewsWidget(ttk.Frame):
    def __init__(self, parent, news_manager, ui_after=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.news_manager = news_manager
        self.ui_after = ui_after
        self.setup_ui()
        self.load_news_data()

    def _ui(self, ms, callback):
        if self.ui_after:
            try:
                self.ui_after(ms, callback)
                return
            except Exception:
                pass
        try:
            if threading.current_thread() is threading.main_thread():
                self.after(ms, callback)
        except Exception:
            pass
        
    def setup_ui(self):
        """设置新闻界面"""
        # 标题框架
        title_frame = ttk.Frame(self)
        title_frame.pack(fill=X, pady=(0, 10))
        
        title_label = ttk.Label(title_frame, text="每日早报 - 60秒读懂世界", 
                               font=("Microsoft YaHei", 16, "bold"))
        title_label.pack(side=LEFT)
        
        # 按钮区域
        btn_frame = ttk.Frame(title_frame)
        btn_frame.pack(side=RIGHT)
        
        ttk.Button(btn_frame, text="刷新", command=self.refresh_news, bootstyle=PRIMARY).pack(side=LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="设置", command=self.show_settings, bootstyle=SECONDARY).pack(side=LEFT)

        self.header_frame = ttk.Frame(self)
        self.header_frame.pack(fill=X, pady=(0, 10))

        self.header_date_label = ttk.Label(self.header_frame, text="", bootstyle="info")
        self.header_date_label.pack(side=LEFT, padx=(0, 20))
        self.header_source_label = ttk.Label(self.header_frame, text="", bootstyle="secondary")
        self.header_source_label.pack(side=LEFT)
        
        self._create_scroll_area()
        
        # 状态栏
        self.status_label = ttk.Label(self, text="准备就绪", font=("Microsoft YaHei", 9), bootstyle="secondary")
        self.status_label.pack(fill=X, pady=(10, 0))

    def _create_scroll_area(self):
        container = ttk.Frame(self)
        container.pack(fill=BOTH, expand=True)

        try:
            style = ttk.Style()
            bg = getattr(style.colors, "bg", None) or "#1E1E1E"
            fg = getattr(style.colors, "fg", None) or "#FFFFFF"
            selbg = getattr(style.colors, "selectbg", None) or "#3A7AFE"
            selfg = getattr(style.colors, "selectfg", None) or "#FFFFFF"
        except Exception:
            bg, fg, selbg, selfg = "#1E1E1E", "#FFFFFF", "#3A7AFE", "#FFFFFF"

        self.news_text = tk.Text(
            container,
            wrap="word",
            borderwidth=0,
            highlightthickness=0,
            relief="flat",
            undo=False,
            autoseparators=False,  # 禁用撤销分隔符
            exportselection=False, # 禁止导出选中，避免卡顿
            font=("Microsoft YaHei", 11),
            background=bg,
            foreground=fg,
            selectbackground=selbg,
            selectforeground=selfg,
            cursor="arrow",
            state="disabled",
            takefocus=0,
        )
        self.v_scrollbar = ttk.Scrollbar(container, orient=VERTICAL, command=self.news_text.yview)
        self.news_text.configure(yscrollcommand=self.v_scrollbar.set)

        self.v_scrollbar.pack(side=RIGHT, fill=Y)
        self.news_text.pack(side=LEFT, fill=BOTH, expand=True)

        def block_interaction(_event=None):
            return "break"

        for key in [
            "<Key>",
            "<Button-1>",
            "<B1-Motion>",
            "<Double-Button-1>",
            "<Triple-Button-1>",
            "<Shift-Button-1>",
            "<Control-a>",
            "<Control-A>",
            "<Control-c>",
            "<Control-C>",
            "<<Copy>>",
            "<<Cut>>",
            "<<Paste>>",
            "<<Clear>>",
        ]:
            self.news_text.bind(key, block_interaction)

    def _on_mousewheel(self, event):
        # 此函数已不再使用，保留空实现以防万一
        pass

    def _set_news_text(self, text: str):
        try:
            # 临时允许编辑以写入内容
            self.news_text.configure(state="normal")
            self.news_text.delete("1.0", "end")
            self.news_text.insert("1.0", text or "")
            self.news_text.configure(state="disabled")
        except Exception:
            pass
        
    def load_news_data(self):
        """加载新闻数据"""
        cached_news = self.news_manager.get_cached_news()
        if cached_news:
            self.update_news_display({"success": True, "data": cached_news}, from_cache=True)
        else:
            self._show_message("暂无新闻数据，请点击刷新按钮获取最新新闻")
            
        if not self.news_manager.is_today_updated():
            self.refresh_news()
            
    def refresh_news(self):
        """刷新新闻数据"""
        current_source_config = self.news_manager.api_sources.get(self.news_manager.current_source, {})
        if current_source_config.get("token") is None and self.news_manager.current_source == "alapi":
            messagebox.showwarning("提示", "请先在设置中配置API Token\n\n请访问 https://www.alapi.cn 注册账号获取Token")
            self.show_settings()
            return
            
        self.status_label.config(text="正在获取最新数据...")
        
        def fetch_data():
            result = self.news_manager.fetch_daily_news()
            self._ui(0, lambda: self.update_news_display(result))
            
        threading.Thread(target=fetch_data, daemon=True).start()
        
    def update_news_display(self, result, from_cache=False):
        """更新新闻显示"""
        if not result["success"]:
            error_msg = result.get('message', '未知错误')
            self.status_label.config(text=f"更新失败: {error_msg}")
            if not from_cache:
                self._show_message(f"获取新闻失败:\n{error_msg}\n\n请检查网络连接或联系管理员。")
            return

        news_data = result["data"]

        try:
            self.header_date_label.config(text=f"📅 {news_data.get('date', '未知日期')}")
            self.header_source_label.config(text=f"📡 数据源: {news_data.get('source', '未知')}")
        except Exception:
            pass
        
        # 新闻列表
        cleaned_list = self.news_manager.get_cleaned_news(news_data)
        
        if not cleaned_list:
            self._show_message("暂无新闻内容")
            return

        content = "\n\n".join([f"{i}. {item}" for i, item in enumerate(cleaned_list, 1)])
        self._set_news_text(content)
            
        msg = f"最后更新: {self.news_manager.last_update}" if from_cache else f"更新成功 - {self.news_manager.last_update}"
        self.status_label.config(text=msg)

    def _show_message(self, message):
        try:
            self.header_date_label.config(text="")
            self.header_source_label.config(text="")
        except Exception:
            pass
        self._set_news_text(message)
            
    def show_settings(self):
        """显示设置窗口"""
        settings_window = ttk.Toplevel(self)
        settings_window.title("早报设置")
        settings_window.geometry("400x300")
        settings_window.resizable(False, False)
        settings_window.transient(self)
        settings_window.grab_set()
        
        # API Token设置
        token_frame = ttk.LabelFrame(settings_window, text="API设置", padding=10)
        token_frame.pack(fill=X, padx=10, pady=10)
        
        ttk.Label(token_frame, text="ALAPI Token:").pack(anchor=W)
        token_var = tk.StringVar(value=self.news_manager.get_token() or "")
        token_entry = ttk.Entry(token_frame, textvariable=token_var, width=50, show="*")
        token_entry.pack(fill=X, pady=(5, 0))
        
        ttk.Label(token_frame, text="请访问 https://www.alapi.cn 注册获取Token", 
                 font=("Microsoft YaHei", 8), foreground="gray").pack(anchor=W, pady=(5, 0))
        
        # 通知设置
        notify_frame = ttk.LabelFrame(settings_window, text="通知设置", padding=10)
        notify_frame.pack(fill=X, padx=10, pady=10)
        
        notify_var = tk.BooleanVar(value=self.news_manager.notification_enabled)
        notify_check = ttk.Checkbutton(notify_frame, text="启用每日推送通知", variable=notify_var)
        notify_check.pack(anchor=W)
        
        time_frame = ttk.Frame(notify_frame)
        time_frame.pack(fill=X, pady=(10, 0))
        
        ttk.Label(time_frame, text="推送时间:").pack(side=LEFT)
        time_var = tk.StringVar(value=self.news_manager.notification_time)
        time_entry = ttk.Entry(time_frame, textvariable=time_var, width=10)
        time_entry.pack(side=LEFT, padx=(10, 0))
        ttk.Label(time_frame, text="(格式: HH:MM)").pack(side=LEFT, padx=(5, 0))
        
        # 按钮框架
        btn_frame = ttk.Frame(settings_window)
        btn_frame.pack(fill=X, padx=10, pady=10)
        
        def save_settings():
            self.news_manager.set_token(token_var.get().strip())
            self.news_manager.set_notification_settings(notify_var.get(), time_var.get())
            messagebox.showinfo("提示", "设置已保存")
            settings_window.destroy()
            
        ttk.Button(btn_frame, text="保存", command=save_settings, 
                   bootstyle=PRIMARY).pack(side=RIGHT)
        ttk.Button(btn_frame, text="取消", command=settings_window.destroy, 
                   bootstyle=SECONDARY).pack(side=RIGHT, padx=(0, 10))

class DailyNewsWindow:
    def __init__(self, parent, news_manager):
        self.parent = parent
        self.news_manager = news_manager
        self.window = None
        
    def show_news_window(self):
        """显示新闻窗口"""
        if self.window and self.window.winfo_exists():
            self.window.lift()
            self.window.focus_force()
            return
            
        self.window = ttk.Toplevel(self.parent)
        self.window.title("每日早报 - 60秒读懂世界")
        self.window.geometry("800x600")
        self.window.resizable(True, True)
        
        # 设置窗口图标
        try:
            icon_path = os.path.join(os.getenv('APPDATA'), 'WallpaperApp', 'icon.ico')
            if os.path.exists(icon_path):
                self.window.iconbitmap(icon_path)
        except:
            pass
            
        # 使用 NewsWidget
        self.news_widget = NewsWidget(self.window, self.news_manager)
        self.news_widget.pack(fill=BOTH, expand=YES)
        
    # 保留 refresh_news 方法以兼容外部调用（如果有）
    def refresh_news(self):
        if hasattr(self, 'news_widget'):
            self.news_widget.refresh_news()
