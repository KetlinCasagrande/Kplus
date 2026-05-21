import os
from splash import mostrar_splash
import app


# CRIAR PASTAS

pastas = [
    "assets",
    "perfil",
    "resultados",
    "checkpoint",
    "clientes"
]

for pasta in pastas:
    os.makedirs(pasta, exist_ok=True)


# SPLASH

mostrar_splash()


# START APP

app.start()