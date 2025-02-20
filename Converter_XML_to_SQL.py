# Converter_XML_to_SQL.py


import lxml.etree as ET
import os
import psutil
import re
import time  # Do mierzenia czasu

# Pliki wejściowe/wyjściowe
INPUT_XML = "base-20241001T000000-20241005T010000.xml"
SCHEMA_OUTPUT_SQL = "schema_output.sql"
LOG_FILE = "process_log.txt"

# Słownik przechowujący struktury tabel
tables = {}

# Funkcja zapisująca logi do pliku
def log_message(message):
    print(message)
    with open(LOG_FILE, "a", encoding="utf-8") as log_file:
        log_file.write(message + "\n")

# Funkcja monitorująca pamięć
def log_memory_usage(step):
    process = psutil.Process(os.getpid())
    memory_usage = process.memory_info().rss / (1024 * 1024)  # MB
    log_message(f"[{step}] Zużycie pamięci: {memory_usage:.2f} MB")

# Funkcja do określenia typu danych na podstawie wartości
def infer_data_type(value):
    if value is None or value.strip() == "":
        return "TEXT"  # Domyślnie NULL -> TEXT
    if value.isdigit():
        return "BIGINT" if int(value) > 2147483647 else "INT"
    try:
        float(value)
        return "DECIMAL(18,6)"
    except ValueError:
        pass
    if "T" in value and ":" in value:  # Podejrzany format daty
        return "TIMESTAMP"
    return "TEXT"

# Funkcja do przetwarzania XML i zbierania struktury tabel
def analyze_xml_structure(input_file):
    log_message("Rozpoczynam analizę struktury XML...")
    log_memory_usage("Start")

    # Mierzenie czasu
    start_time = time.time()

    context = ET.iterparse(input_file, events=("start", "end"), huge_tree=False)

    processed_elements = 0  # Zliczanie przetworzonych elementów
    #total_elements = sum(1 for _ in open(input_file))  # Całkowita liczba linii w pliku

    for event, elem in context:
        if event == "start":
            tag = elem.tag.split("}")[-1]  # Obsługa przestrzeni nazw
            if tag not in tables:
                tables[tag] = {}  # Nowa tabela

            # Iteracja po wszystkich dzieciach elementu i dodanie do schematu
            for child in elem:
                field = child.tag.split("}")[-1]  # Obsługa przestrzeni nazw
                value = child.text
                data_type = infer_data_type(value)

                if field not in tables[tag]:
                    tables[tag][field] = data_type  # Nowe pole
                else:
                    # Jeśli istnieje, sprawdź, czy trzeba zmienić na bardziej ogólny
                    existing_type = tables[tag][field]
                    if existing_type != data_type:
                        tables[tag][field] = "TEXT"  # Jeśli są różne -> TEXT jako bezpieczny wybór

            elem.clear()  # Usuwamy przetworzony element z pamięci

        processed_elements += 1
        if processed_elements % 1 == 0:  # Co 1 elementów
            # Zaktualizuj liczbę przetworzonych elementów
            elapsed_time = time.time() - start_time
            # Nadpisanie poprzedniej linii w terminalu
            print(f"Przetworzono {processed_elements} elementów. Czas: {elapsed_time:.2f} sekund", end="\r")
            #log_message(f"Przetworzono {processed_elements} z {total_elements} elementów. Czas: {elapsed_time:.2f} sekund")

    # Zakończenie
    elapsed_time = time.time() - start_time
    log_message(f"Całkowity czas działania skryptu: {elapsed_time:.2f} sekund")
    log_memory_usage("Po analizie")
    log_message(f"Zidentyfikowano {len(tables)} tabel.")

# Funkcja zapisująca schemat bazy danych do pliku SQL
def save_schema_to_sql(output_file):
    log_message("Zapisywanie schematu do pliku SQL...")
    
    with open(output_file, "w", encoding="utf-8") as sql_file:
        for table_name, columns in tables.items():
            sql_file.write(f"CREATE TABLE IF NOT EXISTS {table_name} (\n")
            sql_columns = [f"    {col} {dtype}" for col, dtype in columns.items()]
            sql_file.write(",\n".join(sql_columns))
            sql_file.write("\n);\n\n")

    log_message(f"Schemat zapisany do {output_file}")

# Główna funkcja
def create_schema_table():
    # Najpierw analizujemy strukturę XML i zapisujemy schemat
    analyze_xml_structure(INPUT_XML)
    save_schema_to_sql(SCHEMA_OUTPUT_SQL)


from tqdm import tqdm


# Ścieżki plików wejściowych/wyjściowych
SCHEMA_INPUT_SQL = "schema_output.sql"
SCHEMA_FILTERED_OUTPUT_SQL = "filtered_schema_output.sql"

# Funkcja wczytująca schemat z pliku SQL
def load_schema(input_file):
    with open(input_file, "r", encoding="utf-8") as file:
        return file.read()

# Funkcja zapisująca przefiltrowany schemat do nowego pliku SQL
def save_filtered_schema(output_file, schema_content):
    with open(output_file, "w", encoding="utf-8") as file:
        file.write(schema_content)

