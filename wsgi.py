from config import DevelopConfig
from fhirserver import create_app, DEVELOPMENT

app = create_app(DEVELOPMENT)

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)