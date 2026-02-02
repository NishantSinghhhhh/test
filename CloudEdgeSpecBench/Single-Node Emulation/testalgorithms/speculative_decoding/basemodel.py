# Standard Interface for Ianvs Algorithms
# This acts as a blueprint that our specific Scheduler must follow.

class BaseModel:
    def __init__(self, config):
        """
        Base initialization.
        Args:
            config (dict): Configuration dictionary from algorithm.yaml
        """
        self.config = config
        self.model_loaded = False

    def load_model(self):
        """
        Placeholder for loading model weights.
        """
        pass

    def predict(self, input_data, network_env):
        """
        Main inference function.
        Args:
            input_data: The input prompt/data.
            network_env: The simulated network environment.
        Returns:
            dict: The inference results (latencies, accuracy, etc.)
        """
        raise NotImplementedError("You must implement the predict method in your Scheduler.")