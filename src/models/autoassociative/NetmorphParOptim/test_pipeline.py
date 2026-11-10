"""End-to-end smoke tests (small forests for speed). Run: python -m unittest -v test_pipeline
Synthetic-label tests only verify plumbing; they say nothing about biology or Netmorph."""
import os
import sys
import tempfile
import unittest

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "app"))
import bio_check  # noqa: E402
import multi_target_optim as mto  # noqa: E402

REAL = os.path.join(HERE, "Phase1_1500_700_combined_labeled-RS20240628.xlsx")
WITH_INT = os.path.join(HERE, "ParameterSpace_700_samples-labeled.xlsx")


class TestBio(unittest.TestCase):
    def test_density_and_fraction(self):
        ok = dict(days=22, pyramidal=90, interneuron=30, minneuronseparation=14, **{"shape.radius": 150, "shape.thickness": 35, "dm.weight": 0.5})
        r = bio_check.check_frame(pd.DataFrame([ok]))
        # volume = pi*150^2*35 um^3 = 2.47e-3 mm^3 -> 120/2.47e-3 = 48.6k/mm^3, fraction 0.75
        self.assertTrue(r.bio_ok.iloc[0], r.iloc[0].to_dict())
        bad = dict(ok, interneuron=90)  # fraction 0.5
        rb = bio_check.check_frame(pd.DataFrame([bad]))
        self.assertTrue(rb.bio_ok.iloc[0] and rb.warn_pyr_fraction.iloc[0])  # warning only
        sparse = dict(ok, pyramidal=30, interneuron=16, **{"shape.radius": 200, "shape.thickness": 50})
        rs = bio_check.check_frame(pd.DataFrame([sparse]))
        self.assertTrue(rs.bio_ok.iloc[0] and rs.warn_density.iloc[0])  # warning only
        out_of_limits = dict(ok, **{"shape.thickness": 55})
        self.assertFalse(bio_check.check_frame(pd.DataFrame([out_of_limits])).bio_ok.iloc[0])  # HARD
        with self.assertRaises(ValueError):
            bio_check.assert_hard_limits(pd.DataFrame([out_of_limits]))


class TestPyrPyr(unittest.TestCase):
    def test_joint_single_target(self):
        df, feats = mto.load_labeled(REAL, ["usable_conns2"])
        mtm = mto.MultiTargetModel(["usable_conns2"], feats, 200).fit(df)
        m = mtm.models["usable_conns2"].metrics
        self.assertGreater(m["test_r2"], 0.7)
        cfs = mto.generate_joint_cfs(mtm, {"usable_conns2": {"min": 500, "max": 2500}}, total_CFs=4)
        self.assertGreater(len(cfs), 0)
        self.assertTrue((cfs.joint_margin >= 1).all() and (cfs.bio_hard_violations == 0).all())


class TestSyntheticAndNeedsMore(unittest.TestCase):
    def test_synthetic_path(self):
        raw = bio_check.clean_columns(pd.read_excel(WITH_INT))
        df = mto.make_synthetic_labels(raw)
        self.assertTrue(df.attrs["synthetic"] and df["_SYNTHETIC_LABELS"].all())
        T = ["usable_pyr_int", "usable_int_pyr", "usable_int_int"]
        mtm = mto.MultiTargetModel(T, mto.load_labeled(df, T)[1], 150, synthetic=True).fit(df)
        self.assertEqual(sorted(mtm.trained), sorted(T))
        cfs = mto.generate_joint_cfs(mtm, {t: {"min": 200, "max": None} for t in T}, total_CFs=3, method="bio_pool")
        self.assertTrue(cfs.attrs["synthetic"])
        self.assertGreater(len(cfs), 0)

    def test_tiny_labels_needs_more(self):
        raw = bio_check.clean_columns(pd.read_excel(WITH_INT))
        df = mto.make_synthetic_labels(raw)
        tiny = df.head(6).copy()  # simulate "a few rows" of real new labels
        T = ["usable_pyr_int"]
        feats = mto.load_labeled(tiny, T)[1]
        mtm = mto.MultiTargetModel(T, feats, 50).fit(tiny)
        self.assertFalse(mtm.models[T[0]].metrics["trained"])   # refuses to train on 6 rows
        ref = bio_check.clean_columns(pd.read_excel(REAL))
        with tempfile.TemporaryDirectory() as d:
            rep, sug = mto.needs_more_samples(tiny, T, feats, mtm, reference_df=ref, n_suggest=30,
                                              out_xlsx=os.path.join(d, "s.xlsx"))
        self.assertGreater(rep["targets"][T[0]]["additional_netmorph_runs_recommended"], 100)
        self.assertTrue(bio_check.bio_ok_mask(sug.rename(columns={"dm.weight ": "dm.weight"})).all())


