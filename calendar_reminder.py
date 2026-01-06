import tkinter as tk
from tkinter import messagebox, colorchooser
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledFrame
from datetime import datetime, timedelta, date
import json
import os
import threading
import time
import uuid
import queue
from typing import Callable, Dict, List, Optional
import calendar as cal

def _append_calendar_debug(app_data_dir: str, message: str):
    try:
        if not app_data_dir:
            return
        path = os.path.join(app_data_dir, "calendar_debug.log")
        with open(path, "a", encoding="utf-8") as f:
            f.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " " + str(message) + "\n")
    except Exception:
        pass

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
        self.repeat_type = repeat_type  # none, daily, weekly, monthly, yearly
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
        d = dict(data or {})
        reminder_id = str(d.get("id") or "").strip() or str(uuid.uuid4())
        title = str(d.get("title") or "")
        date_str = str(d.get("date") or "").strip() or date.today().strftime("%Y-%m-%d")
        time_str = str(d.get("time") or "").strip() or "09:00"
        color = str(d.get("color") or "").strip() or "#FF6B6B"
        description = str(d.get("description") or "")
        repeat_type = str(d.get("repeat_type") or "none").strip() or "none"
        is_active = bool(d.get("is_active", True))

        return cls(
            id=reminder_id,
            title=title,
            date=date_str,
            time=time_str,
            color=color,
            description=description,
            repeat_type=repeat_type,
            is_active=is_active,
        )

