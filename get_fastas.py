import argparse
import csv
import functools
import subprocess
import traceback
from datetime import datetime
from multiprocessing import Pool
from pathlib import Path

# class args:
#     config = Path("default_fastas_wishlist.csv")
#     output = Path("/tmp/fastas")


parser = argparse.ArgumentParser(description="Download fasta files.")
parser.add_argument(
    "config",
    help="csv file with columns TAG|URL|NAME|*others",
    type=Path,
)
parser.add_argument(
    "-o",
    "--output",
    help="Output folder.",
    type=Path,
    default=None,
)
args = parser.parse_args()


def count_entries(fastafile):
    cnt = 0
    with open(fastafile, "r") as f:
        for l in f:
            if l[0] == ">":
                cnt += 1
    return cnt


RUN = functools.partial(subprocess.run, check=True, shell=True)


def download_or_pass(tag_url_name):
    tag, url, name = tag_url_name
    date = datetime.today().strftime("%Y_%m_%d")
    try:
        RUN(f'wget -O {args.output/name} "{url}"')
        cnt = count_entries(args.output / name)
        final_name = name.format(yyyymmdd=date, cnt=cnt)
        RUN(f"mv {args.output/name} {args.output/final_name}")
    except subprocess.CalledProcessError:
        (args.output / name).unlink()
        return url, name
    return tag, final_name, cnt


if __name__ == "__main__":
    with open(args.config, newline="") as csvfile:
        spamreader = iter(csv.reader(csvfile, delimiter=","))
        cols = next(spamreader)[:3]
        values = [row[:3] for row in spamreader]

    with Pool(mp.cpu_count()) as pool:
        results = pool.map(download_or_pass, values)

    noncompound_entries = {x[0]: (x[1], x[2]) for x in results if len(x) == 3}
    compound_entries = list(filter(lambda x: len(x) == 2, results))

    for noncompound_tags, name in compound_entries:
        try:
            noncompound_tags = noncompound_tags.split("+")
            for noncompound_tag in noncompound_tags:
                if noncompound_tag not in noncompound_entries:
                    print(f"Tag {noncompound_tag} not among the downloaded tags.")
                    break
            else:
                date = datetime.today().strftime("%Y_%m_%d")
                files_to_cat = []
                total_cnt = 0
                for tag in noncompound_tags:
                    file, cnt = noncompound_entries[tag]
                    files_to_cat.append(str(args.output / file))
                    total_cnt += cnt
                final_name = name.format(yyyymmdd=date, cnt=cnt)

                files = " ".join(files_to_cat)

                RUN(f"cat {files} > {args.output/final_name}")
            break
        except Exception as exp:
            traceback.print_exc()
