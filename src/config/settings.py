from dotenv import load_dotenv
import os

load_dotenv()

BASE_URL = 'https://api.worldbank.org/v2'
PAISES = ['CL', 'AR', 'PE']
INDICADORES = ['NY.GDP.MKTP.CD', 'SP.POP.TOTL', 'FP.CPI.TOTL.ZG', 'SL.UEM.TOTL.ZS', 'NY.GDP.MKTP.KD.ZG']
#   - NY.GDP.MKTP.CD  — PIB nominal (GDP en dólares corrientes)
#   - SP.POP.TOTL     — Población total
#   - FP.CPI.TOTL.ZG  — Inflación (IPC anual %)
#   - SL.UEM.TOTL.ZS  — Desempleo (% de la fuerza laboral)
#   - NY.GDP.MKTP.KD.ZG — Crecimiento PIB real (% anual)

DB_HOST = os.environ.get("DB_HOST")
DB_PORT = os.environ.get("DB_PORT")
DB_NAME = os.environ.get("DB_NAME")
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_SSLMODE = os.environ.get("DB_SSLMODE")
DB_TABLE = "datos_bm"
