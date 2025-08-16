import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from tkinter.scrolledtext import ScrolledText
from PIL import Image, ImageTk
import zipfile
import os
import re
import time

# --- LBIMG5 encoder/decoder (for PNG) --- #
# We keep this because main image display is needed.

def encode_lbimg(png_path):
    # Just store PNG bytes directly
    with open(png_path, "rb") as f:
        return f.read()

def decode_lbimg(data):
    from io import BytesIO
    return Image.open(BytesIO(data))

# --- LBScript interpreter --- #

class LBScriptRunner:
    def __init__(self, master, main_img, lbix_name):
        self.master = master
        self.main_img = main_img
        self.lbix_name = lbix_name
        self.image_window = None
        self.img_tk = None
        self.transparency = 255
        self.txtboxinput = ""
        self.filepicked = ""
    def strip_quotes(self, text):
        if not text:
            return text
        if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
            return text[1:-1]
        return text
        
    def show_image(self):
        if self.image_window is None or not self.image_window.winfo_exists():
            self.image_window = tk.Toplevel(self.master)
            self.image_window.title(self.lbix_name)
            self.image_window.protocol("WM_DELETE_WINDOW", self.cmd_close)

            self.canvas = tk.Canvas(self.image_window, width=self.main_img.width, height=self.main_img.height)
            self.canvas.pack()

        img = self.main_img.copy()
        if self.transparency < 255:
            img.putalpha(self.transparency)
        self.img_tk = ImageTk.PhotoImage(img)
        self.canvas.create_image(0, 0, anchor="nw", image=self.img_tk)

    def substitute_vars(self, text):
        text = text.replace("%txtboxinput%", self.txtboxinput)
        text = text.replace("%lbixname%", self.lbix_name)
        text = text.replace("%filepicked%", self.filepicked)
        return text

    def run_script(self, script):
        # Split lines, support quotes for showmsgbox
        lines = script.strip().splitlines()
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                self.execute_line(line)
            except Exception as e:
                messagebox.showerror("LBScript Error", f"Error executing line:\n{line}\n\n{e}")
                break

    def execute_line(self, line):
        # Parse commands:
        # setwintitle <text>
        # showmsgbox "title", "text"
        # wait <milliseconds>
        # transparency add|sub <value>
        # showtxtbox <text>
        # math add|sub <number>
        # showfilepicker <title>
        # close

        # Regex to match showmsgbox "title", "text"
        if line.startswith("setwintitle "):
            arg = line[len("setwintitle "):].strip()
            arg = self.substitute_vars(arg)
            arg = self.strip_quotes(arg)
            if self.image_window and self.image_window.winfo_exists():
                self.image_window.title(arg)

        elif line.startswith("showmsgbox"):
            # Extract "title", "text"
            m = re.match(r'showmsgbox\s+"([^"]+)"\s*,\s*"([^"]+)"', line)
            if not m:
                raise ValueError("showmsgbox requires syntax: showmsgbox \"title\", \"text\"")
            title = self.strip_quotes(self.substitute_vars(m.group(1)))
            text = self.strip_quotes(self.substitute_vars(m.group(2)))
            messagebox.showinfo(title, text)

        elif line.startswith("wait "):
            arg = line[len("wait "):].strip()
            try:
                ms = int(arg)
                self.master.update()
                time.sleep(ms / 1000.0)
            except:
                raise ValueError("wait requires an integer milliseconds argument")

        elif line.startswith("transparency "):
            parts = line.split()
            if len(parts) != 3:
                raise ValueError("transparency requires 2 arguments")
            op = parts[1].lower()
            try:
                val = int(parts[2])
            except:
                raise ValueError("transparency second argument must be a number")
            if op == "add":
                self.transparency = max(0, min(255, self.transparency + val))
            elif op == "sub":
                self.transparency = max(0, min(255, self.transparency - val))
            else:
                raise ValueError("transparency operation must be 'add' or 'sub'")
            self.show_image()

        elif line.startswith("showtxtbox "):
            text = line[len("showtxtbox "):].strip()
            text = self.strip_quotes(self.substitute_vars(text))
            self.txtboxinput = simpledialog.askstring("Input", text)

        elif line.startswith("math "):
            parts = line.split()
            if len(parts) != 3:
                raise ValueError("math requires 2 arguments")
            op = parts[1].lower()
            try:
                val = float(parts[2])
            except:
                raise ValueError("math second argument must be a number")
            # We keep math command to modify transparency for example (or other numeric state)
            if op == "add":
                self.transparency = max(0, min(255, self.transparency + int(val)))
            elif op == "sub":
                self.transparency = max(0, min(255, self.transparency - int(val)))
            else:
                raise ValueError("math operation must be 'add' or 'sub'")
            self.show_image()

        elif line.startswith("showfilepicker "):
            title = line[len("showfilepicker "):].strip()
            title = self.strip_quotes(self.substitute_vars(title))
            fname = filedialog.askopenfilename(title=title)
            if fname:
                self.filepicked = fname

        elif line == "close":
            self.cmd_close()

        else:
            raise ValueError(f"Unknown command: {line}")

    def cmd_close(self):
        if self.image_window and self.image_window.winfo_exists():
            self.image_window.destroy()
            self.image_window = None

