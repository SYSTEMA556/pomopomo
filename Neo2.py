import tkinter as tk
import win32gui
import time
import threading
from PIL import Image, ImageChops, ImageTk
import mss
import winsound

def enum_windows():
    """現在開いているウインドウの一覧を取得する関数"""
    windows = []
    def callback(hwnd, extra):
        if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd).strip():
            windows.append((hwnd, win32gui.GetWindowText(hwnd)))
    win32gui.EnumWindows(callback, None)
    return windows

class RegionSelector(tk.Toplevel):
    """スクリーンショット上で監視領域をドラッグして選択するためのウィンドウ"""
    def __init__(self, screenshot):
        super().__init__()
        self.title("監視領域選択")
        self.screenshot = screenshot
        self.tk_image = ImageTk.PhotoImage(screenshot)
        self.canvas = tk.Canvas(self, width=self.tk_image.width(), height=self.tk_image.height())
        self.canvas.pack()
        self.canvas.create_image(0, 0, anchor="nw", image=self.tk_image)
        
        self.rect = None
        self.start_x = None
        self.start_y = None
        self.selected_area = None
        
        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_move_press)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)
    
    def on_button_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        if self.rect:
            self.canvas.delete(self.rect)
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline="red", width=2)
    
    def on_move_press(self, event):
        curX, curY = event.x, event.y
        self.canvas.coords(self.rect, self.start_x, self.start_y, curX, curY)
    
    def on_button_release(self, event):
        end_x, end_y = event.x, event.y
        self.selected_area = (min(self.start_x, end_x), min(self.start_y, end_y),
                              max(self.start_x, end_x), max(self.start_y, end_y))
        print("Selected area:", self.selected_area)
        self.destroy()

class WindowMonitorApp(tk.Tk):
    """ウインドウの選択、領域選択、変化検出を統合したアプリケーション"""
    def __init__(self):
        super().__init__()
        self.title("バックグラウンド対応ウインドウ監視ツール")
        self.geometry("400x500")
        self.selected_hwnd = None
        self.monitoring = False
        self.selected_region = None
        self.last_image = None

        # UI部品の設定
        tk.Label(self, text="監視対象ウインドウを選択してください").pack(pady=5)
        self.window_list = tk.Listbox(self, width=50, height=10)
        self.window_list.pack()
        self.refresh_button = tk.Button(self, text="ウインドウリスト更新", command=self.refresh_windows)
        self.refresh_button.pack(pady=5)
        self.region_select_button = tk.Button(self, text="領域選択", command=self.select_region, state=tk.DISABLED)
        self.region_select_button.pack(pady=10)
        self.start_button = tk.Button(self, text="監視開始", command=self.start_monitoring, state=tk.DISABLED)
        self.start_button.pack(pady=10)
        self.stop_button = tk.Button(self, text="監視停止", command=self.stop_monitoring, state=tk.DISABLED)
        self.stop_button.pack(pady=5)
        self.result_label = tk.Label(self, text="結果: 未監視", fg="blue")
        self.result_label.pack(pady=10)

        self.refresh_windows()
        self.window_list.bind("<<ListboxSelect>>", self.on_window_select)

    def refresh_windows(self):
        self.window_list.delete(0, tk.END)
        self.windows = enum_windows()
        for hwnd, title in self.windows:
            self.window_list.insert(tk.END, f"{hwnd}: {title}")

    def on_window_select(self, event):
        selection = self.window_list.curselection()
        if selection:
            index = selection[0]
            self.selected_hwnd = self.windows[index][0]
            self.region_select_button.config(state=tk.NORMAL)

    def select_region(self):
        if not self.selected_hwnd:
            self.result_label.config(text="ウインドウを選択してください", fg="red")
            return
        # ウインドウ全体のスクリーンショットを取得
        rect = win32gui.GetWindowRect(self.selected_hwnd)
        left, top, right, bottom = rect
        with mss.mss() as sct:
            screenshot = sct.grab({"left": left, "top": top, "width": right - left, "height": bottom - top})
            image = Image.frombytes("RGB", (screenshot.width, screenshot.height), screenshot.rgb)

        # インタラクティブな領域選択ウィンドウを表示
        selector = RegionSelector(image)
        self.wait_window(selector)
        self.selected_region = selector.selected_area
        if self.selected_region:
            self.result_label.config(text=f"選択された領域: {self.selected_region}", fg="green")
            self.start_button.config(state=tk.NORMAL)

    def start_monitoring(self):
        if not self.selected_region:
            self.result_label.config(text="監視領域を選択してください", fg="red")
            return
        self.monitoring = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.result_label.config(text="監視中...", fg="green")
        threading.Thread(target=self.monitor_loop, daemon=True).start()

    def stop_monitoring(self):
        self.monitoring = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.result_label.config(text="監視停止", fg="blue")

    def monitor_loop(self):
        with mss.mss() as sct:
            while self.monitoring:
                try:
                    # ウインドウの現在の位置を取得
                    rect = win32gui.GetWindowRect(self.selected_hwnd)
                    left, top, right, bottom = rect
                    x1, y1, x2, y2 = self.selected_region
                    region = {"left": left + x1, "top": top + y1, "width": x2 - x1, "height": y2 - y1}

                    # 領域のスクリーンショットを取得
                    screenshot = sct.grab(region)
                    current_image = Image.frombytes("RGB", (screenshot.width, screenshot.height), screenshot.rgb)

                    if self.last_image is not None:
                        diff = ImageChops.difference(self.last_image, current_image)
                        if diff.getbbox() is not None:
                            self.result_label.config(text="変化を検出しました！", fg="orange")
                            winsound.Beep(1000, 500)
                        else:
                            self.result_label.config(text="変化なし", fg="green")
                    self.last_image = current_image
                except Exception as e:
                    self.result_label.config(text=f"エラー: {e}", fg="red")
                time.sleep(1)

if __name__ == "__main__":
    app = WindowMonitorApp()
    app.mainloop()
