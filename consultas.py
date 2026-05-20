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

STATUS_OK = "ok"
STATUS_NAO_ELEGIVEL = "nao_elegivel"

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
                txt = f.read().strip()
                if not txt:
                    return {}
                return json.loads(txt)
        except:
            return {}
    return {}

def salvar(data):
    with open(CHECKPOINT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# =========================
# BASE
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
        permissions=["clipboard-read", "clipboard-write"]
    )

    page = context.new_page()
    return context, page

# =========================
# ACEITE
# =========================
def aceitar_termo(page, link, cpf):
    try:
        page.goto(link, wait_until="domcontentloaded")
        page.wait_for_timeout(2000)

        checkbox = page.locator("text=Li e aceito").first
        if checkbox.count() == 0:
            checkbox = page.locator("input[type='checkbox']").first

        checkbox.click(force=True)

        btn = page.get_by_role("button", name="Confirmar aceite do termo")
        if btn.count() == 0:
            btn = page.get_by_role("button", name="Confirmar")

        btn.first.click(force=True)

        print(f"✅ aceite ok -> {cpf}")
        return True

    except Exception as e:
        print(f"❌ erro aceite {cpf}: {e}")
        return False

# =========================
# CONSULTA ESTEIRA
# =========================
def consultar_esteira(page, cpf):
    try:
        page.locator("button[title='Filtros']").first.click()
        time.sleep(1)

        campo = page.get_by_role("textbox", name="CPF Cliente")
        campo.fill(cpf)

        page.get_by_role("button", name="Confirmar", exact=True).click()
        time.sleep(3)

        linhas = page.locator("tbody tr")
        if linhas.count() == 0:
            return None, None

        linha = linhas.first
        cols = linha.locator("td")

        status = cols.nth(1).inner_text().lower()
        margem = cols.nth(8).inner_text().strip() if cols.count() >= 9 else None

        if "não eleg" in status or "nao eleg" in status:
            return "nao_elegivel", "SEM MARGEM"

        if "eleg" in status:
            return "ok", margem

        return None, None

    except Exception as e:
        print(f"❌ erro consulta {cpf}: {e}")
        return None, None

# =========================
# 🔥 FIX PRINCIPAL (NÃO TRAVA NO 1 CPF)
# =========================
pendentes = [
    (cpf, data)
    for cpf, data in resultados.items()
    if data["status"] == STATUS_PENDENTE
]

# =========================
# EXECUÇÃO
# =========================
with sync_playwright() as p:

    context, page = browser(p)

    for cpf, data in pendentes:

        try:
            print(f"\n📤 PROCESSANDO {cpf}")

            # =========================
            # ENVIO
            # =========================
            page.goto(URL)
            page.wait_for_timeout(2000)

            page.get_by_role("button", name="Nova Consulta").click()

            page.get_by_role("textbox", name="CPF do cliente").fill(cpf)
            page.get_by_role("button", name="Verificar").click()

            page.get_by_role("textbox", name="Nome do cliente").fill(data["nome"])
            page.get_by_role("textbox", name="Celular cliente").fill(data["telefone"])

            page.get_by_role("button", name="Confirmar").click()

            time.sleep(3)

            # =========================
            # LINK
            # =========================
            linhas = page.locator("tr")
            link = None

            for i in range(linhas.count()):
                linha = linhas.nth(i)

                if data["nome"].lower() in linha.inner_text().lower():
                    cols = linha.locator("td")

                    cols.nth(5).click(force=True)
                    time.sleep(1)

                    try:
                        link = page.evaluate("navigator.clipboard.readText()")
                    except:
                        link = None

                    break

            if not link:
                resultados[cpf]["status"] = STATUS_ERRO
                salvar(resultados)
                continue

            resultados[cpf]["link"] = link
            resultados[cpf]["status"] = STATUS_ENVIADO
            salvar(resultados)

            # =========================
            # ACEITE
            # =========================
            aceite_page = context.new_page()
            aceitar_termo(aceite_page, link, cpf)
            aceite_page.close()

            # =========================
            # CONSULTA FINAL
            # =========================
            status_final, margem = consultar_esteira(page, cpf)

            if status_final:
                resultados[cpf]["status"] = status_final
                resultados[cpf]["margem"] = margem

            salvar(resultados)

        except Exception as e:
            print(f"❌ erro geral {cpf}: {e}")
            resultados[cpf]["status"] = STATUS_ERRO
            salvar(resultados)

    context.close()

# =========================
# EXPORT FINAL
# =========================
output = f"resultado_final_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

pd.DataFrame(resultados.values()).to_excel(output, index=False)

print(f"\n📁 FINAL: {output}")