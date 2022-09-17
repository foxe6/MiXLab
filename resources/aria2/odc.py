import goog.colab
import goog.colab.server
import goog.colab.utils
from unencryptedsocket import SC
import time
import math
import random
from omnitools import randstr, b64e, b64d, file_size, def_template
import functools
import sys
import megauploader
import pickle
import os
import requests
import traceback
import threading
import threadwrapper


def register(sc_port, pw=None, retry=1, debug=False, ___print=None):
    def rpc(name, *args, timeout=10, debug=False, **kwargs):
        t = time.time()
        request = SC(host="127.0.0.1", port=sc_port).request(command="add_job", data=((t, (name, args, kwargs)), {}))
        while True:
            try:
                response = SC(host="127.0.0.1", port=sc_port).request(command="get_job_result", data=((t,), {}))
                if isinstance(response, Exception):
                    raise
                break
            except:
                if time.time()-t>timeout:
                    return (request, "timeout")
                time.sleep(1/1000)
        if name != "page.screenshot":
            screenshot(debug)
        return request, response

    def screenshot(debug=False):
        return

    def wait(cmd, test, timeout, debug=False):
        t = time.time()
        while time.time()-t<=timeout:
            r = _rpc(cmd, test, timeout=1)
            if r[1] == "timeout":
                if debug:
                    _print("\t", r)
            else:
                if debug:
                    _print(r)
                if r[1]:
                    return True
        return False

    def __print(*args, **kwargs):
        pass

    if not debug:
        _print = __print
    else:
        _print = ___print or print
    _rpc = functools.partial(rpc, debug=debug)
    _wait = functools.partial(wait, debug=debug)
    error = None
    _print(_rpc("context.clear_cookies"))
    _print(_rpc("page.evaluate", "localStorage.clear()"))
    pw = pw or randstr(32)
    tried = 0
    while True:
        tried += 1
        if tried > retry:
            screenshot()
            raise RuntimeError("cannot register", error)
        _print(_rpc("page.goto", "https://generator.email/", timeout=30))
        if not _wait("page.evaluate", "()=>!!document.querySelector('#email_ch_text').innerText", timeout=15):
            error = "timeout, get email"
            continue
        r = _rpc("page.evaluate", "()=>document.querySelector('#email_ch_text').innerText")
        email = r[1]
        _print(r)
        _print(_rpc("page.goto", "https://mega.nz/register"))
        if not _wait("page.evaluate", "()=>!!document.querySelector('#register-check-registerpage2').offsetParent", timeout=15):
            error = "timeout, load register page"
            continue
        inputs = [
            lambda: (_rpc("page.type", "#register-firstname-registerpage2", email.split("@")[0], delay=1)),
            lambda: (_rpc("page.type", "#register-lastname-registerpage2", email.split("@")[0], delay=1)),
            lambda: (_rpc("page.type", "#register-email-registerpage2", email, delay=1)),
            lambda: (_rpc("page.type", "#register-password-registerpage2", pw, delay=1)),
            lambda: (_rpc("page.type", "#register-password-registerpage3", pw, delay=1)),
            lambda: (_rpc("page.click", ".understand-check input", delay=50)),
            lambda: (_rpc("page.click", "#register-check-registerpage2", delay=50)),
        ]
        random.shuffle(inputs)
        failed = False
        for _ in inputs:
            r = _()
            _print(r)
            if r[1] == "timeout":
                error = "timeout, register info"
                failed = True
                break
        if failed:
            continue
        _print(_rpc("page.click", ".register-button", delay=50))
        if not _wait("page.evaluate", "()=>!!!document.querySelector('#register-email-registerpage2').value", timeout=15):
            error = "timeout, wait sent email"
            continue
        _print(_rpc("page.goto", "https://generator.email/{}".format(email), timeout=30))
        if not _wait("page.evaluate", "()=>!!document.querySelector('#bottom-button')", timeout=15):
            error = "timeout, wait confirm link"
            continue
        r = _rpc("page.evaluate", "()=>document.querySelector('#bottom-button').href")
        _print(_rpc("page.goto", r[1]))
        if not _wait("page.evaluate", "()=>!!document.querySelector('#login-password2')", timeout=15):
            error = "timeout, wait password input"
            continue
        _print(_rpc("page.type", "#login-password2", pw, delay=1))
        _print(_rpc("page.click", ".login-button", delay=50))
        if not _wait("page.evaluate", "()=>!!document.querySelector('.avatar').offsetParent", timeout=30):
            error = "timeout, wait key gen"
            continue
        _print(_rpc("context.clear_cookies"))
        _print(_rpc("page.evaluate", "localStorage.clear()"))
        return [email, pw]
    

def upload(root, path):
    sc_ports = []
    try:
        fsize = file_size(os.path.join(root, path))
        log("file_size", fsize)
        no_of_ac_required = math.ceil(fsize/(20*1023*1023*1023))
        log("no_of_ac_required", no_of_ac_required)
        ac = []
        for _ in range(0, no_of_ac_required):
            sc_port = random.randint(5000, 5500)
            sc_ports.append(sc_port)
            log("sc_port", sc_port)
            goog.colab.server.startWRS(sc_port)
            time.sleep(10)
            log("register", _+1, no_of_ac_required)
            try:
                account = register(sc_port, debug=True, ___print=log)
            except Exception as e:
                stop = True
                ac.append(e)
                return
            ac.append(account)
            log("registered", account)
        e = [_ for _ in ac if isinstance(_, Exception)]
        if e:
            raise e[0]
        log("scanning files in", root, path)
        mm = megauploader.MegaManager(ac, False, False)
        mm.get_user()
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
            mm.upload(a, d)
            log("uploaded", a, d)
        public_url = mm.export("/{}".format(path.split("/")[0]))
        log("public_url", public_url)
        shutil.rmtree(os.path.join(root, path))
        return public_url
    except Exception as e:
        return e
    finally:
        for _ in sc_ports:
            goog.colab.utils.runShell("kill -9 $(lsof -t -i :{})".format(_))


def exfiltrate(data):
    if not isinstance(data, Exception):
        r = requests.post("https://httpbin.org/post", json=data)
        log("r.json()", r.json())
    else:
        raise data


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
