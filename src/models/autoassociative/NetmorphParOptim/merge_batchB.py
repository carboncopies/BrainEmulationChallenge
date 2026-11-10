"""Merge batchB_labels_part1..4.xlsx into batchB_labels_all.xlsx (100 rows, sample 1-100)."""
import os, pandas as pd
import bio_check
HERE = os.path.dirname(os.path.abspath(__file__))
LAB = ["usable_conns1","usable_conns2","usable_pyr_int","usable_int_pyr","usable_int_int",
       "frac_int_driven","frac_pyr_inhibited","frac_pyr_inhibited_w05"]

def merge(out=None):
    parts = []
    for i in range(1, 5):
        d = bio_check.clean_columns(pd.read_excel(os.path.join(HERE, f"batchB_labels_part{i}.xlsx")))
        if i == 1:
            d["sample"] = range(1, len(d) + 1)
        if "rc" not in d.columns:
            d["rc"] = float("nan")   # part 1/2 have no rc column (all completed, per reports)
        d["part"] = i
        parts.append(d)
    a = pd.concat(parts, ignore_index=True)
    a["sample"] = a["sample"].astype(int)
    assert a["sample"].is_unique, "duplicate sample numbers"
    assert sorted(a["sample"]) == list(range(1, len(a) + 1)), "sample numbering inconsistent"
    assert a["NES_SIM_ID"].is_unique, "duplicate NES_SIM_ID"
    a = a.sort_values("sample").reset_index(drop=True)
    if out:
        a.to_excel(out, index=False)
    return a

if __name__ == "__main__":
    a = merge(os.path.join(HERE, "batchB_labels_all.xlsx"))
    print(a.shape)
    print("rc counts:", a.rc.value_counts(dropna=False).to_dict())
    print("rc!=0 (non-NaN):", a[a.rc.notna() & (a.rc != 0)][["sample","rc"]].values.tolist())
    print("missing labels:", a[a[LAB].isna().any(axis=1)][["sample"]+LAB].to_string())
    print("sim id range", a.NES_SIM_ID.min(), a.NES_SIM_ID.max())
    bio_check.assert_hard_limits(a)
    print("hard limits ok; pyr max", a.pyramidal.max(), "int max", a.interneuron.max())
    print(a[LAB].describe().T[["mean","min","50%","max"]])
    print((a[LAB]>0).sum())
