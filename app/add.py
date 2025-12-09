from base import app, db, User

def add_user(rf_id: int, password: str, balance: int = 0) -> bool:
    with app.app_context():
        if User.query.filter_by(rf_id=rf_id).first():
            print(f"Пользователь с rf_id={rf_id} уже существует.")
            return False
        user = User(rf_id=rf_id, password=password, balance=balance)
        db.session.add(user)
        db.session.commit()
        print(f"Пользователь {rf_id} добавлен (баланс: {balance}).")
        return True

def add_users_bulk(users_data):
    with app.app_context():
        added = 0
        for item in users_data:
            if len(item) == 2:
                rf_id, pwd = item
                bal = 0
            elif len(item) == 3:
                rf_id, pwd, bal = item
            else:
                print(f"Неверный формат данных: {item}")
                continue

            if not User.query.filter_by(rf_id=rf_id).first():
                user = User(rf_id=rf_id, password=pwd, balance=bal)
                db.session.add(user)
                added += 1
        db.session.commit()
        print(f"Добавлено {added} новых пользователей.")

def delete_user_by_rf_id(rf_id: int) -> bool:
    with app.app_context():
        user = User.query.filter_by(rf_id=rf_id).first()
        if user:
            db.session.delete(user)
            db.session.commit()
            print(f"Пользователь с rf_id={rf_id} удалён.")
            return True
        else:
            print(f"Пользователь с rf_id={rf_id} не найден.")
            return False


if __name__ == '__main__':
    users_data = [
        (5001, "pass123", 100),
        (5002, "qwerty30", 250),
        (5003, "admin777", 0)
    ]
