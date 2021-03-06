# Create your views here.

from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.urls import reverse
from itertools import chain
import subprocess, re, os.path, pathlib, random, string
from pathlib import Path

from .forms import SubmitForm
from django.views.decorators.csrf import csrf_exempt

def index(request):
    page_title = "WebImblaze Server"
    page_heading = "WebImblaze Server"
    error = ''

    context = {
        'page_title': page_title,
        'page_heading': page_heading,
        'error': error,
    }
    
    return render(request, 'server/index.html', context)

def run(request):
    path = _normalise_path( substitute_star_with_slash( request.GET.get('path', None) ) )
    batch = request.GET.get('batch', None)
    target = request.GET.get('target', None)

    #print ('Started existing test execution:', path)
    result_stdout = run_wif_for_test_file_at_path(path, batch, target)
    #print ('result_stdout:', result_stdout)
    #print ('Finished existing test execution:', path)

    http_status, result_status, result_status_message = get_status(result_stdout)
    result_link = get_result_link(result_stdout)
    options = get_options_summary(batch, target)

    page_title = path
    page_heading = 'Run existing test: ' + path
    error = ''

    context = {
        'page_title': page_title,
        'page_heading': page_heading,
        'result_stdout': result_stdout,
        'result_status': result_status,
        'result_status_message': result_status_message,
        'result_link': result_link,
        'options': options,
        'error': error,
    }
    
    return render(request, 'server/run.html', context, status=http_status)

def _normalise_path( relative_path ):
    script_path = os.path.dirname( os.path.realpath(__file__) )
    path_for_test_steps_if_is_in_this_project = script_path + '/../../' + relative_path
    if ( os.path.isfile(path_for_test_steps_if_is_in_this_project) ):
        return path_for_test_steps_if_is_in_this_project
    else:
        return relative_path # let wif.pl try and find the test script

def substitute_star_with_slash(path):
    return path.replace('*','/')

def get_result_link(result_stdout):
    m = re.search(r'Result at: ([^\s]*)', result_stdout)
    if (m):
        return m.group(1)
    else:
        return '/DEV/Summary.xml'

def get_options_summary(batch, target):

    # this is to prevent a leading space if we have a Target but no Batch
    options_summary = formattedStringBuilder(next_prefix=' ', glue=' [', suffix=']')
    options_summary.append_non_blank_value(batch, 'Batch')
    options_summary.append_non_blank_value(target, 'Target')

    return options_summary.summary

def get_status(result_stdout):
    if ( re.search(r'(Test Steps Failed: 0)', result_stdout) ):
        return 200, 'pass', 'WEBIMBLAZE TEST PASSED'
    if ( re.search(r'(Test Steps Failed: [1-9])', result_stdout) ):
        return 200, 'fail', 'WEBIMBLAZE TEST FAILED'
    return 500, 'error', 'WEBIMBLAZE TEST ERROR'

def run_wif_for_test_file_at_path(path, batch, target):
    cmd = get_wif_command(path, batch, target)
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE)
    output, errors = proc.communicate()
    decoded = output.decode('cp850') # western european Windows code page is cp850
    return decoded

def get_wif_command(path, batch, target):

    if (not batch):
        batch = 'WebImblaze-Server'

    if (not target):
        target = 'default'

    return ['perl', wif_location(), path, '--env', 'DEV', '--target', target, '--batch', batch, '--no-update-config', '--headless']

def wif_location():

    if os.name == 'nt':
        return wif_location_windows()

    return wif_location_linux()

def wif_location_linux():

    locations = []
    locations.append(r'/usr/local/bin/WebImblaze-Framework')
    for l in locations:
        if ( os.path.isfile(l+r'/wif.pl') ):
            return l+r'/wif.pl'
    return ('WebImblaze Framework wif.pl file not found - suggest deploying to /usr/local/bin/WebImblaze-Framework \n\n')

