import argparse
from tchat.menu import MessengerApp


def main():
    parser = argparse.ArgumentParser(
        description="TChat - A Messenger Client Application"
    )
    parser.add_argument(
        "--session",
        required=False,
        help="Specify the file path to save session credentials. Example: /path/to/file.json",
        default=None,
    )
    parser.add_argument("--ip", required=False, help="Server IP", default="localhost")
    parser.add_argument("--port", required=False, help="Server Port", default=10443)

    args = parser.parse_args()

    app = MessengerApp(session_file=args.session, ip=args.ip, port=args.port)
    app.run()


if __name__ == "__main__":
    main()
