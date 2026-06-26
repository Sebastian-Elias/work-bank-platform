import requests
import logging
from config.settings import BASE_URL, PAISES, INDICADORES 

def extract_data (paises, indicadores):
    resultados = []
    for pais in paises:
      for indicador in indicadores:
        url = BASE_URL + "/country" + "/" + pais + "/" + "indicator" + "/" + indicador + "?format=json" 
        response = requests.get(url)
        if response.status_code == 200:
           logging.info("Obteniendo datos del Banco Mundial")
           data = response.json()
           resultados.append(data)
        else: 
           logging.error("error")

    return resultados