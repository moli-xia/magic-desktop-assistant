import tkinter as tk
from tkinter import messagebox, colorchooser
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from datetime import datetime, timedelta, date
import json
import os
import threading
import time
from typing import Dict, List, Optional
import calendar as cal

class ReminderData:
    """提醒事项数据类"""
    def __init__(self, id: str, title: str, date: str, time: str, color: str, description: str = "", 
                 repeat_type: str = "none", is_active: bool = True):
        self.id = id
        self.title = title
        self.date = date  # YYYY-MM-DD 格式
        self.time = time  # HH:MM 格式
        self.color = color
        self.description = description
        self.repeat_type = repeat_type  # none, daily, weekly, monthly
        self.is_active = is_active
        
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'date': self.date,
            'time': self.time,
            'color': self.color,
            'description': self.description,
            'repeat_type': self.repeat_type,
            'is_active': self.is_active
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(**data)

class CalendarReminderManager:
    """日历提醒管理器"""
    
    def __init__(self, app_data_dir: str):
        self.app_data_dir = app_data_dir
        self.reminders_file = os.path.join(app_data_dir, "reminders.json")
        self.reminders: Dict[str, ReminderData] = {}
        self.notification_callback = None
        self.check_timer = None
        # 触发去重：在同一分钟内同一提醒只触发一次
        self._last_trigger_minute: Optional[str] = None
        self._fired_ids_in_minute: set[str] = set()
        self.load_reminders()
        self.start_reminder_checker()
        
    def load_reminders(self):
        """从文件加载提醒数据"""
        if os.path.exists(self.reminders_file):
            try:
                with open(self.reminders_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for reminder_data in data:
                        reminder = ReminderData.from_dict(reminder_data)
                        self.reminders[reminder.id] = reminder
            except Exception as e:
                print(f"加载提醒数据失败: {e}")
    
    def save_reminders(self):
        """保存提醒数据到文件"""
        try:
            data = [reminder.to_dict() for reminder in self.reminders.values()]
            with open(self.reminders_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存提醒数据失败: {e}")
    
    def add_reminder(self, reminder: ReminderData) -> str:
        """添加提醒事项"""
        self.reminders[reminder.id] = reminder
        self.save_reminders()
        return reminder.id
    
    def update_reminder(self, reminder: ReminderData):
        """更新提醒事项"""
        if reminder.id in self.reminders:
            self.reminders[reminder.id] = reminder
            self.save_reminders()
    
    def delete_reminder(self, reminder_id: str):
        """删除提醒事项"""
        if reminder_id in self.reminders:
            del self.reminders[reminder_id]
            self.save_reminders()
    
    def get_reminders_by_date(self, target_date: str) -> List[ReminderData]:
        """获取指定日期的提醒事项"""
        reminders = []
        for reminder in self.reminders.values():
            if not reminder.is_active:
                continue
                
            if reminder.date == target_date:
                reminders.append(reminder)
            elif reminder.repeat_type != "none":
                # 处理重复提醒
                if self._should_repeat_on_date(reminder, target_date):
                    reminders.append(reminder)
        
        return sorted(reminders, key=lambda x: x.time)
    
    def _should_repeat_on_date(self, reminder: ReminderData, target_date: str) -> bool:
        """判断重复提醒是否应在指定日期触发"""
        reminder_date = datetime.strptime(reminder.date, "%Y-%m-%d").date()
        target_date_obj = datetime.strptime(target_date, "%Y-%m-%d").date()
        
        if target_date_obj < reminder_date:
            return False
            
        if reminder.repeat_type == "daily":
            return True
        elif reminder.repeat_type == "weekly":
            return (target_date_obj - reminder_date).days % 7 == 0
        elif reminder.repeat_type == "monthly":
            return (target_date_obj.day == reminder_date.day and 
                   target_date_obj > reminder_date)
        elif reminder.repeat_type == "yearly":
            return (target_date_obj.month == reminder_date.month and 
                   target_date_obj.day == reminder_date.day and 
                   target_date_obj > reminder_date)
        
        return False
    
    def set_notification_callback(self, callback):
        """设置通知回调函数"""
        self.notification_callback = callback
    
    def start_reminder_checker(self):
        """启动提醒检查器"""
        def check_reminders():
            while True:
                try:
                    now = datetime.now()
                    current_date = now.strftime("%Y-%m-%d")
                    current_time = now.strftime("%H:%M")
                    minute_key = now.strftime("%Y-%m-%d %H:%M")

                    # 跨分钟重置触发去重集合
                    if minute_key != self._last_trigger_minute:
                        self._last_trigger_minute = minute_key
                        self._fired_ids_in_minute.clear()
                    
                    reminders = self.get_reminders_by_date(current_date)
                    for reminder in reminders:
                        if reminder.time == current_time and reminder.id not in self._fired_ids_in_minute:
                            if self.notification_callback:
                                self.notification_callback(reminder, self)
                            self._fired_ids_in_minute.add(reminder.id)
                    
                    time.sleep(1)  # 提高检查频率，降低弹出延迟
                except Exception as e:
                    print(f"提醒检查错误: {e}")
                    time.sleep(1)
        
        self.check_timer = threading.Thread(target=check_reminders, daemon=True)
        self.check_timer.start()

class CalendarWidget(ttk.Frame):
    """日历组件"""
    
    def __init__(self, parent, reminder_manager: CalendarReminderManager, **kwargs):
        super().__init__(parent, **kwargs)
        self.reminder_manager = reminder_manager
        self.current_date = datetime.now().date()
        self.selected_date = None
        self.day_buttons = {}
        self.setup_ui()
        
    def setup_ui(self):
        """设置日历界面"""
        # 月份导航
        nav_frame = ttk.Frame(self)
        nav_frame.pack(fill=X, pady=5)
        
        self.prev_button = ttk.Button(nav_frame, text="◀", width=3, command=self.prev_month)
        self.prev_button.pack(side=LEFT)
        
        # 年份选择框
        self.year_var = tk.StringVar()
        self.year_combo = ttk.Combobox(nav_frame, textvariable=self.year_var, width=6, state="readonly")
        self.year_combo.pack(side=LEFT, padx=(10, 5))
        
        # 月份选择框
        self.month_var = tk.StringVar()
        self.month_combo = ttk.Combobox(nav_frame, textvariable=self.month_var, width=8, state="readonly")
        self.month_combo.pack(side=LEFT, padx=(5, 10))
        
        # 设置下拉框选项
        self.setup_dropdowns()
        
        # 绑定选择事件
        self.year_combo.bind("<<ComboboxSelected>>", self.on_year_changed)
        self.month_combo.bind("<<ComboboxSelected>>", self.on_month_changed)
        
        self.next_button = ttk.Button(nav_frame, text="▶", width=3, command=self.next_month)
        self.next_button.pack(side=RIGHT)
        
        # 星期标题
        week_frame = ttk.Frame(self)
        week_frame.pack(fill=X, pady=2)
        
        weekdays = ['一', '二', '三', '四', '五', '六', '日']
        for i, day in enumerate(weekdays):
            label = ttk.Label(week_frame, text=day, font=("Arial", 10, "bold"))
            label.grid(row=0, column=i, sticky="ew", padx=1)
            week_frame.grid_columnconfigure(i, weight=1)
        
        # 日期网格
        self.calendar_frame = ttk.Frame(self)
        self.calendar_frame.pack(fill=BOTH, expand=True, pady=2)
        
        for i in range(7):
            self.calendar_frame.grid_columnconfigure(i, weight=1)
        for i in range(6):
            self.calendar_frame.grid_rowconfigure(i, weight=1)
        
        self.update_calendar()
    
    def setup_dropdowns(self):
        """设置下拉框选项"""
        # 年份选项（当前年份前后50年）
        current_year = self.current_date.year
        years = [str(year) for year in range(current_year - 50, current_year + 51)]
        self.year_combo['values'] = years
        self.year_var.set(str(current_year))
        
        # 月份选项
        month_names = ['一月', '二月', '三月', '四月', '五月', '六月',
                      '七月', '八月', '九月', '十月', '十一月', '十二月']
        self.month_combo['values'] = month_names
        self.month_var.set(month_names[self.current_date.month - 1])
    
    def on_year_changed(self, event=None):
        """年份选择改变事件"""
        try:
            new_year = int(self.year_var.get())
            self.current_date = self.current_date.replace(year=new_year)
            self.update_calendar()
        except ValueError:
            pass
    
    def on_month_changed(self, event=None):
        """月份选择改变事件"""
        try:
            month_names = ['一月', '二月', '三月', '四月', '五月', '六月',
                          '七月', '八月', '九月', '十月', '十一月', '十二月']
            new_month = month_names.index(self.month_var.get()) + 1
            self.current_date = self.current_date.replace(month=new_month)
            self.update_calendar()
        except ValueError:
            pass
    
    def prev_month(self):
        """上一个月"""
        if self.current_date.month == 1:
            self.current_date = self.current_date.replace(year=self.current_date.year - 1, month=12)
        else:
            self.current_date = self.current_date.replace(month=self.current_date.month - 1)
        self.update_calendar()
    
    def next_month(self):
        """下一个月"""
        if self.current_date.month == 12:
            self.current_date = self.current_date.replace(year=self.current_date.year + 1, month=1)
        else:
            self.current_date = self.current_date.replace(month=self.current_date.month + 1)
        self.update_calendar()
    
    def update_calendar(self):
        """更新日历显示"""
        # 清除现有按钮
        for widget in self.calendar_frame.winfo_children():
            widget.destroy()
        self.day_buttons.clear()
        
        # 更新下拉框的值
        self.year_var.set(str(self.current_date.year))
        month_names = ['一月', '二月', '三月', '四月', '五月', '六月',
                      '七月', '八月', '九月', '十月', '十一月', '十二月']
        self.month_var.set(month_names[self.current_date.month - 1])
        
        # 获取月历数据
        calendar_data = cal.monthcalendar(self.current_date.year, self.current_date.month)
        
        # 创建日期按钮
        for week_num, week in enumerate(calendar_data):
            for day_num, day in enumerate(week):
                if day == 0:
                    continue
                
                date_obj = date(self.current_date.year, self.current_date.month, day)
                date_str = date_obj.strftime("%Y-%m-%d")
                
                # 检查是否有提醒
                reminders = self.reminder_manager.get_reminders_by_date(date_str)
                
                # 创建按钮框架
                btn_frame = tk.Frame(self.calendar_frame)
                btn_frame.grid(row=week_num, column=day_num, sticky="ew", padx=1, pady=1)

                # 根据状态选择样式：有提醒优先(红色圆点)、今日(蓝色)、普通(默认)
                if reminders:
                    # 有提醒：使用大红圆点，更加显眼
                    if date_obj == date.today():
                        # 既是今天又有提醒：红色圆点 + 蓝色背景
                        btn = tk.Button(
                            btn_frame,
                            text=f"●{day}",  # 使用红色圆点图标
                            command=lambda d=date_str: self.on_date_click(d),
                            bg="#4A90E2",     # 蓝色背景（今日）
                            fg="#FF0000",     # 红色圆点和文字
                            font=("Arial", 18, "bold"),
                            relief="raised",
                            bd=3,
                            highlightthickness=3,
                            highlightbackground="#FF0000"
                        )
                    else:
                        # 有提醒但不是今天：红色圆点 + 白色背景
                        btn = tk.Button(
                            btn_frame,
                            text=f"●{day}",  # 使用红色圆点图标
                            command=lambda d=date_str: self.on_date_click(d),
                            bg="white",     # 白色背景让红圆点更突出
                            fg="#FF0000",   # 红色圆点和文字
                            font=("Arial", 18, "bold"),
                            relief="raised",
                            bd=3,
                            highlightthickness=3,
                            highlightbackground="#FF0000"
                        )
                elif date_obj == date.today():
                    # 今天但没有提醒：蓝色背景
                    btn = tk.Button(
                        btn_frame,
                        text=str(day),
                        command=lambda d=date_str: self.on_date_click(d),
                        bg="#4A90E2",
                        fg="white",
                        font=("Arial", 10, "bold"),
                        relief="raised",
                        bd=1
                    )
                else:
                    btn = ttk.Button(
                        btn_frame,
                        text=str(day),
                        command=lambda d=date_str: self.on_date_click(d)
                    )

                btn.pack(fill=BOTH, expand=True)
                
                self.day_buttons[date_str] = btn
    
    def _is_dark_color(self, hex_color):
        """判断颜色是否为深色"""
        try:
            # 移除#号
            hex_color = hex_color.lstrip('#')
            # 转换为RGB
            r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            # 计算亮度 (使用标准亮度公式)
            brightness = (r * 0.299 + g * 0.587 + b * 0.114)
            return brightness < 128
        except Exception:
            return False
    
    def _lighten_color(self, hex_color, factor=0.7):
        """将颜色变浅，factor越大颜色越浅"""
        try:
            # 移除#号
            hex_color = hex_color.lstrip('#')
            # 转换为RGB
            r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            
            # 向白色(255,255,255)混合
            r = int(r + (255 - r) * factor)
            g = int(g + (255 - g) * factor)
            b = int(b + (255 - b) * factor)
            
            # 确保值在0-255范围内
            r = max(0, min(255, r))
            g = max(0, min(255, g))
            b = max(0, min(255, b))
            
            result = f"#{r:02x}{g:02x}{b:02x}"
            print(f"颜色淡化: {hex_color} -> {result} (factor={factor})")  # 调试输出
            return result
        except Exception as e:
            print(f"颜色淡化失败: {e}")
            return "#F0F0F0"  # 默认浅灰色
    
    def on_date_click(self, date_str):
        """日期点击事件"""
        self.selected_date = date_str
        # 触发外部事件处理
        if hasattr(self, 'date_click_callback'):
            self.date_click_callback(date_str)

class ReminderEditDialog:
    """提醒事项编辑对话框"""
    
    def __init__(self, parent, reminder_manager: CalendarReminderManager, 
                 selected_date: str, reminder: Optional[ReminderData] = None):
        self.parent = parent
        self.reminder_manager = reminder_manager
        self.selected_date = selected_date
        self.reminder = reminder
        self.result = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("编辑提醒" if reminder else "添加提醒")
        self.dialog.geometry("560x520")  # 增加宽度和高度
        try:
            self.dialog.minsize(560, 520)
        except Exception:
            pass
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # 设置关闭协议
        self.dialog.protocol("WM_DELETE_WINDOW", self.cancel)
        
        # 居中显示
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() - self.dialog.winfo_reqwidth()) // 2
        y = (self.dialog.winfo_screenheight() - self.dialog.winfo_reqheight()) // 2
        self.dialog.geometry(f"+{x}+{y}")
        
        self.setup_ui()
        
        if reminder:
            self.load_reminder_data()
    
    def setup_ui(self):
        """设置对话框界面"""
        try:
            main_frame = ttk.Frame(self.dialog, padding=20)
            main_frame.pack(fill=BOTH, expand=True)
            
            # 标题
            ttk.Label(main_frame, text="标题:", font=("Arial", 10)).grid(row=0, column=0, sticky=W, pady=5)
            self.title_entry = ttk.Entry(main_frame, width=30)
            self.title_entry.grid(row=0, column=1, columnspan=2, sticky=EW, pady=5)
            
            # 日期
            ttk.Label(main_frame, text="日期:", font=("Arial", 10)).grid(row=1, column=0, sticky=W, pady=5)
            self.date_entry = ttk.Entry(main_frame, width=15)
            self.date_entry.grid(row=1, column=1, sticky=W, pady=5)
            self.date_entry.insert(0, self.selected_date)
            
            # 时间
            ttk.Label(main_frame, text="时间:", font=("Arial", 10)).grid(row=2, column=0, sticky=W, pady=5)
            time_frame = ttk.Frame(main_frame)
            time_frame.grid(row=2, column=1, columnspan=2, sticky=EW, pady=5)
            
            self.hour_var = tk.StringVar(value="09")
            self.minute_var = tk.StringVar(value="00")
            
            hour_combo = ttk.Combobox(time_frame, textvariable=self.hour_var, width=3, 
                                     values=[f"{i:02d}" for i in range(24)], state="readonly")
            hour_combo.pack(side=LEFT)
            
            ttk.Label(time_frame, text=":").pack(side=LEFT, padx=2)
            
            minute_combo = ttk.Combobox(time_frame, textvariable=self.minute_var, width=3,
                                       values=[f"{i:02d}" for i in range(60)], state="readonly")
            minute_combo.pack(side=LEFT)
            
            # 颜色选择
            ttk.Label(main_frame, text="颜色:", font=("Arial", 10)).grid(row=3, column=0, sticky=W, pady=5)
            color_frame = ttk.Frame(main_frame)
            color_frame.grid(row=3, column=1, columnspan=2, sticky=EW, pady=5)
            
            self.selected_color = "#FF6B6B"  # 默认红色
            self.color_button = ttk.Button(color_frame, text="选择颜色", command=self.choose_color)
            self.color_button.pack(side=LEFT)
            
            self.color_preview = tk.Label(color_frame, width=3, height=1, bg=self.selected_color, relief="solid")
            self.color_preview.pack(side=LEFT, padx=(10, 0))
            
            # 重复类型
            ttk.Label(main_frame, text="重复:", font=("Arial", 10)).grid(row=4, column=0, sticky=W, pady=5)
            self.repeat_var = tk.StringVar(value="不重复")
            self.repeat_combo = ttk.Combobox(main_frame, textvariable=self.repeat_var, width=15,
                                       values=["不重复", "每天", "每周", "每月", "每年"],
                                       state="readonly")
            self.repeat_combo.grid(row=4, column=1, sticky=W, pady=5)
            
            # 描述
            ttk.Label(main_frame, text="描述:", font=("Arial", 10)).grid(row=5, column=0, sticky=NW, pady=5)
            self.description_text = tk.Text(main_frame, width=30, height=4)
            self.description_text.grid(row=5, column=1, columnspan=2, sticky=EW, pady=5)
            
            # 按钮
            button_frame = ttk.Frame(main_frame)
            button_frame.grid(row=6, column=0, columnspan=3, pady=20)
            
            ttk.Button(button_frame, text="保存", command=self.save_reminder).pack(side=LEFT, padx=5)
            ttk.Button(button_frame, text="取消", command=self.cancel).pack(side=LEFT, padx=5)
            
            if self.reminder:  # 编辑模式显示删除按钮
                ttk.Button(button_frame, text="删除", command=self.delete_reminder,
                          bootstyle="danger").pack(side=LEFT, padx=5)
            
            # 配置网格权重
            main_frame.grid_columnconfigure(1, weight=1)
        except Exception as e:
            print(f"编辑窗口渲染错误: {e}")
            # 后备布局，保证至少可编辑与保存
            f = ttk.Frame(self.dialog, padding=20)
            f.pack(fill=BOTH, expand=True)
            self.title_entry = ttk.Entry(f)
            self.title_entry.pack(fill=X)
            self.date_entry = ttk.Entry(f)
            self.date_entry.insert(0, self.selected_date)
            self.date_entry.pack(fill=X, pady=6)
            self.hour_var = tk.StringVar(value="09"); self.minute_var = tk.StringVar(value="00")
            ttk.Entry(f, textvariable=self.hour_var, width=4).pack(side=LEFT)
            ttk.Entry(f, textvariable=self.minute_var, width=4).pack(side=LEFT, padx=6)
            ttk.Button(f, text="保存", command=self.save_reminder).pack(side=LEFT, padx=10)
            ttk.Button(f, text="取消", command=self.cancel).pack(side=LEFT)
    
    def load_reminder_data(self):
        """加载提醒数据到界面"""
        if not self.reminder:
            return
            
        self.title_entry.insert(0, self.reminder.title)
        self.date_entry.delete(0, tk.END)
        self.date_entry.insert(0, self.reminder.date)
        
        time_parts = self.reminder.time.split(":")
        self.hour_var.set(time_parts[0])
        self.minute_var.set(time_parts[1])
        
        self.selected_color = self.reminder.color
        self.color_preview.config(bg=self.selected_color)
        
        repeat_map = {"none": "不重复", "daily": "每天", "weekly": "每周", "monthly": "每月", "yearly": "每年"}
        self.repeat_var.set(repeat_map.get(self.reminder.repeat_type, "不重复"))
        
        self.description_text.insert("1.0", self.reminder.description)
    
    def choose_color(self):
        """选择颜色"""
        try:
            color = colorchooser.askcolor(initialcolor=self.selected_color)[1]
            if color:
                self.selected_color = color
                if hasattr(self, 'color_preview') and self.color_preview.winfo_exists():
                    self.color_preview.config(bg=color)
        except Exception as e:
            print(f"颜色选择错误: {e}")
    
    def save_reminder(self):
        """保存提醒"""
        title = self.title_entry.get().strip()
        if not title:
            messagebox.showerror("错误", "请输入标题")
            return
        
        date_str = self.date_entry.get().strip()
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("错误", "日期格式错误，请使用 YYYY-MM-DD 格式")
            return
        
        # 规范化时间，避免空值/非法值
        hour = self.hour_var.get() or "00"
        minute = self.minute_var.get() or "00"
        try:
            h = max(0, min(23, int(hour)))
            m = max(0, min(59, int(minute)))
        except ValueError:
            h, m = 0, 0
        time_str = f"{h:02d}:{m:02d}"
        
        repeat_map = {"不重复": "none", "每天": "daily", "每周": "weekly", "每月": "monthly", "每年": "yearly"}
        # 支持两种取值（中文/英文），双向映射
        raw_repeat = self.repeat_var.get()
        if raw_repeat in repeat_map:
            repeat_type = repeat_map[raw_repeat]
        else:
            reverse_map = {v: k for k, v in repeat_map.items()}
            repeat_type = raw_repeat if raw_repeat in reverse_map else "none"
        
        description = self.description_text.get("1.0", tk.END).strip()
        
        if self.reminder:
            # 更新现有提醒
            self.reminder.title = title
            self.reminder.date = date_str
            self.reminder.time = time_str
            self.reminder.color = self.selected_color
            self.reminder.repeat_type = repeat_type
            self.reminder.description = description
            self.reminder_manager.update_reminder(self.reminder)
            self.result = "updated"
        else:
            # 创建新提醒
            # 生成稳定唯一ID，避免同一分钟内重复ID冲突
            unique_suffix = f"{int(time.time()*1000)}_{os.getpid()}"
            reminder_id = f"{date_str}_{time_str}_{unique_suffix}"
            new_reminder = ReminderData(
                id=reminder_id,
                title=title,
                date=date_str,
                time=time_str,
                color=self.selected_color,
                repeat_type=repeat_type,
                description=description
            )
            self.reminder_manager.add_reminder(new_reminder)
            self.result = "added"
        
        self.dialog.destroy()
    
    def delete_reminder(self):
        """删除提醒"""
        if self.reminder and messagebox.askyesno("确认", "确定要删除这个提醒吗？"):
            self.reminder_manager.delete_reminder(self.reminder.id)
            self.result = "deleted"
            self.dialog.destroy()
    
    def cancel(self):
        """取消"""
        self.result = "cancelled"
        self.dialog.destroy()

class CalendarReminderWindow:
    """日历提醒主窗口"""
    
    def __init__(self, parent, reminder_manager: CalendarReminderManager):
        self.parent = parent
        self.reminder_manager = reminder_manager
        
        self.window = tk.Toplevel(parent)
        self.window.title("日历提醒")
        self.window.geometry("900x700")  # 增加窗口尺寸
        self.window.transient(parent)
        
        # 居中显示
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() - self.window.winfo_reqwidth()) // 2
        y = (self.window.winfo_screenheight() - self.window.winfo_reqheight()) // 2
        self.window.geometry(f"+{x}+{y}")
        
        self.setup_ui()
    
    def setup_ui(self):
        """设置主界面"""
        # 主框架
        main_frame = ttk.Frame(self.window, padding=10)
        main_frame.pack(fill=BOTH, expand=True)
        
        # 左侧日历
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 10))
        
        ttk.Label(left_frame, text="日历", font=("Arial", 14, "bold")).pack(pady=(0, 10))
        
        self.calendar_widget = CalendarWidget(left_frame, self.reminder_manager)
        self.calendar_widget.pack(fill=BOTH, expand=True)
        self.calendar_widget.date_click_callback = self.on_date_selected
        
        # 右侧提醒列表
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=RIGHT, fill=BOTH, expand=True)
        
        # 提醒列表标题和按钮
        list_header = ttk.Frame(right_frame)
        list_header.pack(fill=X, pady=(0, 10))
        
        self.reminders_title = ttk.Label(list_header, text="今日提醒", font=("Arial", 14, "bold"))
        self.reminders_title.pack(side=LEFT)
        
        ttk.Button(list_header, text="添加提醒", command=self.add_reminder).pack(side=RIGHT)
        
        # 提醒列表
        list_frame = ttk.Frame(right_frame)
        list_frame.pack(fill=BOTH, expand=True)
        
        # 改为Canvas + Frame，支持每条提醒右侧放操作按钮
        self.canvas = tk.Canvas(list_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.items_container = ttk.Frame(self.canvas)
        self.container_window = self.canvas.create_window((0, 0), window=self.items_container, anchor="nw")

        def _on_configure(event):
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            # 宽度自适应
            self.canvas.itemconfigure(self.container_window, width=self.canvas.winfo_width())
        self.items_container.bind("<Configure>", _on_configure)

        self.canvas.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)
        
        # 不绑定全局双击，改为行级绑定，避免多次触发
        
        # 存储提醒数据以便编辑
        self.current_reminders = []
        
        # 初始化显示今日提醒
        self.selected_date = datetime.now().strftime("%Y-%m-%d")
        self.update_reminders_list()
    
    def _lighten_color(self, hex_color, factor=0.7):
        """将颜色变浅，factor越大颜色越浅"""
        try:
            # 移除#号
            hex_color = hex_color.lstrip('#')
            # 转换为RGB
            r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            
            # 向白色(255,255,255)混合
            r = int(r + (255 - r) * factor)
            g = int(g + (255 - g) * factor)
            b = int(b + (255 - b) * factor)
            
            # 确保值在0-255范围内
            r = max(0, min(255, r))
            g = max(0, min(255, g))
            b = max(0, min(255, b))
            
            return f"#{r:02x}{g:02x}{b:02x}"
        except Exception:
            return "#F0F0F0"  # 默认浅灰色
    
    def on_date_selected(self, date_str):
        """日期选择事件"""
        self.selected_date = date_str
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        self.reminders_title.config(text=f"{date_obj.month}月{date_obj.day}日 提醒")
        self.update_reminders_list()
    
    def update_reminders_list(self):
        """更新提醒列表"""
        # 控件存在性检查，避免窗口已销毁导致异常
        if not hasattr(self, 'canvas') or not self.canvas.winfo_exists() or not hasattr(self, 'items_container'):
            return
        # 清空容器
        for child in list(self.items_container.winfo_children()):
            child.destroy()
        
        reminders = self.reminder_manager.get_reminders_by_date(self.selected_date)
        self.current_reminders = reminders
        
        if not reminders:
            empty_row = tk.Frame(self.items_container, bg="#F5F5F5")
            empty_row.pack(fill=X, padx=6, pady=8)
            tk.Label(empty_row, text="暂无提醒", bg="#F5F5F5", fg="#888", font=("Arial", 10)).pack(anchor=W, padx=12, pady=6)
        
        for i, reminder in enumerate(reminders):
            repeat_text = ""
            if reminder.repeat_type != "none":
                repeat_map = {"daily": "[每天]", "weekly": "[每周]", "monthly": "[每月]", "yearly": "[每年]"}
                repeat_text = repeat_map.get(reminder.repeat_type, "")
            
            # 行容器 - 确保背景色正确显示
            bgc = self._lighten_color(reminder.color, 0.85)
            print(f"提醒 {reminder.title} 原色: {reminder.color}, 背景色: {bgc}")  # 调试输出
            
            # 创建带背景色的行容器
            row = tk.Frame(self.items_container, bg=bgc, relief="solid", bd=1)
            row.pack(fill=X, padx=4, pady=3)

            # 左侧彩色标识与文本
            left = tk.Frame(row, bg=bgc)
            left.pack(side=LEFT, fill=X, expand=True, padx=(8, 0), pady=6)

            dot = tk.Label(left, text="●", fg=reminder.color, bg=bgc, font=("Arial", 12, "bold"))
            dot.pack(side=LEFT, padx=(0, 6))

            text = tk.Label(left, text=f"{reminder.time}  {reminder.title}  {repeat_text}",
                            bg=bgc, fg="#222", font=("Arial", 10))
            text.pack(side=LEFT)

            # 右侧操作按钮
            right = tk.Frame(row, bg=bgc)
            right.pack(side=RIGHT, padx=8)
            
            # 设置子组件的背景色
            left.configure(bg=bgc)
            right.configure(bg=bgc)
            dot.configure(bg=bgc)
            text.configure(bg=bgc)

            # 为整行添加双击编辑功能
            def make_edit_handler(index):
                def handler(event=None):  # event参数可选，兼容双击和按钮点击
                    self.edit_reminder_by_index(index)
                return handler
            
            def make_delete_handler(index):
                def handler():
                    self.delete_reminder_by_index(index)
                return handler

            # 绑定整行双击事件
            row.bind("<Double-Button-1>", make_edit_handler(i))
            left.bind("<Double-Button-1>", make_edit_handler(i))
            text.bind("<Double-Button-1>", make_edit_handler(i))

            # 按钮
            ttk.Button(right, text="编辑", width=6, command=make_edit_handler(i)).pack(side=LEFT, padx=(0, 6))
            ttk.Button(right, text="删除", width=6, command=make_delete_handler(i), bootstyle="danger-outline").pack(side=LEFT)
        
        # 更新滚动区域与日历显示
        self.items_container.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self.calendar_widget.update_calendar()
    
    def add_reminder(self):
        """添加提醒"""
        dialog = ReminderEditDialog(self.window, self.reminder_manager, self.selected_date)
        self.window.wait_window(dialog.dialog)
        
        if dialog.result in ["added", "updated"]:
            self.update_reminders_list()
    
    def edit_reminder_by_index(self, index):
        """根据索引编辑提醒"""
        # 防止重复调用
        if hasattr(self, '_editing') and self._editing:
            return
            
        try:
            self._editing = True
            if 0 <= index < len(self.current_reminders):
                reminder = self.current_reminders[index]
                dialog = ReminderEditDialog(self.window, self.reminder_manager, 
                                          self.selected_date, reminder)
                self.window.wait_window(dialog.dialog)
                
                if hasattr(dialog, 'result') and dialog.result in ["updated", "deleted"]:
                    self.update_reminders_list()
        finally:
            self._editing = False
    
    def edit_selected_reminder(self, event=None):
        """编辑选中的提醒（保持兼容性）"""
        # 如果有提醒，编辑第一个
        if self.current_reminders:
            self.edit_reminder_by_index(0)

    def delete_reminder_by_index(self, index):
        """删除指定索引的提醒并刷新"""
        if 0 <= index < len(self.current_reminders):
            reminder = self.current_reminders[index]
            try:
                self.reminder_manager.delete_reminder(reminder.id)
                self.update_reminders_list()
            except Exception as e:
                print(f"删除提醒失败: {e}")
