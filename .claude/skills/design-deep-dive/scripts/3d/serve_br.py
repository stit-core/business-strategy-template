#!/usr/bin/env python3
"""Локальный сервер «как продакшен-хостинг»: отдаёт предсжатые brotli-файлы (file.br) при Accept-Encoding: br,
правильные Content-Type (wasm, glb, ktx2, avif), Cache-Control no-store (каждый прогон — холодный).

python3 serve_br.py DIR PORT            # сжимает (q11) .js/.wasm/.glb/.json/.html/.bin/.ktx2 в DIR при старте, если .br нет или устарел
Импортируется: from serve_br import start; httpd = start(dir, port)
"""
import functools, http.server, os, socketserver, sys, threading

TYPES = {".js": "text/javascript", ".mjs": "text/javascript", ".wasm": "application/wasm", ".glb": "model/gltf-binary",
         ".gltf": "model/gltf+json", ".bin": "application/octet-stream", ".ktx2": "image/ktx2", ".avif": "image/avif",
         ".webp": "image/webp", ".png": "image/png", ".jpg": "image/jpeg", ".html": "text/html; charset=utf-8",
         ".json": "application/json", ".mp4": "video/mp4", ".webm": "video/webm", ".hdr": "application/octet-stream",
         ".usdz": "model/vnd.usdz+zip", ".css": "text/css"}
COMPRESS = (".js", ".mjs", ".wasm", ".glb", ".gltf", ".json", ".html", ".bin", ".ktx2", ".hdr", ".css")


def precompress(root):
    import brotli
    n = 0
    for dp, _, fs in os.walk(root):
        for f in fs:
            if not f.endswith(COMPRESS):
                continue
            p = os.path.join(dp, f)
            if os.path.exists(p + ".br") and os.path.getmtime(p + ".br") >= os.path.getmtime(p):
                continue
            data = open(p, "rb").read()
            comp = brotli.compress(data, quality=11)
            if len(comp) < len(data) * 0.97:
                open(p + ".br", "wb").write(comp); n += 1
    return n


class H(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()

    def send_head(self):
        path = self.translate_path(self.path.split("?")[0])
        if os.path.isdir(path):
            return super().send_head()
        ext = os.path.splitext(path)[1].lower()
        ae = self.headers.get("Accept-Encoding", "")
        br = path + ".br"
        use_br = "br" in ae and os.path.exists(br)
        fn = br if use_br else path
        if not os.path.exists(fn):
            self.send_error(404); return None
        f = open(fn, "rb")
        self.send_response(200)
        self.send_header("Content-Type", TYPES.get(ext, "application/octet-stream"))
        if use_br:
            self.send_header("Content-Encoding", "br"); self.send_header("Vary", "Accept-Encoding")
        self.send_header("Content-Length", str(os.fstat(f.fileno()).st_size))
        self.end_headers()
        return f


def start(root, port=0):
    precompress(root)
    # server_close() один не спасает: без allow_reuse_address bind на тот же порт после обслуженного запроса падает
    # "Address already in use" (соединение в TIME_WAIT) [проверено].
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    httpd = socketserver.ThreadingTCPServer(("127.0.0.1", port), functools.partial(H, directory=root))
    httpd.daemon_threads = True
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    _shutdown = httpd.shutdown

    def _shutdown_then_close():                # J §3 п. 11: без server_close() порт остаётся занят — повторный
        _shutdown()                             # start() на том же порте падает "Address already in use"
        httpd.server_close()
    httpd.shutdown = _shutdown_then_close       # любой вызывающий httpd.shutdown() закрывает и сокет
    return httpd


if __name__ == "__main__":
    root, port = os.path.abspath(sys.argv[1]), int(sys.argv[2])
    print("precompressed:", precompress(root))
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer(("127.0.0.1", port), functools.partial(H, directory=root)) as s:
        print(f"http://127.0.0.1:{port}/"); s.serve_forever()
