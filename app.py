import customtkinter as ctk
from tkinter import filedialog
import threading
import pandas as pd
import core
import os
from PIL import Image
import sys
import os


def resource_path(relative_path):

    try:
        base_path = sys._MEIPASS

    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


logo_img = ctk.CTkImage(
    light_image=Image.open(
        resource_path("assets/logo.png")
    ),
    dark_image=Image.open(
        resource_path("assets/logo.png")
    ),
    size=(70, 70)
)




from event_bus import event_queue

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


app = ctk.CTk()

app.geometry("1280x760")
app.title("K+")
app.minsize(1100, 700)


# CORES

BG = "#0d0d0d"
CARD = "#151515"
CARD2 = "#111111"
TEXT = "#f5f5f5"
SUBTEXT = "#8f8f8f"

app.configure(fg_color=BG)


resultados = {}
last_file = None
output_file = None


header = ctk.CTkFrame(
    app,
    fg_color=BG
)

header.pack(fill="x", pady=(20, 10), padx=25)

# LOGO

logo_label = ctk.CTkLabel(
    header,
    image=logo_img,
    text=""
)

logo_label.pack(side="left", padx=(0, 15))


# BRAND



subtitle = ctk.CTkLabel(
    header,
    text="Automação inteligente de consultas CLT",
    font=("Segoe UI", 20),
    text_color=SUBTEXT
)

subtitle.pack(side="left", padx=(15, 0), pady=(10, 0))


# STATUS

status_label = ctk.CTkLabel(
    header,
    text="🟢 Sistema pronto",
    font=("Segoe UI", 13, "bold"),
    text_color="#8df58d"
)

status_label.pack(side="right")


# MAIN

main = ctk.CTkFrame(
    app,
    fg_color="transparent"
)

main.pack(fill="both", expand=True, padx=25, pady=10)


# LEFT

left = ctk.CTkFrame(
    main,
    fg_color="transparent"
)

left.pack(side="left", fill="y", padx=(0, 15))




progress_card = ctk.CTkFrame(
    left,
    width=340,
    height=220,
    fg_color=CARD,
    corner_radius=24
)

progress_card.pack(pady=(0, 15))
progress_card.pack_propagate(False)

progress_title = ctk.CTkLabel(
    progress_card,
    text="PROCESSAMENTO",
    font=("Segoe UI", 13, "bold"),
    text_color=SUBTEXT
)

progress_title.pack(anchor="w", padx=22, pady=(20, 0))

percent_label = ctk.CTkLabel(
    progress_card,
    text="0%",
    font=("Segoe UI", 48, "bold"),
    text_color=TEXT
)

percent_label.pack(anchor="w", padx=22, pady=(10, 0))

count_label = ctk.CTkLabel(
    progress_card,
    text="0 de 0 CPFs processados",
    font=("Segoe UI", 14),
    text_color=SUBTEXT
)

count_label.pack(anchor="w", padx=22)

progress = ctk.CTkProgressBar(
    progress_card,
    width=280,
    height=14,
    corner_radius=20,
    progress_color="#ec4899"
)

progress.pack(pady=(25, 0))
progress.set(0)


# ACTIONS

actions_card = ctk.CTkFrame(
    left,
    width=340,
    height=260,
    fg_color=CARD,
    corner_radius=24
)

actions_card.pack()
actions_card.pack_propagate(False)

actions_title = ctk.CTkLabel(
    actions_card,
    text="AÇÕES",
    font=("Segoe UI", 13, "bold"),
    text_color=SUBTEXT
)

actions_title.pack(anchor="w", padx=22, pady=(20, 10))

buttons_frame = ctk.CTkFrame(
    actions_card,
    fg_color="transparent"
)

buttons_frame.pack(pady=10)


right = ctk.CTkFrame(
    main,
    fg_color=CARD,
    corner_radius=24
)

right.pack(side="left", fill="both", expand=True)

log_title = ctk.CTkLabel(
    right,
    text="LOGS DO SISTEMA",
    font=("Segoe UI", 13, "bold"),
    text_color=SUBTEXT
)

log_title.pack(anchor="w", padx=22, pady=(20, 10))

log_box = ctk.CTkTextbox(
    right,
    fg_color=CARD2,
    corner_radius=18,
    font=("Consolas", 13),
    text_color="#d6d6d6"
)

log_box.pack(fill="both", expand=True, padx=20, pady=(0, 20))


def log(msg):

    log_box.insert("end", msg + "\n")
    log_box.see("end")



def load_csv():

    global resultados
    global last_file

    path = filedialog.askopenfilename(
        initialdir="clientes",
        filetypes=[("CSV", "*.csv")]
    )

    if not path:
        return

    df = pd.read_csv(path, sep=";", dtype=str)

    df.columns = df.columns.str.strip().str.lower()

    clientes = df.to_dict("records")

    resultados = {}

    for c in clientes:

        cpf = str(c["cpf"]).strip()

        resultados[cpf] = {
            "cpf": cpf,
            "nome": c["nome"],
            "telefone": c["telefone"],
            "status": "pendente",
            "margem": None,
            "link": None
        }

    last_file = path

    log("📁 CSV carregado")


# RUN

def run():

    if not resultados:

        log("⚠ carregue um CSV")
        return

    status_label.configure(
        text="🟡 Processando...",
        text_color="#f5d78d"
    )

    threading.Thread(
        target=core.executar_pipeline,
        args=(
            list(resultados.values()),
            resultados,
            last_file
        ),
        daemon=True
    ).start()


def open_csv():

    global output_file

    if output_file and os.path.exists(output_file):

        os.startfile(output_file)


def open_folder():

    os.startfile("resultados")

# BUTTONS

btn_style = {
    "width": 125,
    "height": 48,
    "corner_radius": 14,
    "font": ("Segoe UI", 14, "bold"),
    "fg_color": "#ec4899",
    "hover_color": "#db2777",
    "text_color": "white"
}


btn1 = ctk.CTkButton(
    buttons_frame,
    text="📁 CSV",
    command=load_csv,
    **btn_style
)

btn1.grid(row=0, column=0, padx=8, pady=8)

btn2 = ctk.CTkButton(
    buttons_frame,
    text="▶ Executar",
    command=run,
    **btn_style
)

btn2.grid(row=0, column=1, padx=8, pady=8)

btn3 = ctk.CTkButton(
    buttons_frame,
    text="📄 Resultado",
    command=open_csv,
    **btn_style
)

btn3.grid(row=1, column=0, padx=8, pady=8)

btn4 = ctk.CTkButton(
    buttons_frame,
    text="📂 Pasta",
    command=open_folder,
    **btn_style
)

btn4.grid(row=1, column=1, padx=8, pady=8)


# EVENT LOOP

def event_loop():

    global output_file

    try:

        while True:

            event, data = event_queue.get_nowait()

            if event == "log":

                log(data)

            elif event == "progress":

                done, total = data

                pct = done / total if total else 0

                progress.set(pct)

                percent_label.configure(
                    text=f"{int(pct * 100)}%"
                )

                count_label.configure(
                    text=f"{done} de {total} CPFs processados"
                )

            elif event == "done":

                output_file = data["file"]

                status_label.configure(
                    text="🟢 Finalizado",
                    text_color="#8df58d"
                )

                log("")
                log("✔ PROCESSAMENTO FINALIZADO")
                log(output_file)

    except:
        pass

    app.after(200, event_loop)


# START

def start():

    event_loop()

    app.mainloop()