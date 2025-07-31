from dotenv import load_dotenv
load_dotenv()
from flask import Flask, send_from_directory
from routes.core_routes import core_blueprint
from routes.notebook_runner import notebook_blueprint

app = Flask(__name__)
app.register_blueprint(core_blueprint)
app.register_blueprint(notebook_blueprint)

# Serve JS files
@app.route('/js/<path:filename>')
def serve_js(filename):
    return send_from_directory('js', filename)

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 8100))
    app.run(host='0.0.0.0', port=port, debug=True)
