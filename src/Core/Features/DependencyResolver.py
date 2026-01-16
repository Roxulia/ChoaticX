

from .meta_registry import FEATURE_META_REGISTRY

class DependencyResolver:

    def resolve(self, target_classes, config):
        required = set()

        for cls in target_classes:
            meta = FEATURE_META_REGISTRY.get_meta(cls.__name__)
            req = meta.get("requires", set())
            required |= req(config) if callable(req) else req

        execution = []
        resolved = set()

        while required:
            progress = False

            for name, meta in FEATURE_META_REGISTRY.all().items():
                provides = meta.get("provides", set())
                provides = provides(config) if callable(provides) else provides

                if required & provides:
                    execution.append(name)
                    resolved |= provides
                    required -= provides
                    progress = True

            if not progress:
                raise Exception(f"Unresolvable dependencies: {required}")

        return execution