def wif_location_windows():

    locations = []
    locations.append(r'D:\WebImblazeSERVER')
    locations.append(r'C:\WebImblazeSERVER')
    locations.append(r'C:\git\WebImblaze-Framework')
    locations.append(r'C:\WebImblaze')
    locations.append(r'D:\WebImblaze')
    locations.append(r'C:\WebImblaze-Framework')
    locations.append(r'C:\WebInject')
    locations.append(r'D:\WebInject')
    for l in locations:
        if ( os.path.isfile(l+r'\wif.pl') ):
            return l+r'\wif.pl'
    return ('WebImblaze Framework wif.pl file not found - suggest deploying to C:\\WebImblazeSERVER\\wif.pl \n\n')

@csrf_exempt
def submit(request):
    if request.method == 'POST':
        return _process_submit(request)
    else:
        form = SubmitForm()

    batch = request.GET.get('batch', None)
    target = request.GET.get('target', None)
    page_title = 'Submit'
    page_heading = 'Submit test for immediate run'
    query_string = get_query_string(batch, target)

    context = {
        'page_title': page_title,
        'page_heading': page_heading,
        'batch': batch,
        'target': target,
        'query_string': query_string,
        'form': form,
    }

    return render(request, 'server/submit.html', context)

def get_query_string(batch, target):

    # this is to prevent a leading space if we have a Target but no Batch
    query_string = formattedStringBuilder(initial_prefix='?', next_prefix='&', glue='=')
    query_string.append_non_blank_value(batch, 'batch')
    query_string.append_non_blank_value(target, 'target')

    return query_string.summary

class formattedStringBuilder:

    already_appended_item = False
    summary = ''

    initial_prefix=''
    next_prefix=''
    glue=''
    suffix=''
    
    def __init__(self, initial_prefix='', next_prefix='', glue='', suffix=''):
        self.already_appended_item = False
        self.summary = ''
        
        self.initial_prefix=initial_prefix
        self.next_prefix=next_prefix
        self.glue=glue
        self.suffix=suffix

    def append_non_blank_value(self, value, desc):
        if (not value):
            return
        if (self.already_appended_item):
            self.summary += self.next_prefix + self.formatted(value, desc)
            return 
        else:
            self.already_appended_item = True
            self.summary += self.initial_prefix + self.formatted(value, desc)
            return

    def formatted(self, value, desc):
        return desc + self.glue + value + self.suffix


def _process_submit(request):
    steps = request.POST.get('steps', None)
    batch = request.GET.get('batch', None)
    target = request.GET.get('target', None)
    name = request.GET.get('name', None)

    path = _write_steps_to_file_in_temp_folder(steps, name)

    #print ('Started submitted test execution:', path)
    result_stdout = run_wif_for_test_file_at_path(path, batch, target)
    #print ('Finished submitted test execution:', path)

    _remove_random_test_step_file_ignoring_os_errors(path)

    http_status, result_status, result_status_message = get_status(result_stdout)
    result_link = get_result_link(result_stdout)
    options = get_options_summary(batch, target)

    page_title = 'Result'
    page_heading = 'Run submitted test ' + os.path.basename(path)
    error = ''

    context = {
        'page_title': page_title,
        'page_heading': page_heading,
        'result_stdout': result_stdout,
        'result_status': result_status,
        'result_status_message': result_status_message,
        'result_link': result_link,
        'options': options,
        'error': error,
    }

    return render(request, 'server/run.html', context, status=http_status)

def _write_steps_to_file_in_temp_folder(steps, name):

    temp_file_name = ''.join(random.sample(string.ascii_uppercase + string.digits, k=5)) + '.test'
    if name != None:
        temp_file_name = name + '.test'

    temp_folder_path = _get_temp_folder_location_and_ensure_exists()
    temp_file_path = temp_folder_path + '/' + temp_file_name

    with open(temp_file_path, 'w') as f:
        f.write(steps)
    return temp_file_path

def _get_temp_folder_location_and_ensure_exists():
    script_path = os.path.dirname(os.path.realpath(__file__))
    temp_folder_path = script_path + '/../../temp/webimblaze-server'
    pathlib.Path(temp_folder_path).mkdir(parents=True, exist_ok=True)
    return temp_folder_path

def _remove_random_test_step_file_ignoring_os_errors(file_path):
    try:
        os.remove(file_path)
    except OSError:
        pass

