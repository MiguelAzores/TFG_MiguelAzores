import subprocess
import argparse

def read_params():
    parser = argparse.ArgumentParser()
    parser.add_argument("-l","--links", type=str, nargs='+', help="Enlaces de los perfiles de contratación, por defecto carga los perfiles del municipio Jerez de la Frontera")
    parser.add_argument("-p", "--patience", type=int, default=5, help="Paciencia del scrapper en segundos para las esperas implicitas (default=5)")
    parser.add_argument("-hd", "--headless", action="store_true", help="Activa el flag para que desaparezca la ventana de navegador durante el scrapping")

    args = parser.parse_args()
    
    return args

Municipio_Jerez = [
        "https://contrataciondelestado.es/wps/poc?uri=deeplink:perfilContratante&idBp=xO%2BVWYM1HLcQK2TEfXGy%2BA%3D%3D", # Aena. Dirección del Aeropuerto de Jerez
        "https://contrataciondelestado.es/wps/poc?uri=deeplink:perfilContratante&idBp=AWzudWVfdurnSoTX3z%2F7wA%3D%3D", # C. Administración COMUJESA
        "https://contrataciondelestado.es/wps/poc?uri=deeplink:perfilContratante&idBp=uZeB9RW2UzkBPRBxZ4nJ%2Fg%3D%3D", # C. Administración MERCAJEREZ
        "https://contrataciondelestado.es/wps/poc?uri=deeplink:perfilContratante&idBp=isSUZ3Wb6qguf4aBO%2BvQlQ%3D%3D", # C.Administración Empresa Municipal de vivienda
        "https://contrataciondelestado.es/wps/poc?uri=deeplink:perfilContratante&idBp=mqwnEBYK3SoQK2TEfXGy%2BA%3D%3D", # C.Administración Parque Tecnológico Agroindustrial
        "https://contrataciondelestado.es/wps/poc?uri=deeplink:perfilContratante&idBp=7OhhaoN%2FfAWXQV0WE7lYPw%3D%3D", # Gerencia COMUJESA
        "https://contrataciondelestado.es/wps/poc?uri=deeplink:perfilContratante&idBp=RbpYQD4ZOZs%3D", # Gerencia Parque tecnológico Agroindustrial
        "https://contrataciondelestado.es/wps/poc?uri=deeplink:perfilContratante&idBp=8KXIej0TvMWXQV0WE7lYPw%3D%3D", # Gerencia MERCAJEREZ
        "https://contrataciondelestado.es/wps/poc?uri=deeplink:perfilContratante&idBp=XWw4npqzY9USugstABGr5A%3D%3D", # Gerencia Empresa Minucipal Vivienda
        "https://contrataciondelestado.es/wps/poc?uri=deeplink:perfilContratante&idBp=kL4JRvSx8lhvYnTkQN0%2FZA%3D%3D", # Gerencia FUNDARTE
        "https://contrataciondelestado.es/wps/poc?uri=deeplink:perfilContratante&idBp=rah94wmkSOY%3D", # Junta Gobierno Local Ayuntamiento de Jerez
        "https://contrataciondelestado.es/wps/poc?uri=deeplink:perfilContratante&idBp=Kl19yCF%2FEFOrz3GQd5r6SQ%3D%3D", # Patronato FUNDARTE
        "https://contrataciondelestado.es/wps/poc?uri=deeplink:perfilContratante&idBp=6vcXcT%2BkwNerz3GQd5r6SQ%3D%3D", # Presidencia Asociación Desarrollo Rural de la Campiña
        "https://contrataciondelestado.es/wps/poc?uri=deeplink:perfilContratante&idBp=%2Fht1J5NkW8kuf4aBO%2BvQlQ%3D%3D", # Presidencia FUNDARTE
        "https://contrataciondelestado.es/wps/poc?uri=deeplink:perfilContratante&idBp=6EG3tH2QThurz3GQd5r6SQ%3D%3D", # Presidencia circuito de Jerez
        "https://contrataciondelestado.es/wps/poc?uri=deeplink:perfilContratante&idBp=67eFk%2FswtPUBPRBxZ4nJ%2Fg%3D%3D" # Presidencia COMUJESA
    ]


args = read_params()

if args.links:
    Enlaces = ["-l "+" ".join(args.links)]
    print(Enlaces)
    
else:
    Enlaces = ["-l"]+(Municipio_Jerez)
    print(Enlaces)

# Ruta de los ficheros Python
scraping = 'raw_db.py'
crea_clean_db = 'clean_db.py'
carga_clean_db = 'standar_upload.py'

# Ejecuta el primer script
script1 = subprocess.run(['python', scraping]+Enlaces, capture_output=True, text=True)

# Si el primer script se ejecutó correctamente, ejecuta el segundo script
if script1.returncode == 0:
    script2 = subprocess.run(['python', crea_clean_db], capture_output=True, text=True)
else:
    print("El primer script falló, no se ejecutará el segundo script.")

# Si el primer script se ejecutó correctamente, ejecuta el segundo script
if script2.returncode == 0:
    script3 = subprocess.run(['python', carga_clean_db], capture_output=True, text=True)
else:
    print("El segundo script falló, no se ejecutará el segundo script.")
