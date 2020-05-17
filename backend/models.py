from pathlib import Path
from typing import Dict, Iterator, List, Optional

import aiofiles
import aiohttp
import log
from aiofiles import os
from datafiles import converters, datafile, field
from sanic import Sanic

from backend import settings
from . import images


@datafile
class Text:

    color: str = "white"

    anchor_x: float = 0.1
    anchor_y: float = 0.1

    angle: float = 0

    scale_x: float = 0.8
    scale_y: float = 0.2


@datafile("../templates/{self.key}/config.yml")
class Template:

    key: str
    name: str = ""
    source: Optional[str] = None
    text: List[Text] = field(default_factory=lambda: [Text(), Text()])
    styles: List[str] = field(default_factory=lambda: ["default"])
    sample: List[str] = field(default_factory=lambda: ["YOUR TEXT", "GOES HERE"])

    @property
    def valid(self) -> bool:
        return bool(self.name and not self.name.startswith("<"))

    @property
    def background_image_path(self) -> Path:
        for ext in ["png", "jpg"]:
            path = self.datafile.path.parent / f"default.{ext}"
            if path.exists():
                return path
        raise ValueError(f"No background image for template: {self}")

    def jsonify(self, app: Sanic) -> Dict:
        return {
            "name": self.name,
            "styles": [s for s in self.styles if s != "default"],
            "blank": app.url_for("images.blank", key=self.key, _external=True),
            "sample": self.build_sample_url(app),
            "source": self.source,
            "_self": app.url_for("templates.detail", key=self.key, _external=True),
        }

    def build_sample_url(self, app: Sanic) -> str:
        return app.url_for(
            "images.text",
            key=self.key,
            lines="/".join(self._encode(*self.sample)),
            _external=True,
        )

    async def render(self, lines: str) -> Path:
        image_path = Path(f"images/{self.key}/{lines}.jpg")
        image_path.parent.mkdir(parents=True, exist_ok=True)

        # TODO: handle external images
        # background_image_path = self._get_background_image_path()
        # background_image_url = f"{settings.IMAGES_URL}/{background_image_path}"
        # log.debug(f"Fetching background image: {background_image_url}")

        # async with aiohttp.ClientSession() as session:
        #     async with session.get(background_image_url) as response:
        #         if response.status == 200:
        #             f = await aiofiles.open(image_path, mode="wb")
        #             await f.write(await response.read())
        #             await f.close()
        #             images.render_legacy(image_path, lines)

        image = images.render(self, lines)
        image.save(image_path)

        return image_path

    @staticmethod
    def _encode(*lines: str) -> Iterator[str]:
        for line in lines:
            if line:
                yield line.lower().replace(" ", "_").replace("?", "~q")
            else:
                yield "_"