class CalendarReminderManager:
    """日历提醒管理器"""
    
    def __init__(self, app_data_dir: str, tk_root: Optional[tk.Misc] = None):
        self.app_data_dir = app_data_dir
        self.tk_root = tk_root
        self.reminders_file = os.path.join(app_data_dir, "reminders.json")
        self.reminders: Dict[str, ReminderData] = {}
        self.notification_callback = None
        self.check_timer = None
        self._lock = threading.RLock()
        self._checker_thread_started = False
        self._ui_event_queue: "queue.Queue[ReminderData]" = queue.Queue()
        self._ui_poller_timer = None
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
                loaded: Dict[str, ReminderData] = {}
                for reminder_data in (data or []):
                    reminder = ReminderData.from_dict(reminder_data)
                    loaded[reminder.id] = reminder
                with self._lock:
                    self.reminders = loaded
            except Exception as e:
                print(f"加载提醒数据失败: {e}")
    
    def save_reminders(self):
        """保存提醒数据到文件"""
        try:
            with self._lock:
                snapshot = list(self.reminders.values())
            data = [reminder.to_dict() for reminder in snapshot]
            with open(self.reminders_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存提醒数据失败: {e}")
    
    def add_reminder(self, reminder: ReminderData) -> str:
        """添加提醒事项"""
        with self._lock:
            self.reminders[reminder.id] = reminder
        self.save_reminders()
        return reminder.id
    
    def update_reminder(self, reminder: ReminderData):
        """更新提醒事项"""
        updated = False
        with self._lock:
            if reminder.id in self.reminders:
                self.reminders[reminder.id] = reminder
                updated = True
        if updated:
            self.save_reminders()
    
    def delete_reminder(self, reminder_id: str):
        """删除提醒事项"""
        deleted = False
        with self._lock:
            if reminder_id in self.reminders:
                del self.reminders[reminder_id]
                deleted = True
        if deleted:
            self.save_reminders()
    
    def get_reminders_by_date(self, target_date: str) -> List[ReminderData]:
        """获取指定日期的提醒事项"""
        with self._lock:
            values = list(self.reminders.values())

        reminders = []
        for reminder in values:
            if not reminder.is_active:
                continue
                
            if reminder.date == target_date:
                reminders.append(reminder)
            elif reminder.repeat_type != "none":
                # 处理重复提醒
                if self._should_repeat_on_date(reminder, target_date):
                    reminders.append(reminder)
        
        return sorted(reminders, key=lambda x: str(getattr(x, "time", "") or ""))

    def get_reminders_for_dates(self, date_strings: List[str]) -> Dict[str, List[ReminderData]]:
        date_map: Dict[str, List[ReminderData]] = {ds: [] for ds in date_strings if ds}
        if not date_map:
            return {}

        date_objs: Dict[str, date] = {}
        for ds in list(date_map.keys()):
            try:
                date_objs[ds] = datetime.strptime(ds, "%Y-%m-%d").date()
            except Exception:
                date_map.pop(ds, None)
        if not date_map:
            return {}

        sorted_dates = sorted(date_objs.items(), key=lambda kv: kv[1])

        with self._lock:
            values = list(self.reminders.values())

        for reminder in values:
            if not getattr(reminder, "is_active", True):
                continue

            r_date_str = str(getattr(reminder, "date", "") or "").strip()
            try:
                r_date = datetime.strptime(r_date_str, "%Y-%m-%d").date()
            except Exception:
                continue

            repeat_type = str(getattr(reminder, "repeat_type", "none") or "none").strip()
            if repeat_type == "none":
                if r_date_str in date_map:
                    date_map[r_date_str].append(reminder)
                continue

            if repeat_type == "daily":
                for ds, d_obj in sorted_dates:
                    if d_obj >= r_date:
                        date_map[ds].append(reminder)
                continue

            if repeat_type == "weekly":
                for ds, d_obj in sorted_dates:
                    if d_obj >= r_date:
                        if (d_obj - r_date).days % 7 == 0:
                            date_map[ds].append(reminder)
                continue

            if repeat_type == "monthly":
                day_num = r_date.day
                for ds, d_obj in sorted_dates:
                    if d_obj > r_date and d_obj.day == day_num:
                        date_map[ds].append(reminder)
                continue

            if repeat_type == "yearly":
                m = r_date.month
                day_num = r_date.day
                for ds, d_obj in sorted_dates:
                    if d_obj > r_date and d_obj.month == m and d_obj.day == day_num:
                        date_map[ds].append(reminder)
                continue

        for ds in list(date_map.keys()):
            date_map[ds].sort(key=lambda x: str(getattr(x, "time", "") or ""))
        return date_map
    
    def _should_repeat_on_date(self, reminder: ReminderData, target_date: str) -> bool:
        """判断重复提醒是否应在指定日期触发"""
        try:
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
        except ValueError:
            return False
        
        return False
    
    def set_notification_callback(self, callback):
        """设置通知回调函数"""
        self.notification_callback = callback
        self.start_reminder_checker()
        self._ensure_ui_poller()

    def set_tk_root(self, tk_root: Optional[tk.Misc]):
        self.tk_root = tk_root
        self.start_reminder_checker()
        self._ensure_ui_poller()

    def debug_log(self, message: str):
        _append_calendar_debug(self.app_data_dir, message)

    def _ensure_ui_poller(self):
        tk_root = self.tk_root
        if not tk_root or not getattr(tk_root, "winfo_exists", lambda: False)():
            return
        try:
            if self._ui_poller_timer:
                tk_root.after_cancel(self._ui_poller_timer)
        except Exception:
            pass

        def drain_once():
            try:
                while True:
                    reminder = self._ui_event_queue.get_nowait()
                    if self.notification_callback:
                        try:
                            self.notification_callback(reminder, self)
                        except Exception:
                            pass
            except Exception:
                pass
            finally:
                try:
                    self._ui_poller_timer = tk_root.after(200, drain_once)
                except Exception:
                    self._ui_poller_timer = None

        try:
            self._ui_poller_timer = tk_root.after(200, drain_once)
        except Exception:
            self._ui_poller_timer = None
    
    def start_reminder_checker(self):
        """启动提醒检查器"""
        if self._checker_thread_started:
            return
        self._checker_thread_started = True

        def check_reminders():
            while True:
                try:
                    now = datetime.now()
                    current_date = now.strftime("%Y-%m-%d")
                    current_time = now.strftime("%H:%M")
                    minute_key = now.strftime("%Y-%m-%d %H:%M")

                    if minute_key != self._last_trigger_minute:
                        self._last_trigger_minute = minute_key
                        self._fired_ids_in_minute.clear()

                    reminders = self.get_reminders_by_date(current_date)
                    for reminder in reminders:
                        if reminder.time == current_time and reminder.id not in self._fired_ids_in_minute:
                            if self.notification_callback:
                                try:
                                    self._ui_event_queue.put_nowait(reminder)
                                except Exception:
                                    pass
                            self._fired_ids_in_minute.add(reminder.id)

                    time.sleep(1)
                except Exception:
                    time.sleep(1)

        t = threading.Thread(target=check_reminders, daemon=True)
        t.start()

class CalendarWidget(ttk.Frame):
    """日历组件"""
    
    def __init__(self, parent, reminder_manager: CalendarReminderManager, **kwargs):
        super().__init__(parent, **kwargs)
        self.reminder_manager = reminder_manager
        try:
            if getattr(self.reminder_manager, "tk_root", None) is None:
                self.reminder_manager.set_tk_root(parent.winfo_toplevel())
        except Exception:
            pass
        self.current_date = datetime.now().date()
        self.selected_date = None
        self.day_buttons = {}
        self._reminder_style_cache = {}
        self._active_reminder_dialog = None
        self._render_token = None
        self.setup_ui()

    def _hex_to_rgb(self, color: str):
        c = (color or "").strip()
        if c.startswith("#"):
            c = c[1:]
        if len(c) != 6:
            return 255, 255, 255
        try:
            return int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)
        except Exception:
            return 255, 255, 255

    def _safe_hex_color(self, color: str, default: str = "#FF6B6B") -> str:
        c = str(color or "").strip()
        if not c:
            return default
        if not c.startswith("#"):
            c = "#" + c
        if len(c) != 7:
            return default
        try:
            int(c[1:], 16)
        except Exception:
            return default
        return c.upper()

    def _rgb_to_hex(self, r: int, g: int, b: int) -> str:
        r = max(0, min(255, int(r)))
        g = max(0, min(255, int(g)))
        b = max(0, min(255, int(b)))
        return f"#{r:02X}{g:02X}{b:02X}"

    def _blend(self, a: str, b: str, t: float) -> str:
        t = 0.0 if t is None else float(t)
        t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
        ar, ag, ab = self._hex_to_rgb(a)
        br, bg, bb = self._hex_to_rgb(b)
        r = ar + (br - ar) * t
        g = ag + (bg - ag) * t
        b2 = ab + (bb - ab) * t
        return self._rgb_to_hex(r, g, b2)

    def _is_dark(self, color: str) -> bool:
        r, g, b = self._hex_to_rgb(color)
        brightness = r * 0.299 + g * 0.587 + b * 0.114
        return brightness < 140

    def _get_theme_bg(self) -> str:
        try:
            style = ttk.Style()
            return getattr(style.colors, "bg", None) or "#FFFFFF"
        except Exception:
            return "#FFFFFF"

    def _get_theme_fg(self) -> str:
        try:
            style = ttk.Style()
            return getattr(style.colors, "fg", None) or "#000000"
        except Exception:
            return "#000000"

    def _reminder_tint(self, color: str) -> str:
        base_bg = self._get_theme_bg()
        if self._is_dark(base_bg):
            return self._blend(color, base_bg, 0.75)
        return self._blend(color, "#FFFFFF", 0.82)

    def setup_ui(self):
        """设置日历界面"""
        # 主布局：左侧日历，右侧提醒列表
        self.paned_window = ttk.PanedWindow(self, orient=HORIZONTAL)
        self.paned_window.pack(fill=BOTH, expand=YES)
        
        # 左侧日历区域
        self.left_frame = ttk.Frame(self.paned_window, padding=10)
        self.paned_window.add(self.left_frame, weight=3)
        
        # 右侧提醒列表区域
        self.right_frame = ttk.Frame(self.paned_window, padding=10)
        self.paned_window.add(self.right_frame, weight=2)
        
        self._setup_calendar_area()
        self._setup_reminder_list_area()
        
    def _setup_calendar_area(self):
        """设置日历区域"""
        # 导航栏
        nav_frame = ttk.Frame(self.left_frame)
        nav_frame.pack(fill=X, pady=(0, 10))
        
        # 上一月
        ttk.Button(
            nav_frame, 
            text="◀", 
            command=self.prev_month,
            bootstyle="link",
            width=4
        ).pack(side=LEFT)
        
        # 年月选择
        center_nav = ttk.Frame(nav_frame)
        center_nav.pack(side=LEFT, expand=YES)
        
        self.year_var = tk.StringVar()
        self.year_combo = ttk.Combobox(center_nav, textvariable=self.year_var, width=6, state="readonly", font=("Microsoft YaHei", 10))
        self.year_combo.pack(side=LEFT, padx=5)
        self.year_combo.bind("<<ComboboxSelected>>", self.on_year_changed)
        
        self.month_var = tk.StringVar()
        self.month_combo = ttk.Combobox(center_nav, textvariable=self.month_var, width=5, state="readonly", font=("Microsoft YaHei", 10))
        self.month_combo.pack(side=LEFT, padx=5)
        self.month_combo.bind("<<ComboboxSelected>>", self.on_month_changed)
        
        # 下一月
        ttk.Button(
            nav_frame, 
            text="▶", 
            command=self.next_month,
            bootstyle="link",
            width=4
        ).pack(side=RIGHT)
        
        # 星期标题
        self.week_frame = ttk.Frame(self.left_frame)
        self.week_frame.pack(fill=X, pady=5)
        
        weekdays = ['一', '二', '三', '四', '五', '六', '日']
        for i, day in enumerate(weekdays):
            label = ttk.Label(self.week_frame, text=day, font=("Microsoft YaHei", 10, "bold"), anchor=CENTER)
            label.grid(row=0, column=i, sticky="ew", padx=1)
            self.week_frame.grid_columnconfigure(i, weight=1)
            
        # 日期网格
        self.calendar_grid = ttk.Frame(self.left_frame)
        self.calendar_grid.pack(fill=BOTH, expand=YES)
        try:
            style = ttk.Style()
            bg = getattr(style.colors, "bg", None) or "#FFFFFF"
            fg = getattr(style.colors, "fg", None) or "#000000"

            frame_style = "CalendarGrid.TFrame"
            label_style = "CalendarWeek.TLabel"
            style.configure(frame_style, background=bg)
            style.configure(label_style, background=bg, foreground=fg)

            self.left_frame.configure(style=frame_style)
            self.week_frame.configure(style=frame_style)
            self.calendar_grid.configure(style=frame_style)
            for w in self.week_frame.winfo_children():
                if isinstance(w, ttk.Label):
                    w.configure(style=label_style)
        except Exception:
            pass
        
        for i in range(7):
            self.calendar_grid.grid_columnconfigure(i, weight=1)
        for i in range(6):
            self.calendar_grid.grid_rowconfigure(i, weight=1)
            
        self.update_calendar()
        
    def _setup_reminder_list_area(self):
        """设置右侧提醒列表区域"""
        # 标题
        header = ttk.Frame(self.right_frame)
        header.pack(fill=X, pady=(0, 10))
        
        self.list_title = ttk.Label(
            header, 
            text="今日提醒", 
            font=("Microsoft YaHei", 12, "bold"),
            bootstyle="primary"
        )
        self.list_title.pack(side=LEFT)
        
        ttk.Button(
            header,
            text="+ 添加",
            command=self.add_new_reminder,
            bootstyle="success-outline",
            width=8
        ).pack(side=RIGHT)
        
        # 滚动列表
        self.list_container = ScrolledFrame(self.right_frame, autohide=True)
        self.list_container.pack(fill=BOTH, expand=YES)
        
        self.update_reminder_list(date.today().strftime("%Y-%m-%d"))

    def update_calendar(self):
        """更新日历显示"""
        # 清除现有按钮
        for widget in self.calendar_grid.winfo_children():
            widget.destroy()
        self.day_buttons.clear()
        
        # 更新下拉框
        self.setup_dropdowns()
        
        # 获取月历数据
        calendar_data = cal.monthcalendar(self.current_date.year, self.current_date.month)
        
        today = date.today()
        theme_bg = self._get_theme_bg()
        theme_fg = self._get_theme_fg()
        hover_bg = self._blend(theme_bg, theme_fg, 0.06) if theme_bg and theme_fg else theme_bg
        
        date_strs_in_month: List[str] = []
        for week in calendar_data:
            for day in week:
                if day == 0:
                    continue
                date_strs_in_month.append(date(self.current_date.year, self.current_date.month, day).strftime("%Y-%m-%d"))

        reminders_map = {}
        try:
            reminders_map = self.reminder_manager.get_reminders_for_dates(date_strs_in_month)
        except Exception:
            reminders_map = {}

        for week_num, week in enumerate(calendar_data):
            for day_num, day in enumerate(week):
                if day == 0:
                    continue

                date_obj = date(self.current_date.year, self.current_date.month, day)
                date_str = date_obj.strftime("%Y-%m-%d")

                has_reminders = bool(reminders_map.get(date_str))
                is_today = (date_obj == today)
                
                # 样式逻辑
                text = f"{day} ●" if has_reminders else str(day)

                if has_reminders:
                    bg = "#FF7F24"
                    fg = "white"
                    active_bg = "#E06C1F"
                    active_fg = "white"
                    font = ("Microsoft YaHei", 14, "bold")
                else:
                    bg = theme_bg
                    fg = theme_fg
                    active_bg = hover_bg
                    active_fg = theme_fg
                    font = ("Microsoft YaHei", 14)

                btn = tk.Button(
                    self.calendar_grid,
                    text=text,
                    command=lambda d=date_str: self.on_date_click(d),
                    width=4,
                    bg=bg,
                    fg=fg,
                    activebackground=active_bg,
                    activeforeground=active_fg,
                    relief="flat",
                    bd=0,
                    highlightthickness=1,
                    highlightbackground=self._blend(bg, fg, 0.12),
                    font=font,
                    cursor="hand2",
                )
                setattr(btn, "_fixed_color", True)
                btn.grid(row=week_num, column=day_num, sticky="nsew", padx=2, pady=2)
                
                self.day_buttons[date_str] = btn
                
    def setup_dropdowns(self):
        """设置下拉框选项"""
        current_year = self.current_date.year
        years = [str(year) for year in range(current_year - 50, current_year + 51)]
        self.year_combo['values'] = years
        self.year_var.set(str(current_year))
        
        month_names = ['一月', '二月', '三月', '四月', '五月', '六月',
                      '七月', '八月', '九月', '十月', '十一月', '十二月']
        self.month_combo['values'] = month_names
        self.month_var.set(month_names[self.current_date.month - 1])

    def on_year_changed(self, event=None):
        try:
            new_year = int(self.year_var.get())
            self.current_date = self.current_date.replace(year=new_year)
            self.update_calendar()
        except ValueError:
            pass

    def on_month_changed(self, event=None):
        try:
            month_names = ['一月', '二月', '三月', '四月', '五月', '六月',
                          '七月', '八月', '九月', '十月', '十一月', '十二月']
            new_month = month_names.index(self.month_var.get()) + 1
            self.current_date = self.current_date.replace(month=new_month)
            self.update_calendar()
        except ValueError:
            pass

    def prev_month(self):
        if self.current_date.month == 1:
            self.current_date = self.current_date.replace(year=self.current_date.year - 1, month=12)
        else:
            self.current_date = self.current_date.replace(month=self.current_date.month - 1)
        self.update_calendar()

    def next_month(self):
        if self.current_date.month == 12:
            self.current_date = self.current_date.replace(year=self.current_date.year + 1, month=1)
        else:
            self.current_date = self.current_date.replace(month=self.current_date.month + 1)
        self.update_calendar()

    def on_date_click(self, date_str):
        self.selected_date = date_str
        self.update_reminder_list(date_str)
        
    def update_reminder_list(self, date_str):
        """更新右侧提醒列表"""
        self.selected_date = date_str
        self._render_token = str(uuid.uuid4())
        token = self._render_token
        
        # 更新标题
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            display_date = f"{date_obj.month}月{date_obj.day}日"
            if date_str == date.today().strftime("%Y-%m-%d"):
                display_date += " (今天)"
            self.list_title.config(text=f"{display_date} 提醒")
        except:
            self.list_title.config(text=f"{date_str} 提醒")
            
        # 清除旧列表
        for widget in self.list_container.winfo_children():
            widget.destroy()
            
        reminders = self.reminder_manager.get_reminders_by_date(date_str)
        
        if not reminders:
            ttk.Label(
                self.list_container, 
                text="暂无提醒事项", 
                font=("Microsoft YaHei", 10),
                bootstyle="secondary"
            ).pack(pady=20)
            return

        batch_size = 40

        def render_batch(start_index: int):
            if token != self._render_token:
                return
            end_index = min(len(reminders), start_index + batch_size)
            for reminder in reminders[start_index:end_index]:
                try:
                    self._create_reminder_card(reminder)
                except Exception:
                    pass
            if end_index < len(reminders):
                try:
                    self.after(1, lambda: render_batch(end_index))
                except Exception:
                    render_batch(end_index)

        render_batch(0)
            
    def _create_reminder_card(self, reminder: ReminderData):
        """创建单个提醒卡片"""
        safe_color = self._safe_hex_color(getattr(reminder, "color", None))
        theme_name = None
        try:
            theme_name = ttk.Style().theme_use()
        except Exception:
            theme_name = None
        key = (theme_name, safe_color)
        cached = self._reminder_style_cache.get(key)
        if cached:
            frame_style, label_style, sub_label_style = cached
        else:
            tint = self._reminder_tint(safe_color)
            fg = "#FFFFFF" if self._is_dark(tint) else "#1F1F1F"
            sub_fg = self._blend(fg, tint, 0.35)
            base = (safe_color or "").strip().lstrip("#").upper() or "FF6B6B"
            theme_part = (theme_name or "theme").replace(" ", "_")
            frame_style = f"ReminderCard_{theme_part}_{base}.TFrame"
            label_style = f"ReminderCard_{theme_part}_{base}.TLabel"
            sub_label_style = f"ReminderCard_{theme_part}_{base}.Sub.TLabel"
            try:
                s = ttk.Style()
                s.configure(frame_style, background=tint)
                s.configure(label_style, background=tint, foreground=fg)
                s.configure(sub_label_style, background=tint, foreground=sub_fg)
            except Exception:
                pass
            self._reminder_style_cache[key] = (frame_style, label_style, sub_label_style)

        card = ttk.Frame(self.list_container, padding=10, style=frame_style)
        card.pack(fill=X, pady=5, padx=5)
        
        # 颜色条
        color_bar = tk.Frame(card, bg=safe_color, width=5)
        color_bar.pack(side=LEFT, fill=Y, padx=(0, 10))
        
        # 内容区域
        content = ttk.Frame(card, style=frame_style)
        content.pack(side=LEFT, fill=BOTH, expand=YES)
        
        header = ttk.Frame(content, style=frame_style)
        header.pack(fill=X)
        
        ttk.Label(
            header, 
            text=str(getattr(reminder, "time", "") or ""), 
            font=("Microsoft YaHei", 12, "bold"),
            style=label_style
        ).pack(side=LEFT)
        
        ttk.Label(
            header, 
            text=str(getattr(reminder, "title", "") or ""), 
            font=("Microsoft YaHei", 11, "bold"),
            style=label_style
        ).pack(side=LEFT, padx=10)
        
        desc = str(getattr(reminder, "description", "") or "")
        if desc:
            ttk.Label(
                content, 
                text=desc, 
                font=("Microsoft YaHei", 9),
                style=sub_label_style,
                wraplength=200
            ).pack(fill=X, pady=(5, 0))
            
        # 操作按钮
        actions = ttk.Frame(card, style=frame_style)
        actions.pack(side=RIGHT)
        
        ttk.Button(
            actions,
            text="✎",
            command=lambda r=reminder: self.edit_reminder(r),
            bootstyle="link-secondary",
            width=3
        ).pack(side=TOP)
        
        ttk.Button(
            actions,
            text="×",
            command=lambda r=reminder: self.delete_reminder(r),
            bootstyle="link-danger",
            width=3
        ).pack(side=BOTTOM)
        
    def add_new_reminder(self):
        """添加新提醒"""
        try:
            self.reminder_manager.debug_log("ui add_new_reminder clicked")
        except Exception:
            pass
        target_date = self.selected_date or date.today().strftime("%Y-%m-%d")

        def _open():
            try:
                self.reminder_manager.debug_log(f"ui add_new_reminder open date={target_date}")
            except Exception:
                pass
            try:
                if (
                    self._active_reminder_dialog
                    and getattr(self._active_reminder_dialog, "dialog", None) is not None
                    and getattr(self._active_reminder_dialog.dialog, "winfo_exists", lambda: 0)()
                ):
                    try:
                        try:
                            self._active_reminder_dialog.dialog.deiconify()
                        except Exception:
                            pass
                        self._active_reminder_dialog.dialog.lift()
                        try:
                            self._active_reminder_dialog.dialog.focus_set()
                        except Exception:
                            pass
                        try:
                            self.reminder_manager.debug_log("ui add_new_reminder reused existing dialog")
                        except Exception:
                            pass
                        return
                    except Exception:
                        pass
            except Exception:
                pass

            try:
                self._active_reminder_dialog = ReminderEditDialog(
                    self,
                    self.reminder_manager,
                    target_date,
                    on_saved=lambda *_: (self.update_calendar(), self.update_reminder_list(target_date)),
                    on_closed=lambda: setattr(self, "_active_reminder_dialog", None),
                )
                try:
                    self.reminder_manager.debug_log("ui add_new_reminder dialog created")
                except Exception:
                    pass
            except Exception as e:
                try:
                    self.reminder_manager.debug_log(f"ui add_new_reminder failed: {repr(e)}")
                except Exception:
                    pass
                try:
                    messagebox.showerror("错误", f"打开添加提醒窗口失败: {str(e)}", parent=self.winfo_toplevel())
                except Exception:
                    pass
                self._active_reminder_dialog = None

        try:
            self.winfo_toplevel().after(0, _open)
            return
        except Exception:
            pass
        try:
            self.after(0, _open)
            return
        except Exception:
            pass
        _open()
        
    def edit_reminder(self, reminder):
        """编辑提醒"""
        try:
            self.reminder_manager.debug_log(f"ui edit_reminder clicked id={getattr(reminder,'id',None)}")
        except Exception:
            pass
        def _open():
            try:
                self.reminder_manager.debug_log(f"ui edit_reminder open id={getattr(reminder,'id',None)}")
            except Exception:
                pass
            try:
                if (
                    self._active_reminder_dialog
                    and getattr(self._active_reminder_dialog, "dialog", None) is not None
                    and getattr(self._active_reminder_dialog.dialog, "winfo_exists", lambda: 0)()
                ):
                    try:
                        try:
                            self._active_reminder_dialog.dialog.deiconify()
                        except Exception:
                            pass
                        self._active_reminder_dialog.dialog.lift()
                        try:
                            self._active_reminder_dialog.dialog.focus_set()
                        except Exception:
                            pass
                        try:
                            self.reminder_manager.debug_log("ui edit_reminder reused existing dialog")
                        except Exception:
                            pass
                        return
                    except Exception:
                        pass
            except Exception:
                pass

            try:
                self._active_reminder_dialog = ReminderEditDialog(
                    self,
                    self.reminder_manager,
                    getattr(reminder, "date", self.selected_date or date.today().strftime("%Y-%m-%d")),
                    reminder,
                    on_saved=lambda *_: (
                        self.update_calendar(),
                        self.update_reminder_list(getattr(reminder, "date", self.selected_date or date.today().strftime("%Y-%m-%d"))),
                    ),
                    on_closed=lambda: setattr(self, "_active_reminder_dialog", None),
                )
                try:
                    self.reminder_manager.debug_log("ui edit_reminder dialog created")
                except Exception:
                    pass
            except Exception as e:
                try:
                    self.reminder_manager.debug_log(f"ui edit_reminder failed: {repr(e)}")
                except Exception:
                    pass
                try:
                    messagebox.showerror("错误", f"打开编辑提醒窗口失败: {str(e)}", parent=self.winfo_toplevel())
                except Exception:
                    pass
                self._active_reminder_dialog = None

        try:
            self.winfo_toplevel().after(0, _open)
            return
        except Exception:
            pass
        try:
            self.after(0, _open)
            return
        except Exception:
            pass
        _open()
        
    def delete_reminder(self, reminder):
        """删除提醒"""
        if messagebox.askyesno("确认", "确定要删除这条提醒吗？"):
            self.reminder_manager.delete_reminder(reminder.id)
            self.update_calendar()
            self.update_reminder_list(reminder.date)

