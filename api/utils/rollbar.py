import rollbar, os
ROLLBAR_POST_ACCESS_TOKEN = os.environ.get('ROLLBAR_POST_ACCESS_TOKEN')

# rollbar.init(ROLLBAR_ACCESS_TOKEN)
# rollbar.report_message('Rollbar is configured correctly')