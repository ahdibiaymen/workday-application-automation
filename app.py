import time

import selenium.common.exceptions as selenium_exceptions
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver import Keys
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils import check_element_text_is_empty
import yaml

from webdrivers_installer import install_web_driver


class PageStep:
    def __init__(self, action, params, options=None):
        self.action = action
        self.params = params
        if options is None:
            self.options = {}
        else:
            self.options = options


class WorkdayAutofill:
    def __init__(self, application_link, resume_path):
        self.application_link = application_link
        self.resume_path = resume_path
        self.driver = WorkdayAutofill.create_webdriver("chrome")
        self.resume_data = self.load_resume()
        self.current_url = None
        self.ELEMENT_WAITING_TIMEOUT = 5
        self.IMPLICIT_FILLING_WAIT = 3

    @classmethod
    def create_webdriver(cls, browser_name):
        try:
            if browser_name.lower() == "firefox":
                driver = webdriver.Firefox()
            elif browser_name.lower() == "chrome":
                driver = webdriver.Chrome()
            else:
                raise RuntimeError(f"{browser_name} is not supported !")
        except selenium_exceptions.WebDriverException:
            # trying to install the web driver if not installed in the system
            if browser_name.lower() == "firefox":
                web_driver_path = install_web_driver(requested_browser=browser_name)
                driver = webdriver.Firefox(service=FirefoxService(executable_path=web_driver_path))
            elif browser_name.lower() == "chrome":
                web_driver_path = install_web_driver(requested_browser=browser_name)
                driver = webdriver.Chrome(service=ChromeService(executable_path=web_driver_path))
            else:
                raise RuntimeError(f"{browser_name} is not supported !")
        else:
            return driver

    def load_resume(self):
        with open(self.resume_path) as resume:
            try:
                return yaml.safe_load(resume)
            except yaml.YAMLError as e:
                print(e)

    def load_work_experiences(self):
        try:
            works = self.resume_data["my-experience"]["work-experiences"]
            return [work_dict[f"work{idx}"] for idx, work_dict in enumerate(works, start=1)]
        except KeyError:
            raise ValueError("Something went wrong while parsing your resume.yml WORK-EXPERIENCE"
                             f" -> please review the works order !")

    def load_education_experiences(self):
        try:
            educations = self.resume_data["my-experience"]["education-experiences"]
            return [education_dict[f"education{idx}"] for idx, education_dict in enumerate(educations, start=1)]
        except KeyError:
            raise ValueError("Something went wrong while parsing your resume.yml EDUCATION-EXPERIENCES"
                             f" -> please review the educations order !")

    def load_languages(self):
        try:
            languages = self.resume_data["my-experience"]["languages"]
            return [language_dict[f"language{idx}"] for idx, language_dict in enumerate(languages, start=1)]
        except KeyError:
            raise ValueError("Something went wrong while parsing your resume.yml LANGUAGES"
                             f" -> please review the languages order !")

    def locate_and_fill(self, element_xpath, input_data, kwoptions):
        try:
            element = WebDriverWait(self.driver, self.ELEMENT_WAITING_TIMEOUT).until(
                EC.presence_of_element_located((By.XPATH, element_xpath)))
        except (selenium_exceptions.NoSuchElementException, selenium_exceptions.TimeoutException):
            if not kwoptions.get("required"):
                return
            raise RuntimeError(
                f"Cannot locate element '{element_xpath}' in the following page : {self.driver.current_url}"
            )
        else:
            if kwoptions.get("only_if_empty") and not check_element_text_is_empty(element):
                # quit if the element is already filled
                return
            if input_data:
                if "input" in element_xpath:
                    self.driver.execute_script(
                        'arguments[0].value="";', element)
                element.send_keys(input_data)
            if kwoptions.get("press_enter"):
                element.send_keys(Keys.ENTER)

    def locate_dropdown_and_fill(self, element_xpath, input_data, kwoptions):
        try:
            element = WebDriverWait(self.driver, self.ELEMENT_WAITING_TIMEOUT).until(
                EC.presence_of_element_located((By.XPATH, element_xpath)))
        except (selenium_exceptions.NoSuchElementException, selenium_exceptions.TimeoutException):
            raise RuntimeError(
                f"Cannot locate element '{element_xpath}' in the following page : {self.driver.current_url}"
            )
        else:
            self.driver.execute_script("arguments[0].click();", element)
            element.send_keys(input_data)
            if kwoptions.get("value_is_pattern"):
                select_xpath = f'//div[contains(text(),"{input_data}")'
            else:
                select_xpath = f'//div[text()="{input_data}"]'
            try:
                choice = WebDriverWait(self.driver, self.ELEMENT_WAITING_TIMEOUT).until(
                    EC.presence_of_element_located((By.XPATH, select_xpath)))
            except (selenium_exceptions.NoSuchElementException, selenium_exceptions.TimeoutException):
                raise RuntimeError(
                    f"Cannot locate option: >'{input_data}'< in the following drop down : {element_xpath}"
                    " Check your resume data"
                )
            else:
                self.driver.execute_script("arguments[0].click();", choice)

    def locate_and_click(self, button_xpath):
        try:
            clickable_element = WebDriverWait(self.driver, self.ELEMENT_WAITING_TIMEOUT).until(
                EC.presence_of_element_located((By.XPATH, button_xpath)))
        except (selenium_exceptions.NoSuchElementException, selenium_exceptions.TimeoutException):
            raise RuntimeError(
                f"Cannot locate submit button '{button_xpath}' in the following page : {self.driver.current_url}"
            )
        else:
            self.driver.execute_script("arguments[0].click();", clickable_element)

    def locate_and_upload(self, button_xpath, file_location):
        try:
            element = WebDriverWait(self.driver, self.ELEMENT_WAITING_TIMEOUT).until(
                EC.presence_of_element_located((By.XPATH, button_xpath)))
        except (selenium_exceptions.NoSuchElementException, selenium_exceptions.TimeoutException):
            raise RuntimeError(
                f"Cannot locate button '{button_xpath}' in the following page : {self.driver.current_url}"
            )
        else:
            element.send_keys(file_location)

    def locate_and_drag_drop(self, element1_xpath, element2_xpath):
        try:
            element1 = WebDriverWait(self.driver, self.ELEMENT_WAITING_TIMEOUT).until(
                EC.presence_of_element_located((By.XPATH, element1_xpath)))
            element2 = WebDriverWait(self.driver, self.ELEMENT_WAITING_TIMEOUT).until(
                EC.presence_of_element_located((By.XPATH, element2_xpath)))
        except (selenium_exceptions.NoSuchElementException, selenium_exceptions.TimeoutException):
            raise RuntimeError(
                f"Cannot locate '{element1_xpath}' or '{element2_xpath}'  in the following page : "
                f"{self.driver.current_url}"
            )
        else:
            action = ActionChains(self.driver)
            action.drag_and_drop(element1, element2).perform()

    def execute_instructions(self, instructions):
        for page_step in instructions:

            if page_step.action == "LOCATE_AND_FILL":
                self.locate_and_fill(*page_step.params, page_step.options)
            elif page_step.action == "LOCATE_AND_CLICK":
                self.locate_and_click(*page_step.params)
            elif page_step.action == "LOCATE_DROPDOWN_AND_FILL":
                self.locate_dropdown_and_fill(*page_step.params, page_step.options)
            elif page_step.action == "LOCATE_AND_UPLOAD":
                self.locate_and_upload(*page_step.params, page_step.options)
            elif page_step.action == "LOCATE_AND_DRAG_DROP":
                self.locate_and_drag_drop(*page_step.params, page_step.options)
            else:
                raise RuntimeError(f"Unknown instruction: {page_step.action} \n"
                                   f" called with params : {page_step.params} \n "
                                   f"and options : {page_step.options} ")

    def login(self, email, password):
        email_xpath = '//text()[contains(.,"Email Address")]/following::input[1]'
        password_xpath = '//text()[contains(.,"Password")]/following::input[@data-automation-id="password"][1]'
        submit_xpath = '//div[contains(@aria-label,"Sign In")]'

        self.execute_instructions([
            # locate email input & fill
            PageStep(action="LOCATE_AND_FILL",
                     params=[email_xpath, email]),
            # locate password input & fill
            PageStep(action="LOCATE_AND_FILL",
                     params=[password_xpath, password])
        ])

        # submit
        time.sleep(2)
        self.execute_instructions([
            PageStep(action="LOCATE_AND_CLICK",
                     params=[submit_xpath])
        ])

    def fill_my_information_page(self):
        # Previous work
        if self.resume_data["my-information"]["previous-work"]:
            previous_work_xpath = '//text()[contains(.,"former")]/following::input[1]'

        else:
            previous_work_xpath = '//text()[contains(.,"former")]/following::input[2]'

        # instructions List of ordered steps :
        # a list of (Action, HTML Xpath, Value, options ...)
        # options is not required
        instructions = [
            # How Did You Hear About Us
            (PageStep(action="LOCATE_AND_FILL",
                      params=['//div//text()[contains(., "How Did You Hear About Us?")]'
                              '/following::input[1]',
                              self.resume_data["my-information"]["source"]],
                      options={"press_enter": True})),
            # Previous work
            PageStep(action="LOCATE_AND_CLICK",
                     params=[previous_work_xpath]),
            # Country
            PageStep(action="LOCATE_DROPDOWN_AND_FILL",
                     params=['//div//text()[contains(., "Country")]'
                             '/following::button[@aria-haspopup="listbox"][1]',
                             self.resume_data["my-information"]["country"]]),
            # ****** Legal Name ******
            # First Name
            PageStep(action="LOCATE_AND_FILL",
                     params=['//div//text()[contains(., "First Name")]'
                             '/following::input[1]',
                             self.resume_data["my-information"]["first-name"]]),
            # Last Name
            PageStep(action="LOCATE_AND_FILL",
                     params=['//div//text()[contains(., "Last Name")]'
                             '/following::input[1]',
                             self.resume_data["my-information"]["last-name"]]),
            # ****** Address ******
            # Line 1
            PageStep(action="LOCATE_AND_FILL",
                     params=['//div[@data-automation-id="addressSection"]'
                             '//text()[contains(., "Address Line 1")]'
                             '/following::input[1]',
                             self.resume_data["my-information"]["address-line"]]),
            # City
            PageStep(action="LOCATE_AND_FILL",
                     params=['//div[@data-automation-id="addressSection"]'
                             '//text()[contains(., "City")]'
                             '/following::input[1]',
                             self.resume_data["my-information"]["city"]]),
            # State
            PageStep(action="LOCATE_DROPDOWN_AND_FILL",
                     params=['//div[@data-automation-id="addressSection"]'
                             '//text()[contains(., "State")]'
                             '/following::button[@aria-haspopup="listbox"][1]',
                             self.resume_data["my-information"]["state"]]),
            # Zip
            PageStep(action="LOCATE_AND_FILL",
                     params=['//div[@data-automation-id="addressSection"]'
                             '//text()[contains(., "Postal Code")]'
                             '/following::input[1]',
                             self.resume_data["my-information"]["zip"]]),

            # ****** Phone ******
            # Device Type
            PageStep(action="LOCATE_DROPDOWN_AND_FILL",
                     params=['//div//text()[contains(., "Phone Device Type")]'
                             '/following::button[@aria-haspopup="listbox"][1]',
                             self.resume_data["my-information"]["phone-device-type"]]),
            # Phone Code
            PageStep(action="LOCATE_AND_FILL",
                     params=['//div//text()[contains(., "Country Phone Code")]/following::input[1]',
                             self.resume_data["my-information"]["phone-code-country"]],
                     options={'press_enter': True}),
            # Number
            PageStep(action="LOCATE_AND_FILL",
                     params=['//div//text()[contains(., "Phone Number")]/following::input[1]',
                             self.resume_data["my-information"]["phone-number"]]),
            # Extension
            PageStep(action="LOCATE_AND_FILL",
                     params=['//div//text()[contains(., "Phone Extension")]'
                             '/following::input[1]',
                             self.resume_data["my-information"]["phone-extension"]]),
            # # Submit
            PageStep(action="LOCATE_AND_CLICK",
                     params=['//div//button[contains(text(),"Save and Continue")]']),
        ]

        self.execute_instructions(instructions)

    def add_works(self, instructions):
        # check if there are work experiences
        if len(self.load_work_experiences()):
            # click ADD button
            instructions.append(PageStep(action="LOCATE_AND_CLICK",
                     params=['//button[@aria-label="Add Work Experience" and @data-automation-id="Add"]']))
            # fill work experiences
            works_count = len(self.load_work_experiences())
            for idx, work in enumerate(self.load_work_experiences(), start=1):
                instructions += [
                    # Job title
                    PageStep(action="LOCATE_AND_FILL",
                             params=[f'//text()[contains(.,"Work Experience {idx}")]'
                                     f'/following::text()[contains(.,"Job Title")]'
                                     f'/following::Input[1]',
                                     work["job-title"]]),
                    # Company
                    PageStep(action="LOCATE_AND_FILL",
                             params=[f'//text()[contains(.,"Work Experience {idx}")]'
                                     f'/following::text()[contains(.,"Company")]'
                                     f'/following::Input[1]',
                                     work["company"]]),
                    # Location
                    PageStep(action="LOCATE_AND_FILL",
                             params=[f'//text()[contains(.,"Work Experience {idx}")]'
                                     f'/following::text()[contains(.,"Location")]/following::Input[1]',
                                     work["location"]]),
                    # From Date
                    PageStep(action="LOCATE_AND_FILL",
                             params=[f'//text()[contains(.,"Work Experience {idx}")]'
                                     f'/following::text()[contains(.,"From")]'
                                     f'/following::input[contains(@aria-valuetext, "MM") '
                                     f'or contains(@aria-valuetext, "YYYY")][1]',
                                     work["from"]]),
                    # Description
                    PageStep(action="LOCATE_AND_FILL",
                             params=[f'//text()[contains(.,"Work Experience {idx}")]'
                                     f'/following::text()[contains(.,"Role Description")]'
                                     f'/following::textarea[1]',
                                     work["description"]])
                ]
                # Current work
                if not work["current-work"]:
                    # To Date
                    instructions.append(PageStep(action="LOCATE_AND_FILL",
                                                 params=[f'//text()[contains(.,"Work Experience {idx}")]'
                                                         '/following::text()[contains(.,"To")]'
                                                         '/following::input[contains(@aria-valuetext, "MM") or '
                                                         'contains(@aria-valuetext, "YYYY") ][1]', work["to"]]))

                else:
                    instructions.append(
                        PageStep(action="LOCATE_AND_CLICK",
                                 params=[f'//text()[contains(.,"Work Experience {idx}")]'
                                         '/following::text()[contains(.,"I currently work here")]'
                                         '/following::input[1]']),
                    )
                # check if more work experiences remaining
                if not idx == works_count:
                    # Add another
                    instructions.append(
                        PageStep(action="LOCATE_AND_CLICK",
                                 params=[f'//div//text()[contains(.,"Work Experience {idx}")]'
                                         '/following::button[contains(text(),"Add Another")]']),
                    )
        return instructions

    def add_education(self, instructions):
        # check if there are education experiences
        if len(self.load_education_experiences()):
            # click add button if not initialized
            instructions.append(
                PageStep(action="LOCATE_AND_CLICK",
                         params=['//text()[contains(.,"Education")]'
                                 '/following::button[contains(text(),"Add")][1]'])
            )

            # fill work experiences
            educations_count = len(self.load_education_experiences())
            for idx, education in enumerate(self.load_education_experiences(), start=1):
                instructions += [
                    # School or University
                    PageStep(action="LOCATE_AND_FILL",
                             params=[f'//text()[contains(.,"Education {idx}")]'
                                     f'/following::text()[contains(.,"School or University")]'
                                     f'/following::input[1]',
                                     education["university"]]),
                    # Degree
                    PageStep(action="LOCATE_AND_FILL",
                             params=[f'//text()[contains(.,"Education {idx}")]'
                                     f'/following::text()[contains(.,"Degree")]'
                                     f'/following::button[1]',
                                     education["degree"]]),
                    # Field of study
                    PageStep(action="LOCATE_AND_FILL",
                             params=[f'//text()[contains(.,"Education {idx}")]'
                                     f'/following::text()[contains(.,"Field of Study")]'
                                     f'/following::input[1]',
                                     education["field-of-study"]],
                             options={"press_enter": True}),
                    # Gpa
                    PageStep(action="LOCATE_AND_FILL",
                             params=[f'//text()[contains(.,"Education {idx}")]'
                                     '/following::text()[contains(.,"Overall Result")]/'
                                     'following::input[1]',
                                     education["gpa"]]),
                    # From date
                    PageStep(action="LOCATE_AND_FILL",
                             params=[f'//text()[contains(.,"Education {idx}")]'
                                     '/following::text()[contains(.,"From")]/'
                                     'following::input[contains(@aria-valuetext, "MM")'
                                     ' or contains(@aria-valuetext, "YYYY") ][1]',
                                     education["from"]]),

                    # To date
                    PageStep(action="LOCATE_AND_FILL",
                             params=[f'//text()[contains(.,"Education {idx}")]'
                                     f'/following::text()[contains(.,"To")]'
                                     f'/following::input[contains(@aria-valuetext, "MM")'
                                     f' or contains(@aria-valuetext, "YYYY") ][1]',
                                     education["to"]]),
                ]

                # check if more education experiences remaining
                if not idx == educations_count:
                    # Add another
                    instructions.append(PageStep(action="LOCATE_AND_CLICK",
                                                 params=[f'//text()[contains(.,"Education {idx}")]'
                                                         f'/following::button[contains(text(),"Add Another")][1]']))
        return instructions

    def add_languages(self, instructions):
        if len(self.load_languages()):
            # click ADD button
            instructions.append(
                PageStep(action="LOCATE_AND_CLICK",
                         params=['//text()[contains(.,"Languages")]'
                                 '/following::button[contains(text(),"Add")][1]'])
            )
            # fill Languages
            languages_count = len(self.load_languages())
            for idx, language in enumerate(self.load_languages(), start=1):
                # Fluent ?
                if language["fluent"]:
                    instructions.append(
                        PageStep(action="LOCATE_AND_CLICK",
                                 params=[f'//text()[contains(.,"Languages {idx}")]'
                                         f'/following::text()[contains(.,"I am fluent in this language")]'
                                         f'/following::input[1]']))
                instructions += [
                    # Language
                    PageStep(action="LOCATE_DROPDOWN_AND_FILL",
                             params=[f'//text()[contains(.,"Languages {idx}")]'
                                     f'/following::text()[contains(.,"Language")]'
                                     f'/following::button[1]',
                                     language["language"]],
                             options={"value_is_pattern": True}),
                    # Reading
                    PageStep(action="LOCATE_DROPDOWN_AND_FILL",
                             params=[f'/following::text()[contains(.,"Reading Proficiency")]'
                                     f'/following::button[1]',
                                     language["comprehension"]],
                             options={"value_is_pattern": True}),
                    # Speaking
                    PageStep(action="LOCATE_DROPDOWN_AND_FILL",
                             params=[f'/following::text()[contains(.,"Speaking Proficiency")]'
                                     f'/following::button[1]',
                                     language["overall"]],
                             options={"value_is_pattern": True}),
                    # Translation
                    PageStep(action="LOCATE_DROPDOWN_AND_FILL",
                             params=[f'/following::text()[contains(.,"Translation")]'
                                     f'/following::button[1]',
                                     language["reading"]],
                             options={"value_is_pattern": True}),
                    # Writing
                    PageStep(action="LOCATE_DROPDOWN_AND_FILL",
                             params=[f'/following::text()[contains(.,"Writing Proficiency")]'
                                     f'/following::button[1]',
                                     language["writing"]],
                             options={"value_is_pattern": True}),
                ]

                # check if more languages remaining
                if not idx == languages_count:
                    # Add another
                    instructions.append(
                        PageStep(action="LOCATE_AND_CLICK",
                                 params=[f'//text()[contains(.,"Languages {idx}")]'
                                         f'/following::button[contains(text(),"Add")][1]']),
                    )
        return instructions

    def add_resume(self, instructions):
        instructions.append(
            PageStep(action="LOCATE_AND_FILL",
                     params=['//input[@data-automation-id="file-upload-input-ref"]',
                             self.resume_data["my-experience"]["resume"]]),
        )
        return instructions

    def add_websites(self, instructions):
        websites_count = len(self.resume_data["my-experience"]["websites"])
        if websites_count:
            # click ADD button
            instructions.append(
                PageStep(action="LOCATE_AND_CLICK",
                         params=['//text()[contains(.,"Websites")]'
                                 '/following::button[contains(text(),"Add")]']),

            )
            # fill websites
            for idx, website in enumerate(self.resume_data["my-experience"]["websites"], start=1):
                instructions += [
                    # Website
                    PageStep(action="LOCATE_AND_CLICK",
                             params=[
                                 f'//div[@data-automation-id="websitePanelSet-{idx}"]'
                                 f'//input[@data-automation-id="website"]',
                                 website])
                ]
                # check if more languages remaining
                if not idx == websites_count:
                    # Add another
                    instructions.append(
                        PageStep(action="LOCATE_AND_CLICK",
                                 params=[
                                     '//button[@data-automation-id="Add Another"'
                                     ' and @aria-label="Add Another Websites"]'])
                    )
            # Save and continue
            instructions.append(
                PageStep(action="LOCATE_AND_CLICK",
                         params=[
                             '//button[contains(text(),"Save and Continue")]'])
            )

        return instructions

    def fill_my_experience_page(self):
        instructions = []
        steps = {
            "WORKS": self.add_works,
            "EDUCATION": self.add_education,
            # "LANGUAGES": self.add_languages,
            "RESUME": self.add_resume,
            # "WEBSITES": self.add_websites,
        }
        for step_name, action in steps.items():
            print(f"[INFO] adding {step_name}")
            instructions = action(instructions)

        self.execute_instructions(instructions=instructions)

    def start_application(self):
        self.driver.get(self.application_link)

        self.login(
            self.resume_data["account"]["email"],
            self.resume_data["account"]["password"]
        )

        self.fill_my_information_page()
        self.fill_my_experience_page()

        # exit
        # self.driver.quit()


if __name__ == '__main__':
    APPLICATION_LINK = "https://usaa.wd1.myworkdayjobs.com/en-US/USAAJOBSWD/job/San-Antonio-Home-Office-I/Cyber-Security-Intern_R0092844/apply/applyManually"
    RESUME_PATH = "resume.yml"
    s = WorkdayAutofill(
        application_link=APPLICATION_LINK,
        resume_path=RESUME_PATH
    )
    s.start_application()
    # s.driver.quit()
    print("hello")
