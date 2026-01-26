MODIFIER_REGISTRY = {}

def register_modifier(cls):
    """Decorator to register a class in the modifier registry"""
    MODIFIER_REGISTRY[cls.__name__] = cls
    return cls

def get_modifier(name):
    """Get modifier class by name"""
    return MODIFIER_REGISTRY.get(name,None)

def list_modifiers():
    """Return all available modifier names"""
    return list(MODIFIER_REGISTRY.keys())