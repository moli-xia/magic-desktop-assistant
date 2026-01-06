import os
import time
import threading
import requests
import io
import sys
import ctypes
from ctypes import Structure, c_uint, sizeof, byref
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from PIL import Image, ImageTk

class ScreensaverManager:
    def __init__(self, root, screensaver_dir, update_label_callback):
        self.root = root
        self.screensaver_dir = screensaver_dir
        self.update_label = update_label_callback
        
        self.screensaver_window = None
        self.screensaver_active = False
        self.screensaver_images = []
        self.used_images = set()
        self._images_lock = threading.Lock()
        self.screensaver_timer = None
        
        # Settings
        self.auto_screensaver_enabled = False
        self.idle_time_minutes = 5
        self.interval_minutes = 1.0 # Default interval

        self.last_activity_time = time.time()
        self.last_mouse_pos = None
        self.idle_check_timer = None

        self._last_input_tick = None

        try:
            self.last_mouse_pos = self.root.winfo_pointerxy()
        except Exception:
            self.last_mouse_pos = None
        
        # 仅在非Windows系统或无法使用系统API时使用事件绑定
        if not sys.platform.startswith('win'):
            self.root.bind('<Button>', self.on_user_activity)
            self.root.bind('<Key>', self.on_user_activity)
        
        self.start_idle_check()

    class _LASTINPUTINFO(Structure):
        _fields_ = [("cbSize", c_uint), ("dwTime", c_uint)]

    def _get_idle_seconds(self):
        if sys.platform.startswith('win'):
            try:
                lii = self._LASTINPUTINFO()
                lii.cbSize = sizeof(lii)
                windll = getattr(ctypes, "windll", None)
                if not windll:
                    return max(0.0, time.time() - self.last_activity_time)
                if ctypes.windll.user32.GetLastInputInfo(byref(lii)) == 0:
                    return 0.0
                tick = ctypes.windll.kernel32.GetTickCount()
                idle_ms = int(tick) - int(lii.dwTime)
                if idle_ms < 0:
                    return 0.0
                return idle_ms / 1000.0
            except Exception:
                return max(0.0, time.time() - self.last_activity_time)

        try:
            current_pos = self.root.winfo_pointerxy()
            if self.last_mouse_pos is None:
                self.last_mouse_pos = current_pos
            elif current_pos != self.last_mouse_pos:
                self.last_mouse_pos = current_pos
                self.last_activity_time = time.time()
        except Exception:
            pass
        return max(0.0, time.time() - self.last_activity_time)

    def start_idle_check(self):
        """开始空闲检测"""
        if self.idle_check_timer:
            self.root.after_cancel(self.idle_check_timer)
        
        # 即使未开启屏保，也可以启动定时器来监控鼠标移动（可选），
        # 但为了节省资源，只在开启屏保时启动检测
        if self.auto_screensaver_enabled:
            self.idle_check_timer = self.root.after(1000, self.check_idle_time)

    def check_idle_time(self):
        """检查空闲时间"""
        if self.auto_screensaver_enabled:
            if not self.screensaver_active:
                idle_seconds = self._get_idle_seconds()
                idle_minutes = idle_seconds / 60
                
                if idle_minutes >= self.idle_time_minutes:
                    self.start_screensaver()
                    return
        
        # 继续检查
        if self.auto_screensaver_enabled:
            self.idle_check_timer = self.root.after(1000, self.check_idle_time)

    def on_user_activity(self, event=None):
        """用户活动回调"""
        self.last_activity_time = time.time()
        if self.screensaver_active:
            self.exit_screensaver()

    def get_high_res_image(self):
        try: 
            # 使用支持随机索引的必应壁纸API
            response = requests.get("https://bingw.jasonzeng.dev/?resolution=UHD&index=random", timeout=20)
            return response.content
        except requests.RequestException: return None

    def load_cached_images(self):
        try:
            image_files = [os.path.join(self.screensaver_dir, f) for f in os.listdir(self.screensaver_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            valid_images = []
            for image_path in image_files:
                try:
                    with Image.open(image_path) as img:
                        if img.width > 100 and img.height > 100:
                            valid_images.append(image_path)
                        else:
                            os.remove(image_path)
                except Exception:
                    try: os.remove(image_path)
                    except: pass
            
            with self._images_lock:
                self.screensaver_images = valid_images
                self.screensaver_images.sort()
                self.used_images.clear()
        except FileNotFoundError: 
            with self._images_lock:
                self.screensaver_images = []
                self.used_images.clear()

    def manage_cache(self):
        try:
            files = [os.path.join(self.screensaver_dir, f) for f in os.listdir(self.screensaver_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
            # Max cache size 50
            if len(files) > 50:
                files.sort(key=os.path.getmtime)
                for f in files[:len(files) - 50]: os.remove(f)
        except Exception as e:
            print(f"Cache management failed: {e}")

    def clear_screensaver_cache(self):
        try:
            for f in os.listdir(self.screensaver_dir): os.remove(os.path.join(self.screensaver_dir, f))
            with self._images_lock:
                self.screensaver_images.clear()
                self.used_images.clear()
            self.update_label("屏保缓存已清理")
        except Exception as e: self.update_label(f"清理缓存失败: {e}")

    def start_screensaver(self):
        if self.screensaver_window: return
        self.screensaver_active = True
        self.screensaver_window = ttk.Toplevel(self.root)
        self.screensaver_window.attributes("-fullscreen", True)
        self.screensaver_window.configure(bg='black')
        self.screensaver_window.bind("<Key>", self.exit_screensaver)
        self.screensaver_window.bind("<Motion>", self.exit_screensaver)
        self.screensaver_window.bind("<Button-1>", self.exit_screensaver)
        
        self.ss_label = ttk.Label(self.screensaver_window, background='black', foreground='white', text="正在加载图片...", font=("Microsoft YaHei", 24))
        self.ss_label.pack(expand=YES, fill=BOTH)
        self.ss_label.focus_set()
        
        self.load_cached_images()
        if self.screensaver_images: 
            self.update_screensaver_image()
        else: 
            self.wait_for_first_image()
            
        self.schedule_preload_next_image()

    def exit_screensaver(self, event=None):
        if self.screensaver_window:
            self.screensaver_active = False
            if self.screensaver_timer: 
                try: self.screensaver_window.after_cancel(self.screensaver_timer)
                except: pass
            self.screensaver_window.destroy()
            self.screensaver_window = None
            with self._images_lock:
                self.used_images.clear()
            self.last_activity_time = time.time()  # Reset activity time on exit
            self.update_label("屏保已退出")

    def wait_for_first_image(self):
        if not self.screensaver_window: return
        if self.screensaver_images: 
            self.update_screensaver_image()
        else: 
            threading.Thread(target=self.download_single_screensaver_image, daemon=True).start()
            self.screensaver_timer = self.screensaver_window.after(1000, self.wait_for_first_image)

    def download_single_screensaver_image(self):
        try:
            image_data = self.get_high_res_image()
            if image_data and len(image_data) > 1000:
                img = Image.open(io.BytesIO(image_data))
                if img.width > 100 and img.height > 100:
                    path = os.path.join(self.screensaver_dir, f"ss_{int(time.time() * 1000)}.jpg")
                    with open(path, 'wb') as f: f.write(image_data)
                    with self._images_lock:
                        if path not in self.screensaver_images:
                            self.screensaver_images.append(path)
                    self.manage_cache()
                    return True
        except Exception as e:
            print(f"下载屏保图片失败: {e}")
        return False

    def resize_and_crop(self, img, target_width, target_height):
        img_ratio = img.width / img.height
        target_ratio = target_width / target_height
        if target_ratio > img_ratio:
            new_height = int(target_width / img_ratio)
            img = img.resize((target_width, new_height), Image.Resampling.LANCZOS)
            crop_y = (new_height - target_height) // 2
            return img.crop((0, crop_y, target_width, crop_y + target_height))
        else:
            new_width = int(target_height * img_ratio)
            img = img.resize((new_width, target_height), Image.Resampling.LANCZOS)
            crop_x = (new_width - target_width) // 2
            return img.crop((crop_x, 0, crop_x + target_width, target_height))

    def update_screensaver_image(self):
        if not self.screensaver_window: return
        
        with self._images_lock:
            empty_images = not self.screensaver_images
            exhausted = (len(self.used_images) >= len(self.screensaver_images)) if not empty_images else True

        if exhausted:
            with self._images_lock:
                self.used_images.clear()
                empty_images = not self.screensaver_images
            if empty_images:
                threading.Thread(target=self.download_single_screensaver_image, daemon=True).start()
                self.screensaver_timer = self.screensaver_window.after(1000, self.update_screensaver_image)
                return

        try:
            with self._images_lock:
                available_images = [img for img in self.screensaver_images if img not in self.used_images]
                if not available_images:
                    self.used_images.clear()
                    available_images = list(self.screensaver_images)
            
            path = available_images[0] if available_images else None
            if not path:
                self.screensaver_timer = self.screensaver_window.after(1000, self.update_screensaver_image)
                return
                
            with self._images_lock:
                self.used_images.add(path)
            
            w, h = self.screensaver_window.winfo_width(), self.screensaver_window.winfo_height()
            if w <= 1 or h <= 1: 
                self.screensaver_window.after(100, self.update_screensaver_image)
                return
                
            img = self.resize_and_crop(Image.open(path), w, h)
            tk_img = ImageTk.PhotoImage(img)
            self.ss_label.config(image=tk_img, text="")
            self.ss_label.image = tk_img
        except Exception:
            if 'path' in locals():
                with self._images_lock:
                    if path in self.screensaver_images:
                        self.screensaver_images.remove(path)
            try: os.remove(path)
            except: pass
                
        interval = int(self.interval_minutes * 60 * 1000)
        self.screensaver_timer = self.screensaver_window.after(interval, self.update_screensaver_image)
        
        preload_delay = int(interval * 0.75)
        self.screensaver_window.after(preload_delay, self.preload_next_image)

    def schedule_preload_next_image(self):
        if not self.screensaver_window: return
        interval = int(self.interval_minutes * 60 * 1000)
        preload_delay = int(interval * 0.75)
        self.screensaver_window.after(preload_delay, self.preload_next_image)

    def preload_next_image(self):
        if not self.screensaver_window: return
        with self._images_lock:
            unused_count = len(self.screensaver_images) - len(self.used_images)
            total = len(self.screensaver_images)
        if unused_count <= 1 or total < 3:
            threading.Thread(target=self.download_single_screensaver_image, daemon=True).start()
