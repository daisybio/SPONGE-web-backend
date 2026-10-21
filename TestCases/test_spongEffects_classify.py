import json, os, shutil, subprocess, tempfile, unittest

########################################################################################################################
"""Regression tests for scripts/spongEffects/classify.R (subtype prediction)"""
########################################################################################################################

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.getenv("SPONGEFFECTS_PREDICT_SCRIPT", os.path.join(ROOT, "scripts", "spongEffects", "classify.R"))
MODEL_PATH = os.getenv("SPONGEFFECTS_MODEL_PATH", os.path.join(ROOT, "models.RDS"))
EXAMPLE = os.path.join(ROOT, "uploads", "GSE123845_exp_tpm_matrix_processed.csv")
MODEL = "breast_invasive_carcinoma"
N_SAMPLES = 20
RESPONSE_KEYS = ["meta", "data", "scores", "type_scores", "module_members"]


def run_classify(tmp, name, extra_args, reverse_samples=False):
    """Run classify.R on the first N_SAMPLES samples of the shipped gene-level BRCA example"""
    expr = os.path.join(tmp, f"{name}.csv")
    with open(EXAMPLE) as src, open(expr, "w") as dst:
        for line in src:
            fields = line.rstrip("\n").split(",")
            samples = fields[1:N_SAMPLES + 1]
            dst.write(",".join([fields[0]] + (samples[::-1] if reverse_samples else samples)) + "\n")
    out = os.path.join(tmp, f"{name}.json")
    subprocess.run(["Rscript", SCRIPT, "--expr", expr, "--model_path", MODEL_PATH, "--output", out,
                    "--local", "--log", "--subtypes", "--method", "gsva"] + extra_args,
                   check=True, capture_output=True, text=True)
    with open(out) as f:
        return json.load(f)


def coverage_by_model(response):
    return {c["model"]: c for c in response["meta"][0]["module_coverage"]}


@unittest.skipUnless(shutil.which("Rscript") and os.path.exists(MODEL_PATH) and os.path.exists(EXAMPLE),
                     "needs Rscript, models.RDS and the GSE123845 example upload")
class TestClassifySpecifiedModel(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.response = run_classify(cls.tmp, "specified", ["--model", MODEL])

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp)

    def test_subtype_matrix_covers_model_features(self):
        # modules_matched is |rownames(matrix handed to predict_subtype) ∩ model$coefnames|. Feeding the
        # pancancer enrichment instead of the type-specific one gave ~17 / 1469 here.
        coverage = coverage_by_model(self.response)
        self.assertIn(MODEL, coverage)
        self.assertGreater(coverage[MODEL]["modules_matched"] / coverage[MODEL]["modules_expected"], 0.5)

    def test_meta_reports_headline_coverage(self):
        meta = self.response["meta"][0]
        self.assertGreater(meta["modules_matched"], 0.5 * meta["modules_expected"])
        self.assertFalse(meta["low_coverage"])

    def test_predictions_follow_sample_ids(self):
        # The type enrichment is column-clustered for the heatmap; predictions must still be attached to
        # the right sample. Enrichment, scaling and the forest are column-order independent, so reversing
        # the upload's sample order must not change any sample's label.
        reversed_response = run_classify(self.tmp, "specified_reversed", ["--model", MODEL], reverse_samples=True)
        labels = {r["sampleID"]: r.get("subtypePrediction") for r in self.response["data"]}
        reversed_labels = {r["sampleID"]: r.get("subtypePrediction") for r in reversed_response["data"]}
        self.assertEqual(labels, reversed_labels)

    def test_response_keys_unchanged(self):
        for key in RESPONSE_KEYS:
            self.assertIn(key, self.response)


@unittest.skipUnless(shutil.which("Rscript") and os.path.exists(MODEL_PATH) and os.path.exists(EXAMPLE),
                     "needs Rscript, models.RDS and the GSE123845 example upload")
class TestClassifyPancancer(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.response = run_classify(cls.tmp, "pancancer", [])

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp)

    def test_type_matrices_cover_model_features(self):
        # each predicted type's subtype model must get its own type-specific enrichment (type_splits branch)
        coverage = coverage_by_model(self.response)
        self.assertIn("pancancer", coverage)
        scored = {t.replace(" ", "_").replace("&", "and") for t, s in self.response["type_scores"].items() if s["genes"]}
        type_models = [m for m in coverage if m in scored]
        self.assertTrue(type_models, "no subtype model was run on type-specific scores")
        for m in type_models:
            self.assertGreater(coverage[m]["modules_matched"] / coverage[m]["modules_expected"], 0.5, m)

    def test_unscorable_types_are_flagged(self):
        # e.g. the gene-level cervical model only uses modules smaller than the default min_size=100:
        # it must be reported as low coverage with no label, not silently predicted on noise
        coverage = coverage_by_model(self.response)
        flagged = {m for m, c in coverage.items() if c["low_coverage"]}
        for r in self.response["data"]:
            if (r.get("typePrediction") or "").replace(" ", "_").replace("&", "and") in flagged:
                self.assertIsNone(r.get("subtypePrediction"), r["sampleID"])

    def test_response_keys_unchanged(self):
        for key in RESPONSE_KEYS:
            self.assertIn(key, self.response)


if __name__ == '__main__':
    unittest.main()
