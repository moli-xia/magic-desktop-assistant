import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import threading
import time
from typing import Callable
from calendar_reminder import ReminderData
import os

try:
    import winsound  # type: ignore
except Exception:
    winsound = None

class ReminderNotificationWindow:
    """提醒通知窗口 - 在桌面右下角显示"""
    
    def __init__(self, reminder: ReminderData, reminder_manager=None, close_callback: Callable = None, parent=None):
        self.reminder = reminder
        self.reminder_manager = reminder_manager
        self.close_callback = close_callback
        # 主题色与前景色
        self.bg_color = self.reminder.color
        self.fg_color = self._get_contrast_color(self.bg_color)
        
        if parent is None:
            parent = getattr(reminder_manager, "tk_root", None) if reminder_manager else None
        if parent is None:
            parent = tk._default_root

        self.window = tk.Toplevel(parent) if parent else tk.Toplevel()
        self.window.title("提醒")
        self.window.geometry("380x200")  # 稍大一点以适应现代布局
        self.window.resizable(False, False)
        
        # 移除标准标题栏，使用自定义标题栏
        self.window.overrideredirect(True)
        
        # 设置窗口置顶
        self.window.attributes('-topmost', True)
        
        # 设置窗口位置在右下角
        self.position_window()
        
        # 设置窗口样式
        self.window.configure(bg=self.bg_color)
        
        # 拖拽移动窗口
        self._drag_data = {"x": 0, "y": 0}
        self._details_dialog = None
        
        self.setup_ui()
        self.show_notification()
        
    def position_window(self):
        """将窗口定位到屏幕右下角"""
        self.window.update_idletasks()
        
        # 获取屏幕尺寸
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        
        # 获取窗口尺寸
        window_width = 400
        window_height = 220
        
        # 计算位置（右下角，留出任务栏空间）
        x = screen_width - window_width - 20
        y = screen_height - window_height - 60  # 留出任务栏空间
        
        self.window.geometry(f"{window_width}x{window_height}+{x}+{y}")
    
    def setup_ui(self):
        """设置通知界面"""
        # 主容器（带边框效果）
        container = tk.Frame(self.window, bg=self.bg_color, relief="flat", bd=1)
        container.pack(fill=BOTH, expand=True)
        
        # 内部边框（为了显示深色边框效果）
        inner_border = tk.Frame(container, bg=self._darken_color(self.bg_color, 0.1), padx=1, pady=1)
        inner_border.pack(fill=BOTH, expand=True)
        
        # 内容主面板
        main_panel = tk.Frame(inner_border, bg=self.bg_color)
        main_panel.pack(fill=BOTH, expand=True)
        
        # --- 标题栏 ---
        title_bar = tk.Frame(main_panel, bg=self._darken_color(self.bg_color, 0.05), height=30)
        title_bar.pack(fill=X)
        title_bar.pack_propagate(False)
        
        # 绑定拖拽事件
        title_bar.bind("<Button-1>", self._start_drag)
        title_bar.bind("<B1-Motion>", self._do_drag)
        
        # 标题图标
        tk.Label(title_bar, text="🔔", bg=self._darken_color(self.bg_color, 0.05), fg=self.fg_color, font=("Segoe UI Emoji", 10)).pack(side=LEFT, padx=(10, 5))
        
        # 标题文本
        tk.Label(title_bar, text="日程提醒", bg=self._darken_color(self.bg_color, 0.05), fg=self.fg_color, font=("Microsoft YaHei", 10, "bold")).pack(side=LEFT)
        
        # 关闭按钮 (X)
        close_btn = tk.Label(title_bar, text="✕", bg=self._darken_color(self.bg_color, 0.05), fg=self.fg_color, font=("Arial", 10), cursor="hand2")
        close_btn.pack(side=RIGHT, padx=10)
        close_btn.bind("<Button-1>", lambda e: self.close_window())
        close_btn.bind("<Enter>", lambda e: close_btn.configure(bg="#E81123", fg="white"))
        close_btn.bind("<Leave>", lambda e: close_btn.configure(bg=self._darken_color(self.bg_color, 0.05), fg=self.fg_color))
        
        # --- 内容区域 ---
        content_frame = tk.Frame(main_panel, bg=self.bg_color, padx=20, pady=15)
        content_frame.pack(fill=BOTH, expand=True)
        
        # 提醒标题
        tk.Label(content_frame, text=self.reminder.title, 
                font=("Microsoft YaHei", 16, "bold"),
                bg=self.bg_color, fg=self.fg_color,
                wraplength=360, justify=LEFT, anchor="w").pack(fill=X, pady=(0, 10))
        
        # 时间信息
        time_frame = tk.Frame(content_frame, bg=self.bg_color)
        time_frame.pack(fill=X, pady=(0, 5))
        
        tk.Label(time_frame, text="🕒", font=("Segoe UI Emoji", 10), bg=self.bg_color, fg=self.fg_color).pack(side=LEFT, padx=(0, 5))
        tk.Label(time_frame, text=f"{self.reminder.time}", 
                font=("Microsoft YaHei", 12), bg=self.bg_color, 
                fg=self.fg_color).pack(side=LEFT)
                
        # 描述信息
        if self.reminder.description:
            desc_frame = tk.Frame(content_frame, bg=self.bg_color)
            desc_frame.pack(fill=X, pady=(5, 0))
            tk.Label(desc_frame, text="📝 " + self.reminder.description, 
                    font=("Microsoft YaHei", 10), bg=self.bg_color,
                    fg=self._get_secondary_color(self.bg_color),
                    wraplength=360, justify=LEFT, anchor="w").pack(fill=X)

        # --- 按钮区域 ---
        btn_frame = tk.Frame(main_panel, bg=self.bg_color, pady=15, padx=20)
        btn_frame.pack(fill=X, side=BOTTOM)
        
        # 样式化按钮
        btn_bg = self._lighten_color(self.bg_color, 0.8)
        btn_hover = self._lighten_color(self.bg_color, 0.9)
        
        # 查看详情按钮
        detail_btn = tk.Label(btn_frame, text="查看详情", font=("Microsoft YaHei", 10),
                             bg=btn_bg, fg=self.fg_color, cursor="hand2",
                             padx=15, pady=6, relief="flat")
        detail_btn.pack(side=LEFT)
        detail_btn.bind("<Button-1>", lambda e: self.show_details())
        detail_btn.bind("<Enter>", lambda e: detail_btn.configure(bg=btn_hover))
        detail_btn.bind("<Leave>", lambda e: detail_btn.configure(bg=btn_bg))
        
        # 我知道了按钮
        ok_btn = tk.Label(btn_frame, text="我知道了", font=("Microsoft YaHei", 10, "bold"),
                         bg=self.fg_color, fg=self.bg_color, cursor="hand2", # 反色显示，更醒目
                         padx=20, pady=6, relief="flat")
        ok_btn.pack(side=RIGHT)
        ok_btn.bind("<Button-1>", lambda e: self.close_window())
        ok_btn.bind("<Enter>", lambda e: ok_btn.configure(bg=self._darken_color(self.fg_color, 0.1))) # 简单的hover效果
        ok_btn.bind("<Leave>", lambda e: ok_btn.configure(bg=self.fg_color))

    def _start_drag(self, event):
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def _do_drag(self, event):
        x = self.window.winfo_x() - self._drag_data["x"] + event.x
        y = self.window.winfo_y() - self._drag_data["y"] + event.y
        self.window.geometry(f"+{x}+{y}")

    def show_notification(self):
        """显示通知（播放提示音）"""
        if winsound is not None:
            try:
                winsound.MessageBeep(winsound.MB_ICONINFORMATION)
            except Exception:
                try:
                    winsound.Beep(800, 200)
                except Exception:
                    pass
        
        self.animate_window()
    
    def animate_window(self):
        """窗口显示动画"""
        self.window.attributes('-alpha', 0.0)

        def step(alpha):
            try:
                if not self.window.winfo_exists():
                    return
                next_alpha = alpha + 0.1
                if next_alpha > 0.95:
                    next_alpha = 0.95
                self.window.attributes('-alpha', next_alpha)
                if next_alpha < 0.95:
                    self.window.after(20, lambda: step(next_alpha))
            except tk.TclError:
                return

        self.window.after(20, lambda: step(0.0))

    def _get_contrast_color(self, hex_color: str) -> str:
        """根据背景色返回黑或白的前景色"""
        try:
            c = hex_color.lstrip('#')
            r, g, b = tuple(int(c[i:i+2], 16) for i in (0, 2, 4))
            brightness = r * 0.299 + g * 0.587 + b * 0.114
            return '#FFFFFF' if brightness < 140 else '#333333' # 不使用纯黑
        except Exception:
            return '#333333'

    def _get_secondary_color(self, hex_color: str) -> str:
        """返回次级前景色"""
        base = self._get_contrast_color(hex_color)
        return '#EEEEEE' if base == '#FFFFFF' else '#555555'
    
    def _lighten_color(self, hex_color: str, factor: float) -> str:
        """淡化颜色 (混合白色)"""
        try:
            hex_color = hex_color.lstrip('#')
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            
            r = int(r + (255 - r) * (1 - factor))
            g = int(g + (255 - g) * (1 - factor))
            b = int(b + (255 - b) * (1 - factor))
            
            return f"#{r:02x}{g:02x}{b:02x}"
        except Exception:
            return hex_color

    def _darken_color(self, hex_color: str, factor: float) -> str:
        """加深颜色 (混合黑色) factor: 0.0-1.0, 越大越黑"""
        try:
            hex_color = hex_color.lstrip('#')
            if len(hex_color) != 6: return hex_color # 简单防护
            
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            
            r = int(r * (1 - factor))
            g = int(g * (1 - factor))
            b = int(b * (1 - factor))
            
            return f"#{r:02x}{g:02x}{b:02x}"
        except Exception:
            return hex_color
    
    def show_details(self):
        """显示提醒详情"""
        try:
            if not self.window.winfo_exists():
                return
            from calendar_reminder import ReminderEditDialog
            self._details_dialog = ReminderEditDialog(
                parent=self.window, 
                reminder_manager=self.reminder_manager,
                selected_date=self.reminder.date,
                reminder=self.reminder,
                on_closed=lambda: setattr(self, "_details_dialog", None),
            )
        except Exception as e:
            parent = self.window if getattr(self.window, "winfo_exists", lambda: False)() else None
            messagebox.showerror("错误", f"无法打开详情窗口: {str(e)}", parent=parent)
    
    def close_window(self):
        """关闭窗口"""
        try:
            if self.close_callback:
                self.close_callback(self.reminder)
            self.window.destroy()
        except Exception:
            pass

