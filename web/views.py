import github
from django.shortcuts import render, redirect
from django.conf import settings

if settings.DEBUG:
    github.enable_console_debug_logging()

class GithubWrapper(object):
    def __init__(self, request):
        self.gh = github.Github(
            login_or_token=request.user.social_auth.get().access_token,
            api_preview=True,  # so /user/repos returns repos in
                               # organizations as well.
        )

    def user(self):
        return self.gh.get_user()

    def repo(self, repo):
        return self.gh.get_repo(repo)

def index(request):
    return render(request, 'index.html', {})

def loginerror(request):
    return render(request, 'loginerror.html', {})

def pick(request):
    gh = GithubWrapper(request)
    repos = gh.user().get_repos()
    return render(request, 'pick.html', {
        'repos': repos,
    })

def board(request, full_repo_name):
    gh = GithubWrapper(request)
    issues = gh.repo(full_repo_name).get_issues()
    return render(request, 'board.html', {
        'repo': full_repo_name,
        'issues': issues,
    })

def issue(request, full_repo_name, issue_id):
    issue_id = int(issue_id)
    gh = GithubWrapper(request)
    issue = gh.repo(full_repo_name).get_issue(issue_id)
    return render(request, 'issue.html', {
        'repo': full_repo_name,
        'issue_id': issue_id,
        'issue': issue,
    })

JUCY_LABEL_NAMESPACE = 'jucy'
JUCY_LABELS = {
    'feedback': '00ff55',
    'issue': 'ff0000',
}

def prepare_repo_for_jucy(request, full_repo_name):
    """Prepares a Github repo to support Jucy issues.

    This creates Jucy labels and grants Jucybot access to the
    repository.

    This function is safe to call on a repo that has already been
    initialized for Jucy. In particular, as "initializes a repo for
    Jucy" expands in scope (adding new tags, for instance), it is
    important to be able to call this function on an already partially
    initialized repo to complete the initialization. This does not
    include cleaning up leftovers from previous initialization
    scenarios: this should be done in another function.

    Args:
      request: HTTP request
      full_repo_name: name of the repo to be initialized.
    Returns:
      302 to the board for that repo.

    """
    gh = GithubWrapper(request)
    repo = gh.repo(full_repo_name)
    for label, color in JUCY_LABELS.iteritems():
        try:
            repo.create_label('%s:%s' % (JUCY_LABEL_NAMESPACE, label), color)
        except github.GithubException, e:
            # 422: Label already exists, that's OK.
            if e.status != 422:
                raise e
    # TODO(korfuri): Grant @JucyBot access to the repository.
    return redirect('/%s' % full_repo_name)
