from Exceptions.ServiceExceptions import asyncerrorHandling
from .registry import get_modifier
import asyncio
class Modifier:
    def __init__(self,configs = None):
        self.configs = configs or []
        self.initialize()

    @asyncerrorHandling
    async def add(self,data):
        for k,v in self.modifiers.items() :
            data = await v.get(data)
        return data
    
    def initialize(self):
        self.modifiers = {}
        for modifier in self.configs:
            if modifier["enabled"]:
                cls_name = modifier['name']
                params = modifier['params']
                cls = get_modifier(cls_name)
                # print({cls_name : cls})
                if cls is not None:
                    self.modifiers[cls_name] = cls(**params)
        

