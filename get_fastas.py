#!/usr/bin/env python3
import argparse
import csv
import multiprocessing as mp
import shutil
import subprocess
import sys
import traceback
import urllib.request
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


def fetch(url, path):
    with urllib.request.urlopen(url, timeout=120) as response, open(path, "wb") as f:
        shutil.copyfileobj(response, f)


def concatenate(sources, destination):
    with open(destination, "wb") as out:
        for source in sources:
            with open(source, "rb") as f:
                shutil.copyfileobj(f, out)


def download_or_pass(tag_url_name_date):
    tag, url, name, date = tag_url_name_date
    try:
        fetch(url, args.output / name)
        cnt = count_entries(args.output / name)
        final_name = name.format(yyyymmdd=date, cnt=cnt)
        (args.output / name).rename(args.output / final_name)
    except OSError as e:
        print(f"Download of {tag} failed: {e}", file=sys.stderr)
        (args.output / name).unlink(missing_ok=True)
        return None
    return tag, final_name, cnt


if __name__ == "__main__":
    date = datetime.today().strftime("%Y%m%d")

    # read config csv
    with open(args.config, newline="") as csvfile:
        spamreader = iter(csv.reader(csvfile, delimiter=","))
        cols = next(spamreader)[:3]
        values = [row[:3] for row in spamreader]

    # a row whose URL has no scheme is compound: "tag+tag+...+tag"
    downloads = [row for row in values if "://" in row[1]]
    compound_entries = [row for row in values if "://" not in row[1]]

    # download stuff
    with mp.Pool(mp.cpu_count()) as pool:
        results = pool.map(download_or_pass, [[*v, date] for v in downloads])

    # get compound fastas
    noncompound_entries = {x[0]: (x[1], x[2]) for x in results if x is not None}
    tag_to_name_cnt = {**noncompound_entries}

    for tag, noncompound_tags, name in compound_entries:
        noncompound_tags = noncompound_tags.split("+")
        missing = [t for t in noncompound_tags if t not in noncompound_entries]
        if missing:
            print(f"{tag}: tags not downloaded: {missing}", file=sys.stderr)
            continue
        try:
            files_to_cat = []
            total_cnt = 0
            for noncompound_tag in noncompound_tags:
                file, cnt = noncompound_entries[noncompound_tag]
                files_to_cat.append(args.output / file)
                total_cnt += cnt
            final_name = name.format(yyyymmdd=date, cnt=total_cnt)

            concatenate(files_to_cat, args.output / final_name)
            tag_to_name_cnt[tag] = (final_name, total_cnt)
        except OSError:
            traceback.print_exc()

    # update Hao's contaminants:
    hao_contaminants = Path(f"contaminants/hao.fasta")
    hao_repo = Path("Protein-Contaminant-Libraries-for-DDA-and-DIA-Proteomics")
    shutil.rmtree(hao_repo, ignore_errors=True)
    subprocess.run(
        [
            "git",
            "clone",
            f"https://github.com/HaoGroup-ProtContLib/{hao_repo}.git",
        ],
        check=True,
    )
    Path("contaminants").mkdir(exist_ok=True)
    for fasta in hao_repo.rglob("*.fasta"):
        shutil.copy(fasta, "contaminants")
    shutil.copy(
        hao_repo / "Universal protein contaminant FASTA" / "0602_Universal Contaminants.fasta",
        hao_contaminants,
    )

    # append contaminants:
    tenzer_contaminants = Path("contaminants/tenzer.fasta")
    contaminants = [hao_contaminants, tenzer_contaminants]

    for contaminant in contaminants:
        if contaminant.exists():
            for tag, (fasta_file, cnt) in tag_to_name_cnt.items():
                fasta_path = args.output / fasta_file
                contaminated_fasta = args.output / (
                    fasta_path.stem + f"_contaminant_{contaminant.stem}.fasta"
                )
                concatenate([fasta_path, contaminant], contaminated_fasta)
