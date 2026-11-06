#!/usr/bin/env python3
import argparse
import csv
import shutil
import subprocess
import sys
import threading
import time
import traceback
import urllib.request
from concurrent.futures import ThreadPoolExecutor
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
parser.add_argument(
    "-n",
    "--workers",
    help="Number of parallel downloads (default: %(default)s).",
    type=int,
    default=8,
)
args = parser.parse_args()


class Progress:
    """Live status of running downloads; finished ones scroll up as plain lines.

    On a terminal, the active downloads are redrawn in place below the finished
    ones. Otherwise only the finished lines are printed.
    """

    BAR = 20
    REFRESH = 0.1  # seconds between redraws

    def __init__(self, n_files):
        self.n_files = n_files
        self.n_done = 0
        self.tty = sys.stdout.isatty()
        self.lock = threading.Lock()
        self.active = {}  # tag -> [start, nbytes, entries, total]
        self.drawn = 0  # lines currently occupied by the active block
        self.last_draw = 0.0

    def start(self, tag, total):
        with self.lock:
            self.active[tag] = [time.monotonic(), 0, 0, total]
            self._redraw()

    def update(self, tag, nbytes, entries):
        with self.lock:
            state = self.active[tag]
            state[1], state[2] = nbytes, entries
            if time.monotonic() - self.last_draw >= self.REFRESH:
                self._redraw()

    def finish(self, tag, message):
        with self.lock:
            self.active.pop(tag, None)
            self.n_done += 1
            self._clear()
            print(f"{tag:<28.28} {message}", flush=True)
            self._redraw()

    def _line(self, tag, state):
        start, nbytes, entries, total = state
        elapsed = max(time.monotonic() - start, 1e-9)
        stats = f"{nbytes / 1e6:7.1f} MB {nbytes / 1e6 / elapsed:5.1f} MB/s"
        if total:
            filled = min(entries / total, 1.0)
            bar = "#" * int(filled * self.BAR)
            return (
                f"{tag:<28.28} [{bar:<{self.BAR}}] {filled:6.1%} "
                f"{entries:>9,}/{total:,} entries {stats}"
            )
        return f"{tag:<28.28} {entries:>9,} entries {stats}"

    def _clear(self):
        if self.tty and self.drawn:
            sys.stdout.write(f"\x1b[{self.drawn}F\x1b[J")
            self.drawn = 0

    def _redraw(self):
        if not self.tty:
            return
        self._clear()
        width = shutil.get_terminal_size().columns - 1
        lines = [self._line(t, s) for t, s in self.active.items()]
        lines.append(f"{self.n_done}/{self.n_files} files done")
        sys.stdout.write("\n".join(line[:width] for line in lines) + "\n")
        sys.stdout.flush()
        self.drawn = len(lines)
        self.last_draw = time.monotonic()


def total_entries(url):
    """Entry count announced by UniProt's search endpoint, or None."""
    try:
        search_url = url.replace("/stream?", "/search?") + "&size=1"
        with urllib.request.urlopen(search_url, timeout=60) as response:
            return int(response.headers["X-Total-Results"])
    except (OSError, ValueError, TypeError, KeyError):
        return None


def fetch(url, path, on_progress, chunk_size=1 << 16):
    """Stream url into path; return the number of fasta entries written."""
    nbytes = entries = 0
    previous = b"\n"  # so that a '>' in the very first byte is counted
    with urllib.request.urlopen(url, timeout=120) as response, open(path, "wb") as f:
        while chunk := response.read(chunk_size):
            f.write(chunk)
            nbytes += len(chunk)
            entries += (previous + chunk).count(b"\n>")
            previous = chunk[-1:]
            on_progress(nbytes, entries)
    return entries


def concatenate(sources, destination):
    with open(destination, "wb") as out:
        for source in sources:
            with open(source, "rb") as f:
                shutil.copyfileobj(f, out)


def download_or_pass(tag_url_name_date):
    tag, url, name, date = tag_url_name_date
    progress.start(tag, total_entries(url))
    try:
        cnt = fetch(
            url,
            args.output / name,
            lambda nbytes, entries: progress.update(tag, nbytes, entries),
        )
        final_name = name.format(yyyymmdd=date, cnt=cnt)
        (args.output / name).rename(args.output / final_name)
    except OSError as e:
        (args.output / name).unlink(missing_ok=True)
        progress.finish(tag, f"FAILED: {e}")
        return None
    progress.finish(tag, f"done  {cnt:,} entries")
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
    progress = Progress(len(downloads))
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        results = list(pool.map(download_or_pass, [[*v, date] for v in downloads]))

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
