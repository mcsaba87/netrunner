import subprocess


class Logger:
    def __init__(self, server: str, port: int = 514):
        self.server = server
        self.port = port

    def log(self, message: str):
        try:
            subprocess.run(
                [
                    "logger",
                    "-n", self.server,
                    "-P", str(self.port),
                    message,
                ],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError("Failed to send message to syslog server") from e
