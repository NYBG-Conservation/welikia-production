# increment_md.py

# import
import os
import shutil

# change these directories as needed
from_dir = r'C:\_data\book\a Welikia Atlas\3 - gazetteer\second draft entries\brooklyn'
to_dir = r'C:\_data\book\a Welikia Atlas\3 - gazetteer\third draft entries\brooklyn'
old_num = '2'
new_num = '3'

for f in os.listdir(from_dir):

    # get filename parts
    base = os.path.basename(f)
    parts = base.split('.')
    if parts[2] == old_num:
        parts[2] = new_num
    else:
        print (base, " not changed")
    # assign name new name
    new_base = '.'.join(parts)
    new_f = os.path.join(to_dir, new_base)
    # copy then change name unless file already exists
    if os.path.isfile(new_f):
        print(new_f, "exists, so not overwriting")
        continue
    else:
        old_f_from_dir = os.path.join(from_dir, base)
        shutil.copy(old_f_from_dir,to_dir)
        old_f_to_dir = os.path.join(to_dir, base)
        os.rename(old_f_to_dir, new_f)

	