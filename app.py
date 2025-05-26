import os
import sys
import time
from tkinter import (
    Tk, Label, Button, Entry, Text, Scrollbar, Frame, Canvas, filedialog,
    messagebox, RIGHT, Y, END, BOTH, LEFT, NW, StringVar
)
from PIL import Image, ImageTk

TILE_W, TILE_H = 256, 256
COLS, ROWS = 4, 3

def log(message):
    timestamp = time.strftime("[%Y-%m-%d %H:%M:%S]")
    txt_log.config(state="normal")
    txt_log.insert(END, f"{timestamp} {message}\n")
    txt_log.see(END)
    txt_log.config(state="disabled")

def get_default_cs_background_path():
    home = os.path.expanduser("~")
    candidates = []

    if sys.platform.startswith("win"):
        program_files = os.environ.get("PROGRAMFILES", "C:\\Program Files")
        program_files_x86 = os.environ.get("PROGRAMFILES(X86)", "C:\\Program Files (x86)")
        candidates += [
            os.path.join(program_files, "Steam", "steamapps", "common", "Half-Life", "cstrike", "resource", "background"),
            os.path.join(program_files_x86, "Steam", "steamapps", "common", "Half-Life", "cstrike", "resource", "background"),
            os.path.join(home, "cstrike", "resource", "background")
        ]
    else:
        candidates += [
            os.path.join(home, ".steam", "steam", "steamapps", "common", "Half-Life", "cstrike", "resource", "background"),
            os.path.join(home, ".local", "share", "Steam", "steamapps", "common", "Half-Life", "cstrike", "resource", "background"),
            os.path.join(home, "cstrike", "resource", "background")
        ]

    for path in candidates:
        if os.path.isdir(path):
            return path
    return None

def process_cs_background(input_image_path, output_folder):
    tiles_folder = os.path.join(output_folder, "tiles")
    os.makedirs(tiles_folder, exist_ok=True)

    log(f"Opening image: {input_image_path}")
    img = Image.open(input_image_path)
    img = img.resize((1024, 768), Image.LANCZOS)
    log("Image resized to 1024x768")

    tiles = []
    for i in range(COLS * ROWS):
        row_index = i // COLS
        col_index = i % COLS
        left = col_index * TILE_W
        upper = row_index * TILE_H
        right = left + TILE_W
        lower = upper + TILE_H

        tile = img.crop((left, upper, right, lower))
        tile_path = os.path.join(tiles_folder, f"tile_{i:02d}.tga")
        tile.save(tile_path)
        tiles.append(tile_path)
        log(f"Saved tile {i:02d} to {tile_path}")

    col_letters = ['a', 'b', 'c', 'd']
    for i in range(COLS * ROWS):
        row_index = i // COLS
        row = row_index + 1
        col_letter = col_letters[i % COLS]

        old_path = os.path.join(tiles_folder, f"tile_{i:02d}.tga")
        new_filename = f"800_{row}_{col_letter}_loading.tga"
        new_path = os.path.join(output_folder, new_filename)
        os.rename(old_path, new_path)
        log(f"Renamed tile_{i:02d}.tga -> {new_filename}")

    try:
        os.rmdir(tiles_folder)
        log(f"Removed temporary folder: {tiles_folder}")
    except OSError:
        log(f"Could not remove temporary folder: {tiles_folder}")

    return img

def select_image():
    path = filedialog.askopenfilename(
        title="Select Background Image",
        filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.tga"), ("All files", "*.*")]
    )
    if path:
        image_path_var.set(path)
        log(f"Selected image: {path}")
        load_preview(path)
        check_ready()

def select_output():
    path = filedialog.askdirectory(title="Select Output Folder")
    if path:
        output_dir_var.set(path)
        log(f"Selected output folder: {path}")
        check_ready()

def auto_detect_output():
    detected = get_default_cs_background_path()
    if detected:
        output_dir_var.set(detected)
        log(f"Auto detected output folder: {detected}")
        check_ready()
    else:
        messagebox.showwarning("Not found", "Could not auto detect CS background folder.")
        log("Auto detect failed: folder not found")

def check_ready():
    if image_path_var.get() and output_dir_var.get():
        btn_process.config(state="normal")
    else:
        btn_process.config(state="disabled")

def process_image():
    input_image_path = image_path_var.get()
    output_folder = output_dir_var.get()
    try:
        img = process_cs_background(input_image_path, output_folder)
        messagebox.showinfo("Success", f"Tiles saved successfully to:\n{output_folder}")
        load_preview(input_image_path)  # refresh preview with latest
        log("Processing complete.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to process image:\n{e}")
        log(f"Error during processing: {e}")

def update_window_size(bg_w, bg_h, tile_h):
    # Controls width is fixed at 280px + some spacing
    controls_width = 280
    spacing = 16
    right_width = max(bg_w, COLS * 64) + 16
    total_width = controls_width + spacing + right_width
    total_height = bg_h + tile_h + 70  # extra padding for labels and spacing
    root.geometry(f"{total_width}x{total_height}")

