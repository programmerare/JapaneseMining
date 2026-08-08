from ..AJC.runtime.bootstrap import initialize_ajc
from ..AJC.runtime.config_holder import set_runtime_config
from ..config import Config
from ..jisho_adapter import to_ajc_runtime_config

class JishoService:
    def __init__(self, config: Config):
        self._config = config

    def initialize(self):
        """Initialize the JishoService, ensuring that the AJC runtime is set up."""
        if not self._config.use_jisho:
            return

        runtime = to_ajc_runtime_config(self._config)
        set_runtime_config(runtime)
        initialize_ajc(runtime)