import os
import subprocess
import time

from PIL import Image, ImageDraw, ImageFont
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from loguru import logger
import configparser
from grepy.gre2 import get_words_only


class WallpaperUpdater(FileSystemEventHandler):
    """Wallpaper updater."""

    def __init__(
        self,
        text_file_path: str,
        image_path: str,
        base_path: str,
        font_type: str,
        font_size: int,
        font_color: str,
        dark_mode: bool = True,
    ):
        self.text_file_path = text_file_path
        self.ground_wallpaper = image_path
        self.base_path = base_path
        self.font_type = font_type
        self.font_size = font_size
        self.font_color = font_color
        self.start_pos = (0, 0)
        if dark_mode:
            self.command = (
                f"gsettings set org.gnome.desktop.background picture-uri-dark"
            )
        else:
            self.command = f"gsettings set org.gnome.desktop.background picture-uri"

    def on_modified(self, event):
        if event.src_path == self.text_file_path:
            self.update_wallpaper()

    def write_text(self, text: str, image: Image) -> Image:
        # add the text to the image
        image_size = image.size
        draw = ImageDraw.Draw(image)
        font = ImageFont.truetype(
            self.font_type, size=self.font_size
        )  # choose a font and font size
        text_size = draw.textbbox(self.start_pos, text=text, font=font)
        text_position = (
            int((image_size[0] - text_size[0]) * 0.3),
            int((image_size[1] - text_size[1]) * 0.1),
        )  # center the text
        # logger.info(text_size)
        # logger.info(text_position)
        draw.text(text_position, text, font=font, fill=self.font_color)
        return image

    def update_wallpaper(self):
        # read the text from the file
        with open(self.text_file_path, "r") as f:
            texts = f.readlines()
        text = "".join(texts)
        # logger.info(text)
        # set up the image
        image = Image.open(self.ground_wallpaper)
        image = self.write_text(text, image)
        # save the image
        image_path = os.path.join(self.base_path, "output_image.jpg")
        image.save(image_path)

        # set the wallpaper
        shell_command = f"{self.command} file://{image_path}"
        subprocess.call(shell_command, shell=True)


if __name__ == "__main__":
    logger.info(f"Running the wallpaper updater.")
    config = configparser.ConfigParser()
    base_path = os.path.abspath(os.path.dirname(__file__))
    config_path = os.path.join(base_path, "config.ini")
    logger.info(f"reading config from {config_path}")
    config.read(config_path)
    text_file = config.get("Settings", "text_file")
    image_file = config.get("Settings", "image_file")
    font_file = config.get("Settings", "font_file")
    font_size = config.getint("Settings", "font_size")
    font_color = config.get("Settings", "font_color")
    text_file_path = os.path.join(base_path, text_file)
    wmap = get_words_only(n=5)
    with open(text_file_path, "w") as f:
        for word in wmap:
            f.write(f"{word}::{wmap[word]}\n")
    image_path = os.path.join(base_path, image_file)
    font_file_path = os.path.join(base_path, font_file)
    # initial update of the wallpaper
    logger.info(f"Text file path -> {text_file_path}.")
    logger.info(f"Image file path -> {image_path}.")
    updater = WallpaperUpdater(
        text_file_path,
        image_path,
        base_path=base_path,
        font_type=font_file_path,
        font_size=font_size,
        font_color=font_color,
    )
    updater.update_wallpaper()

    # start the observer to monitor the text file
    observer = Observer()
    observer.schedule(updater, path=os.path.dirname(text_file_path), recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
