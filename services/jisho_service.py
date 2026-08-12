from ..AJC.runtime.bootstrap import initialize_ajc
from ..AJC.runtime.config_holder import set_runtime_config
from ..config import ConfigHolder
from ..jisho_adapter import to_ajc_runtime_config


class JishoService:
    def __init__(self, config_holder: ConfigHolder):
        self._config_holder = config_holder

    @property
    def _config(self):
        return self._config_holder.config

    def initialize(self):
        """Initialize the JishoService, ensuring that the AJC runtime is set up."""
        if not self._config.use_jisho:
            return

        runtime = to_ajc_runtime_config(self._config)
        set_runtime_config(runtime)
        initialize_ajc(runtime)