def canary(request):

    tracker = canaryStatus()
    tracker.append( *_canary_wif_location() ) 

    if (tracker.canary_checks_passed):
        tracker.append( *_canary_wif_can_be_executed() )
        tracker.append( *_canary_dev_environment_config() )
        tracker.append( *_canary_default_config() )
        tracker.append( *_canary_wif_config() )
        if (tracker.canary_checks_passed):
            tracker.append( *_canary_webimblaze_can_be_executed() )
            

    result_status = 'pass'
    http_status = 200
    result_status_message = 'All canary checks passed'
    if (not tracker.canary_checks_passed):
        result_status = 'fail'
        http_status = 500
        result_status_message = 'Canary checks failed'

    page_title = 'Canary'
    page_heading = 'WebImblaze Server Canary'

    context = {
        'page_title': page_title,
        'page_heading': page_heading,
        'result_status': result_status,
        'result_status_message': result_status_message,
        'all_canary_check_results': tracker.summary(),
    }

    return render(request, 'server/canary.html', context, status=http_status)

class canaryStatus:

    canary_checks_passed = True
    canary_checks_count = 0
    canary_summary = None

    def __init__(self):
        self.canary_checks_passed = True
        self.canary_checks_count = 0
        self.canary_summary = formattedStringBuilder(initial_prefix='<p class="', next_prefix='<p class="', glue='">', suffix='</p>')

    def append(self, message, check_passed):

        self.canary_checks_count += 1

        if (check_passed):
            status = 'pass'
        else:
            status = 'fail'
            self.canary_checks_passed = False

        self.canary_summary.append_non_blank_value(message, status)
        # Example append string:  <p class="pass">WebImblaze Framework found at ...</p>
    
    def summary(self):
        return self.canary_summary.summary

def _canary_wif_location():

    if 'not found' in wif_location():
         return wif_location(), False
    else:
         return 'OK --&gt; WebImblaze Framework found at ' + wif_location(), True

def _canary_wif_can_be_executed():

    wif_cmd = ['perl', wif_location(), '--help']
    proc = subprocess.Popen(wif_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE)
    output, errors = proc.communicate()
    decoded = output.decode('cp850') # western european Windows code page is cp850

    if 'Usage: perl wif.pl' in decoded:
        return 'OK --&gt; wif.pl can be executed - shows help info', True
    else:
        return 'Could not execute wif.pl to view help', False

def _canary_dev_environment_config():

    wif_root, wif_script = os.path.split( wif_location() )
    root_dev_config = wif_root + '/environment_config/DEV.config'
    team_dev_config = wif_root + '/environment_config/DEV'
    if ( os.path.isfile(root_dev_config) and
         os.path.isdir(team_dev_config)
        ):
        return 'OK --&gt; DEV environment config found [' + root_dev_config + ' and folder ' + team_dev_config + ']', True
    else:
        return 'Could not find both ' + root_dev_config + ' and folder ' + team_dev_config, False

def _canary_default_config():

    wif_root, wif_script = os.path.split( wif_location() )
    dev_default_config = wif_root + '/environment_config/DEV/default.config'
    if ( os.path.isfile(dev_default_config) ):
        return 'OK --&gt; DEV default config found at ' + dev_default_config, True
    else:
        return 'Could not find DEV default config file ' + dev_default_config, False

def _canary_wif_config():

    wif_root, wif_script = os.path.split( wif_location() )
    wif_config = wif_root + '/wif.config'
    if ( os.path.isfile(wif_config) ):
        return 'OK --&gt; wif.config found at ' + wif_config, True
    else:
        return 'Could not find wif.config file at ' + wif_config, False

def _canary_webimblaze_can_be_executed():
    
    script_path = os.path.dirname(os.path.realpath(__file__))
    test_path = script_path + '/../../tests/check.test'
    result = run_wif_for_test_file_at_path(test_path, 'WebImblaze-Server-Canary', 'default')

    if 'Test Steps Failed: 0' in result and 'Result at: http' in result:
        return 'OK --&gt; WebImblaze Framework can run wi.pl and store result', True
    else:
        return 'WebImblaze Framework could not run wi.pl and store result<br /><br /><pre><code>' + result + '</code></pre>', False
