import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import threading
from tkinter import messagebox
import re
import sys

class InfoPushWidget(ttk.Frame):
    """信息推送显示组件"""
    
    def __init__(self, parent, alapi_manager, on_settings_click=None, ui_after=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.alapi_manager = alapi_manager
        self.on_settings_click = on_settings_click
        self.ui_after = ui_after
        self.selected_services = []
        
        self.setup_ui()

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
        """设置UI"""
        # 顶部按钮框架
        button_frame = ttk.Frame(self)
        button_frame.pack(fill=X, pady=(0, 10))
        
        ttk.Button(button_frame, text="刷新内容", 
                  command=self.refresh_content, 
                  bootstyle=SUCCESS).pack(side=LEFT, padx=(0, 5))
        
        if self.on_settings_click:
            ttk.Button(button_frame, text="Token设置", 
                      command=self.on_settings_click, 
                      bootstyle=SECONDARY).pack(side=LEFT, padx=5)
        
        self._create_scroll_area()
        
    def refresh_content(self):
        """刷新内容"""
        self.load_selected_services()
        
    def load_selected_services(self):
        """加载选中服务的内容"""
        # 清空现有内容
        for widget in self.scroll_content.winfo_children():
            widget.destroy()
            
        if not self.selected_services:
            self._show_message("请先在设置页面勾选要查看的信息推送服务")
            return
        
        self._show_message("正在加载数据，请稍候...", loading=True)
        
        # 在后台线程中加载数据
        threading.Thread(target=self._load_services_data, daemon=True).start()
    
    def _show_message(self, message, loading=False):
        """显示消息"""
        for widget in self.scroll_content.winfo_children():
            widget.destroy()
            
        frame = ttk.Frame(self.scroll_content, padding=20)
        frame.pack(fill=X, expand=True)
        
        if loading:
            ttk.Label(frame, text="⏳", font=("Microsoft YaHei", 24)).pack(pady=10)
            
        ttk.Label(frame, text=message, font=("Microsoft YaHei", 12), 
                 bootstyle=SECONDARY, justify=CENTER).pack(pady=10)

    def _load_services_data(self):
        """在后台线程中加载服务数据"""
        results = []
        
        for service_key in self.selected_services:
            service_name = self.alapi_manager.services.get(service_key, {}).get('name', service_key)
            
            try:
                # 获取数据
                data = self.alapi_manager.fetch_service_data(service_key)
                # 格式化数据
                formatted_data = self.alapi_manager.format_service_data(service_key, data)
                results.append({
                    'name': service_name,
                    'content': formatted_data,
                    'error': False
                })
            except Exception as e:
                results.append({
                    'name': service_name,
                    'content': f"获取失败: {str(e)}",
                    'error': True
                })
        
        # 在主线程中更新UI
        self._ui(0, lambda: self._update_content(results))
    
    def _update_content(self, data):
        """更新内容显示"""
        # 清空现有内容
        for widget in self.scroll_content.winfo_children():
            widget.destroy()
            
        if not data:
             self._show_message("暂无数据")
             return

        for item in data:
            self._create_card(item)
            
        # Re-bind mousewheel for new widgets
        self._bind_mousewheel(self.scroll_content)

    def _create_card(self, item):
        """创建卡片"""
        card = ttk.Labelframe(self.scroll_content, text=f" {item['name']} ", padding=15, bootstyle="info")
        card.pack(fill=X, expand=True, padx=10, pady=10)
        
        # 内容容器
        content_frame = ttk.Frame(card)
        content_frame.pack(fill=X, expand=True)
        
        try:
            style = ttk.Style()
            bg = getattr(style.colors, "bg", "#FFFFFF")
            fg = getattr(style.colors, "fg", "#111111")
        except Exception:
            bg = "#FFFFFF"
            fg = "#111111"

        normalized_content = self._normalize_content(item.get("name", ""), item.get("content", ""))
        content_label = tk.Label(
            content_frame,
            text=normalized_content,
            font=("Microsoft YaHei", 11),
            justify=LEFT,
            anchor="w",
            bg=bg,
            fg=fg,
            wraplength=520,
        )
        if item['error']:
            try:
                content_label.configure(fg="#DC3545")
            except Exception:
                pass
        
        content_label.pack(fill=X, expand=True)
        
        state = {"job": None, "last": None}

        def apply_wrap(w):
            if not w or w <= 0:
                return
            w2 = max(120, int(w) - 30)
            if state["last"] == w2:
                return
            state["last"] = w2
            try:
                content_label.configure(wraplength=w2)
            except Exception:
                pass

        def on_resize(event):
            try:
                w = int(getattr(event, "width", 0) or 0)
            except Exception:
                w = 0
            try:
                if state["job"] is not None:
                    card.after_cancel(state["job"])
            except Exception:
                state["job"] = None
            try:
                state["job"] = card.after(80, lambda: apply_wrap(w))
            except Exception:
                apply_wrap(w)

        card.bind("<Configure>", on_resize, add="+")
        
        # 底部工具栏
        tool_frame = ttk.Frame(card)
        tool_frame.pack(fill=X, pady=(10, 0))
        
        def copy_content(text=item['content']):
            self.clipboard_clear()
            self.clipboard_append(text)
            messagebox.showinfo("提示", "内容已复制到剪贴板", parent=self)
            
        ttk.Button(tool_frame, text="复制", command=copy_content, bootstyle="link-secondary", cursor="hand2").pack(side=RIGHT)

    def _normalize_content(self, title, content):
        if not content:
            return ""
        lines = content.splitlines()
        while lines and not lines[0].strip():
            lines.pop(0)
        if lines:
            first = lines[0].strip()
            first_plain = re.sub(r'^[^\w\u4e00-\u9fff]+', '', first)
            if title and title in first_plain:
                lines.pop(0)
                while lines and not lines[0].strip():
                    lines.pop(0)
        return "\n".join(lines).strip()

    def _create_scroll_area(self):
        container = ttk.Frame(self)
        container.pack(fill=BOTH, expand=True)

        self.canvas = tk.Canvas(container, highlightthickness=0, bd=0)
        self.v_scrollbar = ttk.Scrollbar(container, orient=VERTICAL, command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.v_scrollbar.set)

        self.v_scrollbar.pack(side=RIGHT, fill=Y)
        self.canvas.pack(side=LEFT, fill=BOTH, expand=True)

        self.scroll_content = ttk.Frame(self.canvas)
        self._scroll_window_id = self.canvas.create_window((0, 0), window=self.scroll_content, anchor="nw")

        def on_content_configure(_event=None):
            try:
                self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            except Exception:
                pass

        def on_canvas_configure(event):
            try:
                self.canvas.itemconfigure(self._scroll_window_id, width=event.width)
            except Exception:
                pass

        self.scroll_content.bind("<Configure>", on_content_configure, add="+")
        self.canvas.bind("<Configure>", on_canvas_configure, add="+")

        # Initial binding
        self._bind_mousewheel(self.canvas)
        self._bind_mousewheel(self.scroll_content)

        try:
            style = ttk.Style()
            self.canvas.configure(background=style.colors.bg)
        except Exception:
            pass
        
    def _bind_mousewheel(self, widget):
        """递归绑定滚轮事件"""
        if sys.platform.startswith('win'):
            widget.bind("<MouseWheel>", self._on_mousewheel, add="+")
        else:
            widget.bind("<Button-4>", self._on_mousewheel, add="+")
            widget.bind("<Button-5>", self._on_mousewheel, add="+")
        
        for child in widget.winfo_children():
            self._bind_mousewheel(child)

    def _on_mousewheel(self, event):
        if hasattr(event, "delta") and event.delta:
            delta = int(-1 * (event.delta / 120))
            try:
                self.canvas.yview_scroll(delta, "units")
            except Exception:
                pass
            return "break"
        return None
