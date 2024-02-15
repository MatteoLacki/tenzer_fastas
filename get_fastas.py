#!/usr/bin/env python3
import argparse
import csv
import functools
import multiprocessing as mp
import subprocess
import traceback
from datetime import datetime
from pathlib import Path


class args:
    config = Path("default_fastas_wishlist.csv")
    output = Path("/tmp/fastas")


parser = argparse.ArgumentParser(description="Download fasta files.")
parser.add_argument(
    "config",
    help="csv file with columns TAG|URL|NAME|*others",
    type=Path,
)
parser.add_argument(
    "output",
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


def download_or_pass(tag_url_name_date):
    tag, url, name, date = tag_url_name_date
    try:
        RUN(f'wget -O {args.output/name} "{url}"')
        cnt = count_entries(args.output / name)
        final_name = name.format(yyyymmdd=date, cnt=cnt)
        RUN(f"mv {args.output/name} {args.output/final_name}")
    except subprocess.CalledProcessError:
        (args.output / name).unlink()
        return False, tag, url, name
    return True, tag, final_name, cnt


if __name__ == "__main__":
    date = datetime.today().strftime("%Y_%m_%d")

    # read config csv
    with open(args.config, newline="") as csvfile:
        spamreader = iter(csv.reader(csvfile, delimiter=","))
        cols = next(spamreader)[:3]
        values = [row[:3] for row in spamreader]

    # download stuff
    with mp.Pool(mp.cpu_count()) as pool:
        results = pool.map(download_or_pass, [[*v, date] for v in values])

    # get compound fastas
    # compound_entries = "noncompound_tag+noncompound_tag+...+noncompound_tag"
    noncompound_entries = {x[1]: (x[2], x[3]) for x in results if x[0]}
    compound_entries = [x[1:] for x in results if not x[0]]
    tag_to_name_cnt = {}

    for tag, noncompound_tags, name in compound_entries:
        try:
            noncompound_tags = noncompound_tags.split("+")
            for noncompound_tag in noncompound_tags:
                if noncompound_tag not in noncompound_entries:
                    print(f"Tag {noncompound_tag} not among the downloaded tags.")
                    break
            else:
                files_to_cat = []
                total_cnt = 0
                for noncompound_tag in noncompound_tags:
                    file, cnt = noncompound_entries[noncompound_tag]
                    files_to_cat.append(str(args.output / file))
                    total_cnt += cnt
                final_name = name.format(yyyymmdd=date, cnt=cnt)

                tag_to_name_cnt[tag] = (final_name, total_cnt)
                files = " ".join(files_to_cat)
                RUN(f"cat {files} > {args.output/final_name}")

            break
        except Exception as exp:
            traceback.print_exc()

    # update Hao's contaminants:
    script = f"""
    rm -rf Protein-Contaminant-Libraries-for-DDA-and-DIA-Proteomics || True
    git clone https://github.com/HaoGroup-ProtContLib/Protein-Contaminant-Libraries-for-DDA-and-DIA-Proteomics.git
    shopt -s globstar
    mkdir -p contaminants
    cp Protein-Contaminant-Libraries-for-DDA-and-DIA-Proteomics/**/*.fasta contaminants
    cp Protein-Contaminant-Libraries-for-DDA-and-DIA-Proteomics/Universal\ protein\ contaminant\ FASTA/0602_Universal\ Contaminants.fasta contaminants/hao_{date}.fasta
    """
    RUN(script)

    # append contaminants:
