from analyze.graph import generate_flow_chart

if __name__ == "__main__":
    # D.render(view=False)
    from os.path import join
    import dill
    from pathlib import Path

    results_dir = Path(
        "/home/paolo/Documents/school/master/polimi/thesis/polithesis/results/"
    )

    selected = "2024-08-31T23:59:05&tone_100.Hz_110dB&realistic&inh_model&hrtf2.pic"
    with open(join(results_dir, selected), "rb") as f:
        res = dill.load(f, ignore=True)
    result = generate_flow_chart(
        res["conf"]["model_desc"]["networkdef"],
        res["conf"]["parameters"],
        "fakeConnect",
    )
    print(result)
