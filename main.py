import requests, shutil, ctypes, platform, os, subprocess, time
from pathlib import Path
from PIL import Image
from config import *

def detect_desktop_environment():
    if platform.system() == "Windows":
        return "windows"

    desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
    if "kde" in desktop:
        return "kde"
    elif "gnome" in desktop:
        return "gnome"
    elif "mate" in desktop:
        return "mate"
    elif "xfce" in desktop:
        return "xfce"
    else:
        try:
            if shutil.which("plasmashell"):
                return "kde"
            elif shutil.which("gnome-shell"):
                return "gnome"
            elif shutil.which("mate-session"):
                return "mate"
            elif shutil.which("xfce4-session"):
                return "xfce"
        except:
            pass

    return "unknown"


def get_new_wallpaper_url():
    response = requests.get(API_URL, timeout=15)
    response.raise_for_status()
    data = response.json()

    try:
        return data["url"]
    except KeyError:
        raise ValueError("API не вернуло поле 'url'")


def download_image(url, save_path):
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    with open(save_path, "wb") as handler:
        handler.write(response.content)

    print(f"Изображение сохранено: {save_path}")


def get_screen_resolution(desktop_env):
    if desktop_env == "windows":
        user32 = ctypes.windll.user32
        return (user32.GetSystemMetrics(0), user32.GetSystemMetrics(1))
    else:
        try:
            output = subprocess.check_output(["xrandr"]).decode()
            for line in output.splitlines():
                if '*' in line:
                    parts = line.split()
                    width = int(parts[parts.index('current') + 1])
                    height = int(parts[parts.index('current') + 3].replace(',', ''))
                    return (width, height)
        except:
            pass
        return (1920, 1080)


def prepare_image(src_path, screen_size, desktop_env, mode=WALLPAPER_MODE):
    with Image.open(src_path) as img:
        img = img.convert("RGB")

        screen_width, screen_height = screen_size

        if mode == "stretch":
            new_img = img.resize(
                (screen_width, screen_height),
                Image.LANCZOS
            )

        elif mode == "fit":
            ratio_w = screen_width / img.width
            ratio_h = screen_height / img.height
            scale_ratio = min(ratio_w, ratio_h)

            new_width = int(img.width * scale_ratio)
            new_height = int(img.height * scale_ratio)

            img = img.resize(
                (new_width, new_height),
                Image.LANCZOS
            )

            new_img = Image.new(
                "RGB",
                screen_size,
                (0, 0, 0)
            )

            offset = (
                (screen_width - new_width) // 2,
                (screen_height - new_height) // 2
            )

            new_img.paste(img, offset)

        elif mode == "fill":
            ratio_w = screen_width / img.width
            ratio_h = screen_height / img.height
            scale_ratio = max(ratio_w, ratio_h)

            new_width = int(img.width * scale_ratio)
            new_height = int(img.height * scale_ratio)

            img = img.resize(
                (new_width, new_height),
                Image.LANCZOS
            )

            left = (new_width - screen_width) // 2
            top = (new_height - screen_height) // 2

            new_img = img.crop((
                left,
                top,
                left + screen_width,
                top + screen_height
            ))

        else:
            raise ValueError(
                f"Неизвестный режим обоев: {mode}"
            )

        if desktop_env == "windows":
            dst_path = src_path.with_suffix(".bmp")
            new_img.save(dst_path, "BMP")
        else:
            dst_path = src_path.with_suffix(".jpg")
            new_img.save(dst_path, "JPEG", quality=95)

        return dst_path


def set_wallpaper_windows(image_path):
    abs_path = str(image_path.resolve())
    result = ctypes.windll.user32.SystemParametersInfoW(20, 0, abs_path, 3)
    if result:
        print(f"Обои установлены: {abs_path}")
    else:
        print("Не удалось установить обои")


def set_wallpaper_kde(image_path):
    abs_path = str(image_path.resolve())

    set_cmd = f"""
    qdbus org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.evaluateScript '
    var allDesktops = desktops();
    for (i=0;i<allDesktops.length;i++) {{
        d = allDesktops[i];
        d.wallpaperPlugin = "org.kde.image";
        d.currentConfigGroup = Array("Wallpaper", "org.kde.image", "General");
        d.writeConfig("Image", "file://{abs_path}");
        d.writeConfig("FillMode", "2");  // 0=растянуть, 1=заполнить, 2=вписать
    }}'
    """

    try:
        subprocess.run("qdbus org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.evaluateScript 'var allDesktops = desktops();for (i=0;i<allDesktops.length;i++) {d = allDesktops[i];d.currentConfigGroup = Array(\"Wallpaper\", \"org.kde.image\", \"General\");d.writeConfig(\"Image\", \"\")}'",
                      shell=True, check=False)

        subprocess.run(set_cmd, shell=True, check=True)
        print(f"Обои успешно установлены: {abs_path}")
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при установке обоев: {e}")
        raise Exception("Не удалось установить обои")


