import selenium.common.exceptions as selenium_exceptions
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
import yaml


class WorkdayAutofill:
    def __init__(self, application_link, resume_path):
        self.application_link = application_link
        self.resume_path = resume_path
        self.driver = webdriver.Firefox()
        self.resume_data = None
        self.current_url = None

        self.load_resume()

    def load_resume(self):
        with open(self.resume_path) as resume:
            try:
                self.resume_data = yaml.safe_load(resume)
            except yaml.YAMLError as e:
                print(e)

    def locate_and_fill(self, element_xpath, input_data):
        try:
            element = self.driver.find_element(By.XPATH, element_xpath)
        except selenium_exceptions.NoSuchElementException:
            raise RuntimeError(
                f"Cannot locate element '{element_xpath}' in the following page : {self.driver.current_url}"
            )
        else:
            element.send_keys(input_data)

    def locate_dropdown_and_fill(self, element_xpath, select_value):
        try:
            select = Select(self.driver.find_element(By.XPATH, element_xpath))
        except selenium_exceptions.NoSuchElementException:
            raise RuntimeError(
                f"Cannot locate element '{element_xpath}' in the following page : {self.driver.current_url}"
            )
        else:
            select.select_by_value(select_value)

    def locate_and_click(self, button_xpath):
        try:
            clickable_element = self.driver.find_element(By.XPATH, button_xpath)
        except selenium_exceptions.NoSuchElementException:
            raise RuntimeError(
                f"Cannot locate submit button '{button_xpath}' in the following page : {self.driver.current_url}"
            )
        else:
            clickable_element.click()

    def login(self, email, password):
        email_xpath = '//input[@data-automation-id="email"]'
        password_xpath = '//input[@data-automation-id="password"]'
        submit_xpath = '//div[@data-automation-id="click_filter"]'
        # locate email input & fill
        self.locate_and_fill(email_xpath, email)
        # locate password input & fill
        self.locate_and_fill(password_xpath, password)
        # submit
        self.locate_and_click(submit_xpath)

    def fill_my_information_page(self):
        # How Did You Hear About Us
        self.locate_dropdown_and_fill(
            '//button[@data-automation-id="sourceDropdown" and contains(aria-label,"About Us")]',
            self.resume_data["my-information"]["source"])

        # Previous work
        if self.resume_data["my-information"]["source"]:
            previous_work_xpath = '//div[@data-automation-id="previousWorker"]//input[@id=1]'
        else:
            previous_work_xpath = '//div[@data-automation-id="previousWorker"]//input[@id=2]'
        self.locate_and_click(previous_work_xpath)

        # Country
        self.locate_dropdown_and_fill(
            '//button[@data-automation-id="countryDropdown"]',
            self.resume_data["my-information"]["country"]
        )

        # ****** Address ******
        # Line 1
        '//input[@data-automation-id="addressSection_addressLine1"]'
        # City
        '//input[@data-automation-id="addressSection_city"]'
        # State
        '//button[@data-automation-id="addressSection_countryRegion"]'
        # Zip
        '//input[@data-automation-id="addressSection_postalCode"]'
        # ****** Phone ******
        # Device
        '//button[@data-automation-id="phone-device-type"]'
        # Code
        # Number
        # Extension


    def start_application(self):
        self.driver.get(self.application_link)

        self.login(
            self.resume_data["account"]["email"],
            self.resume_data["account"]["password"]
        )

        self.fill_my_information_page()

        # exit
        self.driver.quit()


if __name__ == '__main__':
    APPLICATION_LINK = "https://bloomenergy.wd1.myworkdayjobs.com/en-US/BloomEnergyCareers/login?redirect=%2Fen-US%2FBloomEnergyCareers%2Fjob%2FSan-Jose%252C-California%2FIT-Software-Engineer---New-College-Grad_JR-17774%2Fapply%2FapplyManually"
    RESUME_PATH = "resume.yml"
    s = WorkdayAutofill(
        application_link=APPLICATION_LINK,
        resume_path=RESUME_PATH
    )
    s.start_application()
    print("hello")