class TestFlask(unittest.TestCase):
    def _client(self, synthetic):
        os.environ["NETMORPH_TREES"] = "100"
        if synthetic:
            os.environ["NETMORPH_SYNTHETIC"] = "1"
        else:
            os.environ.pop("NETMORPH_SYNTHETIC", None)
        import app as flask_app
        flask_app.STATE["mtm"] = None
        return flask_app.app.test_client()

    def test_real_single_and_legacy(self):
        c = self._client(False)
        self.assertEqual(c.get("/").status_code, 200)
        d = c.get("/api/default_values").get_json()
        self.assertEqual([t["name"] for t in d["targets"]], ["usable_conns2"])
        pay = {"query_instance": d["query_instance"], "total_CFs": 3, "permitted_range": d["permitted_ranges"]}
        legacy = c.post("/api/generate", json={**pay, "desired_range": [500, 2500]}).get_json()   # old-UI payload
        self.assertTrue(legacy["success"], legacy)
        new = c.post("/api/generate", json={**pay, "targets": {"usable_conns2": {"min": 500, "max": 2500}}}).get_json()
        self.assertTrue(new["success"], new)
        self.assertFalse(new["synthetic"])

    def test_synthetic_joint(self):
        c = self._client(True)
        d = c.get("/api/default_values").get_json()
        self.assertTrue(d["synthetic"])
        self.assertIn("interneuron", d["features"])
        names = [t["name"] for t in d["targets"]]
        self.assertIn("usable_int_int", names)
        r = c.post("/api/generate", json={"query_instance": d["query_instance"], "total_CFs": 3,
                   "permitted_range": d["permitted_ranges"],
                   "targets": {"usable_pyr_int": {"min": 200, "max": None}, "usable_int_int": {"min": 150, "max": None}}}).get_json()
        self.assertTrue(r["success"], r)
        self.assertTrue(r["synthetic"])
        self.assertGreater(len(r["counterfactuals"]), 0)
        bad = c.post("/api/generate", json={"query_instance": d["query_instance"], "targets": {"nope": {"min": 1}}})
        self.assertEqual(bad.status_code, 400)


class TestBatchBRealLabels(unittest.TestCase):
    """Real batch B labels (REAL Netmorph runs, not synthetic). Skipped if the parts are absent."""
    def test_merge_and_limits(self):
        if not os.path.exists(os.path.join(HERE, "batchB_labels_part4.xlsx")):
            self.skipTest("batch B label parts not present")
        import merge_batchB
        a = merge_batchB.merge()
        self.assertEqual(len(a), 100)
        self.assertEqual(sorted(a["sample"]), list(range(1, 101)))
        self.assertTrue(a["NES_SIM_ID"].is_unique)
        self.assertFalse(a[merge_batchB.LAB].isna().any().any())
        self.assertTrue((a["rc"].dropna() == 0).all())
        bio_check.assert_hard_limits(a)
        self.assertLessEqual(a.pyramidal.max(), 70)
        self.assertLessEqual(a.interneuron.max(), 30)

    def test_candidates_inside_limits(self):
        import batchB_models as bm
        c = bm.candidates(n=2000)
        bio_check.assert_hard_limits(c)
        self.assertTrue(c.pyramidal.between(16, 70).all() and c.interneuron.between(16, 30).all())


if __name__ == "__main__":
    unittest.main(verbosity=2)
