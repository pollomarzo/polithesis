import re
from collections import defaultdict, deque

import graphviz as gv
import json5

dot_template = """
digraph {
    rankdir = "BT"
    subgraph cluster_Left_Hemisphere {
        node [color = gray82; style = filled; ordering = in;];
        color = ivory4;
        style = filled;
<<<LEFT>>>
    }
    subgraph cluster_Right_Hemisphere {
        node [color = gray82; style = filled; ordering = in;];
        color = ivory4;
<<<RIGHT>>>
    }
<<<MIXED>>>
}
"""

invis_subgraph_template = """
        subgraph {
            rank = same;
            edge [style = invis;];
            <<<EDGES>>>
        }
"""


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


def clean_var_name(varname: str):
    varname = varname.replace('"]["', "_")
    for c in ["self.", "pops", "[", "]", '"']:
        varname = varname.replace(c, "")
    return varname


def code_to_edges(networkdef: str, params: dict, connect_fun_name: str):
    "split code into a list of edges"
    connect_calls = networkdef.split(connect_fun_name)[1:]
    output = []
    for call in connect_calls:
        # skip recorders
        if "rec" in call:
            continue

        [src, dst, conn_type, syn_spec, num_sources] = parse_function_args(call)
        # graphviz does not like symbols in names. this would be fixed by enclosing in double quotes
        # i do not want the "self." inside the name label, so i just remove it altogether
        src = clean_var_name(src)
        dst = clean_var_name(dst)
        if syn_spec is not None:
            syn_spec = fill_with_params(syn_spec, params)
        if num_sources is not None:
            num_sources = fill_with_params(num_sources, params)
        output.append([src, dst, conn_type, syn_spec, num_sources])
    return output


def max_distance(graph, src):
    "calculates the maximum distance for for each node from the source"
    max_distances = {}
    queue = deque([(src, 0)])

    while queue:
        node, distance = queue.popleft()
        if node not in max_distances or distance > max_distances[node]:
            max_distances[node] = distance
            for neighbor in graph[node]:
                queue.append((neighbor, distance + 1))
    return max_distances


def print_syn_spec(syn_spec):
    if syn_spec is None:
        return ""
    s = ""
    if "weight" in syn_spec.keys():
        s += f"w:{syn_spec['weight']}"
    if "delay" in syn_spec.keys():
        s += f"\\nd:{syn_spec['delay']}"
    return s


def edge_color_width(syn_spec):
    if syn_spec is None or "weight" not in syn_spec.keys():
        return ""
    weight = syn_spec["weight"]
    w = abs(weight)
    width = 0.5 if w < 1 else 1 if w < 5 else 2 if w < 10 else 3
    return f'color={"indianred3" if syn_spec["weight"] < 0 else "green3"}; {f'penwidth={width};'if width != 1 else ''}'


def edge_to_dot(edge):
    [src, dst, conn_type, syn_spec, num_sources] = edge
    return f'\t{src} -> {dst} [label = "{print_syn_spec(syn_spec)}" {f'taillabel = "{num_sources}:1";' if num_sources else ''} headlabel = ""; labeldistance=1; {edge_color_width(syn_spec)}];\n'


def inverse(d):
    inverse = defaultdict(list)
    for k, v in d.items():
        inverse[v].append(k)
    return inverse


def same_level(distances):
    inv = inverse(distances)
    l = ""
    for dst in inv.keys():
        same_level = str(inv[dst].pop(0))
        for v in inv[dst]:
            same_level += f" -> {v}"
        same_level += ";"
        l += invis_subgraph_template.replace("<<<EDGES>>>", same_level)
    return l


def generate_flow_chart(networkdef: str, params, connect_fun_name="connect"):
    """
    generates a textual representation in DOT language for GraphViz.

    args:
    networkdef -- the function (in text) creating the network
    params -- the parameters given

    """
    edges = code_to_edges(networkdef, params, connect_fun_name)

    # convert [[src,dst1], [src,dst2]] to {src: [dst1, dst2]}
    G = defaultdict(list)
    for [src, dst, conn_type, syn_spec, num_sources] in edges:
        G[src].append(dst)
    G["src"] = [
        "L_ANF",
        "R_ANF",
    ]  # to make it cleaner, connect to whatever node has 0 indegree

    distances = max_distance(G, "src")

    # split distances in left and right
    dist_left, dist_right = {}, {}
    for k, v in distances.items():
        if "L_" in k:
            dist_left[k] = v
        elif "R_" in k:
            dist_right[k] = v

    # split subgraphs from overall (we need two clusters with only left-left
    # and only right-right edges, then a final section with all mixed edges)
    only_left, only_right, mixed = [], [], []
    for edge in edges:
        if "L_" in edge[0] and "l_" in edge[1]:
            only_left.append(edge)
        elif "R_" in edge[0] and "r_" in edge[1]:
            only_right.append(edge)
        else:
            mixed.append(edge)

    # transform edges from list of string to dot language
    # this could use the graphviz python library, but really
    # it's just one more dependency for a couple lines of code,
    # and this gives me complete control. DOT won't change syntax.
    left_edges_dot = right_edges_dot = mixed_edges_dot = ""
    for edge in only_left:
        left_edges_dot += edge_to_dot(edge)
    for edge in only_right:
        right_edges_dot += edge_to_dot(edge)
    for edge in mixed:
        mixed_edges_dot += edge_to_dot(edge)
    same_level_left_dot = same_level(dist_left)
    same_level_right_dot = same_level(dist_right)

    # replace in template
    dot = dot_template
    dot = dot.replace("<<<LEFT>>>", left_edges_dot + "\n" + same_level_left_dot)
    dot = dot.replace("<<<RIGHT>>>", right_edges_dot + "\n" + same_level_right_dot)
    dot = dot.replace("<<<MIXED>>>", mixed_edges_dot)
    return dot