class CalendarReminderWindow(ttk.Toplevel):
    """独立的日历提醒窗口"""
    def __init__(self, parent, reminder_manager: CalendarReminderManager):
        super().__init__(parent)
        self.window = self
        self.title("日历提醒")
        self.geometry("900x600")
        
        self.manager = reminder_manager
        if getattr(self.manager, "tk_root", None) is None:
            try:
                self.manager.set_tk_root(parent)
            except Exception:
                self.manager.tk_root = parent
        
        self.widget = CalendarWidget(self, self.manager)
        self.widget.pack(fill=BOTH, expand=YES)

class ReminderEditDialog:
    """提醒事项编辑对话框"""
    
    def __init__(self, parent, reminder_manager: CalendarReminderManager, 
                 selected_date: str, reminder: Optional[ReminderData] = None,
                 on_saved: Optional[Callable[[ReminderData], None]] = None,
                 on_closed: Optional[Callable[[], None]] = None):
        self.parent = parent
        self.reminder_manager = reminder_manager
        self.selected_date = selected_date
        self.reminder = reminder
        self.on_saved = on_saved
        self.on_closed = on_closed
        self.result = None
        self._closed = False
        self._date_picker = None
        try:
            self.reminder_manager.debug_log(f"dialog init start mode={'edit' if reminder else 'add'} date={selected_date}")
        except Exception:
            pass

        owner = parent
        try:
            owner = parent.winfo_toplevel()
        except Exception:
            owner = parent
        try:
            self.reminder_manager.debug_log("dialog init after owner resolved")
        except Exception:
            pass

        try:
            self.reminder_manager.debug_log("dialog init before toplevel")
        except Exception:
            pass
        self.dialog = tk.Toplevel(owner)
        try:
            self.reminder_manager.debug_log("dialog init after toplevel")
        except Exception:
            pass
        self.dialog.title("编辑提醒" if reminder else "添加提醒")
        try:
            self.dialog.resizable(True, True)
        except Exception:
            pass
        try:
            setattr(self.dialog, "_keepalive", self)
        except Exception:
            pass

        try:
            self.reminder_manager.debug_log("dialog init before setup_ui")
        except Exception:
            pass
        self.setup_ui()
        try:
            self.reminder_manager.debug_log("dialog init after setup_ui")
        except Exception:
            pass
        if reminder:
            try:
                self.reminder_manager.debug_log("dialog init before load_reminder_data")
            except Exception:
                pass
            self.load_reminder_data()
            try:
                self.reminder_manager.debug_log("dialog init after load_reminder_data")
            except Exception:
                pass

        width = 560
        height = 560
        try:
            try:
                self.reminder_manager.debug_log("dialog init before geometry")
            except Exception:
                pass

            try:
                screen_width = int(self.dialog.winfo_screenwidth() or 0)
                screen_height = int(self.dialog.winfo_screenheight() or 0)
            except Exception:
                screen_width = 0
                screen_height = 0

            if screen_width > 0 and screen_height > 0:
                x = max(0, (screen_width - width) // 2)
                y = max(0, (screen_height - height) // 2)
                self.dialog.geometry(f"{width}x{height}+{x}+{y}")
            else:
                self.dialog.geometry(f"{width}x{height}")

            try:
                self.reminder_manager.debug_log("dialog init after geometry")
            except Exception:
                pass
        except Exception:
            pass

        try:
            self.dialog.minsize(520, 520)
        except Exception:
            pass

        try:
            if getattr(owner, "winfo_viewable", lambda: 1)():
                self.dialog.transient(owner)
                try:
                    self.reminder_manager.debug_log("dialog init after transient")
                except Exception:
                    pass
        except Exception:
            pass

        def _activate_dialog():
            try:
                self.dialog.lift()
                self.dialog.focus_set()
            except Exception:
                pass

        try:
            self.dialog.after(0, _activate_dialog)
        except Exception:
            _activate_dialog()

        self.dialog.protocol("WM_DELETE_WINDOW", self._on_cancel)
        try:
            self.reminder_manager.debug_log("dialog init after protocol")
        except Exception:
            pass
        try:
            self.dialog.bind("<Destroy>", lambda _e: self._finalize_close(), add="+")
        except Exception:
            pass
        try:
            self.dialog.bind("<Escape>", lambda _e: self._on_cancel(), add="+")
        except Exception:
            pass
        try:
            self.dialog.bind("<Return>", lambda _e: self.save(), add="+")
        except Exception:
            pass
        try:
            self.reminder_manager.debug_log("dialog init after binds")
        except Exception:
            pass

        try:
            try:
                self.reminder_manager.debug_log("dialog init before show")
            except Exception:
                pass
            try:
                self.dialog.state("normal")
            except Exception:
                pass
            self.dialog.deiconify()
            self.dialog.lift()
            try:
                self.dialog.focus_set()
            except Exception:
                pass
            try:
                self.reminder_manager.debug_log("dialog init after show")
            except Exception:
                pass
        except Exception:
            pass
        try:
            self.reminder_manager.debug_log("dialog init done")
        except Exception:
            pass

    def _finalize_close(self):
        if self._closed:
            return
        self._closed = True
        try:
            if self.on_closed:
                self.on_closed()
        except Exception:
            pass

    def _close_dialog(self):
        try:
            self.dialog.grab_release()
        except Exception:
            pass
        try:
            self.dialog.destroy()
        except Exception:
            pass
    
    def setup_ui(self):
        bg = "#FFFFFF"
        fg = "#111111"
        font = ("Microsoft YaHei", 10)
        try:
            self.reminder_manager.debug_log("dialog setup_ui start")
        except Exception:
            pass
        try:
            self.dialog.configure(bg=bg)
        except Exception:
            pass

        container = tk.Frame(self.dialog, bg=bg)
        container.pack(fill="both", expand=True, padx=20, pady=20)
        container.grid_columnconfigure(1, weight=1)

        tk.Label(container, text="标题:", font=font, bg=bg, fg=fg).grid(row=0, column=0, sticky="w", pady=10)
        self.title_entry = tk.Entry(container, font=font, bg="#FFFFFF", fg="#111111", relief="solid", bd=1)
        self.title_entry.grid(row=0, column=1, sticky="ew", pady=10)

        tk.Label(container, text="日期:", font=font, bg=bg, fg=fg).grid(row=1, column=0, sticky="w", pady=10)
        self.date_var = tk.StringVar(master=self.dialog, value=str(self.selected_date or "").strip())
        date_frame = tk.Frame(container, bg=bg)
        date_frame.grid(row=1, column=1, sticky="w", pady=10)
        self.date_entry = tk.Entry(
            date_frame,
            font=font,
            bg="#FFFFFF",
            fg="#111111",
            relief="solid",
            bd=1,
            width=18,
            textvariable=self.date_var,
            state="readonly",
            readonlybackground="#FFFFFF",
        )
        self.date_entry.pack(side="left")
        tk.Button(date_frame, text="选择", command=self._open_date_picker, width=6).pack(side="left", padx=8)

        tk.Label(container, text="时间:", font=font, bg=bg, fg=fg).grid(row=2, column=0, sticky="w", pady=10)
        time_frame = tk.Frame(container, bg=bg)
        time_frame.grid(row=2, column=1, sticky="w", pady=10)

        self.hour_var = tk.StringVar(master=self.dialog, value="09")
        self.minute_var = tk.StringVar(master=self.dialog, value="00")
        hour_combo = ttk.Combobox(
            time_frame,
            values=tuple(f"{i:02d}" for i in range(24)),
            width=4,
            textvariable=self.hour_var,
            state="readonly",
            font=font,
        )
        minute_combo = ttk.Combobox(
            time_frame,
            values=tuple(f"{i:02d}" for i in range(60)),
            width=4,
            textvariable=self.minute_var,
            state="readonly",
            font=font,
        )
        hour_combo.pack(side="left")
        tk.Label(time_frame, text=":", font=font, bg=bg, fg=fg).pack(side="left", padx=6)
        minute_combo.pack(side="left")

        tk.Label(container, text="颜色:", font=font, bg=bg, fg=fg).grid(row=3, column=0, sticky="w", pady=10)
        self.selected_color = "#FF6B6B"
        color_frame = tk.Frame(container, bg=bg)
        color_frame.grid(row=3, column=1, sticky="w", pady=10)
        self.color_btn = tk.Button(color_frame, bg=self.selected_color, width=4, command=self.choose_color, relief="solid", bd=1)
        self.color_btn.pack(side="left")
        self.color_entry = tk.Entry(color_frame, font=font, bg="#FFFFFF", fg="#111111", relief="solid", bd=1, width=12)
        try:
            self.color_entry.insert(0, self.selected_color)
        except Exception:
            pass
        self.color_entry.pack(side="left", padx=10)

        tk.Label(container, text="重复:", font=font, bg=bg, fg=fg).grid(row=4, column=0, sticky="w", pady=10)
        repeat_frame = tk.Frame(container, bg=bg)
        repeat_frame.grid(row=4, column=1, sticky="w", pady=10)
        self.repeat_type_var = tk.StringVar(master=self.dialog, value="none")
        self.repeat_display_var = tk.StringVar(master=self.dialog, value="不重复")
        self._repeat_code_to_label = {
            "none": "不重复",
            "daily": "每天",
            "weekly": "每周",
            "monthly": "每月",
            "yearly": "每年",
        }

        def set_repeat(code: str):
            code = str(code or "none").strip() or "none"
            if code not in self._repeat_code_to_label:
                code = "none"
            try:
                self.repeat_type_var.set(code)
            except Exception:
                pass
            try:
                self.repeat_display_var.set(self._repeat_code_to_label.get(code, "不重复"))
            except Exception:
                pass

        self._set_repeat = set_repeat
        set_repeat("none")

        repeat_btn = tk.Menubutton(
            repeat_frame,
            textvariable=self.repeat_display_var,
            font=font,
            bg="#FFFFFF",
            fg="#111111",
            activebackground="#FFFFFF",
            activeforeground="#111111",
            relief="solid",
            bd=1,
            padx=10,
            pady=2,
            direction="below",
        )
        repeat_menu = tk.Menu(repeat_btn, tearoff=0)
        repeat_btn.configure(menu=repeat_menu)
        repeat_menu.add_command(label="不重复", command=lambda: set_repeat("none"))
        repeat_menu.add_command(label="每天", command=lambda: set_repeat("daily"))
        repeat_menu.add_command(label="每周", command=lambda: set_repeat("weekly"))
        repeat_menu.add_command(label="每月", command=lambda: set_repeat("monthly"))
        repeat_menu.add_command(label="每年", command=lambda: set_repeat("yearly"))
        repeat_btn.pack(side="left")

        tk.Label(container, text="备注:", font=font, bg=bg, fg=fg).grid(row=5, column=0, sticky="nw", pady=10)
        self.desc_text = tk.Text(container, height=6, font=("Microsoft YaHei", 9), wrap="word", bg="#FFFFFF", fg="#111111", relief="solid", bd=1)
        self.desc_text.grid(row=5, column=1, sticky="nsew", pady=10)
        container.grid_rowconfigure(5, weight=1)

        btn_frame = tk.Frame(container, bg=bg)
        btn_frame.grid(row=6, column=0, columnspan=2, pady=20)
        tk.Button(btn_frame, text="保存", command=self.save, width=10).pack(side="left", padx=10)
        tk.Button(btn_frame, text="取消", command=self._on_cancel, width=10).pack(side="left", padx=10)
        try:
            self.reminder_manager.debug_log("dialog setup_ui done")
        except Exception:
            pass
        
    def choose_color(self):
        try:
            current = str(getattr(self, "selected_color", "") or "").strip().upper()
        except Exception:
            current = ""
        try:
            _rgb, hex_color = colorchooser.askcolor(color=current or None, parent=self.dialog, title="选择颜色")
        except Exception:
            _rgb, hex_color = (None, None)

        if not hex_color:
            return

        c = str(hex_color).strip().upper()
        if c and not c.startswith("#"):
            c = "#" + c
        if len(c) != 7:
            return
        try:
            int(c[1:], 16)
        except Exception:
            return

        self.selected_color = c
        try:
            self.color_btn.configure(bg=c)
        except Exception:
            pass
        try:
            self.color_entry.delete(0, "end")
            self.color_entry.insert(0, c)
        except Exception:
            pass
            
    def load_reminder_data(self):
        if not self.reminder: return
        self.title_entry.delete(0, "end")
        self.title_entry.insert(0, str(getattr(self.reminder, "title", "") or ""))
        try:
            self.date_var.set(str(getattr(self.reminder, "date", "") or ""))
        except Exception:
            pass
        
        time_raw = str(getattr(self.reminder, "time", "") or "").strip()
        h = "09"
        m = "00"
        try:
            if ":" in time_raw:
                parts = time_raw.split(":")
                if len(parts) >= 2:
                    h = f"{int(parts[0]):02d}"
                    m = f"{int(parts[1]):02d}"
            elif len(time_raw) in (3, 4) and time_raw.isdigit():
                if len(time_raw) == 3:
                    h = f"{int(time_raw[0:1]):02d}"
                    m = f"{int(time_raw[1:3]):02d}"
                else:
                    h = f"{int(time_raw[0:2]):02d}"
                    m = f"{int(time_raw[2:4]):02d}"
        except Exception:
            h, m = "09", "00"
        if int(h) < 0 or int(h) > 23:
            h = "09"
        if int(m) < 0 or int(m) > 59:
            m = "00"
        self.hour_var.set(h)
        self.minute_var.set(m)
        
        raw_c = getattr(self.reminder, "color", None)
        c = str(raw_c or "").strip()
        if c and not c.startswith("#"):
            c = "#" + c
        if len(c) != 7:
            c = "#FF6B6B"
        try:
            int(c[1:], 16)
        except Exception:
            c = "#FF6B6B"
        self.selected_color = c.upper()
        try:
            self.color_btn.config(bg=self.selected_color)
        except Exception:
            pass
        try:
            self.color_entry.delete(0, "end")
            self.color_entry.insert(0, self.selected_color)
        except Exception:
            pass
        
        self.desc_text.delete("1.0", "end")
        self.desc_text.insert("1.0", str(getattr(self.reminder, "description", "") or ""))
        try:
            code = getattr(self.reminder, "repeat_type", "none") or "none"
            if hasattr(self, "_set_repeat"):
                self._set_repeat(code)
            else:
                self.repeat_type_var.set(code)
        except Exception:
            pass
        
    def save(self):
        title = self.title_entry.get().strip()
        if not title:
            messagebox.showwarning("提示", "请输入标题", parent=self.dialog)
            return
            
        reminder_id = self.reminder.id if self.reminder else str(uuid.uuid4())
        date_str = ""
        try:
            date_str = str(self.date_var.get() or "").strip()
        except Exception:
            date_str = ""
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except Exception:
            messagebox.showwarning("提示", "日期格式应为 YYYY-MM-DD", parent=self.dialog)
            return
        try:
            hh = f"{int(str(self.hour_var.get()).strip()):02d}"
        except Exception:
            hh = "00"
        try:
            mm = f"{int(str(self.minute_var.get()).strip()):02d}"
        except Exception:
            mm = "00"
        if int(hh) < 0 or int(hh) > 23:
            hh = "00"
        if int(mm) < 0 or int(mm) > 59:
            mm = "00"
        time_str = f"{hh}:{mm}"

        raw_color = ""
        try:
            raw_color = self.color_entry.get().strip()
        except Exception:
            raw_color = self.selected_color
        if raw_color and not raw_color.startswith("#"):
            raw_color = "#" + raw_color
        if len(raw_color) != 7:
            raw_color = self.selected_color
        try:
            int(raw_color[1:], 16)
        except Exception:
            raw_color = self.selected_color
        self.selected_color = str(raw_color).upper()
        repeat_type = "none"
        try:
            repeat_type = str(self.repeat_type_var.get() or "none").strip()
        except Exception:
            repeat_type = "none"
        if repeat_type not in ("none", "daily", "weekly", "monthly", "yearly"):
            repeat_type = "none"
        is_active = True
        
        new_reminder = ReminderData(
            id=reminder_id,
            title=title,
            date=date_str,
            time=time_str,
            color=self.selected_color,
            description=self.desc_text.get("1.0", "end-1c").strip(),
            repeat_type=repeat_type,
            is_active=is_active,
        )
        
        if self.reminder:
            self.reminder_manager.update_reminder(new_reminder)
        else:
            self.reminder_manager.add_reminder(new_reminder)
            
        self.result = "saved"
        try:
            if self.on_saved:
                self.on_saved(new_reminder)
        except Exception:
            pass
        self._close_dialog()

    def _on_cancel(self):
        self.result = "cancelled"
        self._close_dialog()

    def _open_date_picker(self):
        try:
            if self._date_picker and getattr(self._date_picker, "winfo_exists", lambda: 0)():
                try:
                    self._date_picker.deiconify()
                except Exception:
                    pass
                try:
                    self._date_picker.lift()
                except Exception:
                    pass
                try:
                    self._date_picker.focus_set()
                except Exception:
                    pass
                return
        except Exception:
            pass

        try:
            current = str(self.date_var.get() or "").strip()
        except Exception:
            current = ""

        y = date.today().year
        m = date.today().month
        try:
            if current:
                dt = datetime.strptime(current, "%Y-%m-%d")
                y, m = int(dt.year), int(dt.month)
        except Exception:
            y = date.today().year
            m = date.today().month

        picker = tk.Toplevel(self.dialog)
        self._date_picker = picker
        picker.title("选择日期")
        try:
            picker.resizable(False, False)
        except Exception:
            pass
        try:
            picker.transient(self.dialog)
        except Exception:
            pass

        def _on_destroy(_e=None):
            try:
                self._date_picker = None
            except Exception:
                pass

        try:
            picker.bind("<Destroy>", _on_destroy, add="+")
        except Exception:
            pass

        try:
            picker.configure(bg="#FFFFFF")
        except Exception:
            pass

        header = tk.Frame(picker, bg="#FFFFFF")
        header.pack(fill="x", padx=12, pady=(12, 6))

        year_var = tk.StringVar(master=picker, value=str(y))
        month_var = tk.StringVar(master=picker, value=f"{m:02d}")

        years = tuple(str(i) for i in range(max(1970, y - 50), y + 51))
        months = tuple(f"{i:02d}" for i in range(1, 13))

        def _render():
            for w in grid.winfo_children():
                w.destroy()

            try:
                yy = int(year_var.get())
            except Exception:
                yy = date.today().year
            try:
                mm = int(month_var.get())
            except Exception:
                mm = date.today().month

            weekdays = ("一", "二", "三", "四", "五", "六", "日")
            for c, wd in enumerate(weekdays):
                tk.Label(grid, text=wd, bg="#FFFFFF", fg="#111111", font=("Microsoft YaHei", 10, "bold"), width=4).grid(
                    row=0, column=c, padx=2, pady=2
                )

            def _select_day(dd: int):
                try:
                    self.date_var.set(f"{yy:04d}-{mm:02d}-{dd:02d}")
                except Exception:
                    pass
                try:
                    picker.destroy()
                except Exception:
                    pass

            month_data = cal.monthcalendar(yy, mm)
            for r, week in enumerate(month_data, start=1):
                for c, day_num in enumerate(week):
                    if day_num == 0:
                        tk.Label(grid, text="", bg="#FFFFFF", width=4).grid(row=r, column=c, padx=2, pady=2)
                        continue
                    btn = ttk.Button(grid, text=str(day_num), width=4, command=lambda d=day_num: _select_day(d), bootstyle="secondary")
                    btn.grid(row=r, column=c, padx=2, pady=2, sticky="nsew")

        def _prev_month():
            try:
                yy = int(year_var.get())
                mm = int(month_var.get())
            except Exception:
                yy, mm = date.today().year, date.today().month
            mm -= 1
            if mm <= 0:
                mm = 12
                yy -= 1
            year_var.set(str(yy))
            month_var.set(f"{mm:02d}")
            _render()

        def _next_month():
            try:
                yy = int(year_var.get())
                mm = int(month_var.get())
            except Exception:
                yy, mm = date.today().year, date.today().month
            mm += 1
            if mm >= 13:
                mm = 1
                yy += 1
            year_var.set(str(yy))
            month_var.set(f"{mm:02d}")
            _render()

        tk.Button(header, text="◀", command=_prev_month, width=4).pack(side="left")
        year_combo = ttk.Combobox(header, textvariable=year_var, values=years, width=6, state="readonly", font=("Microsoft YaHei", 10))
        year_combo.pack(side="left", padx=(8, 4))
        month_combo = ttk.Combobox(header, textvariable=month_var, values=months, width=4, state="readonly", font=("Microsoft YaHei", 10))
        month_combo.pack(side="left", padx=4)
        tk.Button(header, text="▶", command=_next_month, width=4).pack(side="left", padx=(4, 0))

        grid = tk.Frame(picker, bg="#FFFFFF")
        grid.pack(fill="both", expand=True, padx=12, pady=(6, 12))

        try:
            year_combo.bind("<<ComboboxSelected>>", lambda _e: _render(), add="+")
            month_combo.bind("<<ComboboxSelected>>", lambda _e: _render(), add="+")
        except Exception:
            pass

        _render()

        try:
            picker.update_idletasks()
            x = self.dialog.winfo_rootx() + 60
            y2 = self.dialog.winfo_rooty() + 80
            picker.geometry(f"+{x}+{y2}")
        except Exception:
            pass

        try:
            picker.grab_set()
        except Exception:
            pass
