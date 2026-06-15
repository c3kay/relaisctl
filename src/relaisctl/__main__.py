import logging
import argparse
from pathlib import Path

from relaisctl.xsense import XsenseMqtt

try:
    import tomllib as toml
except ImportError:
    import tomli as toml

logger = logging.getLogger(__package__)


def run(config_path: Path) -> None:
    with config_path.open("rb") as f:
        conf = toml.load(f)

    conf_mqtt = conf.get("mqtt", {})
    host = conf_mqtt.get("host", "localhost")
    port = conf_mqtt.get("port", 1883)
    username = conf_mqtt.get("username")
    password = conf_mqtt.get("password")
    stations = conf_mqtt.get("stations")

    XsenseMqtt(
        host=host,
        port=port,
        username=username,
        password=password,
        stations=stations,
    ).listen()

def cli() -> None:
    arg_parser = argparse.ArgumentParser(
        prog="relaisctl", description="Control a Raspberry Pi Relais."
    )

    arg_parser.add_argument(
        "-c",
        "--config-path",
        required=False,
        default="config.toml",
        help="Path to the TOML config file",
        type=Path
    )

    arg_parser.add_argument(
        "-l",
        "--log-path",
        required=False,
        default=None,
        help="Path to the written log file",
        type=Path,
    )

    args = arg_parser.parse_args()

    logging.basicConfig(
        filename=args.log_path,
        filemode="a",
        format="%(asctime)s | %(levelname)-8s | %(message)s",
        level=logging.DEBUG,
    )

    run(config_path=args.config_path)


if __name__ == "__main__":
    cli()
