from . import WitWorldImpl, MetadataImpl

try:
    import wit_world
except ImportError:
    from .wit import wit_world

class WitWorld(WitWorldImpl, wit_world.WitWorld):
    pass

class Metadata(MetadataImpl, wit_world.exports.Metadata):
    pass