# --- LBIX file handling --- #

def save_lbix(path, main_img_path, script_text):
    main_data = encode_lbimg(main_img_path)
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("main.lbimg", main_data)
        z.writestr("script.lbix", script_text)

def load_lbix(path):
    with zipfile.ZipFile(path, "r") as z:
        main_data = z.read("main.lbimg")
        script_text = z.read("script.lbix").decode("utf-8")
    main_img = decode_lbimg(main_data)
    return main_img, script_text

# --- GUI --- #

class LBIXApp:
    def __init__(self, master):
        self.master = master
        self.master.title("LBIX Builder & Viewer")
        self.main_img = None
        self.script_text = ""
        self.lbix_path = None

        self.notebook = ttk.Notebook(master)
        self.notebook.pack(fill="both", expand=True)

        # Builder tab
        self.builder_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.builder_frame, text="Builder")

        self.main_img_path_var = tk.StringVar()

        row = 0
        ttk.Label(self.builder_frame, text="Main Image PNG:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(self.builder_frame, textvariable=self.main_img_path_var, width=40).grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        ttk.Button(self.builder_frame, text="Browse", command=self.browse_main_img).grid(row=row, column=2, padx=5, pady=5)
        row += 1

        ttk.Label(self.builder_frame, text="LBScript for images:").grid(row=row, column=0, sticky="nw", padx=5, pady=5)
        self.script_textbox = ScrolledText(self.builder_frame, width=60, height=15)
        self.script_textbox.grid(row=row, column=1, columnspan=2, sticky="nsew", padx=5, pady=5)
        row += 1

        self.builder_frame.grid_rowconfigure(row-1, weight=1)
        self.builder_frame.grid_columnconfigure(1, weight=1)

        ttk.Button(self.builder_frame, text="Save LBIX File", command=self.save_lbix_file).grid(row=row, column=1, sticky="e", padx=5, pady=10)

        # Viewer tab
        self.viewer_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.viewer_frame, text="Viewer")

        self.lbix_open_path_var = tk.StringVar()

        ttk.Label(self.viewer_frame, text="Open LBIX File:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(self.viewer_frame, textvariable=self.lbix_open_path_var, width=50).grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        ttk.Button(self.viewer_frame, text="Browse", command=self.browse_lbix_file).grid(row=0, column=2, padx=5, pady=5)
        ttk.Button(self.viewer_frame, text="View image", command=self.run_script_from_lbix).grid(row=1, column=1, sticky="e", padx=5, pady=5)

        self.viewer_frame.grid_columnconfigure(1, weight=1)

        self.script_runner = None

    def browse_main_img(self):
        path = filedialog.askopenfilename(title="Select Main Image PNG", filetypes=[("PNG Images", "*.png")])
        if path:
            self.main_img_path_var.set(path)

    def save_lbix_file(self):
        main_img_path = self.main_img_path_var.get()
        script = self.script_textbox.get("1.0", "end").strip()
        if not main_img_path or not os.path.isfile(main_img_path):
            messagebox.showerror("Error", "Valid main image PNG must be selected.")
            return
        if not script:
            messagebox.showerror("Error", "Script cannot be empty.")
            return
        save_path = filedialog.asksaveasfilename(title="Save LBIX File", defaultextension=".lbix",
                                                 filetypes=[("LBIX files", "*.lbix")])
        if save_path:
            try:
                save_lbix(save_path, main_img_path, script)
                messagebox.showinfo("Success", f"LBIX file saved to {save_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save LBIX file: {e}")


    def browse_lbix_file(self):
        path = filedialog.askopenfilename(title="Open LBIX File", filetypes=[("LBIX files", "*.lbix")])
        if path:
            self.lbix_open_path_var.set(path)

    def run_script_from_lbix(self):
        path = self.lbix_open_path_var.get()
        if not path or not os.path.isfile(path):
            messagebox.showerror("Error", "Valid LBIX file must be selected.")
            return
        try:
            main_img, script_text = load_lbix(path)
            self.script_runner = LBScriptRunner(self.master, main_img, os.path.basename(path))
            self.script_runner.show_image()
            self.script_runner.run_script(script_text)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to run script: {e}")

def main():
    root = tk.Tk()
    app = LBIXApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
