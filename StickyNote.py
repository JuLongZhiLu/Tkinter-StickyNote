import tkinter as tk
from tkinter import Menu, Text, Toplevel
import json
import os
import time
from uuid import uuid4

class StickyNotesApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()  # 隐藏主窗口
        self.notes = []
        self.load_notes()
        
        # 创建系统托盘图标
        self.create_tray_icon()
        
    def create_tray_icon(self):
        """创建系统托盘图标和菜单"""
        self.tray_menu = Menu(self.root, tearoff=0)
        self.tray_menu.add_command(label="新建便签", command=self.create_note)
        self.tray_menu.add_separator()
        self.tray_menu.add_command(label="退出", command=self.quit_app)
        
    def create_note(self, content="", note_id=None, position=None):
        """创建新便签窗口"""
        note_id = note_id or str(uuid4())
        note = {
            "id": note_id,
            "content": content,
            "window": None
        }
        self.notes.append(note)
        
        # 创建便签窗口
        note_window = Toplevel(self.root)
        note_window.overrideredirect(True)  # 无边框窗口
        note_window.attributes('-topmost', False)  # 窗口置顶
        note_window.lower()
        note_window.configure(bg='#FFFFCC')  # 便签黄色背景
        
        # 设置初始位置
        if position:
            note_window.geometry(f"250x300+{position[0]}+{position[1]}")
        else:
            # 默认位置（稍微错开）
            x = 50 + len(self.notes) * 20
            y = 50 + len(self.notes) * 20
            note_window.geometry(f"250x300+{x}+{y}")
        
        # 创建文本编辑区域
        text_area = Text(note_window, bg='#FFFFCC', wrap="word", 
                         font=("微软雅黑", 11), padx=10, pady=10,
                         relief="flat", highlightthickness=0)
        text_area.insert("1.0", content)
        text_area.pack(fill="both", expand=True)
        
        # 绑定事件
        text_area.bind("<KeyRelease>", lambda e, nid=note_id: self.save_note(nid))
        text_area.bind("<ButtonPress-1>", lambda e: self.start_drag(e, note_window))
        text_area.bind("<B1-Motion>", lambda e, w=note_window: self.drag(e, w))
        text_area.bind("<ButtonRelease-1>", lambda e: self.stop_drag())
        
        # 创建右键菜单
        context_menu = Menu(note_window, tearoff=0)
        context_menu.add_command(label="删除", command=lambda nid=note_id: self.delete_note(nid))
        context_menu.add_command(label="新建", command=self.create_note)
        text_area.bind("<Button-3>", lambda e, m=context_menu: self.show_context_menu(e, m))
        
        note["window"] = note_window
        note["text_area"] = text_area
        note["position"] = note_window.geometry().split("+")[1:]
        
        # 保存初始状态
        self.save_note(note_id)
        
    def start_drag(self, event, window):
        """开始拖拽窗口"""
        window._drag_start_x = event.x
        window._drag_start_y = event.y
        
    def drag(self, event, window):
        """拖拽窗口移动"""
        x = window.winfo_x() - window._drag_start_x + event.x
        y = window.winfo_y() - window._drag_start_y + event.y
        window.geometry(f"+{x}+{y}")
        note_id = self.get_note_id_by_window(window)
        if note_id:
            self.save_note(note_id)
        
    def stop_drag(self):
        """停止拖拽"""
        pass  # 不需要额外操作
        
    def show_context_menu(self, event, menu):
        """显示右键菜单"""
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
        
    def save_note(self, note_id):
        """保存便签内容到文件"""
        note = next((n for n in self.notes if n["id"] == note_id), None)
        if note and note["window"].winfo_exists():
            content = note["text_area"].get("1.0", "end-1c")
            position = [note["window"].winfo_x(), note["window"].winfo_y()]
            
            note_data = {
                "id": note_id,
                "content": content,
                "position": position,
                "timestamp": time.time()
            }
            
            # 保存到JSON文件
            with open(f"note_{note_id}.json", "w") as f:
                json.dump(note_data, f)
    
    def delete_note(self, note_id):
        """删除便签"""
        note = next((n for n in self.notes if n["id"] == note_id), None)
        if note:
            if note["window"].winfo_exists():
                note["window"].destroy()
            self.notes = [n for n in self.notes if n["id"] != note_id]
            
            # 删除保存的文件
            if os.path.exists(f"note_{note_id}.json"):
                os.remove(f"note_{note_id}.json")
    
    def load_notes(self):
        """从文件加载保存的便签"""
        for file in os.listdir():
            if file.startswith("note_") and file.endswith(".json"):
                try:
                    with open(file, "r") as f:
                        note_data = json.load(f)
                    note_id = note_data["id"]
                    self.create_note(
                        content=note_data["content"],
                        note_id=note_id,
                        position=note_data["position"]
                    )
                except Exception as e:
                    print(f"加载便签失败: {file}, 错误: {e}")
        
        # 如果没有便签，创建一个默认的
        if not self.notes:
            self.create_note("这是一个便签示例\n双击拖动位置\n右键菜单删除或新建")
    
    def get_note_id_by_window(self, window):
        """通过窗口实例获取便签ID"""
        for note in self.notes:
            if note["window"] == window:
                return note["id"]
        return None
    
    def quit_app(self):
        """退出应用程序"""
        # 保存所有便签
        for note in self.notes:
            self.save_note(note["id"])
        self.root.destroy()
    
    def run(self):
        """运行应用程序"""
        self.root.mainloop()

if __name__ == "__main__":
    app = StickyNotesApp()
    app.run()
