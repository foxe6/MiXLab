#!/usr/bin/python3
import time
from omnitools import file_size
import pixeldrainuploader
import os
import sys
import traceback
import shutil


def upload(root, path):
    try:
        fsize = file_size(os.path.join(root, path))
        log("file_size", fsize)
        ac = [
            "justauser2",
            "justauser2"
        ]
        log("scanning files in", root, path)
        pu = pixeldrainuploader.PixeldrainUploader(ac, verbose=False)
        files = []
        if os.path.isdir(os.path.join(root, path)):
            for a,b,c in os.walk(os.path.join(root, path)):
                for d in c:
                    e = os.path.join(a, d)
                    files.append([root, e.replace(root, "").strip(os.path.sep)])
        else:
            files.append([root, path])
        for a, d in files:
            log("uploading", a, d)
            pu.upload(a, d)
            log("uploaded", a, d)
        shutil.rmtree(os.path.join(root, path))
        return True
    except Exception as e:
        return e


def exfiltrate(data):
    pass


def log(*args):
    w = "{} {}".format(time.time(), " ".join(list(map(str, args))))
    print(w)
    open("/content/on_download_complete.log", "ab").write(w.encode()+b"\\n")


log("start")
try:
    download_id = sys.argv[1]
    num_files = sys.argv[2]
    first_file = sys.argv[3]
    root = "/mnt/goog"
    path = first_file.replace(root, "").strip(os.path.sep)
    exfiltrate(upload(root, path))
except:
    log(traceback.format_exc())
log("end")
