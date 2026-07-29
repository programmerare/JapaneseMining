from config import load_config
from services import HyperTTSService, CollectionService, DeeplService


def setup_addon():
    config = load_config()

    # Create services
    collection_service = CollectionService(config)
    deepl_service = DeeplService(config)
    # jisho_service = JishoService(config)
    hypertts_service = HyperTTSService(config)