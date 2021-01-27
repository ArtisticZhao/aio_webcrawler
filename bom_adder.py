# coding: utf-8
import os
import codecs


def get_all_file(path):
    g = os.walk(path)
    files = []
    for _, _, files_list in g:
        for file_name in files_list:
            files.append(os.path.join(path, file_name))
    return files


def add_bom(path):
    (dir, filename) = os.path.split(path)
    f = open(path, 'r')
    content = f.read()
    f.close()
    f = codecs.open('doc_bom/{}'.format(filename), 'w', 'utf_8_sig')
    f.write(content)
    f.close()


if __name__ == "__main__":
    files = get_all_file('doc')
    for each in files:
        add_bom(each)

