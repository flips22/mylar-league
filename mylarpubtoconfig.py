import sqlite3
import configparser
import os

# Function to read the database path from config.ini or configPRIVATE.ini
def read_database_path(config_ini_path):
    if os.path.exists(config_ini_path):
        config = configparser.ConfigParser()
        config.read(config_ini_path)
        if 'mylar' in config and 'mylardb' in config['mylar']:
            return config['mylar']['mylardb']
    return None

# Function to update both config files with the database path
def update_config_files(database_path):
    if os.path.exists('configPRIVATE.ini'):
        config_files = ['config.ini', 'configPRIVATE.ini']
    else:
        config_files = ['config.ini']

    for config_file in config_files:
        config = configparser.ConfigParser()
        config.read(config_file)
        if 'mylar' not in config:
            config['mylar'] = {}
        config['mylar']['mylardb'] = database_path
        with open(config_file, 'w') as file:
            config.write(file)

# Function to read unique values from a column in SQLite database
def read_unique_values_from_database(database_path, column_name):
    connection = sqlite3.connect(database_path)
    cursor = connection.cursor()

    query = f"SELECT DISTINCT {column_name} FROM comics"
    cursor.execute(query)
    unique_values = [row[0] for row in cursor.fetchall()]

    connection.close()

    return unique_values

# Function to write unique values to a text file
def write_to_text_file(values, file_path):
    with open(file_path, 'w') as file:
        for value in values:
            file.write(value + '\n')

# Function to match values from two text files and prepend numerical values
def match_and_prepend_values(pubids_file_path, mylar_publishers_file_path):
    matched_values = []
    with open(pubids_file_path, 'r') as pubids_file:
        pubids = pubids_file.readlines()
        for line in pubids:
            pub_id, publisher = line.strip().split(' ', 1)
            matched_values.append(pub_id + ' ' + publisher)

    with open(mylar_publishers_file_path, 'r') as mylar_publishers_file:
        mylar_publishers = mylar_publishers_file.readlines()
        updated_publishers = []
        for publisher in mylar_publishers:
            publisher = publisher.strip()
            for matched_value in matched_values:
                if publisher == matched_value.split(' ', 1)[1]:
                    updated_publishers.append(matched_value)
                    break

    # Write updated publishers back to the file
    with open(mylar_publishers_file_path, 'w') as output_file:
        for updated_publisher in updated_publishers:
            output_file.write(updated_publisher + '\n')

# Function to parse numerical values and write back to config.ini
def parse_and_write_to_config_ini(mylar_publishers_file_path, config_ini_path):
    with open(mylar_publishers_file_path, 'r') as mylar_publishers_file:
        publishers = mylar_publishers_file.readlines()
        pub_ids = [publisher.split(' ', 1)[0] for publisher in publishers]

    config = configparser.ConfigParser()
    config.read(config_ini_path)
    config['yearinreview']['pubidsetting'] = ','.join(pub_ids)

    with open(config_ini_path, 'w') as config_file:
        config.write(config_file)

# Main function
def main():
    # Check configPRIVATE.ini first for the database path
    database_path = read_database_path('configPRIVATE.ini')

    # If not found in configPRIVATE.ini, check config.ini
    if not database_path:
        database_path = read_database_path('config.ini')

    update_config_files(database_path)

    # Read unique values from database and write to text file
    unique_values = read_unique_values_from_database(database_path, 'ComicPublisher')
    mylar_publishers_file = 'mylarpublishers.txt'
    write_to_text_file(unique_values, mylar_publishers_file)

    # Match values from two text files and prepend numerical values
    pubids_file_path = 'pubidsall.txt'
    match_and_prepend_values(pubids_file_path, mylar_publishers_file)

    # Parse numerical values and write back to config.ini
    parse_and_write_to_config_ini(mylar_publishers_file, 'config.ini')

if __name__ == "__main__":
    main()
