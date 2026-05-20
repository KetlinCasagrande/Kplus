import customtkinter as ctk
import time

# ============================================
# SPLASH
# ============================================
def mostrar_splash():

    ctk.set_appearance_mode("dark")

    splash = ctk.CTk()

    splash.overrideredirect(True)

    largura = 520
    altura = 320

    screen_w = splash.winfo_screenwidth()
    screen_h = splash.winfo_screenheight()

    x = int((screen_w / 2) - (largura / 2))
    y = int((screen_h / 2) - (altura / 2))

    splash.geometry(f"{largura}x{altura}+{x}+{y}")

    splash.configure(fg_color="#09090b")

    # ============================================
    # CONTAINER
    # ============================================
    container = ctk.CTkFrame(
        splash,
        fg_color="transparent"
    )

    container.pack(expand=True)

    # ============================================
    # LOGO TEXT
    # ============================================
    logo = ctk.CTkLabel(
        container,
        text="K+",
        font=("Segoe UI", 72, "bold"),
        text_color="#ec4899"
    )

    logo.pack(pady=(30, 10))

    # ============================================
    # SUBTITLE
    # ============================================
    subtitle = ctk.CTkLabel(
        container,
        text="Automação inteligente de consultas CLT",
        font=("Segoe UI", 15),
        text_color="#8f8f8f"
    )

    subtitle.pack(pady=(0, 35))

    # ============================================
    # PROGRESS BAR
    # ============================================
    progress = ctk.CTkProgressBar(
        container,
        width=260,
        height=10,
        corner_radius=20,
        progress_color="#f08eff",
        fg_color="#2a2a2a"
    )

    progress.pack()

    progress.set(0)

    # ============================================
    # LOADING
    # ============================================
    loading = ctk.CTkLabel(
        container,
        text="Inicializando sistema...",
        font=("Segoe UI", 12),
        text_color="#6b7280"
    )

    loading.pack(pady=(15, 0))

    splash.update()

    # ============================================
    # ANIMAÇÃO
    # ============================================
    for i in range(100):

        progress.set(i / 100)

        splash.update()

        time.sleep(0.015)

    splash.destroy()