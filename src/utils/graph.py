import re
import json5
import nest


# don't know who claude stole this from but thank you
def parse_function_args(arg_string):
    # Remove comments if any
    arg_string = arg_string.split("#")[0]
    # Remove leading and trailing parentheses, whitespace and newline
    arg_string = "".join(arg_string.strip()[1:-1].strip().split())

    args = []
    current_arg = ""
    bracket_count = 0
    in_quotes = False
    quote_char = None

    for char in arg_string:
        if char in "\"'" and not in_quotes:
            in_quotes = True
            quote_char = char
            current_arg += char
        elif char == quote_char and in_quotes:
            in_quotes = False
            current_arg += char
        elif char in "({[":
            bracket_count += 1
            current_arg += char
        elif char in ")}]":
            bracket_count -= 1
            current_arg += char
        elif char == "," and bracket_count == 0 and not in_quotes:
            args.append(current_arg.strip())
            current_arg = ""
        else:
            current_arg += char

    if current_arg:
        args.append(current_arg.strip())

    # Remove keywords from keyword arguments
    args = [arg.split("=")[-1].strip() if "=" in arg else arg for arg in args]

    # Pad the list with None to always have 5 elements
    args.extend([None] * (5 - len(args)))

    return args[:5]


def fill_with_params(p: str, params: dict):
    patt = re.compile(r"P\.([^{,|}]*)")
    matches = patt.findall(p)
    for match in matches:
        # print(f"matches: {matches}")
        par = params
        for i in match.split("."):
            par = par[i]
        p = p.replace("P." + match, str(par))
    return json5.loads(p)


def generate_flow_chart(networkdef: str, params):
    connect_calls = networkdef.split("fakeConnect")[1:]
    output = """
```mermaid
flowchart BT\n
"""
    for call in connect_calls:
        if "rec" in call:
            continue
        [src, dst, conn_type, syn_spec, num_sources] = parse_function_args(call)
        if syn_spec is not None:
            syn_spec = fill_with_params(syn_spec, params)
            syn_spec = "<br>".join("{}: {}".format(k, v) for k, v in syn_spec.items())
        if num_sources is not None:
            num_sources = fill_with_params(num_sources, params)
        output += f"    {src} -->|{syn_spec}| {dst}\n"
    return output + "```"
