TA_INDICATORS_REGISTRY = {}

def register_indicator(cls):
    """Decorator to register a class in the indicator registry"""
    TA_INDICATORS_REGISTRY[cls.__name__] = cls
    return cls

def get_indicator(name):
    """Get indicator class by name"""
    return TA_INDICATORS_REGISTRY.get(name,None)

def list_indicators():
    """Return all available indicator names"""
    return list(TA_INDICATORS_REGISTRY.keys())