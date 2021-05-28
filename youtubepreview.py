from ast import parse
from typing import Type
import urllib.parse, re
from mautrix.types import ImageInfo, EventType, MessageType
from mautrix.util.config import BaseProxyConfig, ConfigUpdateHelper
from maubot import Plugin, MessageEvent
from maubot.handlers import event

class Config(BaseProxyConfig):
    def do_update(self, helper: ConfigUpdateHelper) -> None:
        helper.copy("appid")
        helper.copy("source")
        helper.copy("response_type")


youtube_pattern = re.compile(r"^((?:https?:)?\/\/)?((?:www|m)\.)?((?:youtube\.com|youtu.be))(\/(?:[\w\-]+\?v=|embed\/|v\/)?)([\w\-]+)(\S+)?$")

class YoutubePreviewPlugin(Plugin):
    async def start(self) -> None:
        await super().start()

    @classmethod
    def get_config_class(cls) -> Type[BaseProxyConfig]:
        return Config

    @event.on(EventType.ROOM_MESSAGE)
    async def on_message(self, evt: MessageEvent) -> None:
        if evt.content.msgtype != MessageType.TEXT or evt.content.body.startswith("!"):
            return
        for url_tup in youtube_pattern.findall(evt.content.body):
            await evt.mark_read()
            url = ''.join(url_tup)
            if "youtu.be" in url:
                video_id = url.split("youtu.be/")[1]
            else:
                video_id = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)['v'][0]
            thumbnail_link = "https://img.youtube.com/vi/" + video_id + "/hqdefault.jpg"
            resp = await self.http.get(thumbnail_link)
            if resp.status != 200:
                self.log.warning(f"Unexpected status fetching image {thumbnail_link}: {resp.status}")
                return None
            thumbnail = await resp.read()
            filename = video_id + ".jpg"
            uri = await self.client.upload_media(thumbnail, mime_type='image/jpg', filename=filename)
            await self.client.send_image(evt.room_id, url=uri, file_name=filename, info=ImageInfo(
                    mimetype='image/jpg'
                ))