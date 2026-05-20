from playwright.sync_api import sync_playwright
import pandas as pd
import time
import os
import json
from datetime import datetime

# =========================
# CONFIG
# =========================
URL = "https://sistema.somabp2.com.br/privado/consultas"
CHECKPOINT = "checkpoint.json"

STATUS_PENDENTE = "pendente"
STATUS_ENVIADO = "enviado"
STATUS_ERRO = "erro"

# =========================
# CSV
# =========================
df = pd.read_csv("clientes.csv", sep=";", dtype=str)

df.columns = df.columns.str.strip().str.lower()

clientes = df.to_dict("records")

# =========================
# UTIL
# =========================
def carregar():

    if os.path.exists(CHECKPOINT):

        try:
            with open(CHECKPOINT, "r", encoding="utf-8") as f:
                conteudo = f.read().strip()

                if not conteudo:
                    return {}

                return json.loads(conteudo)

        except:
            return {}

    return {}

def salvar(data):

    with open(CHECKPOINT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# =========================
# CHECKPOINT
# =========================
resultados = carregar()

for c in clientes:

    cpf = str(c["cpf"]).strip()

    if cpf not in resultados:

        resultados[cpf] = {
            "cpf": cpf,
            "nome": str(c["nome"]).strip(),
            "telefone": str(c["telefone"]).strip(),
            "status": STATUS_PENDENTE,
            "margem": None,
            "link": None
        }

# =========================
# BROWSER
# =========================
def browser(p):

    chrome_path = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"

    context = p.chromium.launch_persistent_context(
        user_data_dir="perfil",
        headless=False,
        executable_path=chrome_path,

        permissions=[
            "clipboard-read",
            "clipboard-write",
            "geolocation"
        ],

        geolocation={
            "latitude": -22.4122,
            "longitude": -50.5753
        }
    )

    page = context.new_page()

    return context, page

# =========================
# ACEITE
# =========================
def aceitar_termo(page, link, cpf):

    try:

        print(f"🔁 Aceitando termo -> {cpf}")

        page.goto(link, wait_until="domcontentloaded", timeout=60000)

        page.wait_for_load_state("networkidle")

        page.wait_for_timeout(3000)

        checkbox = None

        seletores = [
            "text=Li e aceito",
            "text=Li e aceito o Termo",
            "input[type='checkbox']",
            "label:has-text('aceito')"
        ]

        for sel in seletores:

            try:

                el = page.locator(sel)

                if el.count() > 0:
                    checkbox = el.first
                    break

            except:
                pass

        if not checkbox:
            print("❌ checkbox não encontrado")
            return False

        checkbox.click(force=True)

        page.wait_for_timeout(1000)

        botoes = [
            "Confirmar aceite do termo",
            "Confirmar",
            "Aceitar",
            "Continuar"
        ]

        clicou = False

        for nome in botoes:

            try:

                btn = page.get_by_role("button", name=nome)

                if btn.count() > 0:

                    btn.first.click(force=True)

                    clicou = True

                    print(f"✅ botão clicado -> {nome}")

                    break

            except:
                pass

        if not clicou:
            print("❌ botão confirmar não encontrado")
            return False

        page.wait_for_timeout(3000)

        print(f"✅ Aceite concluído -> {cpf}")

        return True

    except Exception as e:

        print(f"❌ erro aceite {cpf}: {e}")

        return False

# =========================
# EXECUÇÃO
# =========================
with sync_playwright() as p:

    context, page = browser(p)

    for cpf, data in resultados.items():

        if data["status"] != STATUS_PENDENTE:
            continue

        try:

            print(f"\n📤 Enviando {cpf}")

            page.goto(URL)

            page.wait_for_load_state("networkidle")

            # =========================
            # NOVA CONSULTA
            # =========================
            page.get_by_role(
                "button",
                name="Nova Consulta"
            ).click()

            page.wait_for_timeout(1500)

            # =========================
            # CPF
            # =========================
            page.get_by_role(
                "textbox",
                name="CPF do cliente"
            ).fill(cpf)

            page.get_by_role(
                "button",
                name="Verificar"
            ).click()

            page.wait_for_timeout(2000)

            # =========================
            # NOME / TELEFONE
            # =========================
            page.get_by_role(
                "textbox",
                name="Nome do cliente"
            ).fill(data["nome"])

            page.get_by_role(
                "textbox",
                name="Celular cliente"
            ).fill(data["telefone"])

            page.get_by_role(
                "button",
                name="Confirmar"
            ).click()

            page.wait_for_timeout(4000)

            # =========================
            # LOCALIZA LINHA
            # =========================
            linhas = page.locator("tr")

            link = None

            nome_cliente = data["nome"].lower()

            for i in range(linhas.count()):

                linha = linhas.nth(i)

                texto = linha.inner_text().lower()

                if nome_cliente in texto:

                    cols = linha.locator("td")

                    # =========================
                    # COPIA LINK
                    # =========================
                    cols.nth(5).click(force=True)

                    page.wait_for_timeout(1500)

                    try:

                        link = page.evaluate(
                            "navigator.clipboard.readText()"
                        )

                    except:
                        link = None

                    break

            # =========================
            # LINK
            # =========================
            if not link:

                print("❌ link não encontrado")

                resultados[cpf]["status"] = STATUS_ERRO

                salvar(resultados)

                continue

            print(f"🔗 LINK CAPTURADO: {link}")

            resultados[cpf]["link"] = link

            salvar(resultados)

            # =========================
            # NOVA ABA
            # =========================
            aceite_page = context.new_page()

            ok = aceitar_termo(
                aceite_page,
                link,
                cpf
            )

            aceite_page.close()

            if ok:

                resultados[cpf]["status"] = STATUS_ENVIADO

            else:

                resultados[cpf]["status"] = STATUS_ERRO

            salvar(resultados)

        except Exception as e:

            print(f"❌ erro {cpf}: {e}")

            resultados[cpf]["status"] = STATUS_ERRO

            salvar(resultados)

    context.close()

# =========================
# EXPORT FINAL
# =========================
output = f"resultado_envios_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

pd.DataFrame(
    resultados.values()
).to_excel(output, index=False)

print(f"\n📁 arquivo salvo: {output}")