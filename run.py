from app import create_app, db



# Создание приложения
app = create_app()

with app.app_context():
    db.create_all()

# Команда для запуска приложения
if __name__ == '__main__':
    app.run(debug=True, port=5000)
