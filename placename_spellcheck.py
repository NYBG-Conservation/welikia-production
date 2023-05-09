"""

A script to spell check placenames in entries against placename entry titles


Author: Lucinda Royte
Date: 10.13.23

"""

import csv
import os
import re
from difflib import get_close_matches

names_count_dict = {}

# step 1: create a dictionary where canonical placename names are key and value is 0

# Open the placename CSV file 
with open('/Users/lucindaroyte/Documents/Welikia_Script/canonical_placenames_01132023.csv', 'r') as file:
    reader = csv.DictReader(file)

    # Iterate through the rows of the CSV
    for row in reader:
        name = row["Name"].replace("[", "").replace("]", "")
        names_count_dict[name] = 0

# step 2: create CSV to store words not matched to a placename name
with open("not_found_words.csv", "w", newline="") as f:
    writer = csv.writer(f)
    # Write the column headers
    writer.writerow(["emboldened word", "filename", "closest match"])

# step 3: Iterate through all markdown files in the directory
for filename in os.listdir("/Users/lucindaroyte/Documents/Welikia_Script/second_draft_bk_10132023"):
    if filename.endswith(".md"):
        with open("/Users/lucindaroyte/Documents/Welikia_Script/second_draft_bk_10132023/" + filename, "r") as file:
            content = file.read()

            # step 4: Use regular expression to find all emboldened words
            emboldened_words = re.findall(r'\*\*(.+?)\*\*', content)
            for word in emboldened_words:
                if word in names_count_dict:
                    names_count_dict[word] += 1
                else:
                    # step 5: open not found csv in append mode, append unmatched words and assign a close match filename
                    with open("not_found_words.csv", "a", newline="") as f:
                        writer = csv.writer(f)
                        # Get the closest match from data dict
                        closest_match = get_close_matches(word, names_count_dict.keys(), n=1, cutoff=0.8)
                        # Write the word, file name, closest match to the "not found" column
                        writer.writerow([word, filename, closest_match[0] if closest_match else "N/A"])

# step 6: write the data dictionary to a csv file that counts emboldened words that match placename names
with open("/Users/lucindaroyte/Documents/Welikia_Script/SpellCheckEntries/names_count_dict.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["word", "count"])
    for key, value in names_count_dict.items():
        writer.writerow([key, value])
