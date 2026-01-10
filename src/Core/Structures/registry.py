STRUCTURE_REGISTRY = {}

def register_structure(cls):
    """Decorator to register a class in the structure registry"""
    STRUCTURE_REGISTRY[cls.__name__] = cls
    return cls

def get_structure(name):
    """Get structure class by name"""
    return STRUCTURE_REGISTRY.get(name)

def list_structures():
    """Return all available structure names"""
    return list(STRUCTURE_REGISTRY.keys())