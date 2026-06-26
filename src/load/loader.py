import psycopg2
import logging
from config.settings import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD, DB_SSLMODE, DB_TABLE

def loader (dataframe):
    conn = psycopg2.connect(
      host=DB_HOST,
      port=DB_PORT,
      dbname=DB_NAME,
      user=DB_USER,
      password=DB_PASSWORD,
      sslmode=DB_SSLMODE,
  )
    cursor = conn.cursor()
    cursor.execute(f"CREATE TABLE IF NOT EXISTS {DB_TABLE} (pais TEXT, indicador TEXT, valor FLOAT, fecha TEXT)")
    for indice, fila in dataframe.iterrows():
        cursor.execute(f"INSERT INTO {DB_TABLE} (pais, indicador, valor, fecha) VALUES (%s, %s, %s, %s)", (fila["pais"], fila["indicador"], fila["valor"], fila["fecha"]))
    conn.commit()
    logging.info("datos guardados exitosamente en postgress")
    cursor.close()
    conn.close()