def load_preview(image_path):
    global img_preview, tile_images

    try:
        img = Image.open(image_path).resize((1024, 768), Image.LANCZOS)

        # Background preview max size
        max_bg_w, max_bg_h = 400, 300
        preview_img = img.copy()
        preview_img.thumbnail((max_bg_w, max_bg_h), Image.LANCZOS)
        bg_preview_w, bg_preview_h = preview_img.size
        img_preview = ImageTk.PhotoImage(preview_img)

        canvas_preview.config(width=bg_preview_w, height=bg_preview_h)
        canvas_preview.delete("all")
        canvas_preview.create_image(0, 0, anchor=NW, image=img_preview)

        # Tile previews
        tile_images.clear()
        thumb_w, thumb_h = 64, 48
        for i in range(COLS * ROWS):
            row_index = i // COLS
            col_index = i % COLS
            left = col_index * TILE_W
            upper = row_index * TILE_H
            right = left + TILE_W
            lower = upper + TILE_H
            tile_cropped = img.crop((left, upper, right, lower))
            tile_thumb = tile_cropped.resize((thumb_w, thumb_h), Image.LANCZOS)
            tile_imgtk = ImageTk.PhotoImage(tile_thumb)
            tile_images.append(tile_imgtk)

        tile_preview_w = COLS * thumb_w
        tile_preview_h = ROWS * thumb_h
        canvas_grid.config(width=tile_preview_w, height=tile_preview_h)
        canvas_grid.delete("all")
        draw_tile_grid()

        update_window_size(bg_preview_w, bg_preview_h, tile_preview_h)
        log("Preview and tile grid updated.")
    except Exception as e:
        log(f"Error loading preview: {e}")

def draw_tile_grid():
    canvas_grid.delete("all")
    col_letters = ['a', 'b', 'c', 'd']
    thumb_w, thumb_h = 64, 48

    for i in range(COLS * ROWS):
        row_index = i // COLS
        col_index = i % COLS
        x = col_index * thumb_w
        y = row_index * thumb_h

        canvas_grid.create_image(x, y, anchor=NW, image=tile_images[i])
        label = f"{row_index+1}{col_letters[col_index]}"
        canvas_grid.create_text(x + 4, y + 3, text=label, fill="white", font=("Consolas", 9, "bold"), anchor=NW)

root = Tk()
root.title("CS 1.6 Background Tile Creator")

# Remove fixed window size and allow resizing
root.resizable(True, True)

image_path_var = StringVar()
output_dir_var = StringVar(value=get_default_cs_background_path() or "")

tile_images = []
img_preview = None

# Root grid config: 2 columns: left narrow controls, right tall preview stack
root.columnconfigure(0, weight=0, minsize=280)
root.columnconfigure(1, weight=1)
root.rowconfigure(0, weight=1)

# Left controls frame (including moved log)
frm_controls = Frame(root, padx=8, pady=8)
frm_controls.grid(row=0, column=0, sticky="ns")

Label(frm_controls, text="Background Image:").grid(row=0, column=0, sticky="w", pady=(0,3))
entry_img = Entry(frm_controls, textvariable=image_path_var, width=36)
entry_img.grid(row=1, column=0, sticky="ew", pady=(0,8))
btn_img = Button(frm_controls, text="Browse...", command=select_image)
btn_img.grid(row=2, column=0, sticky="ew", pady=(0,10))

Label(frm_controls, text="Output Folder:").grid(row=3, column=0, sticky="w", pady=(0,3))
entry_out = Entry(frm_controls, textvariable=output_dir_var, width=36)
entry_out.grid(row=4, column=0, sticky="ew", pady=(0,8))
frm_out_buttons = Frame(frm_controls)
frm_out_buttons.grid(row=5, column=0, sticky="ew", pady=(0,10))
btn_out = Button(frm_out_buttons, text="Browse...", command=select_output)
btn_out.pack(side=LEFT, expand=True, fill="x", padx=(0,5))
btn_auto = Button(frm_out_buttons, text="Auto Detect", command=auto_detect_output)
btn_auto.pack(side=LEFT, expand=True, fill="x")

btn_process = Button(frm_controls, text="Process Image", command=process_image, state="disabled")
btn_process.grid(row=6, column=0, sticky="ew", pady=(10,10))

# Log under process button, narrower width to fit in smaller window
Label(frm_controls, text="Log:").grid(row=7, column=0, sticky="w", pady=(0,3))
frame_log = Frame(frm_controls)
frame_log.grid(row=8, column=0, sticky="nsew")
frm_controls.rowconfigure(8, weight=1)

scrollbar = Scrollbar(frame_log)
scrollbar.pack(side=RIGHT, fill=Y)

txt_log = Text(frame_log, wrap="word", yscrollcommand=scrollbar.set, state="disabled", height=12, width=36)
txt_log.pack(fill=BOTH, expand=True)
scrollbar.config(command=txt_log.yview)

check_ready()

# Right side frame with vertical stack: background preview above tile grid preview
frm_right = Frame(root, padx=8, pady=8)
frm_right.grid(row=0, column=1, sticky="nsew")
frm_right.columnconfigure(0, weight=1)

# Background Preview Canvas - sized dynamically
Label(frm_right, text="Background Preview:").grid(row=0, column=0, sticky="w", pady=(0,4))
canvas_preview = Canvas(frm_right, bg="#222")
canvas_preview.grid(row=1, column=0, sticky="nsew", pady=(0,10))

# Tile Grid Preview Canvas below background preview
Label(frm_right, text="Tile Grid Preview:").grid(row=2, column=0, sticky="w", pady=(0,4))
canvas_grid = Canvas(frm_right, bg="#222")
canvas_grid.grid(row=3, column=0, sticky="nsew")

root.mainloop()
