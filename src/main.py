#funciones necesarias
from config.settings import PAISES, INDICADORES
from extract.extractor import extract_data
from transform.transformer import transform
from load.loader import loader as loader_data

#inicializa las funciones
def main():
    resultados = extract_data(PAISES, INDICADORES)
    dataframe = transform(resultados)
    loader_data(dataframe)

#pregunta si el nombre name esta ocupado, si no lo esta corre main(), de lo contrario cambia el nombre       
if __name__ == "__main__":
    main()