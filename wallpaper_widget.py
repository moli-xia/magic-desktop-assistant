import os
import time
import threading
import requests
import ctypes
import io
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox
import tkinter as tk
from PIL import Image

MAX_CACHE_SIZE = 50

class WallpaperWidget(ttk.Frame):
    def __init__(self, parent, wallpaper_dir, initial_interval=30, auto_enabled=False, on_config_change=None, ui_after=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.wallpaper_dir = wallpaper_dir
        self.wallpaper_timer = None
        self.on_config_change = on_config_change
        self.ui_after = ui_after
        
        # State variables
        self.interval_var = tk.StringVar(value=str(initial_interval))
        self.auto_change_var = tk.BooleanVar(value=auto_enabled)
        
        self.setup_ui()
        
    def setup_ui(self):
        ttk.Label(self, text="壁纸管理", font=("Microsoft YaHei", 20, "bold")).pack(anchor=W, pady=(0, 20))
        
        # 壁纸设置内容
        wp_frame = ttk.Labelframe(self, text=" 壁纸设置 ", padding=15, bootstyle="info")
        wp_frame.pack(fill=X, pady=5)

        # 自动更换设置
        wp_auto_frame = ttk.Frame(wp_frame)
        wp_auto_frame.pack(pady=10, fill=X)
        
        ttk.Checkbutton(wp_auto_frame, text="启用自动更换", variable=self.auto_change_var, command=self.toggle_auto_change, bootstyle="round-toggle").pack(side=LEFT)
        
        ttk.Label(wp_auto_frame, text="更换间隔 (分钟):", width=15).pack(side=LEFT, padx=(30, 0))
        self.wallpaper_interval_entry = ttk.Entry(wp_auto_frame, textvariable=self.interval_var, width=10)
        self.wallpaper_interval_entry.pack(side=LEFT, padx=5)
        
        ttk.Button(wp_auto_frame, text="应用", command=self.update_interval, bootstyle="info-outline").pack(side=LEFT, padx=10)
        
        # 手动更换区域
        action_frame = ttk.Frame(self, padding=(0, 20))
        action_frame.pack(fill=X)
        
        self.change_button = ttk.Button(action_frame, text="🎲 立即更换壁纸", command=self.start_change_wallpaper_thread, bootstyle="success", width=20)
        self.change_button.pack(anchor=W)
        
        # 状态栏/提示信息
        self.status_label = ttk.Label(self, text="ℹ️ 提示：点击'立即更换壁纸'可立即下载并设置新壁纸。", font=("Microsoft YaHei", 9), bootstyle="secondary")
        self.status_label.pack(anchor=W, pady=10)
        
        # Initialize auto change if enabled
        if self.auto_change_var.get():
            self.schedule_next_wallpaper_change()

    def update_label(self, text, style="secondary"):
        def _do():
            try:
                if self.winfo_exists():
                    self.status_label.config(text=text, bootstyle=style)
            except Exception:
                pass

        if threading.current_thread() is threading.main_thread():
            _do()
        else:
            if self.ui_after:
                try:
                    self.ui_after(0, _do)
                except Exception:
                    pass

    def get_high_res_image(self):
        try: 
            # 使用支持随机索引的必应壁纸API，确保每次获取不同的壁纸
            response = requests.get("https://bingw.jasonzeng.dev/?resolution=UHD&index=random", timeout=20)
            return response.content
        except requests.RequestException: return None

    def set_wallpaper(self, image_path):
        try:
            ctypes.windll.user32.SystemParametersInfoW(20, 0, image_path, 3)
            self.update_label("✅ 壁纸更换成功！", "success")
        except Exception as e: self.update_label(f"❌ 设置壁纸失败: {e}", "danger")

    def manage_cache(self):
        try:
            directory = self.wallpaper_dir
            files = [os.path.join(directory, f) for f in os.listdir(directory) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
            if len(files) > MAX_CACHE_SIZE:
                files.sort(key=os.path.getmtime)
                for f in files[:len(files) - MAX_CACHE_SIZE]: os.remove(f)
        except Exception as e:
            print(f"Cache management failed: {e}")

    def change_wallpaper_logic(self):
        self.update_label("⏳ 正在下载高清壁纸...", "info")
        image_data = self.get_high_res_image()
        if not image_data:
            self.update_label("❌ 下载壁纸失败，请检查网络", "danger"); return
        try:
            if not os.path.exists(self.wallpaper_dir):
                os.makedirs(self.wallpaper_dir)
                
            Image.open(io.BytesIO(image_data)) # Verify image
            new_wallpaper_path = os.path.join(self.wallpaper_dir, f"wallpaper_{int(time.time())}.jpg")
            with open(new_wallpaper_path, "wb") as f: f.write(image_data)
            self.set_wallpaper(new_wallpaper_path)
            self.manage_cache()
        except (IOError, OSError) as e: self.update_label(f"❌ 保存壁纸失败: {e}", "danger")
        except Exception as e: self.update_label(f"❌ 下载的图片文件无效: {e}", "danger")

    def start_change_wallpaper_thread(self):
        self.change_button.config(state=DISABLED)
        threading.Thread(target=self._threaded_change_and_reenable, daemon=True).start()

    def _threaded_change_and_reenable(self):
        self.change_wallpaper_logic()
        def _reenable():
            try:
                if self.winfo_exists():
                    self.change_button.config(state=NORMAL)
            except Exception:
                pass

        if self.ui_after:
            try:
                self.ui_after(0, _reenable)
            except Exception:
                pass
        else:
            try:
                if self.winfo_exists():
                    self.after(0, _reenable)
            except Exception:
                pass

    def get_wallpaper_interval_ms(self):
        try:
            minutes = float(self.interval_var.get())
            return int(minutes * 60 * 1000) if minutes > 0 else None
        except (ValueError, TypeError): return None
        
    def update_interval(self):
        try:
            minutes = float(self.interval_var.get())
            if minutes > 0:
                self.update_label(f"✅ 间隔已更新为 {minutes} 分钟", "success")
                if self.auto_change_var.get():
                     self.schedule_next_wallpaper_change() # Reschedule with new interval
                self._notify_change()
            else:
                self.update_label("❌ 间隔必须大于0", "danger")
        except ValueError:
            self.update_label("❌ 请输入有效的数字", "danger")

    def toggle_auto_change(self):
        if self.auto_change_var.get():
            if self.get_wallpaper_interval_ms():
                self.update_label("✅ 已开启自动更换壁纸", "success")
                self.schedule_next_wallpaper_change()
            else:
                self.update_label("❌ 请输入有效的壁纸间隔时间", "danger"); self.auto_change_var.set(False)
        else:
            if self.wallpaper_timer: self.after_cancel(self.wallpaper_timer)
            self.update_label("ℹ️ 已关闭自动更换壁纸", "secondary")
        
        self._notify_change()

    def schedule_next_wallpaper_change(self):
        if self.wallpaper_timer:
            self.after_cancel(self.wallpaper_timer)
            self.wallpaper_timer = None
            
        interval = self.get_wallpaper_interval_ms()
        if interval and self.auto_change_var.get():
            self.wallpaper_timer = self.after(interval, self.run_scheduled_wallpaper_change)

    def run_scheduled_wallpaper_change(self):
        if self.auto_change_var.get():
            self.start_change_wallpaper_thread(); self.schedule_next_wallpaper_change()
            
    def _notify_change(self):
        if self.on_config_change:
            self.on_config_change()
