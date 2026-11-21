# The World in One Day — 21 November 2026

make.fun entry for competition `news-image-20261121`: sum up 21 November's
world news in one image.

`main.py` (Python 3 stdlib only, no network, deterministic) draws a
1024x1024 newspaper front page: masthead, 3 hero cards, 10 small cards,
world map with numbered pins, 27 one-line briefs (40 stories total), a
DATE CHECK box excluding news first reported 19-20 Nov, and a sources
footer. Run twice → identical bytes:

    MAKEFUN_OUTPUT_DIR=out python3 main.py

Output: `out/entry.png`.
