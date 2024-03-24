import re
import configparser

def extract_pubids(filename):
    pubids = []
    with open(filename, 'r') as file:
        for line in file:
            # Extract numerical digits from the line
            digits = re.findall(r'\d+', line)
            if digits:
                # Convert the digits into a comma-separated value string
                pubid = ','.join(digits)
                pubids.append(pubid)
    return pubids

def write_to_config(pubids, config_filename):
    config = configparser.ConfigParser()
    # Read existing config file if it exists
    config.read(config_filename)

    # Check if [yearinreview] section exists, create if not
    if 'yearinreview' not in config:
        config['yearinreview'] = {}

    # Write pubidsetting value to the [yearinreview] section
    config['yearinreview']['pubidsetting'] = ','.join(pubids)

    # Write the updated config file
    with open(config_filename, 'w') as configfile:
        config.write(configfile)

def main():
    pubids = extract_pubids('pubids.txt')
    if pubids:
        write_to_config(pubids, 'config.ini')
        print('pubidsetting values have been successfully written to config.ini.')
    else:
        print('No valid pubid values found in pubids.txt.')

if __name__ == "__main__":
    main()
