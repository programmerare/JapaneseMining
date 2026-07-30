from ..AJC.runtime.bootstrap import initialize_ajc
from ..config import Config

class JishoService:
    def __init__(self, config: Config):
        self._config = config

    def initialize(self):
        """Initialize the JishoService, ensuring that the AJC runtime is set up."""
        initialize_ajc()