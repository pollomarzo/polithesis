from pathlib import Path

from analyze.report import generate_multi_inputs_single_net
from consts import Paths
from generate_results import CURRENT_TEST
from utils.log import logger, tqdm

if __name__ == "__main__":

    # results_dir = Path(Paths.RESULTS_DIR).absolute() / "amplifcocheffect"
    results_dir = Path(Paths.RESULTS_DIR).absolute() / CURRENT_TEST
    # folders = [i for i in results_dir.iterdir() if not i.is_file()]

    folders = [
        Path(Paths.RESULTS_DIR).absolute() / "v_shaped_diff_ICC" / "hrtf_check" / i
        for i in [
            "hrtftest",
        ]
    ]

    logger.info("generating complete reports")
    for folder in tqdm(folders, desc="overall folders"):
        # folder = folders[0]
        # print("working on ", folder)
        files = [
            i
            for i in (results_dir / folder).iterdir()
            if i.is_file() and str(i).endswith(".pic")
        ]
        logger.info(files)

        generate_multi_inputs_single_net(
            files, rate=False, show_pops=["parrot_ANF"], include_netvis=False
        )
    logger.info("reports generation complete")
