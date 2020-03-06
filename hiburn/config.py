
import copy
import json


def _update_config_by_args(config, args, prefix=""):
    for k, v in config.items():
        arg_name = prefix + k.replace("-", "_")

        if isinstance(v, dict):
            _update_config_by_args(v, args, arg_name + "_")
            continue

        arg_val = args.get(arg_name)
        if arg_val is None:
            continue

        if isinstance(v, bool):
            config[k] = arg_val.upper() == "Y"
        else:
            config[k] = arg_val


def _add_args_from_config(parser, config, prefix="--"):
    for k, v in config.items():
        arg_name = prefix + k
        if isinstance(v, dict):
            _add_args_from_config(parser, v, arg_name + "-")
        elif isinstance(v, bool):
            sv = "Y" if v else "N"
            parser.add_argument(arg_name, type=str, metavar="Y|N", help="default: {}".format(sv), default=sv)
        else:
            parser.add_argument(arg_name, type=type(v), metavar="VAL", help="default: {}".format(v), default=v)


def add_arguments_from_config(parser, default_config):
    parser.add_argument("--config", "-C", type=str, metavar="PATH", help="Config path")
    _add_args_from_config(parser, default_config)


def get_config_from_args(args, default_config):
    config = copy.deepcopy(default_config)

    if args.config is not None:
        with open(args.config, "r") as f:
            user_config = json.load(f)
        config.update(user_config)

    _update_config_by_args(config, vars(args))

    return config
