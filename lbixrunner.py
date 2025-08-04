import zipfile
import io
import struct
import time
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import os

def encode_lbix(png_path, lbix_path, script_text=None, icon_path=None):
    img = Image.open(png_path).convert("RGBA")
    width, height = img.size
    r, g, b, a = img.split()
    rgb = Image.merge("RGB", (r, g, b)).tobytes()
    alpha = a.tobytes()

    img_bytes = io.BytesIO()
    img_bytes.write(b"LBIX5")
    img_bytes.write(struct.pack("I", width))
    img_bytes.write(struct.pack("I", height))
    img_bytes.write(b"TRAN")
    img_bytes.write(rgb)
    img_bytes.write(alpha)
    img_bytes.seek(0)

    with zipfile.ZipFile(lbix_path, "w") as zf:
        zf.writestr("image.lbimg", img_bytes.read())
        if script_text:
            zf.writestr("main.lbscript", script_text)
        if icon_path:
            icon_img = Image.open(icon_path).convert("RGBA")
            w, h = icon_img.size
            r, g, b, a = icon_img.split()
            rgb = Image.merge("RGB", (r, g, b)).tobytes()
            alpha = a.tobytes()

            icon_bytes = io.BytesIO()
            icon_bytes.write(b"LBICON7")
            icon_bytes.write(struct.pack("I", w))
            icon_bytes.write(struct.pack("I", h))
            icon_bytes.write(b"TRAN")
            icon_bytes.write(rgb)
            icon_bytes.write(alpha)
            icon_bytes.seek(0)

            zf.writestr("icon.lbicon", icon_bytes.read())

    messagebox.showinfo("Success", f"LBIX file saved: {lbix_path}")

def decode_lbimg(data):
    if not data.startswith(b"LBIX5"):
        return None
    width = struct.unpack("I", data[5:9])[0]
    height = struct.unpack("I", data[9:13])[0]
    rgb = data[17:17 + width * height * 3]
    alpha = data[17 + width * height * 3:]
    rgb_img = Image.frombytes("RGB", (width, height), rgb)
    alpha_img = Image.frombytes("L", (width, height), alpha)
    return Image.merge("RGBA", (*rgb_img.split(), alpha_img))

def decode_lbicon(data):
    if not data.startswith(b"LBICON7"):
        return None
    width = struct.unpack("I", data[7:11])[0]
    height = struct.unpack("I", data[11:15])[0]
    rgb = data[19:19 + width * height * 3]
    alpha = data[19 + width * height * 3:]
    rgb_img = Image.frombytes("RGB", (width, height), rgb)
    alpha_img = Image.frombytes("L", (width, height), alpha)
    return Image.merge("RGBA", (*rgb_img.split(), alpha_img))

def math_eval(expr):
    expr = expr.replace('x', '*')
    try:
        return str(eval(expr))
    except:
        return "0"

def execute_lbscript(script, root, lbix_name):
    lines = script.splitlines()
    vars = {"txtboxinput": "", "lbixname": lbix_name}
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith("//"):
            continue
        if "#" in line:
            line = line.split("#", 1)[0].strip()
        if "//" in line:
            line = line.split("//", 1)[0].strip()
        if not line:
            continue

        if line.startswith("setwintitle "):
            title = line[13:].strip().strip('"')
            root.title(title)
        elif line.startswith("showmsgbox "):
            args = line[12:].split(",", 1)
            if len(args) == 2:
                title = args[0].strip().strip('"')
                msg = args[1].strip().strip('"')
                msg = msg.replace("txtboxinput", vars["txtboxinput"])
                msg = msg.replace("lbixname", vars["lbixname"])
                if "math " in msg:
                    math_expr = msg[msg.find("math ")+5:]
                    msg = msg.replace(f"math {math_expr}", math_eval(math_expr))
                messagebox.showinfo(title, msg)
        elif line.startswith("wait "):
            sec = float(line[5:].strip())
            root.update()
            time.sleep(sec)
        elif line.startswith("transparency "):
            val = int(line[13:].strip())
            root.attributes("-alpha", val / 255)
        elif line.startswith("showtxtbox "):
            args = line[12:].split(",", 1)
            if len(args) == 2:
                title = args[0].strip().strip('"')
                msg = args[1].strip().strip('"')
                input_box = tk.Toplevel(root)
                input_box.title(title)
                tk.Label(input_box, text=msg).pack()
                entry = tk.Entry(input_box)
                entry.pack()
                def submit():
                    vars["txtboxinput"] = entry.get()
                    input_box.destroy()
                tk.Button(input_box, text="OK", command=submit).pack()
                root.wait_window(input_box)
        elif line.startswith("seticon "):
            continue  # Already handled

