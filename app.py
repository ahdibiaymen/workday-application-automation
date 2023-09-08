import time

import selenium.common.exceptions as selenium_exceptions
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils import check_generator_is_empty, check_element_text_is_empty
import yaml

ELEMENT_WAITING_TIMEOUT = 15
IMPLICIT_FILLING_WAIT = 3


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

    def locate_and_fill(self, element_xpath, input_data, press_enter=False, only_if_empty=False):
        try:
            element = WebDriverWait(self.driver, ELEMENT_WAITING_TIMEOUT).until(
                EC.presence_of_element_located((By.XPATH, element_xpath)))
        except (selenium_exceptions.NoSuchElementException, selenium_exceptions.TimeoutException):
            raise RuntimeError(
                f"Cannot locate element '{element_xpath}' in the following page : {self.driver.current_url}"
            )
        else:
            if only_if_empty and not check_element_text_is_empty(element):
                # quit if the element is already filled
                return
            if input_data:
                if "input" in element_xpath:
                    element.send_keys(Keys.CONTROL + "a")
                    element.send_keys(Keys.DELETE)
                element.send_keys(input_data)
            if press_enter:
                element.send_keys(Keys.ENTER)

    def locate_dropdown_and_fill(self, element_xpath, select_value, value_is_pattern=False):
        try:
            element = WebDriverWait(self.driver, ELEMENT_WAITING_TIMEOUT).until(
                EC.presence_of_element_located((By.XPATH, element_xpath)))
        except (selenium_exceptions.NoSuchElementException, selenium_exceptions.TimeoutException):
            raise RuntimeError(
                f"Cannot locate element '{element_xpath}' in the following page : {self.driver.current_url}"
            )
        else:
            self.driver.execute_script("arguments[0].click();", element)
            element.send_keys(select_value)
            if value_is_pattern:
                select_xpath = f'//div[@data-automation-widget="wd-popup"]//div/ul/li/div[contains(text(),"{select_value}")]'
            else:
                select_xpath = f'//div[@data-automation-widget="wd-popup"]//div/ul/li/div[text()="{select_value}"]'
            try:
                choice = WebDriverWait(self.driver, ELEMENT_WAITING_TIMEOUT).until(
                    EC.presence_of_element_located((By.XPATH, select_xpath)))
            except Exception:
                raise RuntimeError(
                    f"Cannot locate option: >'{select_value}'< in the following drop down : {element_xpath}"
                    " Check your resume data"
                )
            else:
                choice.click()

    def locate_and_click(self, button_xpath):
        try:
            clickable_element = WebDriverWait(self.driver, ELEMENT_WAITING_TIMEOUT).until(
                EC.presence_of_element_located((By.XPATH, button_xpath)))
        except (selenium_exceptions.NoSuchElementException, selenium_exceptions.TimeoutException):
            raise RuntimeError(
                f"Cannot locate submit button '{button_xpath}' in the following page : {self.driver.current_url}"
            )
        else:
            self.driver.execute_script("arguments[0].click();", clickable_element)

    def locate_and_upload(self, button_xpath, file_location):
        try:
            element = WebDriverWait(self.driver, ELEMENT_WAITING_TIMEOUT).until(
                EC.presence_of_element_located((By.XPATH, button_xpath)))
        except (selenium_exceptions.NoSuchElementException, selenium_exceptions.TimeoutException):
            raise RuntimeError(
                f"Cannot locate button '{button_xpath}' in the following page : {self.driver.current_url}"
            )
        else:
            # element.send_keys(Keys.ENTER)
            element.send_keys(file_location)
            # element.send_keys(Keys.ENTER)

    def locate_and_drag_drop(self, element1_xpath, element2_xpath):
        try:
            element1 = WebDriverWait(self.driver, ELEMENT_WAITING_TIMEOUT).until(
                EC.presence_of_element_located((By.XPATH, element1_xpath)))
            element2 = WebDriverWait(self.driver, ELEMENT_WAITING_TIMEOUT).until(
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
        for inst in instructions:
            action = inst[0]
            params = inst[1:]
            if action == "LOCATE_AND_FILL":
                self.locate_and_fill(*params)
            elif action == "LOCATE_AND_CLICK":
                self.locate_and_click(*params)
            elif action == "LOCATE_DROPDOWN_AND_FILL":
                self.locate_dropdown_and_fill(*params)
            elif action == "LOCATE_AND_UPLOAD":
                self.locate_and_upload(*params)
            elif action == "LOCATE_AND_DRAG_DROP":
                self.locate_and_drag_drop(*params)
            else:
                raise RuntimeError(f"Unknown instruction: {action} \n"
                                   f" called with params : {params}")

    def login(self, email, password):
        email_xpath = '//input[@data-automation-id="email"]'
        password_xpath = '//input[@data-automation-id="password"]'
        submit_xpath = '//div[@data-automation-id="click_filter"]'
        # locate email input & fill
        self.locate_and_fill(email_xpath, email)
        # locate password input & fill
        self.locate_and_fill(password_xpath, password)
        # submit
        time.sleep(2)
        self.locate_and_click(submit_xpath)

    def fill_my_information_page(self):
        # Get Previous work XPATH
        if self.resume_data["my-information"]["previous-work"]:
            previous_work_xpath = '//div[@data-automation-id="previousWorker"]//input[@id=1]'
        else:
            previous_work_xpath = '//div[@data-automation-id="previousWorker"]//input[@id=2]'

        # instructions List of ordered steps :
        # a list of (Action, HTML Xpath, Value, options..)
        # options is not required
        instructions = [
            # How Did You Hear About Us
            ("LOCATE_DROPDOWN_AND_FILL", '//button[@data-automation-id="sourceDropdown"]',
             self.resume_data["my-information"]["source"]),
            # Previous work
            ("LOCATE_AND_CLICK", previous_work_xpath),
            # Country
            ("LOCATE_DROPDOWN_AND_FILL", '//button[@data-automation-id="countryDropdown"]',
             self.resume_data["my-information"]["country"]),
            # ****** Legal Name ******
            # First Name
            ("LOCATE_AND_FILL", '//input[@data-automation-id="legalNameSection_firstName"]',
             self.resume_data["my-information"]["first-name"]),
            # Last Name
            ("LOCATE_AND_FILL", '//input[@data-automation-id="legalNameSection_lastName"]',
             self.resume_data["my-information"]["last-name"]),
            # ****** Address ******
            # Line 1
            ("LOCATE_AND_FILL", '//input[@data-automation-id="addressSection_addressLine1"]',
             self.resume_data["my-information"]["address-line"]),
            # State
            ("LOCATE_DROPDOWN_AND_FILL", '//button[@data-automation-id="addressSection_countryRegion"]',
             self.resume_data["my-information"]["state"]),
            # City
            ("LOCATE_AND_FILL", '//input[@data-automation-id="addressSection_city"]',
             self.resume_data["my-information"]["city"]),
            # Zip
            ("LOCATE_AND_FILL", '//input[@data-automation-id="addressSection_postalCode"]',
             self.resume_data["my-information"]["zip"]),
            # ****** Phone ******
            # Device Type
            ("LOCATE_DROPDOWN_AND_FILL", '//button[@data-automation-id="phone-device-type"]',
             self.resume_data["my-information"]["phone-device-type"]),
            # Phone Code
            ("LOCATE_AND_FILL",
             '//div[@data-automation-id="multiselectInputContainer"]//input[contains(@placeholder,"Search")]',
             self.resume_data["my-information"]["phone-code-country"],
             True),
            # Number
            ("LOCATE_AND_FILL", '//input[@data-automation-id="phone-number"]',
             self.resume_data["my-information"]["phone-number"]),
            # Extension
            ("LOCATE_AND_FILL", '//input[@data-automation-id="phone-extension"]',
             self.resume_data["my-information"]["phone-extension"]),
            # Submit
            ("LOCATE_AND_CLICK", '//button[@data-automation-id="bottom-navigation-next-button"]'),
        ]

        self.execute_instructions(instructions)

    def add_works(self, instructions):
        # check if there are work experiences
        if not check_generator_is_empty(self.load_work_experiences()):
            # click ADD button
            instructions.append(
                ("LOCATE_AND_CLICK", '//button[@data-automation-id="Add"]')
            )
            # fill work experiences
            works_count = len(self.load_work_experiences())
            for idx, work in enumerate(self.load_work_experiences(), start=1):
                instructions += [
                    # Job title
                    ("LOCATE_AND_FILL",
                     f'//div[@data-automation-id="workExperience-{idx}"]//input[@data-automation-id="jobTitle"]',
                     work["job-title"]),
                    # Company
                    ("LOCATE_AND_FILL",
                     f'//div[@data-automation-id="workExperience-{idx}"]//input[@data-automation-id="company"]',
                     work["company"]),
                    # Location
                    ("LOCATE_AND_FILL",
                     f'//div[@data-automation-id="workExperience-{idx}"]//input[@data-automation-id="location"]',
                     work["location"]),
                    # From Date
                    ("LOCATE_AND_FILL",
                     f'//div[@data-automation-id="workExperience-{idx}"]'
                     f'//div[@data-automation-id="dateInputWrapper"]'
                     f'//input[contains(@aria-valuetext, "MM") or contains(@aria-valuetext, "YYYY") ]',
                     work["from"]),
                    # Description
                    ("LOCATE_AND_FILL",
                     f'//div[@data-automation-id="workExperience-{idx}"]//textarea[@data-automation-id="description"]',
                     work["description"]),
                ]
                # Current work
                if not work["current-work"]:
                    # To Date
                    instructions += [("LOCATE_AND_FILL",
                                      f'//div[@data-automation-id="workExperience-{idx}"]'
                                      '//div[@data-automation-id="dateInputWrapper"]//input[contains(@aria-valuetext, '
                                      '"MM") or '
                                      'contains(@aria-valuetext, "YYYY") ]', work["to"])]
                else:
                    instructions.append(
                        ("LOCATE_AND_CLICK",
                         f'//div[@data-automation-id="workExperience-{idx}"]'
                         '//input[@data-automation-id="currentlyWorkHere"]')
                    )
                # check if more work experiences remaining
                if not idx == works_count:
                    # Add another
                    instructions.append(
                        ("LOCATE_AND_CLICK",
                         '//button[@data-automation-id="Add Another" and @aria-label="Add Another Work Experience"]')
                    )
        return instructions

    def add_education(self, instructions):
        # check if there are education experiences
        if check_generator_is_empty(self.load_education_experiences()):
            raise RuntimeError("You need to have at least one education experience to fill in your resume")

        # fill work experiences
        educations_count = len(self.load_education_experiences())
        for idx, education in enumerate(self.load_education_experiences(), start=1):
            instructions += [
                # School or University
                (
                    "LOCATE_AND_FILL",
                    f'//div[@data-automation-id="education-{idx}"]//input[@data-automation-id="school"]',
                    education["university"]),
                # Degree
                (
                    "LOCATE_AND_FILL",
                    f'//div[@data-automation-id="education-{idx}"]//button[@data-automation-id="degree"]',
                    education["degree"]),
                # Field of study
                ("LOCATE_AND_FILL",
                 f'//div[@data-automation-id="education-{idx}"]//input[@placeholder="Search"]',
                 education["field-of-study"],
                 True
                 ),
                # Gpa
                ("LOCATE_AND_FILL",
                 f'//div[@data-automation-id="education-{idx}"]'
                 '//input[@data-automation-id="gpa"]',
                 education["gpa"]),
                # From date
                ("LOCATE_AND_FILL", f'//div[@data-automation-id="education-{idx}"]'
                                    '//input[@data-automation-id="dateSectionYear-input" '
                                    'and contains(@aria-valuetext, "YYYY")]',
                 education["from"]),
                # To date
                ("LOCATE_AND_FILL",
                 f'//div[@data-automation-id="education-{idx}"]'
                 f'//input[@data-automation-id="dateSectionYear-input" and contains(@aria-valuetext, "YYYY")]',
                 education["to"]),
            ]
            # check if more education experiences remaining
            if not idx == educations_count:
                # Add another
                instructions.append(
                    ("LOCATE_AND_CLICK",
                     '//button[@data-automation-id="Add Another" and @aria-label="Add Another Education"]')
                )
        return instructions

    def add_languages(self, instructions):
        if not check_generator_is_empty(self.load_languages()):
            # click ADD button
            instructions.append(
                ("LOCATE_AND_CLICK", '//button[@aria-label="Add Languages" and @data-automation-id="Add"]')
            )
            # fill work experiences
            languages_count = len(self.load_languages())
            for idx, language in enumerate(self.load_languages(), start=1):
                # Fluent ?
                if language["fluent"]:
                    instructions += [("LOCATE_AND_CLICK",
                                      f'//div[@data-automation-id="language-{idx}"]'
                                      f'//input[@data-automation-id="nativeLanguage"]')]
                instructions += [
                    # Language
                    ("LOCATE_DROPDOWN_AND_FILL",
                     f'//div[@data-automation-id="language-{idx}"]//button[@data-automation-id="language"]',
                     language["language"], True),
                    # Comprehension
                    ("LOCATE_DROPDOWN_AND_FILL",
                     f'//div[@data-automation-id="language-{idx}"]//button[@data-automation-id="languageProficiency-0"]',
                     language["comprehension"], True),
                    # Overall
                    ("LOCATE_DROPDOWN_AND_FILL",
                     f'//div[@data-automation-id="language-{idx}"]//button[@data-automation-id="languageProficiency-1"]',
                     language["overall"], True),
                    # Reading
                    ("LOCATE_DROPDOWN_AND_FILL",
                     f'//div[@data-automation-id="language-{idx}"]//button[@data-automation-id="languageProficiency-2"]',
                     language["reading"], True),
                    # Speaking
                    ("LOCATE_DROPDOWN_AND_FILL",
                     f'//div[@data-automation-id="language-{idx}"]//button[@data-automation-id="languageProficiency-3"]',
                     language["speaking"], True),
                    # Writing
                    ("LOCATE_DROPDOWN_AND_FILL",
                     f'//div[@data-automation-id="language-{idx}"]//button[@data-automation-id="languageProficiency-4"]',
                     language["writing"], True),
                ]

                # check if more languages remaining
                if not idx == languages_count:
                    # Add another
                    instructions.append(
                        ("LOCATE_AND_CLICK",
                         '//button[@data-automation-id="Add Another" and @aria-label="Add Another Languages"]')
                    )
        return instructions

    def add_resume(self, instructions):
        instructions.append(
            ("LOCATE_AND_UPLOAD",
             '//input[@data-automation-id="file-upload-input-ref"]',
             self.resume_data["my-experience"]["resume"])
        )
        return instructions

    def add_websites(self, instructions):
        websites_count = len(self.resume_data["my-experience"]["websites"])
        if websites_count:
            # click ADD button
            instructions.append(
                ("LOCATE_AND_CLICK", '//button[@aria-label="Add Websites" and @data-automation-id="Add"]')
            )
            # fill websites
            for idx, website in enumerate(self.resume_data["my-experience"]["websites"], start=1):
                instructions += [
                    # Website
                    ("LOCATE_AND_FILL",
                     f'//div[@data-automation-id="websitePanelSet-{idx}"]//input[@data-automation-id="website"]',
                     website),
                ]
                # check if more languages remaining
                if not idx == websites_count:
                    # Add another
                    instructions.append(
                        ("LOCATE_AND_CLICK",
                         '//button[@data-automation-id="Add Another" and @aria-label="Add Another Websites"]')
                    )
        return instructions

    def save_and_continue(self, instructions):
        instructions.append(
            ("LOCATE_AND_CLICK", '//button[@data-automation-id="bottom-navigation-next-button"]')
        )
        return instructions

    def fill_my_experience_page(self):
        instructions = []
        steps = {
            "WORKS": self.add_works,
            "EDUCATION": self.add_education,
            "LANGUAGES": self.add_languages,
            "RESUME": self.add_resume,
            "WEBSITES": self.add_websites,
            "SAVE_AND_CONTINUE": self.save_and_continue
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
    APPLICATION_LINK = "https://bloomenergy.wd1.myworkdayjobs.com/en-US/BloomEnergyCareers/job/San-Jose%2C-California/Shift-Lead--Technical-Support_JR-17598-1/apply/applyManually"
    RESUME_PATH = "resume.yml"
    s = WorkdayAutofill(
        application_link=APPLICATION_LINK,
        resume_path=RESUME_PATH
    )
    s.start_application()
    # s.driver.quit()
    print("hello")
