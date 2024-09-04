from analyze.report import generate_multi_inputs_single_net

if __name__ == "__main__":
    from os.path import join, isfile
    from os import listdir
    import dill
    from pathlib import Path

    results_dir = Path(
        "/home/paolo/Documents/school/master/polimi/thesis/polithesis/results/"
    )

    folders = [
        "hrtf2",
    ]
    for folder in folders:
        # folder = folders[0]
        print("working on ", folder)
        files = [
            i
            for i in (results_dir / folder).iterdir()
            if isfile(i) and str(i).endswith(".pic")
        ]

        generate_multi_inputs_single_net(files, results_dir / folder)