def view_lbix(path):
    if not zipfile.is_zipfile(path):
        messagebox.showerror("Error", "Not a valid LBIX file")
        return

    with zipfile.ZipFile(path, "r") as zf:
        if "image.lbimg" not in zf.namelist():
            messagebox.showerror("Error", "Missing image.lbimg in LBIX")
            return

        img_data = zf.read("image.lbimg")
        img = decode_lbimg(img_data)
        if img is None:
            messagebox.showerror("Error", "Invalid LBIX image format")
            return

        script = None
        icon = None
        if "main.lbscript" in zf.namelist():
            try:
                script = zf.read("main.lbscript").decode("utf-8")
            except:
                script = None

        if "icon.lbicon" in zf.namelist():
            icon_data = zf.read("icon.lbicon")
            icon = decode_lbicon(icon_data)

        win = tk.Toplevel()
        win.title("LBIX Viewer")
        if icon:
            icon_img = ImageTk.PhotoImage(icon)
            win.iconphoto(False, icon_img)
        photo = ImageTk.PhotoImage(img)
        lbl = tk.Label(win, image=photo)
        lbl.image = photo
        lbl.pack()

        if script:
            name = os.path.splitext(os.path.basename(path))[0]
            execute_lbscript(script, win, name)

def gui():
    root = tk.Tk()
    root.title("LBIX Tool")
    root.geometry("250x150")

    def encode():
        img_path = filedialog.askopenfilename(filetypes=[("PNG files", "*.png")])
        if not img_path:
            return
        ask_script = messagebox.askyesno("Script", "Do you want to add a LBScript?")
        script = None
        icon_path = None
        if ask_script:
            script = simple_textbox("LBScript", "Enter your LBScript:")
            if "seticon " in script:
                ask_icon = messagebox.askyesno("Icon", "Do you want to add a window icon? (required for seticon in lbscript)")
                if ask_icon:
                    icon_path = filedialog.askopenfilename(filetypes=[("PNG files", "*.png")])
        out_path = filedialog.asksaveasfilename(defaultextension=".lbix", filetypes=[("LBIX files", "*.lbix")])
        if not out_path:
            return
        encode_lbix(img_path, out_path, script, icon_path)

    def simple_textbox(title, msg):
        popup = tk.Toplevel(root)
        popup.title(title)
        tk.Label(popup, text=msg).pack()
        txt = tk.Text(popup, height=15, width=60)
        txt.pack()
        val = {"result": ""}
        def save():
            val["result"] = txt.get("1.0", tk.END)
            popup.destroy()
        tk.Button(popup, text="OK", command=save).pack()
        root.wait_window(popup)
        return val["result"]

    def view():
        lbix = filedialog.askopenfilename(filetypes=[("LBIX files", "*.lbix")])
        if lbix:
            view_lbix(lbix)

    tk.Button(root, text="Convert PNG to LBIX", command=encode).pack(pady=10)
    tk.Button(root, text="View LBIX File", command=view).pack(pady=10)
    root.mainloop()

if __name__ == "__main__":
    gui()
