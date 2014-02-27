from urlparse import urlparse
from os.path import splitext, basename

# adapted from http://stackoverflow.com/questions/10552188/python-split-url-to-find-image-name-and-extension
def get_filename_and_ext_from_url(url):
    filename, file_ext = splitext(get_full_filename_from_url(url))
    return filename, file_ext

def get_full_filename_from_url(url):
    return basename(urlparse(url).path)