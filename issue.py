from collections import Counter
import re
import datetime


class Issue:
    mongo = None
    status_open = 'Open'
    status_resolved = 'Resolved'
    status_closed = 'Closed'
    type_missing_alt_text = 'Missing Alt Text'
    type_unhelpful_alt_text = 'Unhelpful Alt Text'
    type_other = 'Other'
    var_names =  ['page_url', 'img_url', 'type', 'creator', 'description', 'status', 'img_current_alt_text', 'img_suggested_alt_text']
    
    @staticmethod
    def add_or_update_issue(reporter_user_id, issue):
        issue = Issue.determine_issue_type_and_status(issue)

        if reporter_user_id is None:
            reporter_user_id = 'Unknown'
        n_issue = Issue.mongo.db.issues.find_one({'img_url': issue['img_url'], 'page_url': issue['page_url']})    
        if n_issue is None:
            n_issue = {"img_url": issue['img_url'], \
                        "page_url": issue['page_url'], \
                        "created_on": datetime.datetime.utcnow(), \
                        "img_original_alt_text": issue['img_current_alt_text'], \
                        "creator": reporter_user_id, \
                        "reporters": []}
        n_issue['img_current_alt_text'] = issue['img_current_alt_text']
        n_issue['img_suggested_alt_text'] = issue['img_suggested_alt_text']
        n_issue['description'] = issue['description']
        n_issue['type'] = issue['type']
        n_issue['status'] = issue['status']

        # add reporter_id frequencies
        n_issue['reporters'] = {k:v for (k, v) in (Counter(n_issue['reporters']) + Counter({reporter_user_id:1})).iteritems()}

        n_issue['updated_on'] = datetime.datetime.utcnow()

        Issue.mongo.db.issues.update({'img_url': issue['img_url'], 'page_url': issue['page_url']}, n_issue, True)
        n_issue = Issue.mongo.db.issues.find_one({'img_url': n_issue['img_url'], 'page_url': n_issue['page_url']})    
        return n_issue
    
    @staticmethod    
    def determine_issue_type_and_status(issue):
        issue['type'] = issue['type'].strip()
        issue['description'] = issue['description'].strip()

        cur_alt_text = issue['img_current_alt_text'].strip()
        unhelpful_alt_text = ['image', 'picture', 'photo', 'photograph']

        if cur_alt_text == '':
            issue['type'] = Issue.type_missing_alt_text
            issue['status'] = Issue.status_open
        elif issue['type'] == Issue.type_missing_alt_text:
            issue['status'] = Issue.status_resolved

        if (cur_alt_text.lower() in unhelpful_alt_text) or re.match(r"^\S+\.\S+$", cur_alt_text):
            # alt text is unhelpful because it matches a blacklist term or it is a filename
            issue['description'] = "Unhelpful Alt Text"
            issue['status'] = Issue.status_open
        elif issue['type'] == Issue.type_unhelpful_alt_text:
            issue['status'] = Issue.status_resolved

        if issue['type'] == Issue.type_other and issue['description'] == '':
            # close the issue if there was not description of it
            issue['status'] = Issue.status_closed

        return issue
    
    @staticmethod
    def get_issues_by_params(params=None):
        if params is None:
            issues = Issue.mongo.db.issues.find().sort([("created_on", -1)])
        else:
            issues = Issue.mongo.db.issues.find(params)
        issues = list(issues) # make sure it is reiterable   
        return issues
    
    @staticmethod
    def get_issues_by_user(user=None):
        if user is None:
            return None
        else:
            # https://stackoverflow.com/questions/10242149/sorting-with-mongodb-and-python
            issues = Issue.mongo.db.issues.find({('reporters.' + str(user['_id'])) : {'$exists': True}}).sort([("created_on", -1)])
            issues = list(issues) # make sure it is reiterable   
            return issues