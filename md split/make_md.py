import os
import helpers
import docx

def create_md_files(doc_file):
    # Set the initial start index to 0
    start_index = 0

    # Open the Word document
    doc = docx.Document(doc_file)
    counter = 0
    # Loop through all occurrences of <start_text> in the document
    while True:
        # Find the next occurrence of <start_text> starting from the current start index
        start_index = helpers.find_start_text_index(doc_file,start_index)

        # If no more occurrences of <start_text> are found, exit the loop
        if start_index is None:
            break

        # Get the placename from the two lines above <start_text>
        placename = helpers.get_placename(doc_file, start_index)

        # Find the index of the paragraph containing <end_text> after the start index
        end_index = helpers.find_end_text_index(doc_file, start_index)

        # Get the placename ID from the paragraph containing <end_text>
        placename_id = helpers.get_placename_id(doc_file, end_index)

        # Create the filename for the new Markdown file
        filename = os.path.join(output, placename + "." + placename_id + "." + "5.md")

        # Get the entry text between <start_text> and <end_text>
        entry_text = helpers.get_entry_text(doc_file, start_index, end_index)

        # Create the new Markdown file with the entry text and filename
        with open(filename, "w", encoding='utf-8') as f:
            f.write(entry_text)
        counter += 1
        #set number of entries you want to grab
    return 

word_document = r'C:\Users\lroyte\Documents\Bucket_Connect_Welikia\book\a Welikia Atlas\3 - gazetteer\Eric Himmel edits\bronx-gazetteer-entries_2022-11-02_EH edit-ews Changes Accepted.docx'
output = r'C:\Users\lroyte\Documents\Bucket_Connect_Welikia\book\a Welikia Atlas\3 - gazetteer\fifth draft entries\bronx\\'

create_md_files(word_document)