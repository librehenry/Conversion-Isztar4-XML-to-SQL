Conversion-Isztar4-XML-to-SQL
# XML to SQL Converter for Isztar4 Tariff Data

## Opis
Ten projekt zawiera skrypty do konwersji danych taryfy celnej z projektu **Isztar4** z formatu XML do SQL. Skrypt generuje strukturę bazy danych oraz plik `.sql` zawierający polecenia `INSERT`, umożliwiające załadowanie danych do dowolnej bazy PostgreSQL.

## Wymagania
- **Python 3.x**
- **PostgreSQL**
- **Moduły Python:**  
  - `lxml`
  - `psutil`

Można je zainstalować za pomocą:
```sh
pip install lxml psutil


Pliki

    Converter_XML_to_SQL.py – skrypt do analizy struktury XML, generowania schematu SQL i generowania INSERT INTO
    data_extractor.py – skrypt do przetwarzania XML i generowania INSERT INTO
    schema_output.sql – wygenerowany schemat tabel w SQL
    data_output.sql – plik zawierający dane do zaimportowania

Jak używać?
1. Generowanie schematu bazy danych

python schema_generator.py

To utworzy plik filtered_schema_output.sql, który zawiera definicje tabel.
2. Konwersja danych XML do SQL

python data_extractor.py

Wygenerowany plik data_output.sql można następnie załadować do PostgreSQL.
3. Importowanie do PostgreSQL

Po utworzeniu bazy danych, np.:

CREATE DATABASE isztar4;

Można załadować dane:

psql -U postgres -d isztar4 -f filtered_schema_output.sql
psql -U postgres -d isztar4 -f data_output.sql

Źródło danych

Dane taryfy celnej pochodzą z projektu Isztar4 i są publicznie dostępne na stronie:
🔗 https://ext-isztar4.mf.gov.pl/taryfa_celna/XmlExtractions?lang=PL&date=20250219# 
