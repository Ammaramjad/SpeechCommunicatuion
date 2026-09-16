# LSTM-EHOLF reproduction package

Code, splits, and **derived experiment logs** for:

**Explainable and Noise-Robust Multimodal Emotion Recognition Using LSTM-EHOLF**

Licensed IEMOCAP and SAVEE media are **not** in this repository. Everything required to regenerate **Tables 2–17** and **Figs. 3–7** from the released logs is.

## Reproduce every published table and figure

```bash
pip install -r requirements.txt
python reproduce.py --from-logs
```

This writes:

- `tables/generated/*.md` — Table 2 sync, Table 3 PCA, Table 4 fusion, Table 5 capacity, Table 6 EHOLF, Table 7 compute, Table 8 folds, Table 9 ablation, Table 10 baselines, Table 11 dropout, Table 12 noise/TNN, Table 13 cross-domain, Tables 14–16 SHAP, Table 17 matched re-runs
- `figures/generated/fig3.png` … `fig7.png`

Numbers are **not** typed into the table scripts. `tables/make_tables.py` and `figures/make_figures.py` read `results/paper/tables.json` and `results/paper/figures.json`.

## Run the methodology without licensed data

```bash
python reproduce.py --demo
python -m pytest tests/test_lstm_eholf.py tests/test_paper_tables.py -q
```

Synthetic speaker-independent folds exercise alignment, PCA, LSTM training, EHOLF, SHAP, dropout, noise, and cross-domain transfer.

## Layout (matches the Data Availability statement)

| Path | Content |
|---|---|
| `splits/` | 5-fold IEMOCAP LOSO and 4-fold SAVEE speaker protocol |
| `preprocessing/` | MFCC, landmarks, BERT/PCA, 10 ms A–V alignment |
| `eholf/` | Lévy flight + adaptive inertia weight optimizer |
| `lstm_eholf/` | LSTM, RNN/GRU/GAN/TNN baselines, fusion, training |
| `explain/` | Kernel SHAP, modality aggregation, bootstrap stability |
| `robustness/` | dropout, noise, four-class transfer |
| `configs/` | IEMOCAP / SAVEE / demo hyperparameters (Table 6) |
| `results/paper/` | derived logs used to typeset the article |
| `figures/make_figures.py`, `tables/make_tables.py` | regenerate figures and tables |
| `environment.yml` | pinned Python 3.11 stack |
| `docs/LSTM_EHOLF_METHODOLOGY.md` | equation-level method |

## Retrain on licensed corpora

1. Obtain IEMOCAP (USC SAIL) and SAVEE (University of Surrey).
2. `python scripts/build_official_splits.py --iemocap /path/IEMOCAP --savee /path/SAVEE`
3. Extract features with `preprocessing/` (BERT-base and ResNet-50 weights download separately).
4. Run EHOLF + LSTM with `configs/iemocap.yaml` / `configs/savee.yaml`.

Wall-clock Table 7 is hardware-specific (RTX 4070 Ti). Re-measure with `python scripts/profile_compute.py`.
