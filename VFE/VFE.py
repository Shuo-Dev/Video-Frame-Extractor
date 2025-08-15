import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext, font
import cv2
import os
import threading
from datetime import datetime
import re
import json


class VideoFrameExtractor:
    def __init__(self, root):
        self.root = root
        self.language = self.detect_language()

        window_size = "1200x600" if self.language == "en-US" else "900x600"
        self.root.geometry(window_size)
        self.root.resizable(True, True)

        self.load_language_strings()
        self.root.title(self.lang["app_title"])

        self.root.protocol("WM_DELETE_WINDOW", self.on_window_close)

        self.custom_font = font.Font(family="Arial" if self.language == "en-US" else "楷体", size=12)
        self.title_font = font.Font(family="Arial" if self.language == "en-US" else "楷体", size=14, weight="bold")
        self.warning_font = font.Font(family="Arial" if self.language == "en-US" else "楷体", size=12, weight="bold")

        self.video_path = tk.StringVar()
        self.output_dir = tk.StringVar()
        self.total_frames = 0
        self.processing = False
        self.stop_processing = False
        self.stop_requested = False

        self.create_menu()
        self.create_widgets()
        self.setup_style()

    def detect_language(self):
        en_file = os.path.join("Languages", "en-US.json")
        if os.path.exists(en_file):
            return "en-US"
        return "zh-CN"

    def load_language_strings(self):
        lang_file = os.path.join("Languages", f"{self.language}.json")
        try:
            with open(lang_file, 'r', encoding='utf-8') as f:
                self.lang = json.load(f)
        except Exception as e:
            print(f"Error loading language file: {e}")
            self.lang = {
                "app_title": "视频帧提取工具",
                "menu_help": "帮助",
                "menu_instructions": "使用说明",
                "menu_precautions": "注意事项"
            }
            self.language = "zh-CN"

    def setup_style(self):
        style = ttk.Style()
        style.theme_use('clam')

        style.configure("TFrame", background="#F0F0F0")
        style.configure("TLabel", background="#F0F0F0", font=self.custom_font)
        style.configure("TButton", font=self.custom_font, padding=6)
        style.configure("TProgressbar", thickness=24, troughcolor='#E0E0E0', background='#4CAF50')
        style.configure("Title.TLabel", font=self.title_font, foreground="#2C3E50")
        style.configure("Status.TLabel", font=self.custom_font, foreground="#34495E")
        style.configure("TEntry", font=self.custom_font, padding=6)

        self.root.option_add("*Menu*Font", self.custom_font)
        self.root.option_add("*Menu*Background", "#F0F0F0")
        self.root.option_add("*Menu*Foreground", "#2C3E50")

    def create_menu(self):
        menubar = tk.Menu(self.root)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label=self.lang["menu_instructions"], command=self.show_instructions)
        help_menu.add_command(label=self.lang["menu_precautions"], command=self.show_precautions)
        menubar.add_cascade(label=self.lang["menu_help"], menu=help_menu)

        self.root.config(menu=menubar)

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        title_label = ttk.Label(main_frame, text=self.lang["app_title"], style="Title.TLabel")
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 15))

        ttk.Label(main_frame, text=self.lang["label_video_path"], style="TLabel").grid(row=1, column=0, padx=5, pady=8, sticky='e')
        self.video_entry = ttk.Entry(main_frame, textvariable=self.video_path, width=55, style="TEntry")
        self.video_entry.grid(row=1, column=1, padx=5, pady=8, sticky='ew')
        ttk.Button(main_frame, text=self.lang["btn_browse"], command=self.browse_video, width=8).grid(row=1, column=2, padx=5, pady=8)

        ttk.Label(main_frame, text=self.lang["label_output_dir"], style="TLabel").grid(row=2, column=0, padx=5, pady=8, sticky='e')
        self.output_entry = ttk.Entry(main_frame, textvariable=self.output_dir, width=55, style="TEntry")
        self.output_entry.grid(row=2, column=1, padx=5, pady=8, sticky='ew')
        ttk.Button(main_frame, text=self.lang["btn_browse"], command=self.browse_output, width=8).grid(row=2, column=2, padx=5, pady=8)

        warning_label = ttk.Label(
            main_frame,
            text=self.lang["path_warning"],
            foreground="red",
            font=self.warning_font,
            anchor=tk.CENTER
        )
        warning_label.grid(row=3, column=0, columnspan=3, pady=(5, 10))

        self.path_warning = ttk.Label(
            main_frame,
            text="",
            foreground="red",
            font=self.custom_font,
            anchor=tk.CENTER
        )
        self.path_warning.grid(row=4, column=0, columnspan=3, pady=(0, 5))
        self.path_warning.grid_remove()

        self.total_frames_label = ttk.Label(main_frame, text=self.lang["label_total_frames"], style="TLabel")
        self.total_frames_label.grid(row=5, column=1, padx=5, pady=10, sticky='w')

        frame_control = ttk.Frame(main_frame)
        frame_control.grid(row=6, column=1, pady=10, sticky='w')

        ttk.Label(frame_control, text=self.lang["label_start_frame"], style="TLabel").pack(side=tk.LEFT)
        self.start_frame_entry = ttk.Entry(frame_control, width=10, style="TEntry")
        self.start_frame_entry.pack(side=tk.LEFT, padx=8)

        ttk.Label(frame_control, text=self.lang["label_end_frame"], style="TLabel").pack(side=tk.LEFT)
        self.end_frame_entry = ttk.Entry(frame_control, width=10, style="TEntry")
        self.end_frame_entry.pack(side=tk.LEFT, padx=8)

        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=7, column=1, pady=15)

        self.process_btn = ttk.Button(btn_frame, text=self.lang["btn_process"], command=self.start_processing, width=14)
        self.process_btn.pack(side=tk.LEFT, padx=12)

        self.extract_all_btn = ttk.Button(btn_frame, text=self.lang["btn_extract_all"], command=self.extract_all_frames, width=14)
        self.extract_all_btn.pack(side=tk.LEFT, padx=12)
        self.extract_all_btn.pack_forget()

        self.progress = ttk.Progressbar(main_frame, orient='horizontal', length=650, mode='determinate')
        self.progress.grid(row=8, column=0, columnspan=3, padx=10, pady=15)

        self.status_label = ttk.Label(main_frame, text=self.lang["status_ready"], anchor=tk.CENTER, style="Status.TLabel")
        self.status_label.grid(row=9, column=0, columnspan=3, pady=(5, 0))

        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.grid(row=10, column=0, columnspan=3, pady=(15, 0), sticky='ew')

        ttk.Label(bottom_frame, text=self.lang["version_info"], style="Status.TLabel").pack(side=tk.RIGHT)

    def on_window_close(self):
        if self.processing:
            if not self.stop_requested:
                self.confirm_stop_processing()
            return

        self.root.destroy()

    def confirm_stop_processing(self):
        if messagebox.askyesno(self.lang["confirm_title"], self.lang["confirm_stop"]):
            self.stop_requested = True
            self.stop_processing = True
            self.status_label.config(text=self.lang["status_stopping"])
        else:
            self.stop_requested = False

    def contains_invalid_chars(self, path):
        if not path:
            return False

        if ' ' in path:
            return True

        if re.search(r'[^\x00-\x7F]', path):
            return True

        if re.search(r'[^a-zA-Z0-9_\-\.\\/:]', path):
            return True

        return False

    def update_path_warning(self):
        video_invalid = self.contains_invalid_chars(self.video_path.get())
        output_invalid = self.contains_invalid_chars(self.output_dir.get())

        if video_invalid or output_invalid:
            warning_text = "警告：" if self.language == "zh-CN" else "Warning: "
            if video_invalid:
                warning_text += "视频路径包含非法字符（非英文、数字或允许的特殊字符）" if self.language == "zh-CN" else "Video path contains invalid characters"
            if output_invalid:
                if video_invalid:
                    warning_text += "，且" if self.language == "zh-CN" else ", and "
                warning_text += "输出路径包含非法字符（非英文、数字或允许的特殊字符）" if self.language == "zh-CN" else "output path contains invalid characters"
            warning_text += "，可能导致处理失败！" if self.language == "zh-CN" else ", may cause processing to fail!"

            self.path_warning.config(text=warning_text)
            self.path_warning.grid()
        else:
            self.path_warning.grid_remove()

    def browse_video(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("视频文件", "*.mp4 *.avi *.mov *.mkv *.flv *.wmv")] if self.language == "zh-CN" else
            [("Video Files", "*.mp4 *.avi *.mov *.mkv *.flv *.wmv")]
        )
        if file_path:
            self.video_path.set(file_path)
            self.update_path_warning()
            self.get_video_info()

    def browse_output(self):
        dir_path = filedialog.askdirectory()
        if dir_path:
            self.output_dir.set(dir_path)
            self.update_path_warning()
            self.create_log_file(dir_path)

    def create_log_file(self, output_dir):
        log_path = os.path.join(output_dir, "extraction_log.txt")
        try:
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(
                    f"\n\n=== {'新的提取任务' if self.language == 'zh-CN' else 'New Extraction Task'} {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")
                f.write(f"{'视频文件' if self.language == 'zh-CN' else 'Video File'}: {self.video_path.get()}\n")
        except Exception as e:
            self.show_error(self.lang["log_create_error"].format(str(e)))

    def get_video_info(self):
        try:
            cap = cv2.VideoCapture(self.video_path.get())
            if not cap.isOpened():
                messagebox.showerror(self.lang["error_title"], self.lang["video_open_error"])
                return

            total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            self.total_frames = total
            self.total_frames_label.config(text=f"{'总帧数：' if self.language == 'zh-CN' else 'Total Frames: '}{total}")

            if total < 5000:
                self.extract_all_btn.pack(side=tk.LEFT, padx=12)
            else:
                self.extract_all_btn.pack_forget()

            cap.release()
        except Exception as e:
            self.show_error(self.lang["video_info_error"].format(str(e)))

    def extract_all_frames(self):
        self.start_frame_entry.delete(0, tk.END)
        self.start_frame_entry.insert(0, "0")
        self.end_frame_entry.delete(0, tk.END)
        self.end_frame_entry.insert(0, str(self.total_frames - 1))
        self.start_processing()

    def validate_inputs(self):
        try:
            start = int(self.start_frame_entry.get())
            end = int(self.end_frame_entry.get())
            if start < 0 or end >= self.total_frames or start > end:
                messagebox.showerror(self.lang["error_title"],
                                     self.lang["invalid_frames"].format(self.total_frames - 1))
                return False
            return True
        except ValueError:
            messagebox.showerror(self.lang["error_title"], self.lang["invalid_numbers"])
            return False

    def start_processing(self):
        if self.processing:
            return

        if not self.validate_inputs():
            return

        output_dir = self.output_dir.get()
        if not output_dir:
            messagebox.showerror(self.lang["error_title"], self.lang["no_output_dir"])
            return

        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
            except Exception as e:
                messagebox.showerror(self.lang["error_title"], self.lang["dir_create_error"].format(str(e)))
                return

        video_path = self.video_path.get()
        video_invalid = self.contains_invalid_chars(video_path)
        output_invalid = self.contains_invalid_chars(output_dir)

        if video_invalid or output_invalid:
            warning_msg = self.lang["warning_message"].format(
                f"{'视频路径' if self.language == 'zh-CN' else 'Video path'}: {video_path}" if video_invalid else "",
                f"{'输出路径' if self.language == 'zh-CN' else 'Output path'}: {output_dir}" if output_invalid else ""
            )

            if not messagebox.askyesno(self.lang["warning_title"], warning_msg, icon='warning'):
                return

        self.processing = True
        self.stop_processing = False
        self.stop_requested = False
        self.process_btn.config(text=self.lang["btn_stop"], command=self.confirm_stop_processing)
        self.status_label.config(text=self.lang["status_processing"])

        threading.Thread(
            target=self.process_video,
            args=(
                self.video_path.get(),
                output_dir,
                int(self.start_frame_entry.get()),
                int(self.end_frame_entry.get())
            ),
            daemon=True
        ).start()

    def stop_processing(self):
        self.stop_processing = True
        self.processing = False
        self.stop_requested = False
        self.process_btn.config(text=self.lang["btn_process"], command=self.start_processing)
        self.status_label.config(text=self.lang["status_stopped"])

    def update_progress(self, current, total):
        self.progress['value'] = (current / total) * 100
        self.status_label.config(
            text=f"{'处理进度：' if self.language == 'zh-CN' else 'Processing: '}{current}/{total} {'帧' if self.language == 'zh-CN' else 'frames'} ({current / total:.1%})")
        self.root.update_idletasks()

    def process_video(self, video_path, output_dir, start, end):
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                self.show_error(self.lang["video_open_error"])
                return

            cap.set(cv2.CAP_PROP_BUFFERSIZE, 2)

            actual_start = self.seek_to_frame(cap, start)
            if actual_start != start:
                self.show_error(
                    f"{'无法定位到起始帧' if self.language == 'zh-CN' else 'Cannot seek to start frame'} {start}，{'实际定位到' if self.language == 'zh-CN' else 'actual position'} {actual_start}")
                return

            current_frame = actual_start
            saved_count = 0
            total_to_save = end - start + 1

            ret, frame = cap.read()
            if not ret:
                self.show_error(self.lang["frame_read_error"].format(current_frame))
                return

            while current_frame <= end and not self.stop_processing:
                if current_frame > actual_start:
                    ret, frame = cap.read()
                    if not ret:
                        break

                if not self.save_frame(frame, current_frame, output_dir):
                    break

                saved_count += 1
                if saved_count % 10 == 0:
                    self.root.after(10, self.update_progress, saved_count, total_to_save)
                current_frame += 1

            cap.release()
            self.root.after(10, self.finish_processing, saved_count)
        except Exception as e:
            self.show_error(self.lang["process_error"].format(str(e)))

    def seek_to_frame(self, cap, target_frame):
        try:
            cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
            actual_pos = int(cap.get(cv2.CAP_PROP_POS_FRAMES))

            while actual_pos < target_frame and cap.isOpened():
                ret, _ = cap.read()
                if not ret:
                    break
                actual_pos += 1

            return actual_pos
        except Exception as e:
            self.show_error(self.lang["seek_error"].format(str(e)))
            return target_frame

    def save_frame(self, frame, frame_number, output_dir):
        try:
            if frame is None or frame.size == 0:
                raise ValueError("无效的帧数据" if self.language == "zh-CN" else "Invalid frame data")

            subfolder_num = (frame_number // 5000) + 1
            subfolder = os.path.join(output_dir, f"subarea{subfolder_num}")
            os.makedirs(subfolder, exist_ok=True)

            filename = os.path.join(subfolder, f"frame_{frame_number:08d}.jpg")

            if not cv2.imwrite(filename, frame, [int(cv2.IMWRITE_JPEG_QUALITY), 90]):
                raise IOError("文件写入失败" if self.language == "zh-CN" else "File write failed")

            self.write_log(output_dir, frame_number, filename)
            return True

        except Exception as e:
            self.show_error(self.lang["frame_save_error"].format(frame_number, str(e)))
            return False

    def write_log(self, output_dir, frame_number, filename):
        log_path = os.path.join(output_dir, "extraction_log.txt")
        try:
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(
                    f"{datetime.now().strftime('%H:%M:%S')} - {'已保存帧' if self.language == 'zh-CN' else 'Saved frame'} {frame_number} {'到' if self.language == 'zh-CN' else 'to'} {filename}\n")
        except Exception as e:
            self.show_error(self.lang["log_write_error"].format(str(e)))

    def show_error(self, message):
        self.root.after(10, messagebox.showerror, self.lang["error_title"], message)
        self.root.after(10, self.reset_ui)

    def finish_processing(self, saved_count):
        self.processing = False
        self.process_btn.config(text=self.lang["btn_process"], command=self.start_processing)
        self.status_label.config(text=self.lang["status_complete"].format(saved_count))
        self.progress['value'] = 0
        messagebox.showinfo(self.lang["complete_title"], self.lang["complete_message"])

    def reset_ui(self):
        self.processing = False
        self.process_btn.config(text=self.lang["btn_process"], command=self.start_processing)
        self.status_label.config(text=self.lang["status_ready"])
        self.progress['value'] = 0

    def show_instructions(self):
        self.show_help_window(self.lang["instructions_title"], self.lang["instructions_content"])

    def show_precautions(self):
        self.show_help_window(self.lang["precautions_title"], self.lang["precautions_content"])

    def show_help_window(self, title, content):
        window = tk.Toplevel(self.root)
        window.title(title)
        window.geometry("700x500")
        window.resizable(True, True)

        content_font = font.Font(family="Arial" if self.language == "en-US" else "楷体", size=12)
        title_font = font.Font(family="Arial" if self.language == "en-US" else "楷体", size=16, weight="bold")

        header_frame = ttk.Frame(window)
        header_frame.pack(fill=tk.X, padx=10, pady=(10, 5))

        ttk.Label(header_frame, text=title, font=title_font, foreground="#2C3E50").pack(pady=5)

        text_area = scrolledtext.ScrolledText(window, wrap=tk.WORD,
                                              font=content_font,
                                              padx=15, pady=10,
                                              background="#FFFFFF",
                                              relief=tk.FLAT)
        text_area.insert(tk.INSERT, content)
        text_area.configure(state='disabled')
        text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        btn_frame = ttk.Frame(window)
        btn_frame.pack(pady=(0, 15))

        ttk.Button(btn_frame, text=self.lang["btn_close"], command=window.destroy, width=14).pack()


if __name__ == "__main__":
    root = tk.Tk()
    app = VideoFrameExtractor(root)
    root.mainloop()