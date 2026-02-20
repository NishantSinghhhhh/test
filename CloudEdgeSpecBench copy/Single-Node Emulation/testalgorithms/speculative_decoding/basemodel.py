"""
Base Model Interface for Ianvs

Standard interface that all algorithm implementations must follow.
This ensures compatibility with the Ianvs benchmarking framework.
"""


class BaseModel:
    """
    Abstract base class for Ianvs algorithm implementations.
    
    All schedulers (speculative, baseline, etc.) inherit from this
    to ensure they implement the required interface.
    """
    
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
        
        Override this in subclasses if needed.
        """
        pass

    def train(self, train_data, valid_data=None, **kwargs):
        """
        Train the model.
        
        Args:
            train_data: Training dataset
            valid_data: Validation dataset (optional)
            **kwargs: Additional training parameters
            
        Returns:
            self: The trained model instance
        """
        raise NotImplementedError("train() must be implemented by subclass")

    def predict(self, input_data, **kwargs):
        """
        Main inference function.
        
        Args:
            input_data: The input prompt/data
            **kwargs: Additional inference parameters
            
        Returns:
            dict or list: The inference results (latencies, accuracy, etc.)
        """
        raise NotImplementedError("predict() must be implemented by subclass")
    
    def save(self, model_path):
        """
        Save model to disk.
        
        Args:
            model_path (str): Path to save the model
            
        Returns:
            str: The path where model was saved
        """
        raise NotImplementedError("save() must be implemented by subclass")
    
    def load(self, model_path):
        """
        Load model from disk.
        
        Args:
            model_path (str): Path to load the model from
            
        Returns:
            self: The loaded model instance
        """
        raise NotImplementedError("load() must be implemented by subclass")


# Example usage (for documentation)
if __name__ == "__main__":
    print("BaseModel Interface:")
    print("  - train(train_data, valid_data, **kwargs) -> self")
    print("  - predict(input_data, **kwargs) -> results")
    print("  - save(model_path) -> path")
    print("  - load(model_path) -> self")
    print("\nAll schedulers must implement these methods.")