def set_wallpaper_gnome(image_path):
    abs_path = str(image_path.resolve())
    try:
        subprocess.run(["gsettings", "set", "org.gnome.desktop.background", "picture-uri", f"file://{abs_path}"], check=True)
        subprocess.run(["gsettings", "set", "org.gnome.desktop.background", "picture-options", "zoom"], check=True)
        print(f"Обои успешно установлены в GNOME: {abs_path}")
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при установке обоев в GNOME: {e}")
        raise Exception("Не удалось установить обои в GNOME")

def set_wallpaper_mate(image_path):
    abs_path = str(image_path.resolve())

    try:
        subprocess.run(["gsettings", "set", "org.mate.background", "picture-filename", abs_path], check=True)
        subprocess.run(["gsettings", "set", "org.mate.background", "picture-options", "zoom"], check=True)
        print(f"Обои успешно установлены в MATE: {abs_path}")
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при установке обоев в MATE: {e}")
        raise Exception("Не удалось установить обои в MATE")

def set_wallpaper_xfce(image_path):
    abs_path = str(image_path.resolve())

    try:
        output = subprocess.check_output(
            ["xfconf-query", "-c", "xfce4-desktop", "-l"],
            text=True
        )

        properties = [
            line.strip()
            for line in output.splitlines()
            if line.strip().endswith("/last-image")
        ]

        for prop in properties:
            subprocess.run(
                ["xfconf-query", "-c", "xfce4-desktop",
                 "-p", prop, "-s", abs_path],
                check=True
            )

        for prop in properties:
            style_prop = prop.replace("/last-image", "/image-style")

            subprocess.run(
                ["xfconf-query", "-c", "xfce4-desktop",
                 "-p", style_prop, "-s", "3"],
                check=False
            )

        print(f"Обои успешно установлены в XFCE: {abs_path}")

    except subprocess.CalledProcessError as e:
        print(f"Ошибка при установке обоев в XFCE: {e}")
        raise Exception("Не удалось установить обои в XFCE")

def cleanup_old_wallpapers(wallpapers_dir: Path, keep_file: Path):
    for file in wallpapers_dir.iterdir():
        if file != keep_file and file.is_file():
            try:
                file.unlink()
                print(f"Удален старый файл: {file.name}")
            except Exception as e:
                print(f"Не удалось удалить {file.name}: {e}")


def main_loop(interval_seconds=INTERVAL_SECONDS):
    desktop_env = detect_desktop_environment()
    print(f"Определена графическая среда: {desktop_env}")

    if desktop_env == "windows":
        wallpapers_dir = Path("wallpapers")
        set_wallpaper = set_wallpaper_windows
    else:
        wallpapers_dir = Path.home() / ".local" / "share" / "wallpapers"
        if desktop_env == "kde":
            set_wallpaper = set_wallpaper_kde
        elif desktop_env == "gnome":
            set_wallpaper = set_wallpaper_gnome
        elif desktop_env == "mate":
            set_wallpaper = set_wallpaper_mate
        elif desktop_env == "xfce":
            set_wallpaper = set_wallpaper_xfce
        else:
            set_wallpaper = None

    if set_wallpaper is None:
        print(f"Извините, ваша графическая среда ({desktop_env}) пока не поддерживается")
        return

    wallpapers_dir.mkdir(exist_ok=True, parents=True)
    current_wallpaper = None

    while True:
        screen_size = get_screen_resolution(desktop_env)
        try:
            img_url = get_new_wallpaper_url()
            file_name = img_url.split("/")[-1]
            save_path = wallpapers_dir / file_name

            if current_wallpaper:
                cleanup_old_wallpapers(wallpapers_dir, current_wallpaper)

            download_image(img_url, save_path)
            wallpaper_path = prepare_image(save_path, screen_size, desktop_env)
            set_wallpaper(wallpaper_path)

            current_wallpaper = wallpaper_path
        except Exception as e:
            print(f"Произошла ошибка: {e}")

        print(f"Ожидание {interval_seconds} секунд до следующего обновления...")
        time.sleep(interval_seconds)


try:
    print("Запуск автоматической смены обоев")
    print("Для остановки нажмите Ctrl+C")
    main_loop()
except KeyboardInterrupt:
    print("\nРабота программы завершена")
