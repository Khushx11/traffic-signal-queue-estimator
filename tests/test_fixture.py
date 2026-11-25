import json
from pathlib import Path
import unittest

from scripts.run_fixture import run


class SyntheticRecoveryTests(unittest.TestCase):
    def test_recovery_uses_only_observed_history_and_ends_at_discharge(self):
        source = Path(__file__).resolve().parents[1] / "fixtures/occlusion.json"
        scenario = json.loads(source.read_text())
        recovered = run(scenario, 1.0)
        unavailable = run(scenario, 0.0)
        self.assertEqual(recovered[4]["recovered_ids"], [1])
        self.assertEqual(recovered[4]["count"], 2)
        self.assertEqual(unavailable[4]["state"], "uncertain")
        self.assertEqual(recovered[6]["count"], 0)
