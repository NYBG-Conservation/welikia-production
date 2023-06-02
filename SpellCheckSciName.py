"""

A script to spell check scientific names in entries against placename entry titles


Author: Lucinda Royte
Date: 10.13.23

"""


import os
import re
import csv

def find_italic_phrases(directory_path):
	"""
	Returns a list of italic phrases from markdown files in a single directory

	Italic phrases must be surrounded by parenthesies and asterics i.e. (*Test test*)
	
	"""
    italic_phrases_filename = []

    # Loop through all .md files in the directory
    for filename in os.listdir(directory_path):
        if filename.endswith(".md"):
            with open(os.path.join(directory_path, filename), 'r') as f:
                # Read the contents of the file into a string
                file_contents = f.read()
                # Find all italic phrases in the file
                phrases = re.findall(r'\(\*([^*\n]+)\*\)', file_contents)
                
                # Add the phrases and filenames to the list
                for phrase in phrases:
                    italic_phrases_filename.append([phrase,filename])
    return italic_phrases_filename
italic_phrases_filename = find_italic_phrases('/Users/lucindaroyte/Documents/Work/Welikia_Script/second_draft_bk_10132023')


def write_italic_phrases_to_csv(italic_phrases_filename, csv_file):
    with open(csv_file, 'w', newline='') as f:
        writer = csv.writer(f)
        
        # Write the header row
        writer.writerow(['italic_phrase', 'filename'])
        
        # Write the data
        for row in italic_phrases_filename:
            writer.writerow(row)

    return csv_file
# Example usage
italic_phrases_csv_maker = write_italic_phrases_to_csv(italic_phrases_filename, '/Users/lucindaroyte/Documents/Work/Welikia_Script/SpellCheckSciName/italic_phrases.csv')



import csv

def check_italic_phrases(italic_phrases_csv, sci_names_csv):
    sci_names = {}
    with open(sci_names_csv, 'r') as f:
        reader = csv.reader(f)
        header = next(reader)
        index_of_complete_names = header.index("complete_name")
        for row in reader:
            sci_names[row[index_of_complete_names]] = row[1:]

    missing_names = []
    sci_names_entries = []
    with open(italic_phrases_csv, 'r') as f:
        reader = csv.reader(f)
        header = next(reader)
        index_of_italic_phrase = header.index("italic_phrase")
        index_of_filename = header.index("filename")
        for row in reader:
            italic_phrase = row[index_of_italic_phrase]
            filename = row[index_of_filename]
            if italic_phrase in sci_names:
                sci_names_entries.append([italic_phrase, filename])
            else:
                missing_names.append([italic_phrase, filename])
    
    with open('sci_names_entries.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['italic_phrase', 'filename'])
        writer.writerows(sci_names_entries)
    
    with open('missing_names.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['italic_phrase', 'filename'])
        writer.writerows(missing_names)

check_italic_phrases(italic_phrases_csv_maker, '/Users/lucindaroyte/Documents/Work/Welikia_Script/SpellCheckSciName/COI_sci_name.csv')




