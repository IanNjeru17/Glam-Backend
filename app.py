from app import create_app, db

app = create_app()

# Create database tables before the first request
@app.before_first_request
def initialize_database():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
