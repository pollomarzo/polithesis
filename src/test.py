from utils.graph import generate_flow_chart
import graphviz as gv

if __name__ == "__main__":

    # https://graphviz.readthedocs.io/en/stable/manual.html
    # Create a directed graph
    D = gv.Digraph(filename="auditory_network_graphviz.png", format="png")
    # Define nodes and edges for the left hemisphere
    left_edges = [
        ("l_ANFs", "parrot_l_ANFs", ""),
        ("parrot_l_ANFs", "l_SBCs", "w: 16.0"),
        ("parrot_l_ANFs", "l_GBCs", "w: 8.0"),
        ("l_GBCs", "l_LNTBCs", "w: 16.0\\nd: 0.45"),
        ("l_SBCs", "l_MSO", "w: 1\\nd: 2"),
        ("l_LNTBCs", "l_MSO", "w: -5.0\\nd: 1.64"),
        ("l_MNTBCs", "l_MSO", "w: -5.0\\nd: 1.04"),
        ("l_SBCs", "l_LSO", "w: 4.0"),
        ("l_MNTBCs", "l_LSO", "w: -12.0"),
    ]

    # Define nodes and edges for the right hemisphere
    right_edges = [
        ("r_ANFs", "parrot_r_ANFs", ""),
        ("parrot_r_ANFs", "r_SBCs", "w: 16.0"),
        ("parrot_r_ANFs", "r_GBCs", "w: 8.0"),
        ("r_GBCs", "r_LNTBCs", "w: 16.0\\nd: 0.45"),
        ("r_SBCs", "r_MSO", "w: 1\\nd: 2"),
        ("r_LNTBCs", "r_MSO", "w: -5.0\\nd: 1.64"),
        ("r_MNTBCs", "r_MSO", "w: -5.0\\nd: 1.04"),
        ("r_SBCs", "r_LSO", "w: 4.0"),
        ("r_MNTBCs", "r_LSO", "w: -12.0"),
    ]
    mixed_edges = [
        ("r_SBCs", "l_MSO", "w: 1\\nd: 2"),
        ("r_GBCs", "l_MNTBCs", "w: 16.0\\nd: 0.45"),
        ("l_GBCs", "r_MNTBCs", "w: 16.0\\nd: 0.45"),
        ("l_SBCs", "r_MSO", "w: 1\\nd: 2"),
    ]
    # Add left hemisphere edges to the graph with a subgraph
    with D.subgraph(name="cluster_Left_Hemisphere") as s:
        s.node_attr.update(ordering="out")
        s.attr(style="filled", color="lightgrey")
        s.node_attr.update(style="filled", color="white")
        for edge in left_edges:
            s.edge(edge[0], edge[1], label=edge[2])

    # Add right hemisphere edges to the graph with a subgraph
    with D.subgraph(name="cluster_Right_Hemisphere") as s:
        s.attr(color="blue")
        s.node_attr.update(style="filled", color="lightgrey")
        for edge in right_edges:
            s.edge(edge[0], edge[1], label=edge[2])

    for edge in mixed_edges:
        D.edge(edge[0], edge[1], label=edge[2])

    # Layout and draw the graph
    # D = D.unflatten(stagger=)
    D.render(view=False)
    print(D.source)

    # from os.path import join
    # import dill
    # from pathlib import Path

    # results_dir = Path(
    #     "/home/paolo/Documents/school/master/polimi/thesis/polithesis/results/"
    # )

    # selected = "2024-08-31T23:59:05&tone_100.Hz_110dB&realistic&inh_model&hrtf2.pic"
    # with open(join(results_dir, selected), "rb") as f:
    #     res = dill.load(f, ignore=True)
    # result = generate_flow_chart(
    #     res["conf"]["model_desc"]["networkdef"], res["conf"]["parameters"]
    # )
    # print(result)
    # with open(join(results_dir, "testone.md"), "w+") as f:
    #     f.write(result)
