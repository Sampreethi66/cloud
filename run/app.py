from flask import Flask
from routes.core_routes import core_blueprint
from routes.notebook_runner import notebook_blueprint

app = Flask(__name__)
app.register_blueprint(core_blueprint)
app.register_blueprint(notebook_blueprint)

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 8100))
    app.run(host='0.0.0.0', port=port, debug=True)
