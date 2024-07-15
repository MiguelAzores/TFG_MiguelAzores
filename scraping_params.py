import time
import datetime
import argparse
import logging
import random
from typing import List, Dict, Any
from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Formato de los mensajes
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Lee los orgumentos de entrada
def read_params():
    parser = argparse.ArgumentParser()
    parser.add_argument("-l","--links", type=str, nargs='+', help="Enlaces del perfil del contratante")
    parser.add_argument("-p", "--patience", type=int, default=5, help="Paciencia del scrapper en segundos (default=5)")
    parser.add_argument("-hd", "--headless", action="store_true", help="Activa el flag para que desaparezca la ventana de navegador durante el scrapping")

    args = parser.parse_args()
    
    return args

# Abre la conexión con el navegador y navega a una url concreta
def abrir_navegador(link: str, args: Any) -> WebDriver:
    options = Options()
    if args.headless:
        options.add_argument("--headless=new")

    driver = webdriver.Chrome(options=options)
    driver.get(link)
    driver.implicitly_wait(args.patience)

    return driver

# Recolecta todas las cabeceras de licitaciones de un perfil de contratante
def recopila_cabeceras(driver: WebDriver, args: Any) -> List[Dict[str, Any]]:
    lista_cabeceras = []
    try:
        # Pestaña de licitaciones
        licitaciones_tab = WebDriverWait(driver, args.patience).until(
            EC.element_to_be_clickable((By.ID, "viewns_Z7_AVEQAI930GRPE02BR764FO30G0_:perfilComp:linkPrepLic"))
        )
        licitaciones_tab.click()
        # Obtiene el número de páginas
        n_pags = int(WebDriverWait(driver, args.patience).until(
            EC.presence_of_element_located((By.ID, "viewns_Z7_AVEQAI930GRPE02BR764FO30G0_:form1:textTotalPaginaasdasd"))
        ).text)
    except Exception as e:
        logging.error("No se pudo cargar la página de licitaciones: %s", e)
        return lista_cabeceras

    # Itera sobre las páginas de licitaciones y recopila información de las cabeceras
    for i in range(n_pags):
        time.sleep(0.2)
        try:
            # Busca los nombres de expedientes
            exp_tab = WebDriverWait(driver, args.patience).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "tdExpediente"))
            )
            # Busca los estados de expedientes
            estado_tab = WebDriverWait(driver, args.patience).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "tdEstado"))
            )
        except Exception as e:
            logging.error("No se pudieron seleccionar los nombres de expediente: %s", e)
            break

        # Recopila la información de cada expediente de la página almacenaldola en un diccionario que se añade a la lista de cabeceras
        for e, estado in zip(exp_tab, estado_tab):
            try:
                elements = e.find_elements(By.TAG_NAME, 'a')
                exp_name = elements[0].text
                exp_link = elements[1].get_attribute('href')
                timetrack = datetime.datetime.now()
                lista_cabeceras.append({
                    "Nombre del expediente": exp_name,
                    "url de descarga": exp_link,
                    "Estado de la Licitación": estado.text,
                    "Timetrack": timetrack})
            except Exception as e:
                logging.error("Error al extraer datos del expediente: %s", e)

        # Click en el botón para la siguiente página
        if i <= n_pags-1:
            try:
                next_button = driver.find_element(By.ID, "viewns_Z7_AVEQAI930GRPE02BR764FO30G0_:form1:siguienteLink")
                next_button.click()
                time.sleep(1)
            except Exception as e:
                #logging.info("Última página alcanzada o no se puede hacer clic en 'siguiente': %s", e)
                break

    return lista_cabeceras

# Extrae la información completa de los expedientes
def recopila_expedientes(driver: WebDriver, args: Any, lista_cabeceras: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    time.sleep(random.randrange(1,5))
    lista_expedientes = []
    # Itera sobre la lista de cabeceras para extraer la información de los expedientes
    for cab in lista_cabeceras:
        try:
            driver.get(cab["url de descarga"])
            file_content = driver.page_source
            WebDriverWait(driver, args.patience).until(
                EC.presence_of_element_located((By.ID, "DetalleLicitacionVIS_UOE"))
            )
            date = extract_fecha(driver)
            expediente_info = {
                "url de descarga": cab["url de descarga"],
                "Timetrack": datetime.datetime.now(),
                "Nombre del expediente": cab["Nombre del expediente"],
                "Página HTML": bytearray(file_content,'utf-8'),
                "fecha_anuncio": date
            }
            expediente_info.update(extract_table_info(driver, "DetalleLicitacionVIS_UOE"))
            expediente_info.update(extract_table_info(driver, "InformacionLicitacionVIS_UOE", skip_first=True))
            
            lista_expedientes.append(expediente_info)

        except Exception as e:
            logging.error("Error al abrir el expediente %s: %s", cab[0], e)
        #bar1.next()

   #bar1.finish()
    return lista_expedientes  

def extract_fecha(driver: WebDriver) -> str|None:
    try:
        row = driver.find_element(By.CLASS_NAME, "rowClass1 ")
        date = row.find_element(By.TAG_NAME, "div").text.strip()
    except:
        date = None
    return date

# Extra información de una tabla específica de la página web
def extract_table_info(driver: WebDriver, table_id: str, skip_first: bool = False) -> Dict[str, str]:
    info = {}
    table = driver.find_element(By.ID, table_id)
    table_list = table.find_elements(By.TAG_NAME, 'ul')
    # Salta el título de la tabla
    if skip_first:
        table_list = table_list[1:]
    # Itera sobre la tabla para extraer los datos y rellena el diccionario del expediente
    for t in table_list:
        tab_line = t.find_elements(By.TAG_NAME, 'li')
        if len(tab_line) >= 2:
            browser_key = tab_line[0].find_element(By.TAG_NAME, 'span').get_attribute('title').strip()
            browser_answ = tab_line[1].find_element(By.TAG_NAME, 'span').get_attribute('title').strip()
            info[browser_key] = browser_answ    
    return info

# Recopila las licitaciones
def collect_licitaciones(args: Any) -> List[Dict[str, Any]]:
    expedientes_por_organo = []
    # Recopila licitaciones iterando sobre la lista de enlaces introducida por argumentos
    for link in args.links:
        print(link)
        driver = abrir_navegador(link, args)
        lista_cabeceras = recopila_cabeceras(driver, args)
        if lista_cabeceras:
            expedientes_por_organo.append([link,recopila_expedientes(driver, args, lista_cabeceras)])
        driver.quit()

    return expedientes_por_organo

# Recopila las cabeceras
def collect_cabeceras(args) -> List[Dict[str, Any]]:
    cabeceras_por_organo = []
    for link in args.links:
        driver = abrir_navegador(link,args)
        cabeceras_por_organo.append([link, recopila_cabeceras(driver, args)])
        driver.quit()
        
    return cabeceras_por_organo

if __name__ == "__main__":
    args = read_params()
    licitaciones = collect_licitaciones(args)
    cabeceras = collect_cabeceras(args)
    print(cabeceras)