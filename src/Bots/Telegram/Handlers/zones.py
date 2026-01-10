from .base import BaseHandler
from Utility.UtilityClass import UtilityFunctions as utility
from Exceptions.ServiceExceptions import NoUntouchedZone

class ZoneHandlers(BaseHandler):

    async def _zones(self, update, context, service, title):
        message = self.get_message(update)
        zones = await service.zoneHandler.get_untouched_zones(limit=5)
        msg = f"📊 *Recent {title} Zones*\n\n"

        for i, z in enumerate(zones[:4], 1):
            msg += (
                f"*Zone {i}*\n"
                f"• Type: `{utility.escape_md(z['zone_type'])}`\n"
                f"• High: `{z['zone_high']}`\n"
                f"• Low: `{z['zone_low']}`\n\n"
            )

        await message.reply_text(msg, parse_mode="MarkdownV2")

    def btc(self, service):
        @self.restricted(for_starter=True)
        async def handler(update, context, user):
            await self._zones(update, context, service, "BTCUSDT")
        return handler
