import os
import glob
import numpy as np
import subprocess

from PIL import Image
from PIL import ImageFile

# Fixes "IOError: broken data stream when reading image file"
ImageFile.LOAD_TRUNCATED_IMAGES = True


def list_files(data_dirs):
  '''
  List all images and their labels of a given folder.

  Args:
    - data_dirs: a list to the folders containing the images.
  Returns:
    A tuple containing:
    - A nested list containing the paths to the images.
    - A list of numpy arrays containing the ground-truth labels of each image.
  '''
  corrupted_files = ['data/processed/LivDet2015/Training/GreenBit/Live/019_6_3.png']
  
  files_all = []
  labels_all = []
  for data_dir in data_dirs:
    alldirs = os.walk(data_dir)
    dirs = []
    for i in alldirs:
      dirs.append(i[0] + '/*.tif')
      dirs.append(i[0] + '/*.bmp')
      dirs.append(i[0] + '/*.png')

    files_aux = []     
    for fileglob in dirs:
      files_aux2 = glob.glob(fileglob)
      files_aux2.sort()
      files_aux.extend(files_aux2)  
    files = [file_aux.replace('\\', '/') for file_aux in files_aux if file_aux not in corrupted_files]
    labels = [1 if "live" in file_aux.lower() or "real" in file_aux.lower() else 0 for file_aux in files]
    labels = np.asarray(labels)
    print('Loaded {} ({}/{} real/fake) images from {}'.format(
        len(files),
        (labels == 1).sum(),
        (labels == 0).sum(),
        data_dir))

    files_all.append(files)
    labels_all.append(labels)

  return files_all, labels_all

def pil_loader(path):
  # open path as file to avoid ResourceWarning (https://github.com/python-pillow/Pillow/issues/835)
  with open(path, 'rb') as f:
    img = Image.open(f)
    return img.convert('RGB')

def get_fnmr_op(fmr, fnmr, op):
    """Returns the value of the given FNMR operating point
    Definition:
        fmr: False Match Rates
        fnmr: False Non-Match Rates
        op: Operating point
    returns: Index, The lowest FMR at which the probability of FNMR == op
    """
    temp = abs(fnmr - op)
    min_val = np.min(temp)
    index = np.where(temp == min_val)[0][-1]
    return index, fmr[index]

def get_fmr_op(fmr, fnmr, op):
    """Returns the value of the given FMR operating point
    Definition:
        fmr: False Match Rates
        fnmr: False Non-Match Rates
        op: Operating point
    returns: Index, The lowest FNMR at which the probability of FMR == op
    """
    index = np.argmin(abs(fmr - op))
    return index, fnmr[index]

def get_sha():                                                                  
    cwd = os.path.dirname(os.path.abspath(__file__))

    def _run(command):
        return subprocess.check_output(command, cwd=cwd).decode('ascii').strip()
    sha = 'N/A'
    diff = "clean"
    branch = 'N/A'
    try:
        sha = _run(['git', 'rev-parse', 'HEAD'])
        subprocess.check_output(['git', 'diff'], cwd=cwd)
        diff = _run(['git', 'diff-index', 'HEAD'])
        diff = "has uncommited changes" if diff else "clean"
        branch = _run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'])
    except Exception:
        pass
    message = f"sha: {sha}, status: {diff}, branch: {branch}"
    return message
    