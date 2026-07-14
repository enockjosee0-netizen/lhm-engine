"""Lightweight stub for lhm_modular.features."""
import logging
log = logging.getLogger("LHM.lhm_modular.features")

class FeatureEngine:
    @staticmethod
    def build_features(match_row, state):
        log.debug("lhm_modular.features stub used.")
        return {}

    @staticmethod
    def feature_order():
        return []
