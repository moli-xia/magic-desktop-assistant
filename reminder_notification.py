import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import threading
import time
from typing import Callable
from calendar_reminder import ReminderData
import winsound
import os

class ReminderNotificationWindow:
    """提醒通知窗口 - 在桌面右下角显示"""
    
    def __init__(self, reminder: ReminderData, reminder_manager=None, close_callback: Callable = None):
        self.reminder = reminder
        self.reminder_manager = reminder_manager
        self.close_callback = close_callback
        # 主题色与前景色
        self.bg_color = self.reminder.color
        self.fg_color = self._get_contrast_color(self.bg_color)
        
        self.window = tk.Toplevel()
        self.window.title("提醒")
        self.window.geometry("380x180")  # 调整窗口尺寸
        self.window.resizable(False, False)
        
        # 设置窗口置顶
        self.window.attributes('-topmost', True)
        
        # 设置窗口位置在右下角
        self.position_window()
        
        # 设置窗口样式
        self.window.configure(bg=self.bg_color)
        
        self.setup_ui()
        self.show_notification()
        
        # 移除自动关闭功能，弹窗保持不动直到用户手动关闭
    
    def position_window(self):
        """将窗口定位到屏幕右下角"""
        self.window.update_idletasks()
        
        # 获取屏幕尺寸
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        
        # 获取窗口尺寸
        window_width = 480
        window_height = 280
        
        # 计算位置（右下角，留出任务栏空间）
        x = screen_width - window_width - 20
        y = screen_height - window_height - 80  # 留出任务栏空间
        
        self.window.geometry(f"{window_width}x{window_height}+{x}+{y}")
    
    def setup_ui(self):
        """设置通知界面"""
        # 主框架
        main_frame = tk.Frame(self.window, bg=self.bg_color, bd=0)
        main_frame.pack(fill=BOTH, expand=True, padx=15, pady=15)

        # 创建卡片容器（使用用户选择的颜色作为背景）
        card = tk.Frame(main_frame, bg=self.bg_color, relief="solid", bd=2)
        card.pack(fill=BOTH, expand=True)
        
        # 强制设置背景色
        try:
            card.configure(bg=self.bg_color)
            main_frame.configure(bg=self.bg_color)
        except:
            pass
        
        # 顶部标题栏
        header_frame = tk.Frame(card, bg=self.bg_color, height=50)
        header_frame.pack(fill=X, padx=15, pady=(15, 10))
        header_frame.pack_propagate(False)
        
        # 强制设置标题栏背景色
        header_frame.configure(bg=self.bg_color)
        
        # 左侧：提醒图标
        left_header = tk.Frame(header_frame, bg=self.bg_color)
        left_header.pack(side=LEFT, fill=Y)
        left_header.configure(bg=self.bg_color)
        
        # 提醒图标
        icon_label = tk.Label(left_header, text="🔔", 
                             font=("Arial", 16), bg=self.bg_color, fg=self.fg_color)
        icon_label.pack(side=LEFT, padx=(0, 10))
        icon_label.configure(bg=self.bg_color, fg=self.fg_color)
        
        # 中间：标题
        title_label = tk.Label(header_frame, text=self.reminder.title, 
                               font=("Microsoft YaHei", 14, "bold"),
                               bg=self.bg_color, fg=self.fg_color,
                               wraplength=250, justify=LEFT, anchor="w")
        title_label.pack(side=LEFT, fill=X, expand=True, padx=(0, 10))
        title_label.configure(bg=self.bg_color, fg=self.fg_color)
        
        # 移除关闭按钮，只保留标题
        
        # 内容区域
        content_frame = tk.Frame(card, bg=self.bg_color)
        content_frame.pack(fill=BOTH, expand=True, padx=15, pady=(0, 10))
        content_frame.configure(bg=self.bg_color)
        
        # 时间信息
        time_frame = tk.Frame(content_frame, bg=self.bg_color)
        time_frame.pack(fill=X, pady=(0, 8), anchor="w")
        time_frame.configure(bg=self.bg_color)
        
        time_icon = tk.Label(time_frame, text="⏰", 
                            font=("Arial", 12), bg=self.bg_color, fg=self.fg_color)
        time_icon.pack(side=LEFT, padx=(0, 8))
        time_icon.configure(bg=self.bg_color, fg=self.fg_color)
        
        time_label = tk.Label(time_frame, text=f"提醒时间: {self.reminder.time}", 
                             font=("Microsoft YaHei", 11), bg=self.bg_color,
                             fg=self._get_secondary_color(self.bg_color), anchor="w")
        time_label.pack(side=LEFT, fill=X, expand=True)
        time_label.configure(bg=self.bg_color, fg=self._get_secondary_color(self.bg_color))
        
        # 重复类型信息（如果有重复）
        if self.reminder.repeat_type != "none":
            repeat_frame = tk.Frame(content_frame, bg=self.bg_color)
            repeat_frame.pack(fill=X, pady=(0, 8), anchor="w")
            repeat_frame.configure(bg=self.bg_color)
            
            repeat_icon = tk.Label(repeat_frame, text="🔄", 
                                  font=("Arial", 12), bg=self.bg_color, fg=self.fg_color)
            repeat_icon.pack(side=LEFT, padx=(0, 8))
            repeat_icon.configure(bg=self.bg_color, fg=self.fg_color)
            
            # 重复类型映射
            repeat_map = {"daily": "每天", "weekly": "每周", "monthly": "每月", "yearly": "每年"}
            repeat_text = repeat_map.get(self.reminder.repeat_type, self.reminder.repeat_type)
            
            repeat_label = tk.Label(repeat_frame, text=f"重复类型: {repeat_text}", 
                                   font=("Microsoft YaHei", 11), bg=self.bg_color,
                                   fg=self._get_secondary_color(self.bg_color), anchor="w")
            repeat_label.pack(side=LEFT, fill=X, expand=True)
            repeat_label.configure(bg=self.bg_color, fg=self._get_secondary_color(self.bg_color))
        
        # 描述信息（如果有）
        if self.reminder.description:
            desc_frame = tk.Frame(content_frame, bg=self.bg_color)
            desc_frame.pack(fill=X, pady=(0, 8), anchor="w")
            desc_frame.configure(bg=self.bg_color)
            
            desc_icon = tk.Label(desc_frame, text="📝", 
                                font=("Arial", 12), bg=self.bg_color, fg=self.fg_color)
            desc_icon.pack(side=LEFT, padx=(0, 8))
            desc_icon.configure(bg=self.bg_color, fg=self.fg_color)
            
            desc_label = tk.Label(desc_frame, text=self.reminder.description, 
                                  font=("Microsoft YaHei", 10), bg=self.bg_color,
                                  fg=self._get_secondary_color(self.bg_color),
                                  wraplength=400, justify=LEFT, anchor="w")
            desc_label.pack(side=LEFT, fill=X, expand=True)
            desc_label.configure(bg=self.bg_color, fg=self._get_secondary_color(self.bg_color))
        
        # 按钮区域 - 显示"查看详情"和"我知道了"按钮
        button_frame = tk.Frame(card, bg=self.bg_color)
        button_frame.pack(fill=X, padx=15, pady=(15, 20))
        button_frame.configure(bg=self.bg_color)
        
        # 查看详情按钮
        detail_btn = tk.Button(button_frame, text="查看详情", 
                              font=("Microsoft YaHei", 12, "bold"),
                              bg=self._lighten_color(self.bg_color, 0.7),
                              fg=self.fg_color,
                              activebackground=self._lighten_color(self.bg_color, 0.6),
                              activeforeground=self.fg_color,
                              relief="solid", bd=2,
                              command=self.show_details,
                              padx=20, pady=8,
                              width=8)
        detail_btn.pack(side=LEFT, expand=True, fill=X, padx=(0, 5))
        detail_btn.configure(bg=self._lighten_color(self.bg_color, 0.7), fg=self.fg_color)
        
        # 我知道了按钮
        ok_btn = tk.Button(button_frame, text="我知道了", 
                          font=("Microsoft YaHei", 12, "bold"),
                          bg=self._lighten_color(self.bg_color, 0.6),
                          fg=self.fg_color,
                          activebackground=self._lighten_color(self.bg_color, 0.5),
                          activeforeground=self.fg_color,
                          relief="solid", bd=2,
                          command=self.close_window,
                          padx=20, pady=8,
                          width=8)
        ok_btn.pack(side=LEFT, expand=True, fill=X, padx=(5, 0))
        ok_btn.configure(bg=self._lighten_color(self.bg_color, 0.6), fg=self.fg_color)
        
        # 强制刷新所有组件的背景色
        self.window.update_idletasks()
        try:
            # 强制设置窗口背景色
            self.window.configure(bg=self.bg_color)
            # 强制设置所有框架背景色
            main_frame.configure(bg=self.bg_color)
            card.configure(bg=self.bg_color)
        except:
            pass
        
        # 绑定窗口关闭事件，防止意外关闭
        self.window.protocol("WM_DELETE_WINDOW", self.close_window)
        
        # 绑定点击事件，防止点击内容区域时关闭窗口
        def on_click(event):
            # 只允许点击按钮时关闭，其他区域点击不关闭
            pass
        
        # 为所有组件绑定点击事件
        main_frame.bind("<Button-1>", on_click)
        card.bind("<Button-1>", on_click)
        header_frame.bind("<Button-1>", on_click)
        content_frame.bind("<Button-1>", on_click)
        time_frame.bind("<Button-1>", on_click)
        if self.reminder.description:
            desc_frame.bind("<Button-1>", on_click)

    
    def show_notification(self):
        """显示通知（播放提示音）"""
        try:
            # 播放系统提示音
            winsound.MessageBeep(winsound.MB_ICONINFORMATION)
        except Exception:
            # 如果系统提示音失败，尝试播放默认声音
            try:
                winsound.Beep(800, 200)
            except Exception:
                pass  # 忽略声音播放错误
        
        # 窗口动画效果
        self.animate_window()
    
    def animate_window(self):
        """窗口显示动画"""
        # 简单的淡入效果
        self.window.attributes('-alpha', 0.0)
        
        def fade_in():
            alpha = 0.0
            while alpha < 1.0:
                alpha += 0.1
                try:
                    self.window.attributes('-alpha', alpha)
                    time.sleep(0.02)
                except tk.TclError:
                    break  # 窗口已关闭
        
        fade_thread = threading.Thread(target=fade_in, daemon=True)
        fade_thread.start()

    def _get_contrast_color(self, hex_color: str) -> str:
        """根据背景色返回黑或白的前景色，以保证对比度"""
        try:
            c = hex_color.lstrip('#')
            r, g, b = tuple(int(c[i:i+2], 16) for i in (0, 2, 4))
            brightness = r * 0.299 + g * 0.587 + b * 0.114
            return 'white' if brightness < 140 else 'black'
        except Exception:
            return 'black'

    def _get_secondary_color(self, hex_color: str) -> str:
        """返回用于副标题/描述的次级前景色（在主前景基础上稍作淡化）"""
        base = self._get_contrast_color(hex_color)
        return '#EEEEEE' if base == 'white' else '#333333'
    
    def _lighten_color(self, hex_color: str, factor: float) -> str:
        """淡化颜色"""
        try:
            # 移除#号
            hex_color = hex_color.lstrip('#')
            
            # 转换为RGB
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            
            # 淡化颜色
            r = int(255 - (255 - r) * factor)
            g = int(255 - (255 - g) * factor)
            b = int(255 - (255 - b) * factor)
            
            # 确保值在0-255范围内
            r = max(0, min(255, r))
            g = max(0, min(255, g))
            b = max(0, min(255, b))
            
            # 转换回十六进制
            return f"#{r:02x}{g:02x}{b:02x}"
        except Exception:
            return hex_color
    
    
    def show_details(self):
        """显示提醒详情（打开编辑窗口）"""
        try:
            # 导入编辑对话框
            from calendar_reminder import ReminderEditDialog
            
            # 创建编辑对话框，需要传递 reminder_manager 和 selected_date
            edit_dialog = ReminderEditDialog(
                parent=self.window, 
                reminder_manager=self.reminder_manager,
                selected_date=self.reminder.date,
                reminder=self.reminder
            )
            
            # 显示对话框
            self.window.wait_window(edit_dialog.dialog)
            
            # 如果用户保存了修改，更新提醒数据
            if edit_dialog.result == "saved":
                # 这里可以添加更新提醒的逻辑
                # 由于我们只是查看详情，暂时不处理保存逻辑
                pass
                
        except Exception as e:
            print(f"打开详情窗口失败: {e}")
            # 如果打开详情失败，显示错误信息
            import tkinter.messagebox as mb
            mb.showerror("错误", f"无法打开详情窗口: {str(e)}", parent=self.window)
    
    def close_window(self):
        """关闭窗口"""
        try:
            if self.close_callback:
                self.close_callback(self.reminder)
            
            self.window.destroy()
        except Exception:
            pass  # 忽略关闭错误

class NotificationManager:
    """通知管理器"""
    
    def __init__(self):
        self.active_notifications = {}
    
    def show_reminder_notification(self, reminder: ReminderData, reminder_manager=None):
        """显示提醒通知"""
        # 检查是否已有相同提醒的通知
        if reminder.id in self.active_notifications:
            return
        
        try:
            notification = ReminderNotificationWindow(
                reminder, 
                reminder_manager,
                lambda r, snooze_minutes=0: self.on_notification_closed(r, snooze_minutes)
            )
            self.active_notifications[reminder.id] = notification
        except Exception as e:
            print(f"显示通知失败: {e}")
    
    def on_notification_closed(self, reminder: ReminderData, snooze_minutes: int = 0):
        """通知关闭回调"""
        # 从活动通知中移除
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

# 全局通知管理器实例
notification_manager = NotificationManager()

def show_reminder_notification(reminder: ReminderData, reminder_manager=None):
    """显示提醒通知的便捷函数"""
    notification_manager.show_reminder_notification(reminder, reminder_manager)
