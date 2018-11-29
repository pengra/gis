import io
import requests
import zipfile

# For LOGGER
VERBOSE = False

def download_file(url):
    local_filename = url.split('/')[-1]
    # NOTE the stream=True parameter
    r = requests.get(url, stream=True)
    with io.open(local_filename, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024): 
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)
    return local_filename


def unzip(filename, dirname):
    zip_ref = zipfile.ZipFile(filename, 'r')
    zip_ref.extractall(dirname + "/")
    zip_ref.close()

def log(*args, **kwargs):
    if VERBOSE:
        print('[!]', *args, **kwargs)