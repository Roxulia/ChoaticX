# A global registry to hold all indicator classes
FEATURE_REGISTRY = {}

def register_feature(cls):
    """Decorator to register a class in the indicator registry"""
    FEATURE_REGISTRY[cls.__name__] = cls
    return cls

def get_feature(name):
    """Get indicator class by name"""
    return FEATURE_REGISTRY.get(name)

def list_features():
    """Return all available indicator names"""
    return list(FEATURE_REGISTRY.keys())
