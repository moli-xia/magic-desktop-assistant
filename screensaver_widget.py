import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledFrame
from screensaver_manager import ScreensaverManager

class ScreensaverWidget(ttk.Frame):
    def __init__(self, parent, screensaver_manager: ScreensaverManager, on_config_change=None, use_scroll=True, **kwargs):
        super().__init__(parent, **kwargs)
        self.manager = screensaver_manager
        self.on_config_change = on_config_change
        self.use_scroll = use_scroll
        
        # Initialize variables from manager
        self.auto_screensaver_var = tk.BooleanVar(value=self.manager.auto_screensaver_enabled)
        self.idle_time_var = tk.StringVar(value=str(self.manager.idle_time_minutes))
        self.interval_var = tk.StringVar(value=str(self.manager.interval_minutes))
        
        self.setup_ui()
        
    def setup_ui(self):
        # Use ScrolledFrame for better responsiveness if enabled
        if self.use_scroll:
            self.scrolled_frame = ScrolledFrame(self, autohide=False) # autohide=False to prevent jitter
            self.scrolled_frame.pack(fill=BOTH, expand=YES)
            content_area = self.scrolled_frame.container
        else:
            self.scrolled_frame = None
            content_area = self
        
        # Title
        ttk.Label(content_area, text="屏保设置", font=("Microsoft YaHei", 20, "bold")).pack(anchor=W, pady=(0, 20), padx=10)
        
        # --- Card 1: Automatic Screensaver Settings ---
        self._create_auto_settings_card(content_area)
        
        # --- Card 2: Display Settings ---
        self._create_display_settings_card(content_area)
        
        # --- Card 3: Actions & Cache ---
        self._create_actions_card(content_area)
        
        # Status Bar
        self.status_label = ttk.Label(content_area, text="", font=("Microsoft YaHei", 9), bootstyle="secondary")
        self.status_label.pack(anchor=W, pady=10, padx=10)
        
        self.update_status_text()

    def _create_auto_settings_card(self, parent):
        card = ttk.Labelframe(parent, text=" 自动屏保 ", padding=15, bootstyle="info")
        card.pack(fill=X, expand=True, padx=10, pady=10)
        
        # Enable/Disable Toggle
        header_frame = ttk.Frame(card)
        header_frame.pack(fill=X, pady=(0, 10))
        
        ttk.Checkbutton(
            header_frame, 
            text="启用自动屏保", 
            variable=self.auto_screensaver_var, 
            command=self.toggle_auto_screensaver, 
            bootstyle="round-toggle"
        ).pack(side=LEFT)
        
        ttk.Label(header_frame, text="(无操作一段时间后自动播放)", bootstyle="secondary").pack(side=LEFT, padx=10)
        
        # Idle Time Setting
        setting_frame = ttk.Frame(card)
        setting_frame.pack(fill=X, pady=5)
        
        ttk.Label(setting_frame, text="空闲判定时间 (分钟):", width=20).pack(side=LEFT)
        
        entry = ttk.Entry(setting_frame, textvariable=self.idle_time_var, width=10)
        entry.pack(side=LEFT, padx=5)
        
        ttk.Button(
            setting_frame, 
            text="应用", 
            command=self.update_idle_time, 
            bootstyle="info-outline",
            cursor="hand2"
        ).pack(side=LEFT, padx=10)

    def _create_display_settings_card(self, parent):
        card = ttk.Labelframe(parent, text=" 显示设置 ", padding=15, bootstyle="primary")
        card.pack(fill=X, expand=True, padx=10, pady=10)
        
        # Interval Setting
        setting_frame = ttk.Frame(card)
        setting_frame.pack(fill=X, pady=5)
        
        ttk.Label(setting_frame, text="图片切换间隔 (分钟):", width=20).pack(side=LEFT)
        
        entry = ttk.Entry(setting_frame, textvariable=self.interval_var, width=10)
        entry.pack(side=LEFT, padx=5)
        
        ttk.Button(
            setting_frame, 
            text="应用", 
            command=self.update_interval, 
            bootstyle="primary-outline",
            cursor="hand2"
        ).pack(side=LEFT, padx=10)

    def _create_actions_card(self, parent):
        card = ttk.Labelframe(parent, text=" 操作与维护 ", padding=15, bootstyle="secondary")
        card.pack(fill=X, expand=True, padx=10, pady=10)
        
        btn_frame = ttk.Frame(card)
        btn_frame.pack(fill=X)
        
        # Start Now
        ttk.Button(
            btn_frame, 
            text="⚡ 立即启动屏保", 
            command=self.manager.start_screensaver, 
            bootstyle="success", 
            width=20,
            cursor="hand2"
        ).pack(side=LEFT, padx=(0, 20))
        
        # Clear Cache
        ttk.Button(
            btn_frame, 
            text="🗑️ 清理缓存图片", 
            command=self.clear_cache_with_feedback, 
            bootstyle="warning-outline",
            cursor="hand2"
        ).pack(side=LEFT)

    def _notify_change(self):
        if self.on_config_change:
            self.on_config_change()

    def update_status_text(self):
        if self.manager.auto_screensaver_enabled:
            self.status_label.config(text=f"ℹ️ 自动屏保已启用，{self.manager.idle_time_minutes}分钟无操作后将自动启动")
        else:
            self.status_label.config(text="ℹ️ 自动屏保已禁用")

    def update_interval(self):
        try:
            minutes = float(self.interval_var.get())
            if minutes > 0:
                self.manager.interval_minutes = minutes
                self.status_label.config(text=f"✅ 切换间隔已更新为 {minutes} 分钟")
                self._notify_change()
            else:
                self.status_label.config(text="❌ 间隔时间必须大于0")
        except ValueError:
            self.status_label.config(text="❌ 请输入有效的数字")

    def toggle_auto_screensaver(self):
        enabled = self.auto_screensaver_var.get()
        self.manager.auto_screensaver_enabled = enabled
        if enabled:
            self.manager.start_idle_check()
            self.update_idle_time(silent=True) # Ensure idle time is up to date
        else:
            if self.manager.idle_check_timer:
                self.manager.root.after_cancel(self.manager.idle_check_timer)
                self.manager.idle_check_timer = None
        
        self.update_status_text()
        self._notify_change()

    def update_idle_time(self, silent=False):
        try:
            new_time = int(self.idle_time_var.get())
            if new_time > 0:
                self.manager.idle_time_minutes = new_time
                if not silent:
                    self.status_label.config(text=f"✅ 空闲时间已更新为 {new_time} 分钟")
                    if self.manager.auto_screensaver_enabled:
                         self.after(1000, self.update_status_text)
                self._notify_change()
            else:
                self.status_label.config(text="❌ 空闲时间必须大于0")
        except ValueError:
            self.status_label.config(text="❌ 请输入有效的整数")

    def clear_cache_with_feedback(self):
        self.manager.clear_screensaver_cache()
        self.status_label.config(text="✅ 缓存已清理")
        self.after(3000, self.update_status_text)
