from playwright.sync_api import sync_playwright
from event_bus import emit
import time
import os
import pandas as pd
from datetime import datetime


URL = "https://sistema.somabp2.com.br/privado/consultas"



# CHROME

def get_chrome_path():

    possible_paths = [

        r"C:\Program Files\Google\Chrome\Application\chrome.exe",

        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",

        os.path.expandvars(
            r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"
        )
    ]

    for path in possible_paths:

        if os.path.exists(path):
            return path

    return None



# ACEITE

def aceitar_termo(context, link, cpf):

    try:

        page = context.new_page()

        page.goto(link, wait_until="domcontentloaded")

        page.wait_for_timeout(2000)

        checkbox = page.locator(
            "input[type='checkbox']"
        ).first

        if checkbox.count() > 0:

            checkbox.click(force=True)

        btn = page.get_by_role(
            "button",
            name="Confirmar aceite do termo"
        )

        if btn.count() == 0:

            btn = page.get_by_role(
                "button",
                name="Confirmar"
            )

        btn.first.click(force=True)

        page.wait_for_timeout(2000)

        page.close()

        emit("log", f"✅ aceite ok {cpf}")

        return True

    except Exception as e:

        emit(
            "log",
            f"❌ erro aceite {cpf}: {e}"
        )

        return False



# CONSULTA FINAL

def consultar(page, cpf):

    try:

        page.locator(
            "button[title='Filtros']"
        ).click()

        time.sleep(1)

        page.get_by_role(
            "textbox",
            name="CPF Cliente"
        ).fill(cpf)

        page.get_by_role(
            "button",
            name="Confirmar",
            exact=True
        ).click()

        time.sleep(2)

        linha = page.locator("tbody tr").first

        cols = linha.locator("td")

        status = cols.nth(1).inner_text().lower()

        if "não eleg" in status:

            return "nao_elegivel", "SEM MARGEM"

        margem = cols.nth(8).inner_text()

        return "ok", margem

    except Exception as e:

        emit(
            "log",
            f"❌ erro consulta {cpf}: {e}"
        )

        return None, None



# EXPORT INTELIGENTE

def salvar_resultado_inteligente(
    resultados,
    input_file=None
):

    pasta = "resultados"

    os.makedirs(pasta, exist_ok=True)

    base = "execucao"

    if input_file:

        base = os.path.splitext(
            os.path.basename(input_file)
        )[0]

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    nome = f"{base}_resultado_{timestamp}.csv"

    caminho = os.path.join(
        pasta,
        nome
    )

    pd.DataFrame(
        resultados.values()
    ).to_csv(
        caminho,
        index=False,
        sep=";"
    )

    return caminho



# PIPELINE

def executar_pipeline(
    clientes,
    resultados,
    input_file=None
):

    chrome_path = get_chrome_path()

    if not chrome_path:

        emit(
            "log",
            "❌ Google Chrome não encontrado"
        )

        return

    with sync_playwright() as p:

    
        context = p.chromium.launch_persistent_context(

            executable_path=chrome_path,

            user_data_dir="perfil_browser",

            headless=False
        )

        page = context.new_page()

        total = len(clientes)

        done = 0

        emit(
            "log",
            "🚀 Iniciando processamento..."
        )

        
        # ENVIO + LINK + ACEITE
        
        for c in clientes:

            cpf = c["cpf"]

            try:

                emit("log", f"📤 {cpf}")

                page.goto(URL)

                page.get_by_role(
                    "button",
                    name="Nova Consulta"
                ).click()

                page.get_by_role(
                    "textbox",
                    name="CPF do cliente"
                ).fill(cpf)

                page.get_by_role(
                    "button",
                    name="Verificar"
                ).click()

                page.get_by_role(
                    "textbox",
                    name="Nome do cliente"
                ).fill(c["nome"])

                page.get_by_role(
                    "textbox",
                    name="Celular cliente"
                ).fill(c["telefone"])

                page.get_by_role(
                    "button",
                    name="Confirmar"
                ).click()

                time.sleep(3)

                
                linhas = page.locator("tr")

                link = None

                for i in range(linhas.count()):

                    linha = linhas.nth(i)

                    if c["nome"].lower() in linha.inner_text().lower():

                        cols = linha.locator("td")

                        cols.nth(5).click(force=True)

                        time.sleep(1)

                        try:

                            link = page.evaluate(
                                "navigator.clipboard.readText()"
                            )

                        except:

                            link = None

                        break

                if not link:

                    resultados[cpf]["status"] = "erro"

                    continue

                resultados[cpf]["link"] = link

                ok = aceitar_termo(
                    context,
                    link,
                    cpf
                )

                if not ok:

                    resultados[cpf]["status"] = "erro"

                    continue

                resultados[cpf]["status"] = "enviado"

                done += 1

                emit(
                    "progress",
                    (done, total)
                )

            except Exception as e:

                resultados[cpf]["status"] = "erro"

                emit(
                    "log",
                    f"❌ erro {cpf}: {e}"
                )

      
        # CONSULTA 
       
        emit(
            "log",
            "🔎 Consulta final..."
        )

        for cpf, data in resultados.items():

            if data["status"] != "enviado":

                continue

            status, margem = consultar(
                page,
                cpf
            )

            if status:

                resultados[cpf]["status"] = status

                resultados[cpf]["margem"] = margem

            done += 1

            emit(
                "progress",
                (done, total)
            )

        context.close()

        
        # EXPORT RESULTADOS
        
        output_file = salvar_resultado_inteligente(
            resultados,
            input_file=input_file
        )

        emit(
            "done",
            {
                "data": resultados,
                "file": output_file
            }
        )