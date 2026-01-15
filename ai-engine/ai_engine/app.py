import os
from flask import Flask

from ai_engine.routes.generation import generation_bp
from ai_engine.routes.screens import screens_bp



def create_app() -> Flask:
    app = Flask(__name__)

    # register blueprints
    app.register_blueprint(generation_bp)
    app.register_blueprint(screens_bp)

    return app


def run() -> None:
    app = create_app()
    host = os.getenv('AI_ENGINE_HOST', '0.0.0.0')
    port = int(os.getenv('AI_ENGINE_PORT', '5005'))
    print(f"AI Engine running on {host}:{port}")
    app.run(host=host, port=port)
    


if __name__ == '__main__':
    run()
