from waitress import serve
from new_main import app

if __name__ == "__main__":
    print("Starting server on port 8080...")
    serve(app, host='0.0.0.0', port=8080, threads=4)
    app.run()