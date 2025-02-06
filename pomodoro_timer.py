import tkinter as tk
from tkinter import messagebox
import time
import threading

# カウントダウンの初期値（25分 = 1500秒）
TIMER_SECONDS = 25 * 60

class PomodoroTimer:
    def __init__(self, root):
        self.root = root
        self.root.title("ポモドーロタイマー")
        self.root.geometry("400x450")
        self.root.resizable(False, False)
        self.time_left = TIMER_SECONDS
        self.running = False

        # タイトルラベル
        self.label = tk.Label(root, text="25:00", font=("Helvetica", 48, "bold"))
        self.label.pack(pady=40)

        # スタートボタン
        self.start_button = tk.Button(root, text="スタート", font=("Helvetica", 16), command=self.start_timer)
        self.start_button.pack(pady=10)

        # ストップボタン
        self.stop_button = tk.Button(root, text="ストップ", font=("Helvetica", 16), command=self.stop_timer)
        self.stop_button.pack(pady=10)

        # リセットボタン
        self.reset_button = tk.Button(root, text="リセット", font=("Helvetica", 16), command=self.reset_timer)
        self.reset_button.pack(pady=10)

    def start_timer(self):
        """タイマー開始"""
        if not self.running:
            self.running = True
            threading.Thread(target=self.countdown).start()

    def stop_timer(self):
        """タイマー停止"""
        self.running = False

    def reset_timer(self):
        """タイマーリセット"""
        self.running = False
        self.time_left = TIMER_SECONDS
        self.update_display()

    def countdown(self):
        """カウントダウン処理"""
        while self.time_left > 0 and self.running:
            minutes, seconds = divmod(self.time_left, 60)
            self.label.config(text=f"{minutes:02}:{seconds:02}")
            self.root.update()
            time.sleep(1)
            self.time_left -= 1

        if self.time_left == 0 and self.running:
            self.running = False
            messagebox.showinfo("タイマー終了", "25分経過しました！休憩しましょう！")
            self.reset_timer()

    def update_display(self):
        """タイマー表示の更新"""
        minutes, seconds = divmod(self.time_left, 60)
        self.label.config(text=f"{minutes:02}:{seconds:02}")

if __name__ == "__main__":
    root = tk.Tk()
    app = PomodoroTimer(root)
    root.mainloop()
