from json import load
from server.backend import Backend_Api
from server.website import Website
from server.app import app
import webbrowser
import threading


def open_browser():
    webbrowser.open_new('http://127.0.0.1:8888/')


if __name__ == '__main__':
    print("******************************************************************")

    config = load(open('config.json', 'r', encoding='utf-8'))
    site_config = config['site_config']
    site_config['debug'] = True  # 设置 debug 模式

    site = Website(app)
    for route in site.routes:
        app.add_url_rule(
            route,
            view_func=site.routes[route]['function'],
            methods=site.routes[route]['methods'],
        )

    backend_api = Backend_Api(app, config)
    for route in backend_api.routes:
        app.add_url_rule(
            route,
            view_func=backend_api.routes[route]['function'],
            methods=backend_api.routes[route]['methods'],
        )

    print(f"Running on port {site_config['port']}")
    app.run(**site_config)
    print(f"Closing port {site_config['port']}")
    threading.Timer(2.0, open_browser).start()
