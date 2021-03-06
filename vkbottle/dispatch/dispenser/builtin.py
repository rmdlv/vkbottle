from typing import Dict, Optional

from vkbottle_types import BaseStateGroup, StatePeer

from .abc import ABCStateDispenser


class BuiltinStateDispenser(ABCStateDispenser):
    def __init__(self):
        super().__init__()
        self.dictionary: Dict[int, StatePeer] = {}

    async def get(self, peer_id: int) -> Optional[StatePeer]:
        return self.dictionary.get(peer_id)

    async def set(self, peer_id: int, state: BaseStateGroup, **payload):
        self.dictionary[peer_id] = StatePeer(peer_id=peer_id, state=state, payload=payload)

    async def delete(self, peer_id: int):
        self.dictionary.pop(peer_id)
