# Core/Features/meta_registry.py

class FeatureMetaRegistry:
    def __init__(self):
        self._meta = {}

    def register(self, cls):
        if not hasattr(cls, "META"):
            raise ValueError(f"{cls.__name__} has no META definition")
        self._meta[cls.__name__] = cls.META
        return cls

    def get_meta(self, name):
        return self._meta.get(name)

    def all(self):
        return self._meta
    
FEATURE_META_REGISTRY = FeatureMetaRegistry()

def register_feature_meta(cls):
    return FEATURE_META_REGISTRY.register(cls)