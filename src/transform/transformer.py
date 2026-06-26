import pandas as pd

def transform(resultados):
    dataframe = []

    for resultado in resultados:
        registros = resultado[1]
        dataframe.append(pd.DataFrame(registros))

    df = pd.concat(dataframe, ignore_index=True)

    df["country"] = df["country"].apply(lambda x: x["value"])
    df["indicator"] = df["indicator"].apply(lambda x: x["value"])

    df = df.rename(columns={
        "country": "pais",
        "indicator": "indicador",
        "value": "valor",
        "date": "fecha"
    })

    return df