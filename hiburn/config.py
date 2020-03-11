
import copy
import json
from . import utils


# -------------------------------------------------------------------------------------------------
def _update_config_by_args(config, args, prefix=""):
    for k, v in config.items():
        arg_name = prefix + k.replace("-", "_")

        if isinstance(v, dict):
            _update_config_by_args(v, args, arg_name + "_")
            continue

        arg_val = args.get(arg_name)
        if arg_val is not None:
            config[k] = arg_val


# -------------------------------------------------------------------------------------------------
def _add_args_from_config_desc(parser, config_desc, prefix="--"):
    for key, val in config_desc.items():
        arg_name = prefix + key

        if isinstance(val, dict):
            _add_args_from_config_desc(parser, val, arg_name + "-")
            continue

        if isinstance(val, tuple):  # tuple contains: value, type, help
            parser.add_argument(arg_name, type=val[1], default=val[0], metavar="V",
                help="{}, default: {}".format(val[2], val[0]))
        else:
            t = utils.str2bool if isinstance(val, bool) else type(val)
            parser.add_argument(arg_name, type=t, default=val, metavar="V",
                help="{}, default: {}".format(type(val).__name__, val))


# -------------------------------------------------------------------------------------------------
def _update_config(config, src, path=""):
    for key, new_val in src.items():
        orig_val = config.get()
        if type(new_val) is not type(orig_val):
            raise TypeError(
                "Config value at '{}/{}' has inappropriate typ '{}' but expected '{}'".format(
                    path, key, type(new_val), type(orig_val)
                ))
        if isinstance(new_val, dict):
            _update_config(orig_val, new_val, "{}/{}".format(path, key))
        else:
            config[k] = new_val


# -------------------------------------------------------------------------------------------------
def _create_config_from_desc(config_desc):
    res = {}
    for key, val in config_desc.items():
        if isinstance(val, tuple):  # tuple contains: value, type, help
            res[key] = val[0]
        elif isinstance(val, dict):
            res[key] = _create_config_from_desc(val)
        else:
            res[key] = val
    return res


# -------------------------------------------------------------------------------------------------
def add_arguments_from_config_desc(parser, config_desc, read_from_file=False):
    parser.add_argument("--config", "-C", type=str, metavar="PATH", help="Config path")
    _add_args_from_config_desc(parser, config_desc)


# -------------------------------------------------------------------------------------------------
def get_config_from_args(args, config_desc):
    config = _create_config_from_desc(config_desc)

    if args.config is not None:
        with open(args.config, "r") as f:
            user_config = json.load(f)
        _update_config(config, user_config)

    _update_config_by_args(config, vars(args))
    
    return config
