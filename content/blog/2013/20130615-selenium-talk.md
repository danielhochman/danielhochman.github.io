Title: Selenium: zero to test
Date: 2013-06-20
Category: Testing
Tags: selenium, testing
Slug: selenium-zero-to-test
Author: Daniel Hochman
Summary: This post covers the implementation of a Selenium framework from the ground up.

This post was written specifically for my
[talk](http://www.meetup.com/seleniumsanfrancisco/events/122248712/) at the
[San Francisco Selenium Meetup](http://www.meetup.com/seleniumsanfrancisco/).
It covers my implementation of a Selenium testing framework from the ground up. It includes example code,
in addition to a number of links that were useful when developing my framework. There is also a companion
GitHub repository named [basic_selenium_framework](https://github.com/danielhochman/basic_selenium_framework). 

***

### Design

When you're building a framework, it's important to think about how it's going to be used and who is going to be
using it. Here were my basic requirements:

* Tests should be easy to write
* Tests should be easy to debug
* Tests shouldn't take forever (concurrency)
* Tests should integrate well with developer workflow (all of the above, plus the ability to run locally)
* Tests should integrate with existing tools (like Jenkins)

***

### Implementation

I chose to write my framework in Python. It's a great language for building tools no matter what your
application is written in or what your developers know. Some of the reasons I love Python:

* Great libraries
* Dynamic typing
* Minimal boilerplate

#### A basic suite

One of the libraries I have used for a number of testing projects is [nose](https://nose.readthedocs.org/en/latest/).
It is the foundation of my testing framework and offers:

* Fixtures (setup and teardown)
* Test collection and discovery
* Built-in multiprocessing support
* xUnit report output

First, let's install the dependencies below. You can use a
[virtualenv](http://blog.fruiapps.com/2012/06/An-introductory-tutorial-to-python-virtualenv-and-virtualenvwrapper)
(preferred), but you can also install the packages system-wide.

* `nose`
* `selenium`
* `simplejson`
* `pyvirtualdisplay` (optional)

Open your favorite editor, and let's create an abstract test case with fixtures we can use for all test cases:

    :::python
    from selenium import webdriver
    
    class SeleniumTestCase(object):
        
        def setup(self):
            self.driver = webdriver.Firefox()
            self.driver.implicitly_wait(10)
        
        def teardown(self):
            self.driver.quit()

Fixtures are wrappers around tests that are run before and after the test. In the above example, we create a new browser
for each test and quit the browser when the test has completed. Even if the test fails, the teardown will still run.

The Firefox driver is great because it requires no external dependencies on any platform.
The Firefox WebDriver binary is included in Python's Selenium module.
Chrome can be used with `self.driver = webdriver.Chrome()`, but you will need to have
the [ChromeDriver binary](https://code.google.com/p/chromedriver/downloads/list) in your path.

It's important to include the implicit wait configuration due to the nature of the JavaScript and browser interaction.
JavaScript can modify the DOM even after the page is loaded from the browser's perspective. Implicit waits ensure
that Selenium will look for the element for a number of seconds after the DOM is loaded initially.

Let's write our first test:

    :::python
    class TestBasic(SeleniumTestCase):
	
        def test_search(self):
            self.driver.get('http://duckduckgo.com')
            
            search_box = self.driver.find_element_by_name('q')
            search_box.send_keys('Selenium')
            search_box.submit()
            
            results = self.driver.find_element_by_id('links')
            
            assert 'Selenium' in self.driver.title 
            assert 'Selenium' in results.text

This test searches [DuckDuckGo](http://duckduckgo.com) for 'Selenium' and checks that the browser title
and displayed results contain the search term. Easy.

If you're wondering how I came up with the correct `name` and `id`, I prefer to use Chrome's built-in Developer Tools.
Just right click anywhere on a page and select 'Inspect Element'. If you're wondering about methods like
`find_element_by_id()`, I highly recommend the
[unofficial Selenium with Python](https://selenium-python.readthedocs.org/en/latest/)
documentation by Baiju Muthukadan. It is far better than the
[official API documentation](http://selenium.googlecode.com/svn/trunk/docs/api/py/index.html). 

Save the abstract test case and first test in a file called `test_selenium.py` and run it by invoking `nosetests` in
the same directory (with the verbose flag so the name of the test is displayed as it is run):

    :::shell-session
    $ ls
    test_selenium.py
    $ nosetests -v
    test_selenium.TestBasic.test_search ... ok
    
    ----------------------------------------------------------------------
    Ran 1 test in 5.122s
    
    OK

One of my favorite features of `nose` is the ability to use tests generators. Using generators we can run the
same test multiple times using different parameters, and have the results properly output.

Let's refactor our first test in a new class and include a few more test cases with different parameters.
We can do this with just three additional lines of code:

    :::python
    class TestGenerator(SeleniumTestCase):
        
        def test_search(self):
            for search_term in ['Python', 'Selenium', 'San Francisco', 'Sauce Labs']:
                yield self.verify_search, search_term
        
        def verify_search(self, search_term):
            self.driver.get('http://duckduckgo.com')
            
            search_box = self.driver.find_element_by_name('q')
            search_box.send_keys(search_term)
            search_box.submit()
            
            results = self.driver.find_element_by_id('links')
            
            assert search_term in self.driver.title 
            assert search_term in results.text
            
Save the file and run again.

    :::shell-session
    $ nosetests -v
    test_selenium.TestBasic.test_search ... ok
    test_selenium.TestGenerator.test_search('Python',) ... ok
    test_selenium.TestGenerator.test_search('Selenium',) ... ok
    test_selenium.TestGenerator.test_search('San Francisco',) ... ok
    test_selenium.TestGenerator.test_search('Sauce Labs',) ... ok
    
    ----------------------------------------------------------------------
    Ran 5 tests in 57.678s

The `yield` keyword invokes the designated method with the given parameter(s) and the appropriate fixtures, and reports
the output as if individual tests had been run.

##### Configuration

One of the most common cases where configuration helps is with URLs. If you want to run the suite against
multiple endpoints (localhost, staging, production, etc), it is useful to keep the base netloc in a config
file and have a method to create URLs from a path.

Let's add some features to our abstract test case:

    :::python
    from selenium import webdriver
    import simplejson as json
    import urlparse
    
    _multiprocess_shared_ = True
    
    def setup():
        config_json = """
        {
            "endpoint": "http://duckduckgo.com",
            "timeout": 10
        }
        """
        global config
        config = json.loads(config_json)
    
    class SeleniumTestCase(object):
        
        def setup(self):
            self.driver = webdriver.Firefox()
            self.driver.implicitly_wait(config['timeout'])
        
        def teardown(self):
            self.driver.quit()
        
        def get_path(self, path):
            url = urlparse.urljoin(config['endpoint'], path)
            self.driver.get(url)

Note the use of a module level fixture for our setup. We don't need to create a new configuration dictionary
for every single test. `nose` supports fixtures at the package, module, class, and test level.
`_multiprocess_shared_` allows multiple processes to share the same module fixture.

I chose JSON because it parses directly into a Python dictionary and it can be generated by
something as simple as echoing text to a file.
It's easy to see how we could get the JSON above from an external file.
See [testcases.py](https://github.com/danielhochman/basic_selenium_framework/blob/master/basic_selenium_framework/testcases.py)
for an example of external configuration.

In the example tests, replace `self.driver.get('http://duckduckgo.com')` with `self.get_path('/')`. The tests use the
endpoint in the config in combination with the requested path. In this case we are just requesting the root path of the
endpoint, but it also accepts paths including queryparams.

***

### Expanding the suite

At this point, we have a minimum viable product.
Next we will look at additional features that testing easier and improve integration with other tools.

***

### Tailoring the abstract test case

You may want to add methods specific to your application to ease things like logging in.

For our current example, let's subclass SeleniumTestCase and add any useful methods:

    :::python
    class DuckDuckGoTestCase(SeleniumTestCase):
        
        def search(self, search_term):
            self.get_path('/')
            
            search_box = self.driver.find_element_by_name('q')
            search_box.send_keys(search_term)
            search_box.submit()
            
            results = self.driver.find_element_by_id('links')
            
            return results
    
Be sure to change the test classes to subclass the new app specific test case and leverage the new method:

    :::python
    class TestBasic(DuckDuckGoTestCase):
        
        def test_search(self):
            results = self.search('Selenium')
            
            assert 'Selenium' in self.driver.title 
            assert 'Selenium' in results.text
    
    class TestGenerator(DuckDuckGoTestCase):
        
        def test_search(self):
            for search_term in ['Python', 'Selenium', 'San Francisco', 'Sauce Labs']:
                yield self.verify_search, search_term
        
        def verify_search(self, search_term):
            results = self.search(search_term)
            
            assert search_term in self.driver.title
            assert search_term in results.text

Let's also write a third test method using our tailored class to test DuckDuckGo's calculator:

    :::python
    class TestCalculator(DuckDuckGoTestCase):

        def test_calculator(self):
            self.search('3 + 3')

            assert '= 6' in self.driver.find_element_by_id('zero_click').text

If you're up for it, try refactoring the calculator test using generators to test additional equations.

***

### Jenkins integration

[Jenkins](http://jenkins-ci.org/) is a great tool for automating the deployment process.
Post-commit [git hooks](http://git-scm.com/book/ch7-3.html) can trigger a build in Jenkins
every time a developer pushes code. Tests should run as part the build.

Jenkins also supports test reporting on the front-end from an xUnit test report. A nice graph shows pass, fail,
and test volume history. Each test is visible from Jenkins built-in test browser.

nose has a built-in xUnit output plugin.
Unfortunately, it [does not play nice](https://github.com/nose-devs/nose/issues/2)
with multiprocessing. In fact, many plugins can break or behave unexpectedly when multiprocessing is enabled.
[nose2](https://github.com/nose-devs/nose2) is supposed to remedy these issues. I evaluated it recently and it is not
quite ready for primetime.

Rosen Diankov developed a set of patched plugins to fix the issue and integrate better with Jenkins.
You can find his plugins
[embedded in one of his project repositories](https://github.com/rdiankov/openrave/tree/master/test/noseplugins)
on GitHub. The patches also bring another desirable change to xUnit reports, output capture for all tests. By default,
only failing test output is captured in the result file. In addition, it also manages to allow generated tests to run
in parallel, which is not possible with the built-in `multiprocessing` plugin.

***

### Test runner

Additional features, like headless testing and use of Rosen Diankov's custom plugins require
some setup before invoking nose. A test runner handles the setup. See
[run_tests.py](https://github.com/danielhochman/basic_selenium_framework/blob/master/basic_selenium_framework/run_tests.py)
in the repo. If you want to use the additional features, you will need to use the test runner.

***

### Sauce Labs

Sauce Labs allows you to run your tests in the cloud on
[over 150 platform/browser combinations](https://saucelabs.com/docs/platforms).

To use Sauce Labs, we just need to modify our setup fixture to create a remote webdriver instead of the Firefox
one we were using previously. Let's modify our module and test level fixtures:

    :::python
    ...
    
    def setup():
        config_json = """
        {
            "endpoint": "http://duckduckgo.com",
            "timeout": 10,
            "use_sauce": true,
            "sauce_username": "my_username",
            "sauce_access_key": "accesske-y012-3456-789a-bcdef0123456",
            "sauce_browser": "INTERNETEXPLORER"
        }
        """
        global config
        config = json.loads(config_json)
    
    class SeleniumTestCase(object):
        
        def setup(self):
            if config['use_sauce']:
                desired_capabilities = getattr(webdriver.DesiredCapabilities, config['sauce_browser'])
                self.driver = webdriver.Remote(
                    desired_capabilities=desired_capabilities,
                    command_executor="http://%s:%s@ondemand.saucelabs.com:80/wd/hub" % (
                        config['sauce_username'], config['sauce_access_key']
                    )
                )
            else:
                self.driver = webdriver.Firefox()
            
            self.driver.implicitly_wait(config['timeout'])
    
    ...

##### Cross-browser testing

There are some advanced ways to do cross-browser testing, using a custom nose plugin and method decorators, but it's
more trouble than it's worth. It's easier to just run the suite multiple times with a different configuration file. In
Jenkins, use multiple jobs with different configuration files to make it easier to track test results. This way you can
also fail a build on Firefox test failures, but let the build continue even if tests fail on Internet Explorer.
Personally, I have had a lot of trouble getting tests to be 100% stable on anything but the browser they were written
for once you start writing tests that interact with a lot of JavaScript and navigate between multiple pages.

Look at [Selenium's own Jenkins instance](http://ci.seleniumhq.org:8080/) to understand how browsers may
behave differently.

##### Sauce Connect
You can even test against local, non-internet facing, environments using a
[Sauce Connect tunnel](https://saucelabs.com/docs/connect). They are incredibly easy to use, just execute the .jar
with your credentials. Some things to watch out for when using Sauce Connect:

* Tunnels get stale, and should be refreshed daily using a scheduled job. They can also die unpredictably.
See [Keeping Sauce Connect Fresh](http://support.saucelabs.com/entries/21068387-Keeping-Sauce-Connect-fresh).
* All traffic during Sauce tests go through the tunnel, not just traffic to the local environment. This can slow
things down quite a bit.
* Only one tunnel can be active per account. If you need to tunnel to multiple environments,
you should create [sub-accounts](https://saucelabs.com/docs/subaccounts) and manage credentials accordingly.

##### Sauce API

Sauce Labs has a dashboard where you can view tests. If you want the dashboard to contain any meaningful data:

* Set the `name` parameter in `desired_capabilities` in the setup. Unfortunately a setup has no good way of
knowing what method called it. I like to use `'%s.%s.?' % (__module__, __class__.__name__)`.
This would result in file_name.ClassName.?
* Set the `build` parameter in `desired_capabilities`. Jenkins provides a
[$BUILD_TAG parameter](https://wiki.jenkins-ci.org/display/JENKINS/Building+a+software+project#Buildingasoftwareproject-JenkinsSetEnvironmentVariables)
that contains the job name and build number so you know which build the test originated from.
* Use Sauce Labs' API to [update the job](https://saucelabs.com/docs/rest#resources/update)
after the test has completed. I parse the xUnit report and use the API to complete the test name
and update the pass/fail status.
See [job_update_sauce.py](https://github.com/danielhochman/basic_selenium_framework/blob/master/basic_selenium_framework/job_update_sauce.py).

***

### API Bindings

Applications more often than not rely heavily on data, therefore tests will too.

There are two good ways to handle test data:

* For data that won't be modified, write a script to create the necessary test data and leave it in the database.
* For data that may or may not be modified, create the necessary test data, test against it, and delete it.

The best way to handle either case is to write simple API bindings in a Python module
(using [requests](http://docs.python-requests.org/en/latest/) makes it easy).
Then you can import the module in a script or call a `create()` in the `setup()` and a `delete()` in the `teardown()`
of a test.

***

### Selectors

The most difficult element of testing is writing robust selectors. Brittle selectors can break whenever slight
changes occur in the DOM. Selectors should be:

* Unique
* Descriptive
* Short

CSS selectors are preferred over XPath. They are faster (especially in IE) and more readable. Here's a
[blog post and video](http://sauceio.com/index.php/2011/05/why-css-locators-are-the-way-to-go-vs-xpath/) from
Santi of Sauce Labs about the advantages of CSS selectors. Not covered in Santi's post is the javascript-xpath
library, which should yield significantly better XPath performance.
This tip came from Dr. Wenhua Wang. You should be able to find his presentation with details on javascript-xpath
at his [Meetup event page](http://www.meetup.com/seleniumsanfrancisco/events/101087592/).

Here's a quick guide to targeting elements using `find_element_by_css_selector()`:

Target | Selector example
--- |:---
Tag | div
Direct child | table > tr
Child or subchild | table td 
Id | #my_id
Class | .myclass
Attribute | [name=my_name]
Chained Locators | a.my_class#my_id[name=my_name]

And here's a [comparison of CSS and XPath syntax](http://ejohn.org/blog/xpath-css-selectors/) from John Resig.
Targeting sibling or parent elements are two situations where you cannot use CSS and need to use XPath.

##### Retrofitting selectors

Ideally, every element in the DOM will have a selector that meets the criteria stated above. Unfortunately, that
is almost never the case. Retrofitting selectors can be a problem, particularly if functionality of the site depends
on id or name attributes that cannot be modified.

Fortunately, HTML5 allows for [custom data attributes](http://html5doctor.com/html5-custom-data-attributes/).
These are attributes beginning with `data-` that are valid HTML and can be leveraged as locators. For example,
you might give your otherwise unlocatable element a 'data-selenium' attribute:

    :::html
    <!--Before-->
    <a href="/dynamic_path" class="generic" id="random_secure">Marketing's Text</a>
    
    <!--After-->
    <a href="/dynamic_path" class="generic" id="random_secure" data-selenium="the_link">Marketing's Text</a>
    
Now we can locate the element using the following CSS locator: `[data-selenium=the_link]`.

I have experimented with a script that automatically adds a random 6 hex digit `data-*` attribute to certain elements in
all HTML files passed to it.
The first iteration parsed the HTML using Python's lxml module and added the attributes,
but I found that it changed the HTML unexpectedly, mainly due to bugs in the HTML itself.
The second iteration just uses regular expressions, but in general that's a
[bad idea](http://stackoverflow.com/questions/1732348/regex-match-open-tags-except-xhtml-self-contained-tags).
The other issue is that this method cannot account for elements that are dynamically generated by application code.

A key aspect of testing is having a testable application. It is important to have a strategy for tagging elements during
development so that they can be located easily and elegantly. Try to document a strategy and get buy-in
from other developers.

***

### Headless testing

The [`PyVirtualDisplay`](https://pypi.python.org/pypi/PyVirtualDisplay)
module allows you to wrap your program in `Xvfb` (a virtual X display). This is useful for running tests on your
CI server (without Sauce), or locally if you don't want a ton of browser windows taking over your display. See
[this post](http://coreygoldberg.blogspot.com/2011/06/python-headless-selenium-webdriver.html)
from Corey Goldberg for more details, then add it to your test runner.

***

### Complex input actions

[Action chains](http://selenium-python.readthedocs.org/en/latest/api.html#module-selenium.webdriver.common.action_chains)
allow you to do complex input manipulation.

Here's an example of a hover or mouseover method for the abstract test case:

    :::python
    from selenium.webdriver.common.action_chains import ActionChains
    
    def hover(self, element):
        ActionChains(self.driver).move_to_element(element).perform()

***

### Handling multiple windows

Here's a method you may want to add to the abstract test case
if your application has popups or multiple windows/tabs.

    :::python
    import time   
        
    def find_window(self, title):
        start = time.time()
        while (time.time() - start) <= config['timeout']:
            for window_handle in self.driver.window_handles:
                self.driver.switch_to_window(window_handle)
                if self.driver.title == title:
                    return True
            time.sleep(0.5)
        
        raise Exception("Could not find window '%s'" % title)

***

### Cookie injection

Cookie injection is easy until you try to do it cross-browser. I highly recommend avoiding it altogether.
In my case, I had a developer create a secret page for me that allowed me to add a cookie to prevent a
first-use prompt from appearing. To add the cookie, just navigate to the page using
`self.get_path('/secret_page')` and click the provided button.

***

#### JavaSript execution

[`execute_script()`](http://selenium-python.readthedocs.org/en/latest/api.html#selenium.webdriver.remote.webdriver.WebDriver.execute_script)
is useful for interacting with JavaScript and the browser, particularly libraries like jQuery. Lot of cross-browser
issues can be remedied by using jQuery. If you abstract driver methods into test case methods, it is very
easy to try out different interaction strategies. You could probably rebuild the entire selenium API using jQuery and
`execute_script()`.

***

### Debugging

The [pdb plugin](http://nose.readthedocs.org/en/latest/plugins/debug.html) for nose can be used to drop into the Python
debugger on test failures. The DOM and browser remain available in the failed state for analysis using the
browser or Selenium bindings.

***

### Documentation

Developers can understand and fix tests more easily if they are documented.
Non-developers should be aware of what is being tested and how.

Here's an example of a documented test:

    :::python
    import uuid
    
    def test_user_creation(self):
        """
        Author: Mr. Developer
        Description: Create a user
        """
        
        # step: Get user creation page
        self.get_path('/create_user')
        
        # step: Fill in username with a random UUID
        self.driver.find_element_by_id('username').send_keys(uuid.uuid4())
        
        # step: Fill in password
        self.driver.find_element_by_id('password').send_keys('letmein')
        
        # step: Click create user button
        self.driver.find_element_by_id('create_user_btn').click()
        
        # assert: Success message is displayed
        assert 'Success' in self.find_element_by_id('status_message').text

Now, let's say every single test is documented using this same format. It is relatively easy to write a parser
using [tokenize](http://docs.python.org/2/library/tokenize.html) that can generate a CSV spreadsheet
documenting the entire test suite. No more spreadsheet rot. See
[generate_summary.py](https://github.com/danielhochman/basic_selenium_framework/blob/master/basic_selenium_framework/generate_summary.py).


Conversely, you could also generate code stubs from a spreadsheet that non-developers use to request new tests.

Note: by default, the first line of a method's docstring are used to name the tests in verbose mode. The
[ignore-docstring](https://pypi.python.org/pypi/nose-ignore-docstring) plugin allows you to override
this behavior.

***

### Where to put the suite

Early on in my framework, when it was in a state of constant flux, I did not want to put it in the application
repository. This was a mistake. Tests should live with the code. Using a commit log, you can easily check and
see what code came in with tests. Tests with code also allows you to easily roll back the clock to an older commit to
view the behavior of a test that was passing but is now failing.

***

### Coverage

There is always a question of how much to test on the front-end. Despite the power and flexibility of Selenium,
I think it's important to stay as close to the metal as possible. If Selenium tests are written with the goal of 
providing significant coverage, the resulting suite will be brittle.
Unit testing should be the primary source of coverage.

An additional strategy is to appoint someone to decide where tests for newly discovered bugs should be written.
Closing out a bug should require that a test exists somewhere for the bug.

***

### Other potential features

These are features I have considered and think are valuable,
but have not had the time or need to implement for my use case.

[Page Object Model](http://pragprog.com/magazines/2010-08/page-objects-in-python)
- A page object model allows you to maintain selectors and page actions in one place rather than individual tests.

Performance testing - Write a script to stand up a large number of remote webdrivers in the cloud
and have the framework run the same test or a group of tests repeatedly against the application.

Re-run failed tests - Tests fail because of environment wobble. It happens. It would be nice to re-run the tests that
failed so that testing during build is more robust and less time consuming.

***

### Help!

Ask a question on the [user group](https://groups.google.com/forum/#!forum/selenium-users),
in the IRC channel (#selenium on Freenode),
or attend a [Meetup](http://selenium.meetup.com/).

All of the above resources were invaluable to me when learning about Selenium,
as well as developing and debugging my framework.
