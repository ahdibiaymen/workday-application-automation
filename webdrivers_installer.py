from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
from webdriver_manager.firefox import GeckoDriverManager

DRIVERS_ENV_FILE = "/tmp/custom/web-drivers"


def install_web_driver(requested_browser="firefox"):
    webdriver_installers = {
        "chrome": ChromeDriverManager(
            chrome_type=ChromeType.CHROMIUM
        ).install,
        "firefox": GeckoDriverManager().install,
    }
    path = None

    for webdriver_name in webdriver_installers.keys():
        if webdriver_name == requested_browser.lower():
            try:
                print(
                    f"[INFO] Installing {webdriver_name} web driver"
                )
                path = webdriver_installers[webdriver_name]()
                print(f"[INFO] {webdriver_name} web driver successfully"
                      " installed!")

            except Exception as e:
                raise RuntimeError(
                    "[ERROR] Something went wrong "
                    "while installing {} web driver due"
                    " to the following exception {}".format(webdriver_name, e)
                )
    if path is None:
        raise RuntimeError(
            "[ERROR] Bad browser name "
            "please check the argument browser name passed to this function"
            "and check if the related installer is mentioned in 'webdriver_installers' dictionary"
        )

    return path
