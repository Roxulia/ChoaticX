REGIME_REGISTRY = {}

def register_regime(cls):
    """Decorator to register a class in the regime registry"""
    REGIME_REGISTRY[cls.__name__] = cls
    return cls

def get_regime(name):
    """Get regime class by name"""
    return REGIME_REGISTRY.get(name,None)

def list_regimes():
    """Return all available regime names"""
    return list(REGIME_REGISTRY.keys())