class NotificationManager:
    """通知管理器"""
    
    def __init__(self):
        self.active_notifications = {}
    
    def show_reminder_notification(self, reminder: ReminderData, reminder_manager=None):
        """显示提醒通知"""
        if reminder.id in self.active_notifications:
            return
        
        try:
            notification = ReminderNotificationWindow(
                reminder, 
                reminder_manager,
                lambda r, snooze_minutes=0: self.on_notification_closed(r, snooze_minutes),
                parent=getattr(reminder_manager, "tk_root", None) if reminder_manager else None
            )
            self.active_notifications[reminder.id] = notification
        except Exception as e:
            print(f"显示通知失败: {e}")
    
    def on_notification_closed(self, reminder: ReminderData, snooze_minutes: int = 0):
        """通知关闭回调"""
        if reminder.id in self.active_notifications:
            del self.active_notifications[reminder.id]
    
    def close_all_notifications(self):
        """关闭所有通知"""
        for notification in list(self.active_notifications.values()):
            try:
                notification.close_window()
            except Exception:
                pass
        self.active_notifications.clear()

notification_manager = NotificationManager()

def show_reminder_notification(reminder: ReminderData, reminder_manager=None):
    """显示提醒通知的便捷函数"""
    notification_manager.show_reminder_notification(reminder, reminder_manager)
