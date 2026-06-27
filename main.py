from backend.database import init_db
from ui.app import MiauBoxApp


def main():
    init_db()
    app = MiauBoxApp()
    app.run()


if __name__ == "__main__":
    main()
