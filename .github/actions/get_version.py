import sys
import configparser


def main():
    with open("./pyecotrend_ista/const.py") as f:
        config_string = "[dummy_section]\n" + f.read()
        config = configparser.ConfigParser(allow_no_value=True)
        config.read_string(config_string)
        print(config["dummy_section"]["VERSION"].strip('"'))
    return 0


if __name__ == "__main__":
    sys.exit(main())
