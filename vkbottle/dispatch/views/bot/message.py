from abc import ABC
from typing import Any, Callable, List, Optional, Set, Type

from vkbottle_types.events import GroupEventType

from vkbottle.api.abc import ABCAPI
from vkbottle.dispatch.dispenser.abc import ABCStateDispenser
from vkbottle.dispatch.handlers import ABCHandler
from vkbottle.dispatch.middlewares import BaseMiddleware
from vkbottle.dispatch.return_manager.bot import BotMessageReturnHandler
from vkbottle.modules import logger
from vkbottle.tools.dev_tools import message_min
from vkbottle.tools.dev_tools.mini_types.bot import MessageMin

from ..abc_dispense import ABCDispenseView

DEFAULT_STATE_KEY = "peer_id"


class ABCMessageView(ABCDispenseView, ABC):
    def __init__(self):
        super().__init__()
        self.state_source_key = DEFAULT_STATE_KEY
        self.handlers: List["ABCHandler"] = []
        self.middlewares: Set[Type["BaseMiddleware"]] = set()
        self.middleware_instances: List["BaseMiddleware"] = []
        self.default_text_approximators: List[Callable[[MessageMin], str]] = []
        self.handler_return_manager = BotMessageReturnHandler()
        self.middleware_instances = []

    async def process_event(self, event: dict) -> bool:
        return GroupEventType(event["type"]) == GroupEventType.MESSAGE_NEW

    async def handle_event(
        self, event: dict, ctx_api: "ABCAPI", state_dispenser: "ABCStateDispenser"
    ) -> Any:

        logger.debug("Handling event ({}) with message view".format(event.get("event_id")))
        context_variables: dict = {}
        message = message_min(event, ctx_api)
        message.state_peer = await state_dispenser.cast(self.get_state_key(event))

        for text_ax in self.default_text_approximators:
            message.text = text_ax(message)

        if await self.pre_middleware(message, context_variables) is False:
            return logger.info("Handling stopped, pre_middleware returned error")

        handle_responses = []
        handlers = []

        for handler in self.handlers:
            result = await handler.filter(message)
            logger.debug("Handler {} returned {}".format(handler, result))

            if result is False:
                continue

            elif isinstance(result, dict):
                context_variables.update(result)

            handler_response = await handler.handle(message, **context_variables)
            handle_responses.append(handler_response)
            handlers.append(handler)

            return_handler = self.handler_return_manager.get_handler(handler_response)
            if return_handler is not None:
                await return_handler(
                    self.handler_return_manager, handler_response, message, context_variables
                )

            if handler.blocking:
                break

        await self.post_middleware(self, handle_responses, handlers)


class MessageView(ABCMessageView):
    def get_state_key(self, event: dict) -> Optional[int]:
        return event["object"]["message"].get(self.state_source_key)
