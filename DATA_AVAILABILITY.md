The Data Availability statement is implemented as follows.

**Licensed media (not redistributed)**  
IEMOCAP (USC SAIL) and SAVEE (University of Surrey).

**Derived artefacts (in this repository)**  
`results/paper/tables.json` and `results/paper/figures.json` are the experiment logs from which **every number in Tables 2–17 and every curve in Figs. 3–7** is generated.

```bash
python reproduce.py --from-logs
```

`tables/make_tables.py` and `figures/make_figures.py` contain **no numeric literals** for those results; they only format the logs.

**Code (in this repository)**  
`splits/`, `preprocessing/`, `eholf/`, `lstm_eholf/`, `explain/`, `robustness/`, `configs/`, `environment.yml`.

Retraining from raw audiovisual files requires the licensed corpora plus `scripts/build_official_splits.py`. A synthetic speaker-independent pipeline (`python reproduce.py --demo`) exercises the same methods without those files.

Table 7 wall-clock times are measurements on RTX 4070 Ti / i7-13700K stored in the logs; `scripts/profile_compute.py` re-measures on the local host.
