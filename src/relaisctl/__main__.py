import logging
from logging.handlers import RotatingFileHandler
import argparse
from pathlib import Path

from relaisctl.xsense import XsenseMqtt
from relaisctl.gpio import ZeroRelay

try:
    import tomllib as toml
except ImportError:
    import tomli as toml

logger = logging.getLogger(__package__)


def run(config_path: Path) -> None:
    try:
        with config_path.open("rb") as f:
            conf = toml.load(f)
    except FileNotFoundError:
        conf = {}
        config_path.touch(mode=0o644)
        logger.warning("Config file at '%s' not found! Created new file.", config_path)

    mqtt_conf = conf.get("mqtt", {})
    station_conf = conf.get("station", [])

    host = mqtt_conf.get("host", "localhost")
    port = mqtt_conf.get("port", 1883)
    username = mqtt_conf.get("username")
    password = mqtt_conf.get("password")

    try:
        stations = {}
        for s in station_conf:
            stations[s["id"]] = {
                "r1": s.get("r1", False),
                "r2": s.get("r2", False),
            }
            logger.info(
                "Found station '%s': R1=%s, R2=%s",
                s["id"],
                "active" if stations[s["id"]]["r1"] else "inactive",
                "active" if stations[s["id"]]["r2"] else "inactive",
            )
    except KeyError:
        logger.error("Invalid station configuration!")
        raise

    xsense = XsenseMqtt(
        host=host,
        port=port,
        username=username,
        password=password,
        stations=list(stations.keys()),
    )

    relais_one = ZeroRelay(1)
    relais_two = ZeroRelay(2)

    def on_detect(detected_station: str) -> None:
        if detected_station in stations.keys():
            if stations[detected_station]["r1"]:
                relais_one.on()
                logger.info("Relais 1 opened!")
            if stations[detected_station]["r2"]:
                relais_two.on()
                logger.info("Relais 2 opened!")

    def on_clear(detected_station: str) -> None:
        if detected_station in stations.keys():
            if stations[detected_station]["r1"]:
                relais_one.off()
                logger.info("Relais 1 closed!")
            if stations[detected_station]["r2"]:
                relais_two.off()
                logger.info("Relais 2 closed!")

    xsense.on_detect = on_detect
    xsense.on_clear = on_clear

    logger.info("Start listening for MQTT messages...")
    xsense.listen()

def cli() -> None:
    arg_parser = argparse.ArgumentParser(
        prog="relaisctl", description="Control a Raspberry Pi Relais via MQTT."
    )

    arg_parser.add_argument(
        "-c",
        "--config",
        required=False,
        default="config.toml",
        help="Path to the TOML config file",
        type=Path
    )

    arg_parser.add_argument(
        "--debug",
        required=False,
        help="Toggle debug mode",
        action="store_true",
    )

    args = arg_parser.parse_args()

    logging.basicConfig(
        format="%(asctime)s | %(levelname)-8s | %(message)s",
        level=logging.DEBUG if args.debug else logging.INFO,
        handlers=[
            logging.StreamHandler(),
            RotatingFileHandler(
                filename="/var/log/relaisctl.log",
                maxBytes=10_485_760,
                backupCount=5
            ),
        ],
    )

    run(config_path=args.config)


if __name__ == "__main__":
    cli()