# Funkcja filtrująca schemat, usuwająca puste tabele
def filter_schema(schema_content):
    # Wyrażenie regularne do dopasowania bloków CREATE TABLE
    create_table_pattern = re.compile(r"CREATE TABLE IF NOT EXISTS (\S+)\s*\((.*?)\);", re.DOTALL)

    # Lista do przechowywania schematów tabel z kolumnami
    valid_tables = []

    # Szukamy wszystkich CREATE TABLE
    matches = create_table_pattern.findall(schema_content)

    # Tworzymy pasek postępu na podstawie liczby tabel
    pbar = tqdm(total=len(matches), desc="Filtracja tabel", unit="tabela")

    for table_name, columns in matches:
        # Jeśli tabela zawiera jakiekolwiek kolumny
        if columns.strip():  # Kolumny muszą być niepuste
            valid_tables.append(f"CREATE TABLE IF NOT EXISTS {table_name} (\n{columns}\n);\n")

        # Aktualizujemy pasek postępu po przetworzeniu tabeli
        pbar.update(1)

    # Zamykamy pasek po zakończeniu
    pbar.close()

    # Zwracamy przefiltrowany schemat (tylko tabele z kolumnami)
    return "\n".join(valid_tables)

# Główna funkcja
def filter_schema_finisch_schema_table():
    # Wczytujemy istniejący schemat
    schema_content = load_schema(SCHEMA_INPUT_SQL)

    # Filtrujemy schemat, aby usunąć tabele bez kolumn
    filtered_schema = filter_schema(schema_content)

    # Zapisujemy przefiltrowany schemat do nowego pliku
    save_filtered_schema(SCHEMA_FILTERED_OUTPUT_SQL, filtered_schema)

    print(f"Przefiltrowany schemat zapisany do {SCHEMA_FILTERED_OUTPUT_SQL}")


# Pliki wejściowe/wyjściowe
DATA_OUTPUT_SQL = "data_output.sql"
FINISHE_SCHEMA_INPUT_SQL = "filtered_schema_output.sql"  # Plik z zapisanym schematem tabel

# Słownik przechowujący struktury tabel
tables = {}

# Funkcja zapisująca logi do pliku
def log_message(message):
    print(message)
    with open(LOG_FILE, "a", encoding="utf-8") as log_file:
        log_file.write(message + "\n")

# Funkcja monitorująca pamięć
def log_memory_usage(step):
    process = psutil.Process(os.getpid())
    memory_usage = process.memory_info().rss / (1024 * 1024)  # MB
    log_message(f"[{step}] Zużycie pamięci: {memory_usage:.2f} MB")

# Funkcja wczytująca schemat tabel z pliku SQL
def load_schema_from_sql(input_file):
    log_message(f"Wczytuję schematy tabel z pliku {input_file}...")
    
    with open(input_file, "r", encoding="utf-8") as sql_file:
        sql_content = sql_file.read()

    tables.clear()  # Wyczyść poprzednie dane
    
    create_table_pattern = re.compile(r"CREATE TABLE IF NOT EXISTS (\S+) \((.*?)\);", re.DOTALL)

    matches = create_table_pattern.findall(sql_content)

    for table_name, columns_block in matches:
        tables[table_name] = {}  # Inicjalizacja tabeli

        # Parsowanie kolumn
        columns_lines = columns_block.split("\n")
        for line in columns_lines:
            line = line.strip().rstrip(",")

            # Pomijamy klucze obce, unikalne indeksy itp.
            if "PRIMARY KEY" in line or "FOREIGN KEY" in line or "UNIQUE" in line:
                continue
            
            parts = line.split()
            if len(parts) >= 2:
                column_name = parts[0]
                column_type = parts[1]
                tables[table_name][column_name] = column_type

    log_message(f"Wczytano {len(tables)} tabel.")

# Funkcja do przetwarzania danych z XML i generowania zapytań INSERT INTO
def analyze_and_extract_data(input_file):
    log_message("Rozpoczynam analizę danych z XML...")
    start_time = time.time()  # Start pomiaru czasu
    context = ET.iterparse(input_file, events=("start", "end"), huge_tree=False)

    data_inserts = []
    processed_elements = 0


    for event, elem in context:
        if event == "start":
            tag = elem.tag.split("}")[-1]  # Usunięcie przestrzeni nazw

            # Znajdujemy tabelę o pasującej nazwie
            matching_table = next((t for t in tables if t.lower() == tag.lower()), None)

            if matching_table:
                row_data = []
                columns = []

                for child in elem:
                    field = child.tag.split("}")[-1]  # Nazwa kolumny
                    value = child.text.strip() if child.text else None

                    if field in tables[matching_table]:  # Sprawdzenie, czy kolumna istnieje w tabeli
                        columns.append(field)
                        row_data.append(f"'{value}'" if value else "NULL")

                if columns and row_data:
                    columns_str = ", ".join(columns)
                    values_str = ", ".join(row_data)
                    insert_query = f"INSERT INTO {matching_table} ({columns_str}) VALUES ({values_str});\n"
                    data_inserts.append(insert_query)

            elem.clear()  # Usuwanie z pamięci

        processed_elements += 1
        elapsed_time = time.time() - start_time

        # Wyświetlanie postępu
        if processed_elements % 1 == 0:
            print(f"Przetworzono {processed_elements} Elementy Czas: {elapsed_time:.2f} s", end="\r")

    print()  # Przejście do nowej linii po zakończeniu
    return data_inserts

# Funkcja zapisująca dane do nowego pliku SQL
def save_data_to_sql(data_inserts, output_file):
    log_message(f"Zapisywanie danych do nowego pliku SQL {output_file}...")
    
    with open(output_file, "w", encoding="utf-8") as sql_file:
        sql_file.writelines(data_inserts)

    log_message(f"Dane zapisane do {output_file}")

# Główna funkcja
def insert_data():
    load_schema_from_sql(FINISHE_SCHEMA_INPUT_SQL)
    data_inserts = analyze_and_extract_data(INPUT_XML)
    save_data_to_sql(data_inserts, DATA_OUTPUT_SQL)



def main():
    create_schema_table()
    filter_schema_finisch_schema_table()
    insert_data()


if __name__ == "__main__":
    main()

